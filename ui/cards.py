from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

_DIFF_CLASS = {"Facile": "diff-facile", "Moyen": "diff-moyen", "Difficile": "diff-difficile"}


def _load(name: str, **kwargs) -> str:
    return (TEMPLATES_DIR / name).read_text(encoding="utf-8").format(**kwargs)


def hero_card_html(hero: dict, day: int, difficulty: str) -> str:
    diff_class = _DIFF_CLASS.get(difficulty, "diff-facile")
    return (
        f'<div class="hero-banner {hero["css_class"]}">'
        f'<div class="hero-emoji">{hero["emoji"]}</div>'
        f'<div class="hero-body" style="flex:1">'
        f'<div class="hero-badges">'
        f'<span class="hero-cat-badge">{hero["label"]}</span>'
        f'<span class="{diff_class}">{difficulty}</span>'
        f'</div>'
        f'<div class="hero-day">Jour {day}</div>'
        f'</div>'
        f'</div>'
    )


def render_score_card(title: str, value: str) -> None:
    st.html(_load("score_card.html", title=title, value=value))


def scene_card_html(title: str, body: str) -> str:
    return _load("scene_card.html", title=title, body=body)


def dialogue_html(speaker: str, text: str, avatar: str = "💬") -> str:
    return _load("dialogue.html", speaker=speaker, text=text, avatar=avatar)


def artifact_html(artifact: dict) -> str:
    kind = artifact["type"]
    if kind == "email":
        sl = artifact["sender"][0].upper() if artifact["sender"] else "?"
        return _load("email_card.html", sender=artifact["sender"],
                     recipient=artifact["recipient"], subject=artifact["subject"],
                     body=artifact["body"], sender_letter=sl)
    if kind == "file":
        return _load("file_card.html", icon=artifact["icon"], label=artifact["label"],
                     filename=artifact["filename"], detail=artifact["detail"])
    if kind == "phone":
        return _load("phone_card.html", icon=artifact["icon"], caller=artifact["caller"],
                     label=artifact["label"], detail=artifact["detail"])
    if kind == "popup":
        return _load("popup_card.html", title=artifact["title"], message=artifact["message"],
                     timer=artifact["timer"], button_text=artifact["button_text"])
    if kind == "chat":
        msgs_html = "".join(f'<div class="chat-bubble">{m}</div>' for m in artifact["messages"])
        return _load("chat_card.html", sender=artifact["sender"],
                     avatar=artifact["avatar"], messages_html=msgs_html)
    if kind == "wifi":
        return _load("wifi_card.html", icon=artifact["icon"], ssid=artifact["ssid"],
                     detail=artifact["detail"], security=artifact["security"])
    if kind == "form":
        return _load("form_card.html", title=artifact["title"],
                     field_label=artifact["field_label"], field_value=artifact["field_value"],
                     hint=artifact["hint"])
    return ""


def render_consequence(outcome: str, title: str, feedback: str, story: str) -> None:
    css_class = {"danger": "danger-screen", "success": "success-screen"}.get(outcome, "neutral-screen")
    emoji     = {"danger": "🚨", "success": "✅"}.get(outcome, "ℹ️")
    st.html(_load("consequence.html", css_class=css_class, emoji=emoji,
                  title=title, feedback=feedback, story=story))


def render_lesson(lesson: str) -> None:
    st.markdown(_load("lesson.html", lesson=lesson), unsafe_allow_html=True)
