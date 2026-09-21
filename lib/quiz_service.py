"""Quiz orchestration -- the seam between the pure lib/ modules
(scoring, mastery, selection) and the lib/db/ repos.

Builds a session queue of (topic, subtopic, question) up front, then scores
and persists each answer as it's submitted, updating mastery/spaced
repetition along the way. This is also where a future v2 LLM-marking call
would slot in, without the quiz page needing to change.
"""

import json
import random
from datetime import datetime, timezone

import streamlit as st

from lib import mastery, scoring, selection
from lib.constants import DEFAULT_SESSION_LENGTH
from lib.db import (
    attempt_repo,
    config_repo,
    curriculum_repo,
    learning_note_repo,
    mastery_repo,
    question_repo,
    session_repo,
)

_STATE_KEY = "quiz_state"


def _now():
    return datetime.now(timezone.utc)


def _state() -> dict | None:
    return st.session_state.get(_STATE_KEY)


def has_active_questions() -> bool:
    return len(question_repo.topics_with_active_questions()) > 0


def has_active_session() -> bool:
    return _state() is not None


def _build_topic_candidates() -> list[dict]:
    servable_topic_ids = question_repo.topics_with_active_questions()
    topics = [t for t in mastery_repo.list_topics_for_scheduling() if t["id"] in servable_topic_ids]
    if not topics:
        return []

    now = _now()
    weights = selection.timetable_weights(config_repo.days_to_exam())
    max_exam_weight = max((t["exam_weight"] for t in topics), default=1.0)

    candidates = []
    for t in topics:
        days_since_seen = None
        if t["last_seen_at"]:
            days_since_seen = (now - t["last_seen_at"]).total_seconds() / 86400
        priority = selection.compute_priority(
            {
                "next_due_at": t["next_due_at"],
                "ability": t["ability"],
                "attempts_count": t["attempts_count"],
                "exam_weight": t["exam_weight"],
            },
            now,
            weights,
            max_exam_weight,
            random_component=random.random(),
        )
        candidates.append({**t, "priority": priority, "days_since_seen": days_since_seen})
    return candidates


def _build_multi_topic_queue(selected_topics: list[dict]) -> list[dict]:
    """One question per selected topic -- the "General ML" scheduler path.
    Fetches everything needed in a small, fixed number of bulk queries
    rather than one-topic-at-a-time (building a 10-question session used to
    mean ~50 separate DB round trips, which is what made "Start session"
    feel unresponsive)."""
    topic_ids = [t["id"] for t in selected_topics]

    active_questions = question_repo.list_active_questions_for_topics(topic_ids)
    questions_by_subtopic: dict[str, list[dict]] = {}
    for q in active_questions:
        questions_by_subtopic.setdefault(q["subtopic_id"], []).append(q)

    subtopics = curriculum_repo.list_subtopics_for_topics(topic_ids)
    subtopics_by_topic: dict[str, list[dict]] = {}
    for s in subtopics:
        if s["id"] in questions_by_subtopic:  # only subtopics that actually have servable content
            subtopics_by_topic.setdefault(s["topic_id"], []).append(s)

    subtopic_ids = list(questions_by_subtopic.keys())
    attempt_counts = attempt_repo.subtopic_attempt_counts(subtopic_ids)
    recent_by_subtopic = attempt_repo.recent_question_ids_bulk(subtopic_ids, limit=5)

    queue = []
    for topic in selected_topics:
        topic_subtopics = subtopics_by_topic.get(topic["id"])
        if not topic_subtopics:
            continue
        subtopics_with_counts = [
            {**s, "attempts_count": attempt_counts.get(s["id"], 0)} for s in topic_subtopics
        ]
        subtopic = selection.pick_subtopic_for_topic(subtopics_with_counts)

        available = questions_by_subtopic[subtopic["id"]]
        recent_ids = recent_by_subtopic.get(subtopic["id"], set())
        not_recent = [q for q in available if q["id"] not in recent_ids]
        question = random.choice(not_recent or available)

        queue.append({"topic": topic, "subtopic": subtopic, "question": question})
    return queue


def _build_single_topic_queue(topic_id: str, session_length: int) -> list[dict]:
    """session_length questions, all from one topic -- the "Practice this
    topic" path. Rotates through subtopics by least-attempted-first (updated
    locally each iteration) and avoids repeating a question already served
    earlier in this same session, on top of the usual recent-attempt avoidance."""
    topic = next((t for t in mastery_repo.list_topics_for_scheduling() if t["id"] == topic_id), None)
    if topic is None:
        return []

    active_questions = question_repo.list_active_questions_for_topics([topic_id])
    if not active_questions:
        return []

    questions_by_subtopic: dict[str, list[dict]] = {}
    for q in active_questions:
        questions_by_subtopic.setdefault(q["subtopic_id"], []).append(q)

    subtopics = [
        s for s in curriculum_repo.list_subtopics_for_topics([topic_id])
        if s["id"] in questions_by_subtopic
    ]
    if not subtopics:
        return []

    subtopic_ids = [s["id"] for s in subtopics]
    attempt_counts = dict(attempt_repo.subtopic_attempt_counts(subtopic_ids))
    recent_by_subtopic = attempt_repo.recent_question_ids_bulk(subtopic_ids, limit=5)

    queue = []
    used_question_ids: set[str] = set()
    for _ in range(session_length):
        subtopics_with_counts = [{**s, "attempts_count": attempt_counts.get(s["id"], 0)} for s in subtopics]
        subtopic = selection.pick_subtopic_for_topic(subtopics_with_counts)

        available = questions_by_subtopic[subtopic["id"]]
        recent_ids = recent_by_subtopic.get(subtopic["id"], set()) | used_question_ids
        not_recent = [q for q in available if q["id"] not in recent_ids]
        question = random.choice(not_recent or available)

        queue.append({"topic": topic, "subtopic": subtopic, "question": question})
        used_question_ids.add(question["id"])
        attempt_counts[subtopic["id"]] = attempt_counts.get(subtopic["id"], 0) + 1
    return queue


def _build_area_queue(area_id: str, session_length: int) -> list[dict]:
    """session_length questions drawn from every topic in one area -- the
    "Practice this area" path. An area (e.g. "Unsupervised Learning") is
    what users think of as "a topic to revise"; its topics (K-Means, DBSCAN,
    ...) are too thin on their own (a handful of questions each) to sustain
    a full session without repeating. Rotates across topics by
    least-attempted-first, same pattern as _build_single_topic_queue's
    subtopic rotation, one level up."""
    topics = [t for t in mastery_repo.list_topics_for_scheduling() if t["area_id"] == area_id]
    servable_topic_ids = question_repo.topics_with_active_questions()
    topics = [t for t in topics if t["id"] in servable_topic_ids]
    if not topics:
        return []

    topic_ids = [t["id"] for t in topics]
    active_questions = question_repo.list_active_questions_for_topics(topic_ids)
    questions_by_subtopic: dict[str, list[dict]] = {}
    for q in active_questions:
        questions_by_subtopic.setdefault(q["subtopic_id"], []).append(q)

    subtopics = curriculum_repo.list_subtopics_for_topics(topic_ids)
    subtopics_by_topic: dict[str, list[dict]] = {}
    for s in subtopics:
        if s["id"] in questions_by_subtopic:
            subtopics_by_topic.setdefault(s["topic_id"], []).append(s)

    eligible_topics = [t for t in topics if t["id"] in subtopics_by_topic]
    if not eligible_topics:
        return []

    subtopic_ids = list(questions_by_subtopic.keys())
    subtopic_attempt_counts = dict(attempt_repo.subtopic_attempt_counts(subtopic_ids))
    recent_by_subtopic = attempt_repo.recent_question_ids_bulk(subtopic_ids, limit=5)
    topic_attempt_counts = {t["id"]: t["attempts_count"] for t in eligible_topics}

    queue = []
    used_question_ids: set[str] = set()
    for _ in range(session_length):
        topic = min(eligible_topics, key=lambda t: topic_attempt_counts.get(t["id"], 0))
        topic_subtopics = subtopics_by_topic[topic["id"]]
        subtopics_with_counts = [
            {**s, "attempts_count": subtopic_attempt_counts.get(s["id"], 0)} for s in topic_subtopics
        ]
        subtopic = selection.pick_subtopic_for_topic(subtopics_with_counts)

        available = questions_by_subtopic[subtopic["id"]]
        recent_ids = recent_by_subtopic.get(subtopic["id"], set()) | used_question_ids
        not_recent = [q for q in available if q["id"] not in recent_ids]
        question = random.choice(not_recent or available)

        queue.append({"topic": topic, "subtopic": subtopic, "question": question})
        used_question_ids.add(question["id"])
        subtopic_attempt_counts[subtopic["id"]] = subtopic_attempt_counts.get(subtopic["id"], 0) + 1
        topic_attempt_counts[topic["id"]] += 1
    return queue


def start_session(
    session_length: int = DEFAULT_SESSION_LENGTH,
    topic_id: str | None = None,
    area_id: str | None = None,
    mode: str = "due_review",
) -> bool:
    """Builds and stores the session queue. Returns False if no active
    question exists anywhere in the bank yet (or for the given topic/area,
    if scoped)."""
    if mode == "progress_test":
        candidates = _build_topic_candidates()
        if not candidates:
            return False
        selected_topics = selection.select_progress_test_topics(candidates, session_length, random)
        queue = _build_multi_topic_queue(selected_topics)
    elif topic_id is not None:
        queue = _build_single_topic_queue(topic_id, session_length)
    elif area_id is not None:
        queue = _build_area_queue(area_id, session_length)
    else:
        candidates = _build_topic_candidates()
        if not candidates:
            return False
        selected_topics = selection.select_session_topics(candidates, session_length=session_length)
        queue = _build_multi_topic_queue(selected_topics)

    if not queue:
        return False

    session_id = session_repo.start_session(
        mode=mode,
        config={
            "session_length": session_length,
            "topic_id": str(topic_id) if topic_id else None,
            "area_id": str(area_id) if area_id else None,
        },
    )
    st.session_state[_STATE_KEY] = {
        "session_id": session_id,
        "mode": mode,
        "topic_id": topic_id,
        "queue": queue,
        "pointer": 0,
        "question_started_at": _now().isoformat(),
        "last_result": None,
        "results": [],
    }
    return True


def current_item() -> dict | None:
    state = _state()
    if not state or state["pointer"] >= len(state["queue"]):
        return None
    return state["queue"][state["pointer"]]


def is_complete() -> bool:
    state = _state()
    return state is None or state["pointer"] >= len(state["queue"])


def progress() -> tuple[int, int]:
    state = _state()
    if not state:
        return 0, 0
    return state["pointer"], len(state["queue"])


def last_result() -> dict | None:
    state = _state()
    return state["last_result"] if state else None


def active_session_details() -> dict:
    """Small, UI-safe summary used by the completion reflection."""
    state = _state() or {}
    return {"mode": state.get("mode"), "topic_id": state.get("topic_id")}


def session_results() -> list[dict]:
    """Per-question {area_name, topic_name, score} for the active session."""
    state = _state()
    return list(state.get("results", [])) if state else []


def save_learning_note(
    content: str,
    self_rated_confidence: int | None,
    misconception_tag: str | None,
) -> str | None:
    """Persist an optional end-of-session reflection without scoring it."""
    state = _state()
    if state is None or not content.strip():
        return None
    kind = "teach_back" if state.get("mode") == "epa_practice" else "reflection"
    return learning_note_repo.create_learning_note(
        session_id=state["session_id"],
        topic_id=state.get("topic_id"),
        content=content.strip(),
        kind=kind,
        self_rated_confidence=self_rated_confidence,
        misconception_tag=misconception_tag or None,
    )


def submit_answer(response, confidence: int | None, hint_used: bool) -> dict:
    """Scores the current question, persists the attempt, updates mastery/SR,
    and advances the queue pointer. Returns {score, explanation}."""
    state = _state()
    item = current_item()
    if state is None or item is None:
        raise RuntimeError("no active quiz question to submit an answer for")

    question = item["question"]
    topic_id = item["topic"]["id"]

    started_at = datetime.fromisoformat(state["question_started_at"])
    seconds_taken = int((_now() - started_at).total_seconds())

    score = scoring.score_question(question, response, hint_used=hint_used)

    attempt_repo.create_attempt(
        session_id=state["session_id"],
        question=question,
        response_text=json.dumps(response, default=str),
        score=score,
        rubric_points_hit=None,
        self_rated_confidence=confidence,
        seconds_taken=seconds_taken,
        hint_used=hint_used,
    )

    mastery_row = mastery_repo.get_mastery(topic_id)
    updated = mastery.update_mastery_after_attempt(mastery_row, score, question["difficulty"])
    mastery_repo.upsert_after_attempt(topic_id, updated, seen_at=_now())

    result = {"score": score, "explanation": question["explanation"]}
    state["last_result"] = result
    state["results"].append(
        {
            "area_name": item["topic"]["area_name"],
            "topic_name": item["topic"]["topic_name"],
            "score": score,
        }
    )
    return result


def advance() -> None:
    """Moves to the next question after feedback for the current one has
    been shown. Kept separate from submit_answer() so the page can render a
    feedback step in between."""
    state = _state()
    if not state:
        return
    state["pointer"] += 1
    state["last_result"] = None
    state["question_started_at"] = _now().isoformat()


def end_session() -> None:
    state = _state()
    if state:
        session_repo.end_session(state["session_id"])
    st.session_state.pop(_STATE_KEY, None)
