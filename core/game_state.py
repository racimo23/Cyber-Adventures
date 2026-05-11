import streamlit as st

from config import (
    INITIAL_SECURITY_SCORE,
    INITIAL_HUMAN_RISK,
)


def init_game_state() -> None:
    """
    Initialise toutes les variables nécessaires au jeu.
    Streamlit relance le script à chaque clic, donc on utilise st.session_state
    pour garder la mémoire du joueur.
    """

    if "score" not in st.session_state:
        st.session_state.score = INITIAL_SECURITY_SCORE

    if "risk" not in st.session_state:
        st.session_state.risk = INITIAL_HUMAN_RISK

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


def reset_scene() -> None:
    """
    Réinitialise la scène actuelle.
    Pour l'instant, on revient au score initial.
    Plus tard, on distinguera reset scène et reset partie complète.
    """

    st.session_state.score = INITIAL_SECURITY_SCORE
    st.session_state.risk = INITIAL_HUMAN_RISK
    st.session_state.answered = False
    st.session_state.outcome = None
    st.session_state.feedback = ""
    st.session_state.lesson = ""
    st.session_state.consequence_title = ""
    st.session_state.consequence_story = ""


def set_outcome(
    outcome: str,
    feedback: str,
    consequence_title: str,
    consequence_story: str,
    lesson: str,
) -> None:
    """
    Enregistre la conséquence narrative du choix du joueur.
    """

    st.session_state.outcome = outcome
    st.session_state.feedback = feedback
    st.session_state.consequence_title = consequence_title
    st.session_state.consequence_story = consequence_story
    st.session_state.lesson = lesson
    st.session_state.answered = True