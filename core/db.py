import streamlit as st
import pandas as pd
from sqlalchemy import text


def _is_db_configured() -> bool:
    """Return True only if secrets.toml contains a [connections.supabase] block."""
    try:
        _ = st.secrets["connections"]["supabase"]
        return True
    except (KeyError, FileNotFoundError):
        return False


def _get_conn():
    return st.connection("supabase", type="sql")


def save_session(
    player_name: str,
    campaign_id: str,
    score: int,
    risk: int,
    profile_title: str,
    profile_badge: str,
    nb_success: int,
    nb_neutral: int,
    nb_danger: int,
) -> bool:
    """
    Insert a completed game session into Supabase.
    Silently returns False if Supabase is not configured or the insert fails.
    """
    if not _is_db_configured():
        return False
    try:
        conn = _get_conn()
        with conn.session as s:
            s.execute(
                text(
                    "INSERT INTO game_sessions "
                    "(player_name, campaign_id, score, risk, "
                    " profile_title, profile_badge, "
                    " nb_success, nb_neutral, nb_danger) "
                    "VALUES "
                    "(:pn, :cid, :sc, :ri, :pt, :pb, :ns, :nn, :nd)"
                ),
                {
                    "pn":  player_name or "Anonyme",
                    "cid": campaign_id or None,
                    "sc":  score,
                    "ri":  risk,
                    "pt":  profile_title,
                    "pb":  profile_badge,
                    "ns":  nb_success,
                    "nn":  nb_neutral,
                    "nd":  nb_danger,
                },
            )
            s.commit()
        return True
    except Exception as e:
        st.warning(f"⚠️ Impossible de sauvegarder la session : {e}")
        return False


def get_campaign_sessions(campaign_id: str) -> pd.DataFrame:
    """
    Fetch all sessions matching campaign_id, ordered by score descending.
    Returns an empty DataFrame if Supabase is not configured or the query fails.
    """
    if not _is_db_configured():
        return pd.DataFrame()
    try:
        conn = _get_conn()
        df = conn.query(
            "SELECT player_name, score, risk, profile_badge, profile_title, "
            "nb_success, nb_neutral, nb_danger, created_at "
            "FROM game_sessions "
            "WHERE campaign_id = :cid "
            "ORDER BY score DESC, risk ASC",
            params={"cid": campaign_id.strip().upper()},
            ttl=0,  # always fetch fresh data for live dashboards
        )
        return df
    except Exception as e:
        st.error(f"Erreur lors de la lecture des données : {e}")
        return pd.DataFrame()
