from pathlib import Path

import streamlit as st

STATIC_DIR = Path(__file__).parent.parent / "static"

_GOOGLE_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">'
)


def apply_global_styles() -> None:
    st.markdown(_GOOGLE_FONTS, unsafe_allow_html=True)
    css = (STATIC_DIR / "style.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_header(title: str, subtitle: str) -> None:
    st.markdown(f'<div class="game-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="subtitle">{subtitle}</div>', unsafe_allow_html=True)
