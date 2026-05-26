import streamlit as st

from config import (
    INITIAL_SECURITY_SCORE,
    INITIAL_HUMAN_RISK,
)
from core.scoring import clamp, SCORE_MAX, RISK_MAX


def _base_score_excl(exclude_id: str) -> int:
    """Score total sans la contribution de la scène exclue."""
    total = INITIAL_SECURITY_SCORE + sum(
        v["score_delta"]
        for sid, v in st.session_state.completed_scenes.items()
        if sid != exclude_id
    )
    return clamp(total, 0, SCORE_MAX)


def _base_risk_excl(exclude_id: str) -> int:
    """Risque total sans la contribution de la scène exclue."""
    total = INITIAL_HUMAN_RISK + sum(
        v.get("risk_delta", 0)
        for sid, v in st.session_state.completed_scenes.items()
        if sid != exclude_id
    )
    return clamp(total, 0, RISK_MAX)


def init_game_state() -> None:
    if "score" not in st.session_state:
        st.session_state.score = INITIAL_SECURITY_SCORE
    if "risk" not in st.session_state:
        st.session_state.risk = INITIAL_HUMAN_RISK
    if "scene_index" not in st.session_state:
        st.session_state.scene_index = 0
    if "scene_start_score" not in st.session_state:
        st.session_state.scene_start_score = INITIAL_SECURITY_SCORE
    if "scene_start_risk" not in st.session_state:
        st.session_state.scene_start_risk = INITIAL_HUMAN_RISK
    if "answered" not in st.session_state:
        st.session_state.answered = False
    if "outcome" not in st.session_state:
        st.session_state.outcome = None
    if "feedback" not in st.session_state:
        st.session_state.feedback = ""
    if "lesson" not in st.session_state:
        st.session_state.lesson = ""
    if "consequence_title" not in st.session_state:
        st.session_state.consequence_title = ""
    if "consequence_story" not in st.session_state:
        st.session_state.consequence_story = ""
    if "chosen_label" not in st.session_state:
        st.session_state.chosen_label = ""
    if "score_delta_last" not in st.session_state:
        st.session_state.score_delta_last = 0
    if "risk_delta_last" not in st.session_state:
        st.session_state.risk_delta_last = 0
    if "timer_expired" not in st.session_state:
        st.session_state.timer_expired = False
    # ── Map / Hub ────────────────────────────────────────────────
    if "current_scene" not in st.session_state:
        st.session_state.current_scene = None  # None → affiche la carte
    if "max_unlocked_scene" not in st.session_state:
        st.session_state.max_unlocked_scene = 0  # index de la dernière scène débloquée
    if "completed_scenes" not in st.session_state:
        st.session_state.completed_scenes = {}  # {scene_id: {"score_delta": int, "outcome": str}}
    # ── Campagne multijoueur ──────────────────────────────────────
    if "game_started" not in st.session_state:
        st.session_state.game_started = False   # False → affiche l'écran d'accueil
    if "player_name" not in st.session_state:
        st.session_state.player_name = "Anonyme"
    if "campaign_id" not in st.session_state:
        st.session_state.campaign_id = ""       # "" → mode solo anonyme
    if "session_saved" not in st.session_state:
        st.session_state.session_saved = False  # True → résultats déjà envoyés à Supabase


def _clear_outcome() -> None:
    st.session_state.answered = False
    st.session_state.outcome = None
    st.session_state.feedback = ""
    st.session_state.lesson = ""
    st.session_state.consequence_title = ""
    st.session_state.consequence_story = ""
    st.session_state.chosen_label = ""
    st.session_state.score_delta_last = 0
    st.session_state.risk_delta_last = 0
    st.session_state.timer_expired = False


def reset_scene() -> None:
    """Rejouer la scène depuis le début (revert score/risque au début de la scène)."""
    st.session_state.score = st.session_state.scene_start_score
    st.session_state.risk = st.session_state.scene_start_risk
    key = f"choices_order_{st.session_state.scene_index}"
    if key in st.session_state:
        del st.session_state[key]
    _clear_outcome()


def select_scene(scene_index: int) -> None:
    """Naviguer depuis la carte vers une scène spécifique."""
    from data.scenarios import SCENARIOS
    scene_id   = SCENARIOS[scene_index]["id"]
    base_score = _base_score_excl(scene_id)
    base_risk  = _base_risk_excl(scene_id)
    st.session_state.current_scene       = scene_index
    st.session_state.scene_index         = scene_index
    st.session_state.score               = base_score
    st.session_state.risk                = base_risk
    st.session_state.scene_start_score   = base_score
    st.session_state.scene_start_risk    = base_risk
    key = f"choices_order_{scene_index}"
    if key in st.session_state:
        del st.session_state[key]
    _clear_outcome()


def return_to_map() -> None:
    """Quitter la scène en cours et revenir à la carte."""
    from data.scenarios import SCENARIOS
    if st.session_state.answered:
        # Player already answered — save outcome and keep score/risk
        scene_id = SCENARIOS[st.session_state.scene_index]["id"]
        st.session_state.completed_scenes[scene_id] = {
            "score_delta": st.session_state.score_delta_last,
            "risk_delta":  st.session_state.risk_delta_last,
            "outcome":     st.session_state.outcome,
        }
        next_idx = st.session_state.scene_index + 1
        if next_idx > st.session_state.max_unlocked_scene:
            st.session_state.max_unlocked_scene = next_idx
    else:
        # Left mid-scene without answering — revert score
        st.session_state.score = st.session_state.scene_start_score
        st.session_state.risk  = st.session_state.scene_start_risk
    st.session_state.current_scene = None
    _clear_outcome()


def advance_scene() -> None:
    """Valider la scène : sauvegarder le résultat, passer directement à la scène suivante."""
    from data.scenarios import SCENARIOS
    scene_id = SCENARIOS[st.session_state.scene_index]["id"]
    st.session_state.completed_scenes[scene_id] = {
        "score_delta": st.session_state.score_delta_last,
        "risk_delta":  st.session_state.risk_delta_last,
        "outcome":     st.session_state.outcome,
    }
    next_idx = st.session_state.scene_index + 1
    if next_idx > st.session_state.max_unlocked_scene:
        st.session_state.max_unlocked_scene = next_idx
    # Aller directement à la scène suivante (ou au bilan final)
    st.session_state.scene_index         = next_idx
    st.session_state.current_scene       = next_idx
    st.session_state.scene_start_score   = st.session_state.score
    st.session_state.scene_start_risk    = st.session_state.risk
    key = f"choices_order_{next_idx}"
    if key in st.session_state:
        del st.session_state[key]
    _clear_outcome()


def set_outcome(
    outcome: str,
    feedback: str,
    consequence_title: str,
    consequence_story: str,
    lesson: str,
    chosen_label: str = "",
    score_delta: int = 0,
    risk_delta: int = 0,
) -> None:
    st.session_state.outcome            = outcome
    st.session_state.feedback           = feedback
    st.session_state.consequence_title  = consequence_title
    st.session_state.consequence_story  = consequence_story
    st.session_state.lesson             = lesson
    st.session_state.chosen_label       = chosen_label
    st.session_state.score_delta_last   = score_delta
    st.session_state.risk_delta_last    = risk_delta
    st.session_state.answered           = True
