import streamlit as st

from config import APP_TITLE, APP_ICON
from core.game_state import init_game_state
from ui.layout import apply_global_styles, render_header
from ui.game_view import render_game_view


st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
)

init_game_state()
apply_global_styles()

render_header(
    title=f"{APP_ICON} {APP_TITLE}",
    subtitle="Jour 1 — Premier email d’activation chez NovaCorp",
)

render_game_view()