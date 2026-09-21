import streamlit as st

from app.components.question_render import render_answerable
from lib import quiz_service
from lib.constants import DEFAULT_SESSION_LENGTH, LEARN_SESSION_LENGTH
from lib.db import curriculum_repo, mastery_repo, reading_repo


def render() -> None:
    st.title("Quiz")

    if not quiz_service.has_active_session():
        _render_start_screen()
        return

    if quiz_service.is_complete():
        _render_session_complete()
        return

    if quiz_service.last_result() is None:
        _render_question()
    else:
        _render_feedback(quiz_service.last_result())


def _render_start_screen() -> None:
    if not quiz_service.has_active_questions():
        st.info(
            "No active questions in the bank yet. Open **Question bank** from the "
            "navigation to author some, then come back here."
        )
        return

    st.subheader("Choose your revision mode")
    learn_tab, review_tab, test_tab, epa_tab = st.tabs(
        ["Learn a topic", "Due review", "Test your progress", "EPA practice"]
    )

    with learn_tab:
        _render_learn_mode()
    with review_tab:
        st.write("A mixed, scheduled session that brings back overdue, weak and less-covered topics.")
        if st.button("Start due review", type="primary", use_container_width=True):
            _start_session(mode="due_review")
    with test_tab:
        st.write(
            "One question from each of many topics, spread across every area. No hints. "
            "You get a score breakdown by area at the end. Use it to find your weak areas."
        )
        length = st.selectbox("Number of questions", [10, 20, 30, 40], index=1, key="progress_test_length")
        if st.button("Start progress test", type="primary", width="stretch"):
            _start_session(mode="progress_test", session_length=length)
    with epa_tab:
        st.write(
            "A mixed session followed by a short teach-back reflection. Use this to practise "
            "explaining and applying ideas, not just recognising answers."
        )
        if st.button("Start EPA practice", type="primary", use_container_width=True):
            _start_session(mode="epa_practice")

    st.divider()
    st.caption("Or practise within one area. This is useful after learning, but due review should be your default.")

    topics = mastery_repo.list_topics_for_scheduling()
    by_area: dict[str, list[dict]] = {}
    for t in topics:
        by_area.setdefault(t["area_name"], []).append(t)

    for area_name in sorted(by_area):
        area_topics = sorted(by_area[area_name], key=lambda t: t["topic_name"])
        area_id = area_topics[0]["area_id"]
        area_avg = sum(t["ability"] for t in area_topics) / len(area_topics)
        with st.expander(f"{area_name} · avg ability {area_avg:.0f}/100"):
            if st.button(f"Practice {area_name}", key=f"practice_area_{area_id}", use_container_width=True):
                _start_session(area_id=area_id, mode="focused_area")
            for t in area_topics:
                col1, col2 = st.columns([3, 3])
                with col1:
                    st.write(t["topic_name"])
                with col2:
                    st.progress(min(t["ability"], 100) / 100)
                    st.caption(f"{t['ability']:.0f}/100 · {t['current_band']} · {t['attempts_count']} attempts")


def _render_learn_mode() -> None:
    tree = curriculum_repo.get_curriculum_tree()
    if not tree:
        st.warning("No curriculum found. Run scripts/seed_curriculum.py first.")
        return

    area = st.selectbox("Area", tree, format_func=lambda item: item["name"], key="learn_area")
    if not area["topics"]:
        st.info("This area has no topics yet.")
        return
    topic = st.selectbox("Topic", area["topics"], format_func=lambda item: item["name"], key="learn_topic")

    reading = reading_repo.get_reading(topic["id"])
    if reading:
        with st.expander("Read first", expanded=True):
            st.markdown(reading["content"])
    else:
        st.caption("No reading is available yet. You can still start a short retrieval set.")

    if st.button(f"Learn {topic['name']}", type="primary", use_container_width=True):
        _start_session(topic_id=topic["id"], mode="learn", session_length=LEARN_SESSION_LENGTH)


def _start_session(
    topic_id: str | None = None,
    area_id: str | None = None,
    mode: str = "due_review",
    session_length: int = DEFAULT_SESSION_LENGTH,
) -> None:
    with st.spinner("Building your session..."):
        started = quiz_service.start_session(
            session_length, topic_id=topic_id, area_id=area_id, mode=mode
        )
    if not started:
        st.warning(
            "Couldn't build a session there -- try authoring more active questions "
            "for that area, or pick General ML."
        )
    else:
        st.rerun()


def _render_question() -> None:
    pointer, total = quiz_service.progress()
    st.progress(pointer / total if total else 0, text=f"Question {pointer + 1} of {total}")

    item = quiz_service.current_item()
    question = item["question"]
    st.caption(
        f"{item['topic']['area_name']} / {item['topic']['topic_name']} / "
        f"{item['subtopic']['name']} · {question['difficulty']}"
    )
    st.markdown(f"### {question['stem']}")

    response = render_answerable(question)

    hint_key = f"hint_shown_{question['id']}"
    hints_allowed = quiz_service.active_session_details()["mode"] != "progress_test"
    if hints_allowed and question.get("distractor_notes"):
        if st.session_state.get(hint_key):
            st.info(_format_hint(question["distractor_notes"]))
        elif st.button("Show hint (halves this question's score)", key=f"hint_btn_{question['id']}"):
            st.session_state[hint_key] = True
            st.rerun()

    confidence = st.slider("How confident are you?", 1, 5, 3, key=f"confidence_{question['id']}")

    if st.button("Submit", type="primary", key=f"submit_{question['id']}"):
        hint_used = bool(st.session_state.get(hint_key))
        quiz_service.submit_answer(response, confidence, hint_used)
        st.rerun()


def _format_hint(distractor_notes: dict) -> str:
    return "\n".join(f"- {option}: {reason}" for option, reason in distractor_notes.items())


def _render_feedback(result: dict) -> None:
    score = result["score"]
    if score >= 0.999:
        st.success(f"Score: {score:.2f}")
    elif score <= 0.001:
        st.error(f"Score: {score:.2f}")
    else:
        st.warning(f"Score: {score:.2f}")

    st.write(result["explanation"])

    if st.button("Next question", type="primary"):
        quiz_service.advance()
        st.rerun()


def _render_progress_test_results(results: list[dict]) -> None:
    if not results:
        return
    overall = sum(r["score"] for r in results) / len(results)
    st.metric("Overall score", f"{overall:.0%}", help=f"{len(results)} questions")

    by_area: dict[str, list[float]] = {}
    for r in results:
        by_area.setdefault(r["area_name"], []).append(r["score"])
    rows = sorted(
        (
            {"Area": area, "Questions": len(scores), "Score": sum(scores) / len(scores)}
            for area, scores in by_area.items()
        ),
        key=lambda row: row["Score"],
    )
    st.subheader("By area (weakest first)")
    st.dataframe(
        rows,
        hide_index=True,
        width="stretch",
        column_config={"Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=1, format="percent")},
    )

    missed = [r for r in results if r["score"] < 0.5]
    if missed:
        st.subheader("Topics to revisit")
        for r in missed:
            st.write(f"- {r['topic_name']} ({r['area_name']})")


def _render_session_complete() -> None:
    st.success("Session complete.")
    details = quiz_service.active_session_details()
    if details["mode"] == "progress_test":
        _render_progress_test_results(quiz_service.session_results())
    is_teach_back = details["mode"] == "epa_practice"
    st.subheader("Teach-back" if is_teach_back else "Capture a learning note")
    st.caption(
        "In your own words: what is the key idea, what did you mix up, or how would you apply it? "
        "This is saved for later revision; it is not automatically marked."
    )
    with st.form("session_reflection"):
        note = st.text_area(
            "Explain it back" if is_teach_back else "What should future-you remember?",
            placeholder="For example: I confused precision with recall when the cost of false negatives is high...",
        )
        confidence = st.slider("Confidence after this session", 1, 5, 3)
        misconception = st.selectbox(
            "If relevant, what got in the way?",
            ["", "Forgot term", "Mixed up similar concepts", "Can calculate but cannot explain", "Misread the question", "Need a concrete example"],
        )
        saved = st.form_submit_button("Save note and finish", type="primary")

    if saved:
        quiz_service.save_learning_note(note, confidence, misconception)
        quiz_service.end_session()
        st.rerun()

    if st.button("Finish without a note"):
        quiz_service.end_session()
        st.rerun()
