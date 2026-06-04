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


def render_hero_card(hero: dict, day: int, difficulty: str) -> None:
    st.html(hero_card_html(hero, day, difficulty))


def render_score_card(title: str, value: str) -> None:
    st.html(_load("score_card.html", title=title, value=value))


def scene_card_html(title: str, body: str) -> str:
    return _load("scene_card.html", title=title, body=body)


def render_scene_card(title: str, body: str) -> None:
    st.html(scene_card_html(title, body))


def dialogue_html(speaker: str, text: str, avatar: str = "💬") -> str:
    return _load("dialogue.html", speaker=speaker, text=text, avatar=avatar)


def render_dialogue(speaker: str, text: str, avatar: str = "💬") -> None:
    st.html(dialogue_html(speaker, text, avatar))


def artifact_html(artifact: dict) -> str:
    """Retourne le HTML de l'artefact sans le rendre (pour cache)."""
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


def render_email_card(sender: str, recipient: str, subject: str, body: str) -> None:
    sl = sender[0].upper() if sender else "?"
    st.html(_load("email_card.html", sender=sender, recipient=recipient,
                  subject=subject, body=body, sender_letter=sl))


def render_file_card(icon, label, filename, detail): st.html(_load("file_card.html", icon=icon, label=label, filename=filename, detail=detail))
def render_phone_card(icon, caller, label, detail): st.html(_load("phone_card.html", icon=icon, caller=caller, label=label, detail=detail))
def render_popup_card(title, message, timer, button_text): st.html(_load("popup_card.html", title=title, message=message, timer=timer, button_text=button_text))
def render_wifi_card(icon, ssid, detail, security): st.html(_load("wifi_card.html", icon=icon, ssid=ssid, detail=detail, security=security))
def render_form_card(title, field_label, field_value, hint): st.html(_load("form_card.html", title=title, field_label=field_label, field_value=field_value, hint=hint))


def render_chat_card(sender: str, avatar: str, messages: list) -> None:
    msgs_html = "".join(f'<div class="chat-bubble">{m}</div>' for m in messages)
    st.html(_load("chat_card.html", sender=sender, avatar=avatar, messages_html=msgs_html))


def render_consequence(outcome: str, title: str, feedback: str, story: str) -> None:
    css_class = {"danger": "danger-screen", "success": "success-screen"}.get(outcome, "neutral-screen")
    emoji     = {"danger": "🚨", "success": "✅"}.get(outcome, "ℹ️")
    st.html(_load("consequence.html", css_class=css_class, emoji=emoji,
                  title=title, feedback=feedback, story=story))


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
