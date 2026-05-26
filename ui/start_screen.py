import streamlit as st

from config import APP_ICON, APP_TITLE, COMPANY_NAME
from core.db import _is_db_configured


def render_start_screen() -> None:
    """
    Welcome screen shown before the map.
    On form submit: sets session_state.game_started = True and st.rerun().
    """
    db_ok = _is_db_configured()

    # ── Hero header ───────────────────────────────────────────────
    st.markdown(
        f"""
        <div class="start-hero">
            <div class="start-hero-icon">{APP_ICON}</div>
            <div class="start-hero-title">{APP_TITLE}</div>
            <div class="start-hero-sub">
                Bienvenue chez <strong>{COMPANY_NAME}</strong> —
                ta simulation de cybersécurité commence maintenant.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Step badges ───────────────────────────────────────────────
    st.markdown(
        """
        <div class="start-steps">
            <div class="start-step">
                <div class="start-step-num">1</div>
                <div class="start-step-txt">16 missions<br>de sensibilisation</div>
            </div>
            <div class="start-step-arrow">→</div>
            <div class="start-step">
                <div class="start-step-num">2</div>
                <div class="start-step-txt">Choix critiques<br>face aux menaces</div>
            </div>
            <div class="start-step-arrow">→</div>
            <div class="start-step">
                <div class="start-step-num">3</div>
                <div class="start-step-txt">Bilan &amp; profil<br>de cybersécurité</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Form card ─────────────────────────────────────────────────
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown('<div class="start-card">', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="start-card-header">
                <div class="start-card-title">🚀 Commencer l'intégration</div>
                <div class="start-card-desc">
                    Remplis les champs ci-dessous pour personnaliser ton expérience.<br>
                    Tous les champs sont <strong>optionnels</strong> — tu peux jouer anonymement.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("start_form", border=False):
            player_name = st.text_input(
                "👤 Ton prénom / pseudo",
                placeholder="Ex : Alice, Marie Dupont…",
                help="Personnalise ton bilan de fin de parcours.",
            )

            campaign_id = st.text_input(
                "🏷️ Code de Session (fourni par ton formateur)",
                placeholder="Ex : NOVA-2026, CYBERDAY-01…",
                help=(
                    "Relie tes résultats à la session de ton groupe pour que ton formateur "
                    "puisse les consulter. Laisse vide pour jouer librement."
                ),
            )

            # Only show DB warning if a campaign_id will be expected but DB is missing
            if not db_ok:
                st.markdown(
                    '<div class="start-db-warning">'
                    "⚠️ Mode hors-ligne — les résultats ne seront pas transmis à un formateur "
                    "(Supabase non configuré)."
                    "</div>",
                    unsafe_allow_html=True,
                )

            submitted = st.form_submit_button(
                f"{APP_ICON} Démarrer l'intégration {COMPANY_NAME}",
                use_container_width=True,
                type="primary",
            )

        st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        st.session_state.player_name = player_name.strip() or "Anonyme"
        st.session_state.campaign_id = campaign_id.strip().upper()
        st.session_state.game_started = True
        st.rerun()
