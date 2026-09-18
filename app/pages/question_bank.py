import streamlit as st

from app.components.question_render import render_preview
from lib.constants import DIFFICULTY_BANDS, QUESTION_FORMATS
from lib.db import curriculum_repo, question_repo


def render() -> None:
    st.title("Question bank")
    st.caption(
        "Content is authored as YAML under content/questions/ and loaded with "
        "scripts/load_questions.py -- this page is for browsing, activating and "
        "retiring, not typing questions in by hand."
    )

    tree = curriculum_repo.get_curriculum_tree()
    if not tree:
        st.warning("No curriculum found. Run scripts/seed_curriculum.py first.")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        area_name = st.selectbox("Area (filter)", ["All"] + [a["name"] for a in tree])
    area = next((a for a in tree if a["name"] == area_name), None)

    with col2:
        topic_options = ["All"] + [t["name"] for t in area["topics"]] if area else ["All"]
        topic_name = st.selectbox("Topic (filter)", topic_options)
    topic = next((t for t in area["topics"] if t["name"] == topic_name), None) if area else None

    with col3:
        subtopic_options = ["All"] + [s["name"] for s in topic["subtopics"]] if topic else ["All"]
        subtopic_name = st.selectbox("Subtopic (filter)", subtopic_options)
    subtopic = next((s for s in topic["subtopics"] if s["name"] == subtopic_name), None) if topic else None

    col4, col5, col6 = st.columns(3)
    with col4:
        status = st.selectbox("Status", ["All", "draft", "active", "retired"], key="filter_status")
    with col5:
        difficulty = st.selectbox("Difficulty", ["All"] + DIFFICULTY_BANDS, key="filter_difficulty")
    with col6:
        format_ = st.selectbox("Format", ["All"] + QUESTION_FORMATS, key="filter_format")

    questions = question_repo.list_questions(
        subtopic_id=subtopic["id"] if subtopic else None,
        topic_id=topic["id"] if (topic and not subtopic) else None,
        status=None if status == "All" else status,
        difficulty=None if difficulty == "All" else difficulty,
        format=None if format_ == "All" else format_,
    )

    st.caption(f"{len(questions)} question(s)")
    for q in questions:
        with st.container(border=True):
            st.caption(f"{q['area_name']} / {q['topic_name']} / {q['subtopic_name']}")
            render_preview(q)
            btn_cols = st.columns(3)
            if q["status"] != "active" and btn_cols[0].button("Activate", key=f"activate_{q['id']}"):
                question_repo.set_status(q["id"], "active")
                st.rerun()
            if q["status"] != "retired" and btn_cols[1].button("Retire", key=f"retire_{q['id']}"):
                question_repo.set_status(q["id"], "retired")
                st.rerun()
            if q["status"] == "retired" and btn_cols[2].button("Restore to draft", key=f"restore_{q['id']}"):
                question_repo.set_status(q["id"], "draft")
                st.rerun()
