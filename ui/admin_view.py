import streamlit as st
import pandas as pd

from core.db import get_campaign_sessions, _is_db_configured
from core.scoring import SCORE_MAX, RISK_MAX


# ── Column display config ─────────────────────────────────────────
_COL_CONFIG = {
    "player_name":   st.column_config.TextColumn("Joueur", width="medium"),
    "score":         st.column_config.ProgressColumn(
                         "Score", min_value=0, max_value=SCORE_MAX, format=f"%d / {SCORE_MAX}"
                     ),
    "risk":          st.column_config.ProgressColumn(
                         "Risque", min_value=0, max_value=RISK_MAX, format=f"%d / {RISK_MAX}"
                     ),
    "profile_badge": st.column_config.TextColumn("Badge", width="small"),
    "profile_title": st.column_config.TextColumn("Profil", width="medium"),
    "nb_success":    st.column_config.NumberColumn("✅ Succès",  width="small"),
    "nb_neutral":    st.column_config.NumberColumn("⚠️ Risqués", width="small"),
    "nb_danger":     st.column_config.NumberColumn("🚨 Échecs",  width="small"),
    "created_at":    st.column_config.DatetimeColumn("Date", format="DD/MM/YYYY HH:mm"),
}

_COL_ORDER = [
    "player_name", "score", "risk",
    "profile_badge", "profile_title",
    "nb_success", "nb_neutral", "nb_danger",
    "created_at",
]


def _render_metrics(df: pd.DataFrame) -> None:
    total     = len(df)
    avg_score = df["score"].mean()
    avg_risk  = df["risk"].mean()
    pct_score = round(avg_score / SCORE_MAX * 100)
    pct_risk  = round(avg_risk  / RISK_MAX  * 100)
    nb_success_total = df["nb_success"].sum()
    nb_danger_total  = df["nb_danger"].sum()
    total_choices = (
        df["nb_success"].sum() + df["nb_neutral"].sum() + df["nb_danger"].sum()
    )
    success_rate = round(nb_success_total / total_choices * 100) if total_choices else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Joueurs", total)
    with c2:
        st.metric("Score moyen", f"{avg_score:.1f} / {SCORE_MAX}", f"{pct_score}%")
    with c3:
        st.metric("Risque moyen", f"{avg_risk:.1f} / {RISK_MAX}", f"-{pct_risk}%", delta_color="inverse")
    with c4:
        st.metric("Taux de succès", f"{success_rate}%")
    with c5:
        top = df.loc[df["score"].idxmax(), "player_name"] if total else "—"
        st.metric("Meilleur score", top)


def _render_badge_chart(df: pd.DataFrame) -> None:
    counts = (
        df.groupby(["profile_badge", "profile_title"])
        .size()
        .reset_index(name="Joueurs")
        .rename(columns={"profile_title": "Profil"})
    )
    counts["label"] = counts["profile_badge"] + " " + counts["Profil"]
    counts = counts.sort_values("Joueurs", ascending=False)

    st.markdown("**Répartition des profils obtenus**")
    chart_data = counts.set_index("label")["Joueurs"]
    st.bar_chart(chart_data, use_container_width=True, height=220)


def _render_score_distribution(df: pd.DataFrame) -> None:
    st.markdown("**Distribution des scores (pts)**")
    hist_df = pd.cut(
        df["score"],
        bins=[0, 22, 40, 57, 74, 90, 101, SCORE_MAX],
        labels=["0–22", "23–40", "41–57", "58–74", "75–90", "91–101", "102–112"],
        right=True,
        include_lowest=True,
    ).value_counts().sort_index().rename("Joueurs")
    st.bar_chart(hist_df, use_container_width=True, height=220)


def _export_csv(df: pd.DataFrame, campaign_id: str) -> None:
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Exporter en CSV",
        data=csv,
        file_name=f"resultats_{campaign_id}.csv",
        mime="text/csv",
        use_container_width=True,
    )


def render_admin_view() -> None:
    """Full admin dashboard — rendered in the main content area."""
    st.markdown(
        """
        <div class="admin-header">
            <div class="admin-header-title">🔐 Dashboard Formateur</div>
            <div class="admin-header-sub">
                Entrez un Code de Campagne pour consulter les résultats de votre groupe.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not _is_db_configured():
        st.error(
            "⚠️ Supabase n'est pas configuré. "
            "Ajoutez vos identifiants dans `.streamlit/secrets.toml` pour activer le dashboard."
        )
        return

    with st.form("admin_form"):
        cid = st.text_input(
            "Code de Campagne",
            placeholder="Ex : NOVA-2026",
            help="Sensible à la casse — la recherche est automatiquement convertie en majuscules.",
        )
        submitted = st.form_submit_button("🔍 Charger les résultats", use_container_width=True)

    if not submitted or not cid.strip():
        return

    campaign_id = cid.strip().upper()
    df = get_campaign_sessions(campaign_id)

    if df.empty:
        st.warning(f"Aucun résultat trouvé pour le code **{campaign_id}**.")
        return

    st.markdown(
        f'<div class="admin-campaign-badge">📋 Campagne : <strong>{campaign_id}</strong> — '
        f'{len(df)} participant(s)</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Metrics ──────────────────────────────────────────────────
    _render_metrics(df)
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts side by side ───────────────────────────────────────
    chart_l, chart_r = st.columns(2)
    with chart_l:
        _render_badge_chart(df)
    with chart_r:
        _render_score_distribution(df)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Results table ─────────────────────────────────────────────
    st.markdown("**Détail des résultats**")
    display_cols = [c for c in _COL_ORDER if c in df.columns]
    st.dataframe(
        df[display_cols],
        column_config=_COL_CONFIG,
        use_container_width=True,
        hide_index=True,
    )

    # ── Export ────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    _export_csv(df[display_cols], campaign_id)
