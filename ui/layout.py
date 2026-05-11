import streamlit as st


CUSTOM_CSS = """
<style>
.main {
    background-color: #0f172a;
}

.game-title {
    font-size: 42px;
    font-weight: 800;
    color: #e5e7eb;
    margin-bottom: 0px;
}

.subtitle {
    color: #94a3b8;
    font-size: 18px;
    margin-bottom: 25px;
}

.scene-card {
    background: linear-gradient(135deg, #1e293b, #111827);
    padding: 24px;
    border-radius: 20px;
    border: 1px solid #334155;
    box-shadow: 0 10px 30px rgba(0,0,0,0.35);
    color: #e5e7eb;
    margin-bottom: 20px;
}

.dialogue-box {
    background-color: #020617;
    padding: 18px;
    border-radius: 16px;
    border-left: 5px solid #38bdf8;
    color: #e5e7eb;
    margin-bottom: 15px;
}

.character-name {
    color: #38bdf8;
    font-weight: 800;
    font-size: 18px;
}

.email-card {
    background-color: #f8fafc;
    color: #0f172a;
    padding: 22px;
    border-radius: 16px;
    border-left: 6px solid #f97316;
    box-shadow: 0 8px 24px rgba(0,0,0,0.25);
    margin-top: 15px;
    margin-bottom: 20px;
}

.email-header {
    font-size: 15px;
    color: #334155;
    margin-bottom: 8px;
}

.email-subject {
    font-size: 22px;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 15px;
}

.danger-screen {
    background: linear-gradient(135deg, #7f1d1d, #450a0a);
    padding: 28px;
    border-radius: 20px;
    border: 1px solid #ef4444;
    color: #fee2e2;
    box-shadow: 0 10px 35px rgba(127,29,29,0.45);
    margin-top: 20px;
}

.success-screen {
    background: linear-gradient(135deg, #14532d, #052e16);
    padding: 28px;
    border-radius: 20px;
    border: 1px solid #22c55e;
    color: #dcfce7;
    box-shadow: 0 10px 35px rgba(20,83,45,0.45);
    margin-top: 20px;
}

.neutral-screen {
    background: linear-gradient(135deg, #1e3a8a, #172554);
    padding: 28px;
    border-radius: 20px;
    border: 1px solid #60a5fa;
    color: #dbeafe;
    box-shadow: 0 10px 35px rgba(30,58,138,0.45);
    margin-top: 20px;
}

.lesson-card {
    background-color: #020617;
    color: #e5e7eb;
    padding: 22px;
    border-radius: 16px;
    border: 1px solid #334155;
    margin-top: 20px;
}

.score-card {
    background-color: #020617;
    padding: 16px;
    border-radius: 16px;
    border: 1px solid #334155;
    color: #e5e7eb;
    text-align: center;
}

.big-emoji {
    font-size: 56px;
    margin-bottom: 10px;
}
</style>
"""


def apply_global_styles() -> None:
    """
    Injecte le CSS global de l'application.
    """
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_header(title: str, subtitle: str) -> None:
    """
    Affiche le titre principal du jeu.
    """
    st.markdown(
        f'<div class="game-title">{title}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="subtitle">{subtitle}</div>',
        unsafe_allow_html=True,
    )