import streamlit as st

from lib import quiz_service
from lib.auth import require_passcode
from app.pages import curriculum, dashboard, export, prompts, question_bank, quiz, readings

st.set_page_config(page_title="Revision Engine", initial_sidebar_state="collapsed")

require_passcode()

pages = [
    st.Page(quiz.render, title="Quiz", icon=":material/quiz:", url_path="quiz", default=True),
    st.Page(dashboard.render, title="Dashboard", icon=":material/bar_chart:", url_path="dashboard"),
    st.Page(curriculum.render, title="Curriculum", icon=":material/account_tree:", url_path="curriculum"),
    st.Page(question_bank.render, title="Question bank", icon=":material/library_books:", url_path="question-bank"),
    st.Page(prompts.render, title="Prompts", icon=":material/edit_note:", url_path="prompts"),
    st.Page(readings.render, title="Readings", icon=":material/menu_book:", url_path="readings"),
    st.Page(export.render, title="Export", icon=":material/download:", url_path="export"),
]

with st.sidebar:
    if st.button("🏠  Home", use_container_width=True):
        quiz_service.end_session()
        st.switch_page(pages[0])

st.navigation(pages).run()
