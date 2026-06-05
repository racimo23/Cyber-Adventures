import io
import csv
from datetime import datetime

import streamlit as st

from core.db import (create_session, delete_session, delete_player,
                     get_trainer_sessions, get_session_players,
                     get_all_trainer_players)
from data.scenarios import SCENARIOS

_OUTCOME_ICON = {"success": "✅", "neutral": "⚠️", "danger": "🚨"}


# ── CSS ─────────────────────────────────────────────────────────────

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
    font-weight:700; color:#2A52BE; letter-spacing:1.5px;
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
.tr-player-detail {
    background:#F8FAFC; border-left:3px solid #2A52BE;
    border-radius:0 8px 8px 0; padding:14px 18px; margin:6px 0 12px;
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


def _build_csv(players: list[dict], include_session: bool = False) -> str:
    buf = io.StringIO()
    # Séparateur ";" pour compatibilité Excel France + quoting automatique
    writer = csv.writer(buf, delimiter=";", quoting=csv.QUOTE_ALL)
    base_cols = ["Nom", "Pseudo", "Entreprise", "Score", "Missions terminées", "Inscription"]
    if include_session:
        base_cols = ["Session"] + base_cols
    mission_cols = [f"J{s['day']} - {s['title']}" for s in SCENARIOS]
    choice_cols  = [f"J{s['day']} résultat" for s in SCENARIOS]
    headers = base_cols + [item for pair in zip(mission_cols, choice_cols) for item in pair]
    writer.writerow(headers)
    for p in players:
        cs = p.get("completed_scenes", {})
        row = []
        if include_session:
            row.append(p.get("session_name", ""))
        row += [
            p.get("display_name", ""),
            p.get("username", ""),
            p.get("company_name", ""),
            p.get("score", 0),
            f"{len(cs)}/{len(SCENARIOS)}",
            _format_date(p.get("created_at")),
        ]
        for s in SCENARIOS:
            data = cs.get(s["id"])
            if data:
                row.append(data.get("chosen_label", "—"))
                row.append(_OUTCOME_ICON.get(data.get("outcome", ""), "—"))
            else:
                row.append("Non joué")
                row.append("—")
        writer.writerow(row)
    return buf.getvalue()


# ── Vue détail d'un joueur ───────────────────────────────────────────

def _render_player_detail(p: dict) -> None:
    cs = p.get("completed_scenes", {})
    name = p.get("display_name", "?")
    st.html(f'<div class="tr-player-detail">')
    st.markdown(f"**📋 Réponses de {name}** — Score : {p.get('score', 0)}/100 "
                f"· {len(cs)}/{len(SCENARIOS)} missions")
    if not cs:
        st.caption("Aucune mission jouée.")
    else:
        rows = []
        for s in SCENARIOS:
            data = cs.get(s["id"])
            rows.append({
                "Jour":     s["day"],
                "Mission":  s["title"],
                "Résultat": _OUTCOME_ICON.get(data.get("outcome", ""), "—") if data else "—",
                "Choix":    data.get("chosen_label", "—") if data else "Non joué",
            })
        import pandas as pd
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.html('</div>')


# ── Stats agrégées par question ──────────────────────────────────────

def _render_question_stats(players: list[dict]) -> None:
    import pandas as pd
    import altair as alt

    if not players:
        st.caption("Aucun joueur pour afficher les statistiques.")
        return

    nb_total = len(players)

    for s in SCENARIOS:
        sid = s["id"]

        # Compter les choix de TOUS les joueurs (y compris 0)
        choice_counts: dict[str, int] = {c["label"]: 0 for c in s["choices"]}
        nb_played = 0
        for p in players:
            data = p.get("completed_scenes", {}).get(sid)
            if data:
                nb_played += 1
                label = data.get("chosen_label", "")
                if label in choice_counts:
                    choice_counts[label] += 1

        label_header = f"J{s['day']} — {s['title']}  ({nb_played}/{nb_total} joueurs)"
        with st.expander(label_header, expanded=False):
            if nb_played == 0:
                st.caption("Personne n'a encore joué cette mission.")
                continue

            # Construire le DataFrame avec tous les choix
            outcome_map = {c["label"]: c["outcome"] for c in s["choices"]}
            rows = []
            for c in s["choices"]:
                lbl   = c["label"]
                count = choice_counts[lbl]
                pct   = round(count / nb_played * 100) if nb_played else 0
                icon  = _OUTCOME_ICON.get(outcome_map.get(lbl, ""), "")
                rows.append({
                    "Résultat": icon,
                    "Choix":    lbl,
                    "Joueurs":  count,
                    "%":        pct,
                })
            df = pd.DataFrame(rows)

            # Tableau de résultats
            st.dataframe(
                df[["Résultat", "Choix", "Joueurs", "%"]].rename(columns={"%": "% joueurs"}),
                use_container_width=True, hide_index=True,
            )

            # Camembert centré et grand
            df_pie = df.copy()
            df_pie["label_court"] = df_pie["Choix"].str[:35]
            pie = (
                alt.Chart(df_pie)
                .mark_arc(innerRadius=60, outerRadius=180)
                .encode(
                    theta=alt.Theta("Joueurs:Q"),
                    color=alt.Color(
                        "label_court:N",
                        scale=alt.Scale(
                            range=["#2A52BE", "#F59E0B", "#EF4444", "#10B981"]
                        ),
                        legend=alt.Legend(
                            title="Réponses",
                            orient="bottom",
                            columns=1,
                            labelLimit=400,
                        ),
                    ),
                    tooltip=["Choix:N", "Joueurs:Q",
                             alt.Tooltip("%:Q", title="% joueurs")],
                )
                .properties(width=460, height=420, title="")
            )
            _, col_center, _ = st.columns([1, 3, 1])
            with col_center:
                st.altair_chart(pie, use_container_width=True)


# ── Carte de session ─────────────────────────────────────────────────

def _render_session_card(session: dict) -> None:
    import pandas as pd

    nb      = session.get("nb_players", 0)
    code    = session["code"]
    date_s  = _format_date(session.get("created_at"))
    company = session.get("company_name", "") or ""
    sid     = session["id"]

    try:
        base = st.context.url.split("?")[0].rstrip("/")
        link = f"{base}?session={code}" if base else f"?session={code}"
    except Exception:
        link = f"?session={code}"

    company_pill = f'<div class="tr-stat-pill">🏢 {company}</div>' if company else ""
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
        {company_pill}
      </div>
    </div>
    """)

    # ── Supprimer la session ─────────────────────────────────────────
    confirm_key = f"_confirm_del_sess_{sid}"
    if not st.session_state.get(confirm_key):
        if st.button("🗑️ Supprimer la session", key=f"del_sess_{sid}"):
            st.session_state[confirm_key] = True
            st.rerun()
    else:
        st.warning(f"Supprimer **{session['name']}** ? Les joueurs resteront dans la base.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Oui, supprimer", key=f"confirm_sess_{sid}", type="primary"):
                delete_session(sid, st.session_state.user_id)
                del st.session_state[confirm_key]
                st.rerun()
        with c2:
            if st.button("Annuler", key=f"cancel_sess_{sid}"):
                del st.session_state[confirm_key]
                st.rerun()

    # Lien à partager
    st.markdown(
        '<p style="font-family:Inter,sans-serif;font-size:12px;font-weight:600;'
        'color:#64748B;margin:6px 0 4px;">🔗 Lien à envoyer aux joueurs</p>',
        unsafe_allow_html=True,
    )
    st.code(link, language=None)

    if nb == 0:
        st.caption("Aucun joueur n'a encore rejoint cette session.")
        return

    players = get_session_players(code)

    # ── Onglets ──────────────────────────────────────────────────────
    tab_joueurs, tab_stats, tab_export = st.tabs(
        ["👥 Joueurs", "📊 Stats par question", "⬇️ Export CSV"]
    )

    # ── Tab Joueurs ──────────────────────────────────────────────────
    with tab_joueurs:
        for p in players:
            pid = p["id"]
            cs = p.get("completed_scenes", {})
            nb_ok  = sum(1 for v in cs.values() if v.get("outcome") == "success")
            nb_war = sum(1 for v in cs.values() if v.get("outcome") == "neutral")
            nb_err = sum(1 for v in cs.values() if v.get("outcome") == "danger")

            detail_key = f"_detail_{pid}_{sid}"
            del_key    = f"_del_player_{pid}_{sid}"

            c_name, c_score, c_mis, c_res, c_voir, c_del = st.columns([3, 1, 1.5, 2.5, 1.2, 1.2])
            with c_name:
                st.markdown(f"**{p.get('display_name', '?')}**")
                st.caption(p.get("username", ""))
            with c_score:
                st.markdown(f"**{p.get('score', 0)}** pts")
            with c_mis:
                st.markdown(f"{len(cs)}/{len(SCENARIOS)} missions")
            with c_res:
                st.markdown(f"✅{nb_ok} ⚠️{nb_war} 🚨{nb_err}")
            with c_voir:
                label = "▲ Fermer" if st.session_state.get(detail_key) else "👁️ Détail"
                if st.button(label, key=f"voir_{pid}_{sid}"):
                    st.session_state[detail_key] = not st.session_state.get(detail_key, False)
                    st.rerun()
            with c_del:
                if not st.session_state.get(del_key):
                    if st.button("🗑️ Suppr.", key=f"del_p_{pid}_{sid}"):
                        st.session_state[del_key] = True
                        st.rerun()
                else:
                    st.warning("Confirmer ?")
                    if st.button("✓ Oui", key=f"ok_del_p_{pid}_{sid}", type="primary"):
                        delete_player(pid, st.session_state.user_id)
                        if detail_key in st.session_state:
                            del st.session_state[detail_key]
                        del st.session_state[del_key]
                        st.rerun()
                    if st.button("✕", key=f"cancel_del_p_{pid}_{sid}"):
                        del st.session_state[del_key]
                        st.rerun()

            if st.session_state.get(detail_key, False):
                _render_player_detail(p)

            st.divider()

    # ── Tab Stats ────────────────────────────────────────────────────
    with tab_stats:
        _render_question_stats(players)

    # ── Tab Export ───────────────────────────────────────────────────
    with tab_export:
        csv_data = _build_csv(players)
        safe_name = session["name"].replace(" ", "_")[:30]
        st.download_button(
            label="⬇️ Exporter cette session (CSV)",
            data=csv_data.encode("utf-8-sig"),
            file_name=f"session_{safe_name}_{code}.csv",
            mime="text/csv",
            key=f"csv_{code}",
        )


# ── Création de session ──────────────────────────────────────────────

def _render_create_session() -> None:
    with st.expander("➕ Créer une nouvelle session", expanded=False):
        name = st.text_input("Nom de la session", placeholder="ex : Formation Cyber — Équipe RH",
                              key="new_session_name")
        st.markdown(
            '<div style="font-family:Inter,sans-serif;font-size:11px;font-weight:700;'
            'color:#64748B;letter-spacing:.5px;text-transform:uppercase;margin:10px 0 4px;">'
            'Entreprise imposée aux joueurs '
            '<span style="font-weight:400;color:#CBD5E1">(optionnel)</span></div>',
            unsafe_allow_html=True,
        )
        company_name = st.text_input(
            "company_session", placeholder="ex : NovaCorp",
            label_visibility="collapsed", key="new_session_company",
        )
        if st.button("Créer la session", key="create_session_btn", type="primary"):
            if not name.strip():
                st.error("Donne un nom à la session.")
            else:
                code = create_session(st.session_state.user_id, name, company_name)
                st.session_state["_new_session_code"] = code
                st.rerun()

    if "_new_session_code" in st.session_state:
        code = st.session_state.pop("_new_session_code")
        st.success(f"✅ Session créée ! Code : **{code}**")


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
    else:
        for session in sessions:
            _render_session_card(session)
            st.markdown("")

        # ── Export global tous apprenants ────────────────────────────
        st.markdown("---")
        st.markdown("### 📦 Export global — tous les apprenants")
        all_players = get_all_trainer_players(st.session_state.user_id)
        if all_players:
            csv_global = _build_csv(all_players, include_session=True)
            st.download_button(
                label=f"⬇️ Exporter tous les apprenants ({len(all_players)} au total)",
                data=csv_global.encode("utf-8-sig"),
                file_name="export_global_apprenants.csv",
                mime="text/csv",
                key="csv_global",
            )
        else:
            st.caption("Aucun apprenant inscrit pour l'instant.")

    # ── Déconnexion ──────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Se déconnecter", key="trainer_logout"):
        from core.db import delete_auth_token
        _tok = st.query_params.get("auth", "")
        if _tok:
            delete_auth_token(_tok)
            del st.query_params["auth"]
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
