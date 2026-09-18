"""Single-user passcode gate.

Community Cloud apps are public URLs; a passcode in st.secrets is the
spec's deliberately minimal auth for a single-user tool (spec §1).
"""

import streamlit as st


def require_passcode() -> None:
    if st.session_state.get("authenticated"):
        return

    st.title("Revision Engine")
    with st.form("passcode_form"):
        passcode = st.text_input("Passcode", type="password")
        submitted = st.form_submit_button("Enter")

    if submitted:
        if passcode == st.secrets["app"]["passcode"]:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect passcode.")

    st.stop()
