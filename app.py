import time

import streamlit as st

from config import APP_TITLE, APP_ICON
from core.db import init_db, register_user, login_user, load_progress
from core.game_state import init_game_state, restore_progress
from data.scenarios import SCENARIOS, resolve_scenario
from ui.layout import apply_global_styles, render_header
from ui.game_view import render_game_view
from ui.map_view import render_map


st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
)

# Exécuté une seule fois au démarrage du serveur, pas à chaque rerun
@st.cache_resource
def _setup_db():
    init_db()
    return True

_setup_db()
init_game_state()
apply_global_styles()

# ── Écran d'authentification ───────────────────────────────────────
if st.session_state.user_id is None:
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "register"

    st.markdown("""
    <style>
    /* Page background */
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stHeader"] {
        background: linear-gradient(145deg,#0B1D52 0%,#162B78 55%,#1E3FA0 100%) !important;
    }
    .main .block-container {
        background: transparent !important;
        padding-top: 4vh;
        max-width: 1020px;
    }
    /* Right column: white card — top-level only */
    [data-testid="stColumn"]:last-of-type {
        background: #FFFFFF !important;
        border-radius: 20px !important;
        box-shadow: 0 24px 64px rgba(0,0,0,0.28) !important;
        padding: 36px 32px 32px !important;
    }
    /* Annule le style carte sur les colonnes imbriquées (ex: toggle buttons) */
    [data-testid="stColumn"]:last-of-type [data-testid="stColumn"] {
        background: transparent !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        padding: 0 !important;
    }
    /* Input — border sur le conteneur baseweb, pas sur l'élément input */
    [data-testid="stTextInput"] [data-baseweb="input"] {
        border-radius: 10px !important;
        border: 1.5px solid #E2E8F0 !important;
        background: #F8FAFC !important;
        overflow: hidden !important;
        transition: border-color .2s, box-shadow .2s !important;
    }
    [data-testid="stTextInput"] [data-baseweb="input"]:focus-within {
        border-color: #2A52BE !important;
        box-shadow: 0 0 0 3px rgba(42,82,190,.12) !important;
        background: #fff !important;
    }
    [data-testid="stTextInput"] [data-baseweb="base-input"] {
        background: #FFFFFF !important;
    }
    [data-testid="stTextInput"] input {
        border: none !important;
        background: #FFFFFF !important;
        border-radius: 0 !important;
        padding: 11px 14px !important;
        font-size: 14px !important;
        font-family: 'Inter',sans-serif !important;
        color: #1E293B !important;
        box-shadow: none !important;
    }
    [data-testid="stTextInput"] input:focus { box-shadow: none !important; outline: none !important; }
    [data-testid="stTextInput"] input::placeholder { color: #CBD5E1 !important; }
    /* Inactive toggle button */
    [data-testid="stBaseButton-secondary"] {
        background: #F1F5F9 !important; color: #64748B !important;
        box-shadow: none !important; border: 1.5px solid #E2E8F0 !important;
    }
    [data-testid="stBaseButton-secondary"]:hover {
        background: #E2E8F0 !important; color: #374151 !important;
        transform: none !important; box-shadow: none !important; filter: none !important;
    }
    /* Left panel */
    .ap-left { padding: 32px 36px 32px 8px; display:flex; flex-direction:column;
                justify-content:center; min-height:580px; }
    .ap-logo  { font-size:52px; line-height:1; margin-bottom:18px; }
    .ap-title { font-family:'Inter',sans-serif; font-size:28px; font-weight:800;
                color:#fff; letter-spacing:-.5px; line-height:1.2; margin-bottom:12px; }
    .ap-sub   { font-family:'Inter',sans-serif; font-size:14px;
                color:rgba(255,255,255,.6); line-height:1.65; margin-bottom:28px; }
    .ap-feat  { display:flex; align-items:flex-start; gap:12px; margin-bottom:14px; }
    .ap-fi    { background:rgba(255,255,255,.13); border-radius:8px; width:34px; height:34px;
                display:flex; align-items:center; justify-content:center;
                font-size:17px; flex-shrink:0; }
    .ap-ft    { font-family:'Inter',sans-serif; font-size:13px;
                color:rgba(255,255,255,.85); line-height:1.5; }
    .ap-ft strong { color:#fff; font-weight:600; }
    .ap-ft small  { color:rgba(255,255,255,.5); }
    .ap-hr    { border:none; border-top:1px solid rgba(255,255,255,.12); margin:24px 0; }
    .ap-stats { display:flex; gap:0; }
    .ap-stat  { flex:1; }
    .ap-stat + .ap-stat {
        border-left: 1px solid rgba(255,255,255,.15);
        padding-left: 28px;
    }
    .ap-sv    { font-family:'Inter',sans-serif; font-size:26px;
                font-weight:800; color:#fff; }
    .ap-sl    { font-family:'Inter',sans-serif; font-size:11px;
                color:rgba(255,255,255,.45); margin-top:2px; letter-spacing:.5px; }
    /* Right panel labels */
    .ap-form-title { font-family:'Inter',sans-serif; font-size:22px; font-weight:800;
                     color:#1E293B; letter-spacing:-.3px; margin-bottom:3px; }
    .ap-form-sub   { font-family:'Inter',sans-serif; font-size:13px;
                     color:#94A3B8; margin-bottom:18px; }
    .ap-label { font-family:'Inter',sans-serif; font-size:11px; font-weight:700;
                color:#64748B; letter-spacing:.6px; text-transform:uppercase;
                margin-bottom:4px; margin-top:12px; }
    .ap-hint  { font-family:'Inter',sans-serif; font-size:11px;
                color:#94A3B8; margin-top:12px; text-align:center; }
    </style>
    """, unsafe_allow_html=True)

    left, right = st.columns([1.05, 1], gap="medium")

    # ── Panel gauche : branding ────────────────────────────────────
    with left:
        st.markdown(f"""
        <div class="ap-left">
          <div class="ap-logo">🛡️</div>
          <div class="ap-title">{APP_TITLE}</div>
          <div class="ap-sub">
            Apprends à détecter les vraies menaces cyber en jouant
            le rôle d'un(e) nouvel(le) employé(e) dans une entreprise.
          </div>
          <div class="ap-feat">
            <div class="ap-fi">📧</div>
            <div class="ap-ft"><strong>Phishing &amp; vishing</strong><br>
            <small>Emails frauduleux, appels malveillants</small></div>
          </div>
          <div class="ap-feat">
            <div class="ap-fi">🔐</div>
            <div class="ap-ft"><strong>Mots de passe &amp; accès</strong><br>
            <small>Bonnes pratiques, gestion des identifiants</small></div>
          </div>
          <div class="ap-feat">
            <div class="ap-fi">💾</div>
            <div class="ap-ft"><strong>Clés USB &amp; shadow IT</strong><br>
            <small>Périphériques non autorisés, logiciels pirates</small></div>
          </div>
          <hr class="ap-hr">
          <div class="ap-stats">
            <div class="ap-stat"><div class="ap-sv">16</div><div class="ap-sl">MISSIONS</div></div>
            <div class="ap-stat"><div class="ap-sv">~30 min</div><div class="ap-sl">DURÉE ESTIMÉE</div></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Panel droit : formulaire ───────────────────────────────────
    with right:
        mode = st.session_state.auth_mode
        form_title = "Créer un compte" if mode == "register" else "Bon retour !"
        form_sub   = "Commence ton parcours cybersécurité." if mode == "register" \
                     else "Reprends là où tu t'es arrêté."

        st.markdown(f"""
        <div class="ap-form-title">{form_title}</div>
        <div class="ap-form-sub">{form_sub}</div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            t1 = "primary" if mode == "register" else "secondary"
            if st.button("Nouvelle partie", use_container_width=True, type=t1, key="btn_reg"):
                st.session_state.auth_mode = "register"
                st.rerun()
        with c2:
            t2 = "primary" if mode == "login" else "secondary"
            if st.button("Reprendre", use_container_width=True, type=t2, key="btn_log"):
                st.session_state.auth_mode = "login"
                st.rerun()

        err_msg = st.session_state.pop("auth_error", None)
        if err_msg:
            st.error(err_msg)

        if mode == "register":
            fn_col, ln_col = st.columns(2)
            with fn_col:
                st.markdown('<div class="ap-label">Prénom</div>', unsafe_allow_html=True)
                first_name = st.text_input("fn", placeholder="Marie",
                                            label_visibility="collapsed", key="inp_fn")
            with ln_col:
                st.markdown('<div class="ap-label">Nom</div>', unsafe_allow_html=True)
                last_name = st.text_input("ln", placeholder="Dupont",
                                           label_visibility="collapsed", key="inp_ln")
            display_name = f"{first_name.strip()} {last_name.strip()}".strip()
        else:
            display_name = ""

        st.markdown('<div class="ap-label">Pseudo</div>', unsafe_allow_html=True)
        username = st.text_input("un", placeholder="ex : marie42",
                                  label_visibility="collapsed", key=f"inp_user_{mode}")

        st.markdown('<div class="ap-label">Mot de passe</div>', unsafe_allow_html=True)
        password = st.text_input("pw", placeholder="min. 4 caractères", type="password",
                                  label_visibility="collapsed", key=f"inp_pass_{mode}")

        if mode == "register":
            st.markdown(
                '<div class="ap-label">Entreprise '
                '<span style="font-weight:400;color:#CBD5E1">(optionnel)</span></div>',
                unsafe_allow_html=True)
            company = st.text_input("co", placeholder="NovaCorp",
                                     label_visibility="collapsed", key="inp_company")
        else:
            company = ""

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        btn_label = "Créer mon compte  →" if mode == "register" else "Se connecter  →"
        if st.button(btn_label, use_container_width=True, key="btn_submit", type="primary"):
            if mode == "register":
                ok, err = register_user(username, password, display_name, company)
                if not ok:
                    st.session_state.auth_error = err
                    st.rerun()
                user, _ = login_user(username, password)
            else:
                user, err = login_user(username, password)
                if user is None:
                    st.session_state.auth_error = err
                    st.rerun()

            st.session_state.user_id      = user["id"]
            st.session_state.display_name = user["display_name"]
            st.session_state.company_name = user["company_name"]

            saved = load_progress(user["id"])
            if saved:
                restore_progress(saved)

            st.rerun()

        if mode == "register":
            st.markdown(
                '<div class="ap-hint">Entreprise vide → <strong>NovaCorp</strong> par défaut</div>',
                unsafe_allow_html=True)
    st.stop()

# ── Transition de chargement (déclenchée par un clic sur la carte) ─
if "_loading_msg" in st.session_state:
    msg = st.session_state._loading_msg
    del st.session_state._loading_msg
    with st.spinner(msg):
        time.sleep(0.3)
    st.rerun()

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
        subtitle = resolve_scenario(SCENARIOS[scene_index])["subtitle"]
    else:
        subtitle = "Fin de l'aventure — Bilan de mission"
    render_header(title=f"{APP_ICON} {APP_TITLE}", subtitle=subtitle)
    render_game_view()
