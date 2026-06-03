from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

_DIFF_CLASS = {"Facile": "diff-facile", "Moyen": "diff-moyen", "Difficile": "diff-difficile"}


def _load(name: str, **kwargs) -> str:
    return (TEMPLATES_DIR / name).read_text(encoding="utf-8").format(**kwargs)


def render_hero_card(hero: dict, day: int, difficulty: str) -> None:
    diff_class = _DIFF_CLASS.get(difficulty, "diff-facile")
    html = (
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
    st.markdown(html, unsafe_allow_html=True)


def render_score_card(title: str, value: str) -> None:
    st.markdown(_load("score_card.html", title=title, value=value), unsafe_allow_html=True)


def render_scene_card(title: str, body: str) -> None:
    st.markdown(_load("scene_card.html", title=title, body=body), unsafe_allow_html=True)


def render_dialogue(speaker: str, text: str, avatar: str = "💬") -> None:
    st.markdown(_load("dialogue.html", speaker=speaker, text=text, avatar=avatar), unsafe_allow_html=True)


def render_email_card(sender: str, recipient: str, subject: str, body: str) -> None:
    sender_letter = sender[0].upper() if sender else "?"
    st.markdown(
        _load("email_card.html", sender=sender, recipient=recipient, subject=subject, body=body, sender_letter=sender_letter),
        unsafe_allow_html=True,
    )


def render_file_card(icon: str, label: str, filename: str, detail: str) -> None:
    st.markdown(_load("file_card.html", icon=icon, label=label, filename=filename, detail=detail), unsafe_allow_html=True)


def render_phone_card(icon: str, caller: str, label: str, detail: str) -> None:
    st.markdown(_load("phone_card.html", icon=icon, caller=caller, label=label, detail=detail), unsafe_allow_html=True)


def render_popup_card(title: str, message: str, timer: str, button_text: str) -> None:
    st.markdown(_load("popup_card.html", title=title, message=message, timer=timer, button_text=button_text), unsafe_allow_html=True)


def render_chat_card(sender: str, avatar: str, messages: list) -> None:
    messages_html = "".join(f'<div class="chat-bubble">{msg}</div>' for msg in messages)
    st.markdown(_load("chat_card.html", sender=sender, avatar=avatar, messages_html=messages_html), unsafe_allow_html=True)


def render_wifi_card(icon: str, ssid: str, detail: str, security: str) -> None:
    st.markdown(_load("wifi_card.html", icon=icon, ssid=ssid, detail=detail, security=security), unsafe_allow_html=True)


def render_form_card(title: str, field_label: str, field_value: str, hint: str) -> None:
    st.markdown(_load("form_card.html", title=title, field_label=field_label, field_value=field_value, hint=hint), unsafe_allow_html=True)


def render_consequence(outcome: str, title: str, feedback: str, story: str) -> None:
    if outcome == "danger":
        css_class, emoji = "danger-screen", "🚨"
    elif outcome == "success":
        css_class, emoji = "success-screen", "✅"
    else:
        css_class, emoji = "neutral-screen", "ℹ️"
    st.markdown(
        _load("consequence.html", css_class=css_class, emoji=emoji, title=title, feedback=feedback, story=story),
        unsafe_allow_html=True,
    )


def render_lesson(lesson: str) -> None:
    st.markdown(_load("lesson.html", lesson=lesson), unsafe_allow_html=True)


def render_typewriter_text(text: str, speed: str = "normal") -> None:
    """Affiche du texte lettre par lettre (effet machine à écrire).
    speed: 'slow' (70ms) | 'normal' (35ms) | 'fast' (15ms)
    """
    speed_ms = {"slow": 70, "normal": 35, "fast": 15}.get(speed, 35)
    safe = text.replace("\\", "\\\\").replace("`", "\\`").replace("</", "<\\/")
    html = f"""
<style>
@keyframes tw-blink{{from,to{{opacity:1;}}50%{{opacity:0;}}}}
</style>
<div style="
  background:#ECE5DD;border-radius:0 12px 12px 12px;
  padding:12px 16px 8px;max-width:92%;
  font-size:14px;color:#1A1A1A;line-height:1.6;
  box-shadow:0 1px 4px rgba(0,0,0,0.12);
  font-family:'Inter',sans-serif;word-break:break-word;">
  <span id="tw-out"></span><span id="tw-cur"
    style="color:#075E54;animation:tw-blink .7s step-end infinite;font-weight:700;">▌</span>
</div>
<script>
(function(){{
  var t=`{safe}`,i=0,
      el=document.getElementById('tw-out'),
      cur=document.getElementById('tw-cur');
  function type(){{
    if(i<t.length){{el.textContent+=t[i++];setTimeout(type,{speed_ms});}}
    else{{setTimeout(function(){{cur.style.display='none';}},900);}}
  }}
  type();
}})();
</script>"""
    height = max(80, 52 + (len(text) // 48) * 26)
    components.html(html, height=height)
