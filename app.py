import streamlit as st

from config import APP_TITLE, APP_ICON
from core.game_state import init_game_state
from data.scenarios import SCENARIOS
from ui.layout import apply_global_styles, render_header
from ui.game_view import render_game_view
from ui.map_view import render_map
from ui.start_screen import render_start_screen


st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
)

init_game_state()
apply_global_styles()

# ── Sidebar : accès administrateur ───────────────────────────────
with st.sidebar:
    with st.expander("🔐 Accès formateur", expanded=False):
        admin_pw = st.text_input(
            "Mot de passe",
            type="password",
            placeholder="Mot de passe admin…",
            label_visibility="collapsed",
        )
        enter_admin = st.button("Entrer", use_container_width=True)

    if enter_admin and admin_pw:
        try:
            expected = st.secrets["admin"]["password"]
        except (KeyError, FileNotFoundError):
            expected = "novacorp-admin"   # mot de passe par défaut si secrets.toml absent
        if admin_pw == expected:
            st.session_state.admin_mode = True
        else:
            st.error("Mot de passe incorrect.")

    if st.session_state.get("admin_mode"):
        if st.button("↩ Quitter le dashboard", use_container_width=True):
            st.session_state.admin_mode = False
            st.rerun()

# ── Dashboard administrateur (prioritaire sur le jeu) ────────────
if st.session_state.get("admin_mode"):
    from ui.admin_view import render_admin_view
    render_admin_view()
    st.stop()

# ── Écran d'accueil (avant la carte) ─────────────────────────────
if not st.session_state.get("game_started"):
    render_start_screen()
    st.stop()

# ── Jeu principal ─────────────────────────────────────────────────
if st.session_state.current_scene is None:
    render_header(
        title=f"{APP_ICON} {APP_TITLE}",
        subtitle="Carte de progression — Sélectionne ta mission",
    )
    render_map()
else:
    scene_index = st.session_state.scene_index
    if scene_index < len(SCENARIOS):
        subtitle = SCENARIOS[scene_index]["subtitle"]
    else:
        subtitle = "Fin de l'aventure — Bilan de mission"
    render_header(title=f"{APP_ICON} {APP_TITLE}", subtitle=subtitle)
    render_game_view()
