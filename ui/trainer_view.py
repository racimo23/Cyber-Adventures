import io
import csv
from datetime import datetime

import streamlit as st

from core.db import create_session, get_trainer_sessions, get_session_players
from data.scenarios import SCENARIOS

_OUTCOME_ICON = {"success": "✅", "neutral": "⚠️", "danger": "🚨"}


# ── CSS propre au dashboard formateur ───────────────────────────────

_CSS = """
<style>
.tr-header { font-family:'Inter',sans-serif; }
.tr-page-title { font-size:24px; font-weight:800; color:#1E293B; margin-bottom:2px; }
.tr-page-sub   { font-size:14px; color:#64748B; margin-bottom:28px; }

.tr-session-card {
    background:#FFFFFF; border:1.5px solid #E2E8F0; border-radius:16px;
    padding:20px 24px; margin-bottom:12px;
    box-shadow:0 2px 8px rgba(0,0,0,.05);
}
.tr-session-header { display:flex; align-items:center; justify-content:space-between; }
.tr-session-name   { font-family:'Inter',sans-serif; font-size:16px; font-weight:700; color:#1E293B; }
.tr-session-meta   { font-family:'Inter',sans-serif; font-size:12px; color:#94A3B8; margin-top:4px; }
.tr-code-badge {
    background:#EEF2FF; border:1.5px solid #C7D2FE; border-radius:8px;
    padding:6px 14px; font-family:'Courier New',monospace; font-size:15px;
    font-weight:700; color:#2A52BE; letter-spacing:1.5px; cursor:pointer;
}
.tr-stat-row { display:flex; gap:16px; margin-top:14px; }
.tr-stat-pill {
    background:#F8FAFC; border:1px solid #E2E8F0; border-radius:99px;
    padding:4px 14px; font-family:'Inter',sans-serif; font-size:12px; color:#475569;
}
.tr-no-session {
    text-align:center; padding:48px 24px; color:#94A3B8;
    font-family:'Inter',sans-serif; font-size:14px;
}
</style>
"""


# ── Helpers ─────────────────────────────────────────────────────────

def _format_date(ts) -> str:
    if ts is None:
        return "—"
    try:
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        return ts.strftime("%d/%m/%Y")
    except Exception:
        return str(ts)[:10]


def _build_csv(players: list[dict]) -> str:
    buf = io.StringIO()
    scenarios_by_id = {s["id"]: s for s in SCENARIOS}
    # Header
    base_cols = ["Nom", "Pseudo", "Entreprise", "Score", "Missions terminées", "Inscription"]
    mission_cols = [f"J{s['day']} — {s['title']}" for s in SCENARIOS]
    choice_cols  = [f"J{s['day']} choix" for s in SCENARIOS]

    headers = base_cols + [item for pair in zip(mission_cols, choice_cols) for item in pair]
    writer = csv.writer(buf)
    writer.writerow(headers)

    for p in players:
        cs = p.get("completed_scenes", {})
        nb_done = len(cs)
        row = [
            p.get("display_name", ""),
            p.get("username", ""),
            p.get("company_name", ""),
            p.get("score", 0),
            f"{nb_done}/{len(SCENARIOS)}",
            _format_date(p.get("created_at")),
        ]
        for s in SCENARIOS:
            data = cs.get(s["id"])
            if data:
                row.append(_OUTCOME_ICON.get(data.get("outcome", ""), "—"))
                row.append(data.get("chosen_label", "—"))
            else:
                row.append("—")
                row.append("—")
        writer.writerow(row)

    return buf.getvalue()


# ── Sous-vues ────────────────────────────────────────────────────────

def _render_create_session() -> None:
    with st.expander("➕ Créer une nouvelle session", expanded=False):
        name = st.text_input("Nom de la session", placeholder="ex : Formation Cyber — Équipe RH",
                              key="new_session_name")
        if st.button("Créer la session", key="create_session_btn", type="primary"):
            if not name.strip():
                st.error("Donne un nom à la session.")
            else:
                code = create_session(st.session_state.user_id, name)
                st.session_state["_new_session_code"] = code
                st.rerun()

    if "_new_session_code" in st.session_state:
        code = st.session_state.pop("_new_session_code")
        st.success(f"✅ Session créée ! Code à communiquer aux joueurs : **{code}**")


def _render_session_card(session: dict) -> None:
    nb     = session.get("nb_players", 0)
    code   = session["code"]
    date_s = _format_date(session.get("created_at"))

    st.html(f"""
    <div class="tr-session-card">
      <div class="tr-session-header">
        <div>
          <div class="tr-session-name">{session['name']}</div>
          <div class="tr-session-meta">Créée le {date_s}</div>
        </div>
        <div class="tr-code-badge">{code}</div>
      </div>
      <div class="tr-stat-row">
        <div class="tr-stat-pill">👥 {nb} joueur{'s' if nb != 1 else ''}</div>
        <div class="tr-stat-pill">📋 Copiez le code et partagez-le</div>
      </div>
    </div>
    """)

    if nb == 0:
        st.caption("Aucun joueur n'a encore rejoint cette session.")
        return

    players = get_session_players(code)

    # ── Tableau de résultats ────────────────────────────────────────
    import pandas as pd

    # Résumé par joueur
    rows = []
    for p in players:
        cs     = p.get("completed_scenes", {})
        nb_ok  = sum(1 for v in cs.values() if v.get("outcome") == "success")
        nb_war = sum(1 for v in cs.values() if v.get("outcome") == "neutral")
        nb_err = sum(1 for v in cs.values() if v.get("outcome") == "danger")
        rows.append({
            "Joueur":    p.get("display_name", "?"),
            "Pseudo":    p.get("username", ""),
            "Entreprise": p.get("company_name", ""),
            "Score":     p.get("score", 0),
            "Missions":  f"{len(cs)}/{len(SCENARIOS)}",
            "✅":        nb_ok,
            "⚠️":        nb_war,
            "🚨":        nb_err,
        })
    df_summary = pd.DataFrame(rows)
    st.dataframe(df_summary, use_container_width=True, hide_index=True)

    # ── Détail par mission ──────────────────────────────────────────
    with st.expander("🔍 Détail par mission"):
        detail_rows = []
        for p in players:
            cs = p.get("completed_scenes", {})
            for s in SCENARIOS:
                data = cs.get(s["id"])
                detail_rows.append({
                    "Joueur":   p.get("display_name", "?"),
                    "Jour":     s["day"],
                    "Mission":  s["title"],
                    "Résultat": _OUTCOME_ICON.get(data.get("outcome", ""), "—") if data else "—",
                    "Choix":    data.get("chosen_label", "—") if data else "Non joué",
                })
        df_detail = pd.DataFrame(detail_rows)
        st.dataframe(df_detail, use_container_width=True, hide_index=True)

    # ── Export CSV ──────────────────────────────────────────────────
    csv_data = _build_csv(players)
    safe_name = session["name"].replace(" ", "_")[:30]
    st.download_button(
        label="⬇️ Exporter les résultats (CSV)",
        data=csv_data.encode("utf-8-sig"),  # utf-8-sig pour Excel
        file_name=f"session_{safe_name}_{code}.csv",
        mime="text/csv",
        key=f"csv_{code}",
    )


# ── Vue principale ───────────────────────────────────────────────────

def render_trainer_dashboard() -> None:
    st.html(_CSS)

    display_name = st.session_state.get("display_name", "Formateur")
    st.html(f"""
    <div class="tr-header">
      <div class="tr-page-title">🎓 Tableau de bord formateur</div>
      <div class="tr-page-sub">Bonjour <strong>{display_name}</strong> — gérez vos sessions et consultez les résultats de vos apprenants.</div>
    </div>
    """)

    _render_create_session()
    st.markdown("---")

    sessions = get_trainer_sessions(st.session_state.user_id)

    if not sessions:
        st.html('<div class="tr-no-session">Aucune session pour l\'instant.<br>Créez votre première session ci-dessus.</div>')
        return

    for session in sessions:
        _render_session_card(session)

    # ── Déconnexion ─────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Se déconnecter", key="trainer_logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
