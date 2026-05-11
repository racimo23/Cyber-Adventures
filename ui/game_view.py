import streamlit as st

from core.scoring import apply_score_change, get_risk_label
from core.game_state import set_outcome, reset_scene
from data.scenarios import SCENARIOS
from ui.cards import (
    render_score_card,
    render_scene_card,
    render_dialogue,
    render_email_card,
    render_consequence,
    render_lesson,
)


def get_current_scenario() -> dict:
    """
    Pour l'instant, on retourne la première scène.
    Plus tard, on utilisera un index pour gérer plusieurs scènes.
    """
    return SCENARIOS[0]


def handle_choice(choice: dict) -> None:
    """
    Applique les effets du choix du joueur :
    - score
    - risque
    - conséquence narrative
    """

    new_score, new_risk = apply_score_change(
        current_score=st.session_state.score,
        current_risk=st.session_state.risk,
        score_delta=choice["score_delta"],
        risk_delta=choice["risk_delta"],
    )

    st.session_state.score = new_score
    st.session_state.risk = new_risk

    set_outcome(
        outcome=choice["outcome"],
        feedback=choice["feedback"],
        consequence_title=choice["consequence_title"],
        consequence_story=choice["consequence_story"],
        lesson=choice["lesson"],
    )


def render_game_view() -> None:
    scenario = get_current_scenario()

    score_col, risk_col, status_col = st.columns(3)

    with score_col:
        render_score_card("Score sécurité", f"{st.session_state.score}/100")

    with risk_col:
        render_score_card("Risque humain", f"{st.session_state.risk}/100")

    with status_col:
        render_score_card("Niveau de risque", get_risk_label(st.session_state.risk))

    st.markdown("<br>", unsafe_allow_html=True)

    left_col, right_col = st.columns([1.2, 1])

    with left_col:
        render_scene_card(
            scenario["scene_card"]["title"],
            scenario["scene_card"]["body"],
        )

        for dialogue in scenario["dialogues"]:
            render_dialogue(
                speaker=dialogue["speaker"],
                text=dialogue["text"],
            )

    with right_col:
        artifact = scenario["artifact"]

        if artifact["type"] == "email":
            render_email_card(
                sender=artifact["sender"],
                recipient=artifact["recipient"],
                subject=artifact["subject"],
                body=artifact["body"],
            )

    if not st.session_state.answered:
        st.markdown("## 🎮 Que fais-tu ?")

        columns = st.columns(len(scenario["choices"]))

        for index, choice in enumerate(scenario["choices"]):
            with columns[index]:
                if st.button(choice["label"], use_container_width=True):
                    handle_choice(choice)
                    st.rerun()

    else:
        render_consequence(
            outcome=st.session_state.outcome,
            title=st.session_state.consequence_title,
            feedback=st.session_state.feedback,
            story=st.session_state.consequence_story,
        )

        render_lesson(st.session_state.lesson)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔁 Rejouer la scène", use_container_width=True):
                reset_scene()
                st.rerun()

        with col2:
            if st.button("➡️ Continuer l’aventure", use_container_width=True):
                st.info(
                    "La prochaine étape sera d’ajouter plusieurs scènes avec un moteur de progression."
                )