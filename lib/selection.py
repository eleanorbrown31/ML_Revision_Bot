"""Question/topic selection: priority scoring, timetable-pressure weighting,
and interleaving constraints (spec §4).

Pure functions -- callers pass in already-fetched data (mastery rows, "now",
days_since_seen, etc). Interleaving constraints are reinterpreted at
topic-level mastery, per the build plan:
  - "no 2 consecutive same topic"        -> no 2 consecutive same *area*
  - "≥8 questions touch ≥3 areas"        -> unchanged (already area-level)
  - "subtopic unseen >14 days" guarantee -> "topic unseen >14 days"
"""

from lib.constants import (
    ABILITY_MAX,
    COVERAGE_GAP_DECAY_ATTEMPTS,
    DEFAULT_SESSION_LENGTH,
    MAX_CONSECUTIVE_SAME_AREA,
    MIN_AREAS_IN_LARGE_SESSION,
    MIN_SESSION_LENGTH_FOR_AREA_SPREAD,
    NEGLECT_DAYS_THRESHOLD,
    OVERDUE_NORM_DAYS_CAP,
    PRIORITY_WEIGHT_ABILITY,
    PRIORITY_WEIGHT_COVERAGE_GAP,
    PRIORITY_WEIGHT_EXAM_WEIGHT,
    PRIORITY_WEIGHT_OVERDUE,
    PRIORITY_WEIGHT_RANDOM,
    TIMETABLE_EARLY_WEIGHTS,
    TIMETABLE_INTERPOLATION_WINDOW_DAYS,
    TIMETABLE_LATE_WEIGHTS,
)

DEFAULT_PRIORITY_WEIGHTS = {
    "overdue_norm": PRIORITY_WEIGHT_OVERDUE,
    "ability_gap": PRIORITY_WEIGHT_ABILITY,
    "coverage_gap": PRIORITY_WEIGHT_COVERAGE_GAP,
    "exam_weight_norm": PRIORITY_WEIGHT_EXAM_WEIGHT,
    "random": PRIORITY_WEIGHT_RANDOM,
}


def overdue_norm(next_due_at, now) -> float:
    """Days past due / 7, capped at 1. Never-scheduled topics are treated as
    fully overdue."""
    if next_due_at is None:
        return 1.0
    days_overdue = (now - next_due_at).total_seconds() / 86400
    if days_overdue <= 0:
        return 0.0
    return min(days_overdue / OVERDUE_NORM_DAYS_CAP, 1.0)


def coverage_gap(attempts_count: int) -> float:
    """1 if never attempted, decaying with attempts (spec gives no formula;
    see build plan's open flags for this choice)."""
    return max(0.0, 1 - attempts_count / COVERAGE_GAP_DECAY_ATTEMPTS)


def exam_weight_norm(exam_weight: float, max_exam_weight: float) -> float:
    if max_exam_weight <= 0:
        return 0.0
    return min(exam_weight / max_exam_weight, 1.0)


def timetable_weights(days_to_exam: float | None) -> dict:
    """Interpolate between an early/breadth-first weight vector and a
    late/shore-up-weak-spots vector. days_to_exam=None (no exam date set)
    is treated as "far away" -> fully early weights."""
    if days_to_exam is None:
        t = 0.0
    else:
        days_to_exam = max(days_to_exam, 0)
        t = 1 - min(days_to_exam, TIMETABLE_INTERPOLATION_WINDOW_DAYS) / TIMETABLE_INTERPOLATION_WINDOW_DAYS

    return {
        key: TIMETABLE_EARLY_WEIGHTS[key] + t * (TIMETABLE_LATE_WEIGHTS[key] - TIMETABLE_EARLY_WEIGHTS[key])
        for key in TIMETABLE_EARLY_WEIGHTS
    }


def compute_priority(
    topic: dict,
    now,
    weights: dict,
    max_exam_weight: float,
    random_component: float = 0.0,
) -> float:
    """topic needs: next_due_at, ability, attempts_count, exam_weight."""
    overdue = overdue_norm(topic.get("next_due_at"), now)
    ability_gap_component = 1 - (topic.get("ability", 0) / ABILITY_MAX)
    coverage = coverage_gap(topic.get("attempts_count", 0))
    exam_component = exam_weight_norm(topic.get("exam_weight", 1.0), max_exam_weight)

    return (
        weights["overdue_norm"] * overdue
        + weights["ability_gap"] * ability_gap_component
        + weights["coverage_gap"] * coverage
        + weights["exam_weight_norm"] * exam_component
        + weights["random"] * random_component
    )


def select_session_topics(topics: list[dict], session_length: int = DEFAULT_SESSION_LENGTH) -> list[dict]:
    """Rank by 'priority' (already computed by the caller) and apply
    interleaving constraints. Each topic dict needs: id, area_id, priority,
    and optionally days_since_seen (for the neglect guarantee)."""
    ranked = sorted(topics, key=lambda t: t["priority"], reverse=True)
    remaining = list(ranked)
    selected: list[dict] = []
    area_streak = None
    streak_len = 0

    while remaining and len(selected) < session_length:
        pick_index = next(
            (i for i, c in enumerate(remaining) if not (c["area_id"] == area_streak and streak_len >= MAX_CONSECUTIVE_SAME_AREA)),
            0,  # no candidate satisfies the cap (every remaining topic is in the same area) -- relax it
        )
        candidate = remaining.pop(pick_index)
        selected.append(candidate)
        if candidate["area_id"] == area_streak:
            streak_len += 1
        else:
            area_streak = candidate["area_id"]
            streak_len = 1

    _ensure_neglected_topic_included(selected, ranked)
    _ensure_area_spread(selected, ranked)
    return selected


def _ensure_neglected_topic_included(selected: list[dict], ranked: list[dict]) -> None:
    neglected = [t for t in ranked if (t.get("days_since_seen") or 0) > NEGLECT_DAYS_THRESHOLD]
    if not neglected or not selected:
        return
    selected_ids = {s["id"] for s in selected}
    if any(t["id"] in selected_ids for t in neglected):
        return
    lowest_priority_index = min(range(len(selected)), key=lambda i: selected[i]["priority"])
    selected[lowest_priority_index] = neglected[0]


def _ensure_area_spread(selected: list[dict], ranked: list[dict]) -> None:
    if len(selected) < MIN_SESSION_LENGTH_FOR_AREA_SPREAD:
        return
    distinct_areas = {s["area_id"] for s in selected}
    if len(distinct_areas) >= MIN_AREAS_IN_LARGE_SESSION:
        return

    needed = MIN_AREAS_IN_LARGE_SESSION - len(distinct_areas)
    candidates = [t for t in ranked if t["area_id"] not in distinct_areas]
    for candidate in candidates[:needed]:
        selected.sort(key=lambda t: t["priority"])
        selected[0] = candidate
        distinct_areas.add(candidate["area_id"])
    selected.sort(key=lambda t: t["priority"], reverse=True)


def pick_subtopic_for_topic(subtopics: list[dict]) -> dict:
    """Least-attempted active subtopic under a topic, so every subtopic gets
    covered before any repeats -- fulfils the spec's stated rationale for
    subtopic being a coverage tag rather than its own mastery unit."""
    return min(subtopics, key=lambda s: s.get("attempts_count", 0))
