from datetime import datetime, timedelta, timezone

from lib import selection
from lib.constants import TIMETABLE_EARLY_WEIGHTS, TIMETABLE_LATE_WEIGHTS

NOW = datetime(2026, 8, 1, tzinfo=timezone.utc)


# --- overdue_norm ------------------------------------------------------------

def test_overdue_norm_never_scheduled_is_fully_overdue():
    assert selection.overdue_norm(None, NOW) == 1.0


def test_overdue_norm_not_yet_due():
    future = NOW + timedelta(days=2)
    assert selection.overdue_norm(future, NOW) == 0.0


def test_overdue_norm_partial():
    past = NOW - timedelta(days=3.5)
    assert selection.overdue_norm(past, NOW) == 0.5


def test_overdue_norm_capped_at_1():
    past = NOW - timedelta(days=30)
    assert selection.overdue_norm(past, NOW) == 1.0


# --- coverage_gap ------------------------------------------------------------

def test_coverage_gap_never_attempted():
    assert selection.coverage_gap(0) == 1.0


def test_coverage_gap_decays():
    assert selection.coverage_gap(5) == 0.0


def test_coverage_gap_floored_at_0():
    assert selection.coverage_gap(10) == 0.0


# --- exam_weight_norm ---------------------------------------------------------

def test_exam_weight_norm_basic():
    assert selection.exam_weight_norm(1.5, 2.0) == 0.75


def test_exam_weight_norm_no_candidates():
    assert selection.exam_weight_norm(1.5, 0) == 0.0


# --- timetable_weights (interpolation) ----------------------------------------

def test_timetable_weights_no_exam_date_is_fully_early():
    assert selection.timetable_weights(None) == TIMETABLE_EARLY_WEIGHTS


def test_timetable_weights_exam_today_is_fully_late():
    result = selection.timetable_weights(0)
    for key in TIMETABLE_LATE_WEIGHTS:
        assert abs(result[key] - TIMETABLE_LATE_WEIGHTS[key]) < 1e-9


def test_timetable_weights_far_out_is_fully_early():
    result = selection.timetable_weights(9999)
    for key in TIMETABLE_EARLY_WEIGHTS:
        assert abs(result[key] - TIMETABLE_EARLY_WEIGHTS[key]) < 1e-9


def test_timetable_weights_midpoint_is_halfway():
    from lib.constants import TIMETABLE_INTERPOLATION_WINDOW_DAYS

    result = selection.timetable_weights(TIMETABLE_INTERPOLATION_WINDOW_DAYS / 2)
    for key in TIMETABLE_EARLY_WEIGHTS:
        expected = (TIMETABLE_EARLY_WEIGHTS[key] + TIMETABLE_LATE_WEIGHTS[key]) / 2
        assert abs(result[key] - expected) < 1e-9


# --- compute_priority ----------------------------------------------------------

def test_compute_priority_formula():
    topic = {"next_due_at": NOW - timedelta(days=3.5), "ability": 40, "attempts_count": 0, "exam_weight": 1.5}
    weights = {"overdue_norm": 0.40, "ability_gap": 0.30, "coverage_gap": 0.15, "exam_weight_norm": 0.10, "random": 0.05}
    result = selection.compute_priority(topic, NOW, weights, max_exam_weight=1.5, random_component=1.0)
    expected = 0.40 * 0.5 + 0.30 * 0.6 + 0.15 * 1.0 + 0.10 * 1.0 + 0.05 * 1.0
    assert abs(result - expected) < 1e-9


# --- select_session_topics: area-level interleaving ---------------------------

def _topic(id_, area_id, priority, days_since_seen=None):
    return {"id": id_, "area_id": area_id, "priority": priority, "days_since_seen": days_since_seen}


def test_no_more_than_two_consecutive_same_area_when_alternative_exists():
    topics = [
        _topic("a1", "A", 0.9),
        _topic("a2", "A", 0.8),
        _topic("a3", "A", 0.7),
        _topic("b1", "B", 0.6),
    ]
    selected = selection.select_session_topics(topics, session_length=4)
    area_sequence = [t["area_id"] for t in selected]
    # a1, a2 (2 in a row is fine), then must break before a3
    assert area_sequence[0] == "A"
    assert area_sequence[1] == "A"
    assert area_sequence[2] != "A"


def test_area_cap_relaxes_when_no_alternative_exists():
    topics = [_topic(f"a{i}", "A", 1.0 - i * 0.01) for i in range(5)]
    selected = selection.select_session_topics(topics, session_length=5)
    assert len(selected) == 5  # still fills the session even though every topic is area A


# --- select_session_topics: neglect guarantee ---------------------------------

def test_neglected_topic_is_guaranteed_a_slot():
    # Four distinct areas so the area-interleaving cap never kicks in --
    # this isolates the neglect guarantee itself, rather than having it be
    # incidentally satisfied by the area cap forcing a switch.
    topics = [
        _topic("a1", "A", 0.9),
        _topic("b1", "B", 0.8),
        _topic("c1", "C", 0.7),
        _topic("neglected", "D", 0.1, days_since_seen=20),
    ]
    selected = selection.select_session_topics(topics, session_length=3)
    assert any(t["id"] == "neglected" for t in selected)


def test_no_neglected_topic_no_forced_swap():
    topics = [_topic("a1", "A", 0.9, days_since_seen=1), _topic("a2", "B", 0.8, days_since_seen=2)]
    selected = selection.select_session_topics(topics, session_length=2)
    assert {t["id"] for t in selected} == {"a1", "a2"}


# --- select_session_topics: area spread for large sessions ---------------------

def test_large_session_touches_at_least_three_areas():
    topics = (
        [_topic(f"a{i}", "A", 0.9 - i * 0.01) for i in range(6)]
        + [_topic("b1", "B", 0.3)]
        + [_topic("c1", "C", 0.2)]
    )
    selected = selection.select_session_topics(topics, session_length=8)
    assert len(selected) == 8
    assert len({t["area_id"] for t in selected}) >= 3


# --- pick_subtopic_for_topic -----------------------------------------------------

def test_pick_subtopic_for_topic_picks_least_attempted():
    subtopics = [
        {"id": "s1", "attempts_count": 3},
        {"id": "s2", "attempts_count": 0},
        {"id": "s3", "attempts_count": 1},
    ]
    assert selection.pick_subtopic_for_topic(subtopics)["id"] == "s2"


# --- select_progress_test_topics ---------------------------------------------

def _topics(counts: dict) -> list[dict]:
    return [{"id": f"{area}{i}", "area_id": area} for area, n in counts.items() for i in range(n)]


def test_progress_test_covers_every_area_before_repeating():
    import random

    picked = selection.select_progress_test_topics(_topics({"a": 5, "b": 5, "c": 5}), 3, random.Random(1))
    assert {t["area_id"] for t in picked} == {"a", "b", "c"}


def test_progress_test_uses_each_topic_once():
    import random

    picked = selection.select_progress_test_topics(_topics({"a": 3, "b": 1}), 10, random.Random(1))
    assert len(picked) == 4
    assert len({t["id"] for t in picked}) == 4
