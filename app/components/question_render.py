"""Per-format question rendering, shared by the quiz page and the question
bank's preview.

Response shapes returned by render_answerable() (consumed by lib/scoring.py):
  mcq     -> int                      selected option index
  multi   -> list[int]                selected option indices
  fill    -> list[str]                one entry per blank, in template order
  match   -> dict[str, str]           left text -> chosen right text
  order   -> list[int]                original item indices, in chosen order
  numeric -> float | None
"""

import random

import streamlit as st


def render_answerable(question: dict) -> object:
    """Render interactive widgets for `question` and return the current response."""
    fmt = question["format"]
    payload = question["payload"]
    key_prefix = f"q_{question['id']}"

    if fmt == "mcq":
        options = payload["options"]
        choice = st.radio("Select one:", options, index=None, key=f"{key_prefix}_mcq")
        return options.index(choice) if choice is not None else None

    if fmt == "multi":
        options = payload["options"]
        chosen = st.multiselect("Select all that apply:", options, key=f"{key_prefix}_multi")
        return [options.index(c) for c in chosen]

    if fmt == "fill":
        template = payload["template"]
        blanks = template.count("___")
        parts = template.split("___")
        response = []
        for i in range(blanks):
            st.markdown(parts[i].strip() or "&nbsp;", unsafe_allow_html=True)
            response.append(
                st.text_input(f"Blank {i + 1}", key=f"{key_prefix}_fill_{i}", label_visibility="collapsed")
            )
        st.markdown(parts[-1].strip() or "&nbsp;", unsafe_allow_html=True)
        return response

    if fmt == "match":
        left, right = payload["left"], payload["right"]
        response = {}
        for item in left:
            response[item] = st.selectbox(
                item, options=["-- choose --"] + list(right), key=f"{key_prefix}_match_{item}"
            )
        return {k: v for k, v in response.items() if v != "-- choose --"}

    if fmt == "order":
        # payload["items"] is stored in a fixed order; answer_key["sequence"] gives
        # the correct order as indices into it. Shuffle display order per question
        # (cached in session state) so the storage order never leaks the answer.
        items = payload["items"]
        shuffle_key = f"{key_prefix}_order_shuffle"
        if shuffle_key not in st.session_state:
            shuffled = list(range(len(items)))
            random.shuffle(shuffled)
            st.session_state[shuffle_key] = shuffled
        display_order = st.session_state[shuffle_key]
        labelled = [(idx, items[idx]) for idx in display_order]
        chosen = st.multiselect(
            "Select the items in the correct order:",
            options=labelled,
            format_func=lambda pair: pair[1],
            key=f"{key_prefix}_order",
        )
        return [idx for idx, _ in chosen]

    if fmt == "numeric":
        prompt = payload.get("prompt", "")
        unit = payload.get("unit", "")
        if prompt:
            st.markdown(prompt)
        return st.number_input(f"Answer ({unit})" if unit else "Answer", key=f"{key_prefix}_numeric", value=None)

    raise ValueError(f"unknown question format: {fmt}")


def render_preview(question: dict) -> None:
    """Read-only display of a question: stem, payload, stored answer key, explanation."""
    st.markdown(f"**{question['stem']}**")
    st.caption(f"{question['format']} · {question['difficulty']} · {question['status']}")
    with st.expander("Payload / answer key / explanation"):
        st.json({"payload": question["payload"]})
        st.json({"answer_key": question["answer_key"]})
        if question.get("distractor_notes"):
            st.json({"distractor_notes": question["distractor_notes"]})
        st.write(question["explanation"])
