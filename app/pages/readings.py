import streamlit as st

from lib.db import curriculum_repo, reading_repo


def render() -> None:
    st.title("Readings")
    st.caption(
        "\"Learn First\" mode -- read a topic's summary before quizzing on it. "
        "Content is authored under content/readings/ and loaded with scripts/load_readings.py."
    )

    tree = curriculum_repo.get_curriculum_tree()
    if not tree:
        st.warning("No curriculum found. Run scripts/seed_curriculum.py first.")
        return

    available_topic_ids = reading_repo.topics_with_readings()

    area = st.selectbox("Area", tree, format_func=lambda a: a["name"])
    topics = area["topics"]
    if not topics:
        st.warning("This area has no topics.")
        return

    topic = st.selectbox(
        "Topic",
        topics,
        format_func=lambda t: t["name"] if t["id"] in available_topic_ids else f"{t['name']} (no reading yet)",
    )

    st.divider()

    if topic["id"] not in available_topic_ids:
        st.info(
            f"No reading written for **{topic['name']}** yet. "
            "You can still quiz on it -- readings are being added incrementally."
        )
        return

    reading = reading_repo.get_reading(topic["id"])
    st.subheader(topic["name"])
    st.markdown(reading["content"])
    st.divider()
    st.caption(f"Ready to quiz? Go to **Quiz** and pick '{topic['name']}' under '{area['name']}'.")
