import streamlit as st


def render_score_card(title: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="score-card">
            <h4>{title}</h4>
            <h2>{value}</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_scene_card(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="scene-card">
            <h2>{title}</h2>
            <p>{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dialogue(speaker: str, text: str) -> None:
    st.markdown(
        f"""
        <div class="dialogue-box">
            <span class="character-name">{speaker}</span><br>
            {text}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_email_card(sender: str, recipient: str, subject: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="email-card">
            <div class="email-header"><strong>De :</strong> {sender}</div>
            <div class="email-header"><strong>À :</strong> {recipient}</div>
            <div class="email-subject">{subject}</div>
            <p>{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_consequence(
    outcome: str,
    title: str,
    feedback: str,
    story: str,
) -> None:
    if outcome == "danger":
        css_class = "danger-screen"
        emoji = "🚨"
    elif outcome == "success":
        css_class = "success-screen"
        emoji = "✅"
    else:
        css_class = "neutral-screen"
        emoji = "ℹ️"

    st.markdown(
        f"""
        <div class="{css_class}">
            <div class="big-emoji">{emoji}</div>
            <h2>{title}</h2>
            <p><strong>{feedback}</strong></p>
            <p>{story}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_lesson(lesson: str) -> None:
    st.markdown(
        f"""
        <div class="lesson-card">
            <h3>📘 Leçon à retenir</h3>
            <p>{lesson}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )