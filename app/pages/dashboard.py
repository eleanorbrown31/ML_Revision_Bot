from datetime import date

import pandas as pd
import streamlit as st

from lib.db import attempt_repo, config_repo, learning_note_repo, mastery_repo


def render() -> None:
    st.title("Dashboard")

    _render_exam_date_editor()
    st.metric("Due today", mastery_repo.due_today_count())

    st.subheader("Ability by area")
    _render_ability_by_area()

    st.subheader("Weakest topics")
    _render_weakest_topics()

    st.subheader("Attempts over time")
    _render_attempts_over_time()

    st.subheader("Recent learning notes")
    _render_recent_learning_notes()


def _render_exam_date_editor() -> None:
    current = config_repo.get_exam_date()
    st.caption(
        "Exam date -- shifts revision priority from breadth-first to "
        "weak-spots-first as it approaches."
    )
    col1, col2 = st.columns([3, 1])
    with col1:
        picked = st.date_input("Exam date", value=current or date.today())
    with col2:
        st.write("")
        st.write("")
        if st.button("Save exam date"):
            config_repo.set_exam_date(picked)
            st.rerun()

    if current is None:
        st.caption("No exam date set yet -- scheduler is using breadth-first weighting.")
    else:
        st.caption(f"Currently set to {current.isoformat()}.")


def _render_ability_by_area() -> None:
    rollup = mastery_repo.rollup_by_area()
    if not rollup:
        st.caption("No data yet.")
        return
    df = pd.DataFrame(rollup).set_index("name")[["avg_ability"]]
    df.columns = ["Average ability"]
    st.bar_chart(df)


def _render_weakest_topics() -> None:
    weakest = mastery_repo.weakest_topics(limit=10)
    if not weakest:
        st.caption("No data yet.")
        return
    st.dataframe(
        [
            {
                "Area": w["area_name"],
                "Topic": w["topic_name"],
                "Ability": round(w["ability"], 1),
                "Band": w["current_band"],
                "Attempts": w["attempts_count"],
            }
            for w in weakest
        ],
        hide_index=True,
        use_container_width=True,
    )


def _render_attempts_over_time() -> None:
    history = attempt_repo.attempts_over_time(days=90)
    if not history:
        st.caption("No attempts logged yet.")
        return
    df = pd.DataFrame(history).set_index("day")
    st.line_chart(df[["attempts"]].rename(columns={"attempts": "Attempts per day"}))
    st.line_chart(df[["avg_score"]].rename(columns={"avg_score": "Average score"}))


def _render_recent_learning_notes() -> None:
    notes = learning_note_repo.list_recent()
    if not notes:
        st.caption("No learning notes yet. Finish a revision session with a reflection to build a record.")
        return
    for note in notes:
        heading = note["topic_name"] or "Mixed session"
        details = []
        if note["misconception_tag"]:
            details.append(note["misconception_tag"])
        if note["self_rated_confidence"]:
            details.append(f"confidence {note['self_rated_confidence']}/5")
        with st.container(border=True):
            st.caption(f"{heading} · {note['kind'].replace('_', ' ')}" + (f" · {' · '.join(details)}" if details else ""))
            st.write(note["content"])
