import random

import streamlit as st
import streamlit.components.v1 as components

from core.scoring import apply_score_change, get_risk_label, get_player_profile, SCORE_MAX, RISK_MAX
from core.game_state import set_outcome, reset_scene, advance_scene, return_to_map, reset_game_progress
from data.scenarios import SCENARIOS, resolve_scenario
from ui.cards import (
    render_hero_card,
    render_score_card,
    render_scene_card,
    render_dialogue,
    render_email_card,
    render_file_card,
    render_phone_card,
    render_popup_card,
    render_chat_card,
    render_wifi_card,
    render_form_card,
    render_consequence,
    render_lesson,
)


# ── Helpers ───────────────────────────────────────────────────────



def _get_shuffled_choices(choices: list) -> list:
    key = f"choices_order_{st.session_state.scene_index}"
    if key not in st.session_state:
        order = list(range(len(choices)))
        random.shuffle(order)
        st.session_state[key] = order
    return [choices[i] for i in st.session_state[key]]


def _render_artifact(artifact: dict) -> None:
    kind = artifact["type"]
    if kind == "email":
        render_email_card(artifact["sender"], artifact["recipient"], artifact["subject"], artifact["body"])
    elif kind == "file":
        render_file_card(artifact["icon"], artifact["label"], artifact["filename"], artifact["detail"])
    elif kind == "phone":
        render_phone_card(artifact["icon"], artifact["caller"], artifact["label"], artifact["detail"])
    elif kind == "popup":
        render_popup_card(artifact["title"], artifact["message"], artifact["timer"], artifact["button_text"])
    elif kind == "chat":
        render_chat_card(artifact["sender"], artifact["avatar"], artifact["messages"])
    elif kind == "wifi":
        render_wifi_card(artifact["icon"], artifact["ssid"], artifact["detail"], artifact["security"])
    elif kind == "form":
        render_form_card(artifact["title"], artifact["field_label"], artifact["field_value"], artifact["hint"])


def _render_learn_more(url: str, title: str) -> None:
    st.markdown(
        f'<a href="{url}" target="_blank" rel="noopener noreferrer" class="learn-more-link">'
        f'<div class="learn-more-card">'
        f'<div class="learn-more-icon">📚</div>'
        f'<div class="learn-more-body">'
        f'<div class="learn-more-label">Pour aller plus loin</div>'
        f'<div class="learn-more-title">{title}</div>'
        f'</div>'
        f'<div class="learn-more-arrow">↗</div>'
        f'</div>'
        f'</a>',
        unsafe_allow_html=True,
    )


def _render_indices(indices: list) -> None:
    with st.expander("💡 Voir les indices"):
        items_html = "".join(
            f'<div class="index-item">{item}</div>' for item in indices
        )
        st.markdown(f'<div class="indices-list">{items_html}</div>', unsafe_allow_html=True)


def _render_choices_recap(choices: list, chosen_label: str) -> None:
    _OUTCOME_CONFIG = {
        "success": ("✅", "recap-success", "BONNE RÉPONSE"),
        "danger":  ("🚨", "recap-danger",  "MAUVAIS CHOIX"),
        "neutral": ("ℹ️", "recap-neutral",  "RISQUÉ"),
    }
    items_html = ""
    for choice in choices:
        outcome = choice["outcome"]
        is_chosen = choice["label"] == chosen_label
        icon, css_class, outcome_text = _OUTCOME_CONFIG.get(outcome, ("❓", "recap-neutral", "?"))
        chosen_class = " recap-chosen" if is_chosen else ""
        badge = f'<span class="recap-badge">{outcome_text}</span>' if is_chosen else ""
        items_html += (
            f'<div class="recap-choice {css_class}{chosen_class}">'
            f'<span class="recap-icon">{icon}</span>'
            f'<span class="recap-label">{choice["label"]}</span>'
            f'{badge}'
            f'</div>'
        )
    st.markdown(
        f'<div class="choices-recap">'
        f'<div class="recap-title">Récapitulatif des choix</div>'
        f'{items_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def _render_score_delta() -> None:
    delta = st.session_state.score_delta_last
    if delta > 0:
        st.markdown(
            f'<div class="score-delta-positive">+{delta} pts</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="score-delta-zero">+0 pt</div>',
            unsafe_allow_html=True,
        )


def _render_timer(seconds: int) -> None:
    timer_html = f"""
    <div id="timer-bar" style="
        background:#FFF5F5;border:2px solid #FCA5A5;border-radius:12px;
        padding:12px 20px;display:flex;align-items:center;
        justify-content:space-between;margin-bottom:18px;
        font-family:'Inter',sans-serif;
        animation:timerPulse 1.2s ease-in-out infinite;
    ">
        <span style="color:#DC2626;font-size:13px;font-weight:600;">
            ⏳ L'attaquant attend ta réponse…
        </span>
        <span id="timer-val" style="color:#DC2626;font-size:26px;font-weight:800;font-family:'Courier New',monospace;">
            {seconds}
        </span>
    </div>
    <style>
    @keyframes timerPulse {{
        0%,100% {{ border-color:#FCA5A5; box-shadow:none; }}
        50%      {{ border-color:#EF4444; box-shadow:0 0 14px rgba(239,68,68,0.22); }}
    }}
    </style>
    <script>
    (function() {{
        var remaining = {seconds};
        var el = document.getElementById('timer-val');
        var bar = document.getElementById('timer-bar');
        var interval = setInterval(function() {{
            remaining--;
            if (el) el.textContent = remaining;
            if (remaining <= 10 && bar) {{
                bar.style.background = '#FEE2E2';
            }}
            if (remaining <= 0) {{
                clearInterval(interval);
                var btns = window.parent.document.querySelectorAll('button[kind="secondary"]');
                for (var i = 0; i < btns.length; i++) {{
                    if (btns[i].textContent.trim() !== '' && !btns[i].disabled) {{
                        btns[i].click();
                        break;
                    }}
                }}
            }}
        }}, 1000);
    }})();
    </script>
    """
    components.html(timer_html, height=80)


# ── Navigation breadcrumb ─────────────────────────────────────────

def _render_breadcrumb(scenario: dict) -> None:
    """Bouton retour à la carte + info scène en cours."""
    left, right = st.columns([1, 5])
    with left:
        if st.button("← Carte", key="back_to_map_top", use_container_width=True):
            return_to_map()
            st.rerun()
    with right:
        scene_num = st.session_state.scene_index + 1
        total     = len(SCENARIOS)
        completed = len(st.session_state.completed_scenes)
        st.markdown(
            f'<div style="display:flex;align-items:center;height:38px;'
            f'font-family:Inter,sans-serif;font-size:13px;color:#64748B;">'
            f'<span>Scène {scene_num}/{total} · '
            f'<strong style="color:#2A52BE">{scenario["title"]}</strong> · '
            f'{completed} mission(s) terminée(s)</span>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ── End game ──────────────────────────────────────────────────────

def _render_endgame() -> None:
    score     = st.session_state.score
    risk      = st.session_state.risk
    profile   = get_player_profile(score, risk)
    completed = len(st.session_state.completed_scenes)

    outcomes   = [v["outcome"] for v in st.session_state.completed_scenes.values()]
    nb_success = outcomes.count("success")
    nb_neutral = outcomes.count("neutral")
    nb_danger  = outcomes.count("danger")

    score_pct = round(score / SCORE_MAX * 100)
    risk_pct  = round(risk / RISK_MAX * 100)

    html = (
        f'<div class="endgame-profile-card" style="background:{profile["bg"]};border-color:{profile["border"]};">'
        f'<div class="endgame-profile-badge">{profile["badge"]}</div>'
        f'<div class="endgame-profile-level" style="color:{profile["color"]};">Niveau {profile["level"]} / 8</div>'
        f'<div class="endgame-profile-title" style="color:{profile["color"]};">{profile["title"]}</div>'
        f'<div class="endgame-profile-comment">« {profile["comment"]} »</div>'
        f'<div class="endgame-bars">'
        f'<div class="endgame-bar-row">'
        f'<span class="endgame-bar-label">Score sécurité</span>'
        f'<span class="endgame-bar-val" style="color:{profile["color"]};">{score}/{SCORE_MAX}</span>'
        f'</div>'
        f'<div class="endgame-bar-track">'
        f'<div class="endgame-bar-fill" style="--target-w:{score_pct}%;background:{profile["bar_color"]};"></div>'
        f'</div>'
        f'<div class="endgame-bar-row" style="margin-top:14px;">'
        f'<span class="endgame-bar-label">Risque humain</span>'
        f'<span class="endgame-bar-val" style="color:#DC2626;">{risk}/{RISK_MAX} — {get_risk_label(risk)}</span>'
        f'</div>'
        f'<div class="endgame-bar-track">'
        f'<div class="endgame-bar-fill" style="--target-w:{risk_pct}%;background:#EF4444;"></div>'
        f'</div>'
        f'</div>'
        f'<div class="endgame-stats">'
        f'<div><div class="endgame-stat-label">Missions</div><div class="endgame-stat-value">{completed}/{len(SCENARIOS)}</div></div>'
        f'<div><div class="endgame-stat-label">Succès</div><div class="endgame-stat-value" style="color:#15803D;">✅ {nb_success}</div></div>'
        f'<div><div class="endgame-stat-label">Risqués</div><div class="endgame-stat-value" style="color:#B45309;">⚠️ {nb_neutral}</div></div>'
        f'<div><div class="endgame-stat-label">Échecs</div><div class="endgame-stat-value" style="color:#991B1B;">🚨 {nb_danger}</div></div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗺️ Revoir la carte", use_container_width=True):
            st.session_state.current_scene = None
            st.rerun()
    with col2:
        if st.button("🔁 Rejouer", use_container_width=True):
            reset_game_progress()
            st.rerun()


# ── Core logic ────────────────────────────────────────────────────

def handle_choice(choice: dict) -> None:
    new_score, new_risk, risk_contribution = apply_score_change(
        current_score=st.session_state.score,
        current_risk=st.session_state.risk,
        score_delta=choice["score_delta"],
        risk_delta=choice["risk_delta"],
    )
    st.session_state.score = new_score
    st.session_state.risk  = new_risk
    set_outcome(
        outcome=choice["outcome"],
        feedback=choice["feedback"],
        consequence_title=choice["consequence_title"],
        consequence_story=choice["consequence_story"],
        lesson=choice["lesson"],
        chosen_label=choice["label"],
        score_delta=choice["score_delta"],
        risk_delta=risk_contribution,
    )


# ── Main view ─────────────────────────────────────────────────────

def render_game_view() -> None:
    if st.session_state.scene_index >= len(SCENARIOS):
        _render_endgame()
        return

    scenario  = resolve_scenario(SCENARIOS[st.session_state.scene_index])
    total     = len(SCENARIOS)
    completed = len(st.session_state.completed_scenes)

    # Breadcrumb navigation
    _render_breadcrumb(scenario)
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # Progression
    st.markdown(
        f"<div style='color:#64748B;font-size:13px;margin-bottom:4px;"
        f"font-family:Inter,sans-serif;'>"
        f"{completed} / {total} scènes terminées</div>",
        unsafe_allow_html=True,
    )
    st.progress(completed / total)
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    render_hero_card(hero=scenario["hero"], day=scenario["day"], difficulty=scenario["difficulty"])

    score_col, risk_col, status_col = st.columns(3)
    with score_col:
        render_score_card("Score sécurité", f"{st.session_state.score}/{SCORE_MAX}")
    with risk_col:
        render_score_card("Risque humain", f"{st.session_state.risk}/{RISK_MAX}")
    with status_col:
        render_score_card("Niveau de risque", get_risk_label(st.session_state.risk))

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    left_col, right_col = st.columns([1.2, 1])
    with left_col:
        render_scene_card(scenario["scene_card"]["title"], scenario["scene_card"]["body"])
        for dialogue in scenario["dialogues"]:
            render_dialogue(
                speaker=dialogue["speaker"],
                text=dialogue["text"],
                avatar=dialogue.get("avatar", "💬"),
            )
    with right_col:
        _render_artifact(scenario["artifact"])
        if not st.session_state.answered:
            _render_indices(scenario.get("indices", []))

    # ── Choix (avant réponse) ──────────────────────────────────────
    if not st.session_state.answered:
        timer_seconds = scenario.get("timer")
        if timer_seconds:
            _render_timer(timer_seconds)

        st.markdown("## 🎮 Que fais-tu ?")
        shuffled = _get_shuffled_choices(scenario["choices"])
        n = len(shuffled)
        if n == 4:
            row1 = st.columns(2)
            row2 = st.columns(2)
            grid = [row1[0], row1[1], row2[0], row2[1]]
        else:
            grid = st.columns(n)
        for idx, choice in enumerate(shuffled):
            with grid[idx]:
                if st.button(choice["label"], use_container_width=True, key=f"choice_{idx}"):
                    handle_choice(choice)
                    st.rerun()

    # ── Résultat (après réponse) ───────────────────────────────────
    else:
        shuffled = _get_shuffled_choices(scenario["choices"])
        _render_score_delta()
        render_consequence(
            outcome=st.session_state.outcome,
            title=st.session_state.consequence_title,
            feedback=st.session_state.feedback,
            story=st.session_state.consequence_story,
        )
        render_lesson(st.session_state.lesson)
        learn_url   = scenario.get("learn_more_url", "")
        learn_title = scenario.get("learn_more_title", "")
        if learn_url:
            _render_learn_more(learn_url, learn_title)
        _render_choices_recap(shuffled, st.session_state.chosen_label)

        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔁 Rejouer", use_container_width=True):
                key = f"choices_order_{st.session_state.scene_index}"
                if key in st.session_state:
                    del st.session_state[key]
                reset_scene()
                st.rerun()
        with col2:
            if st.button("🗺️ Retour à la carte", use_container_width=True, key="back_map_bottom"):
                return_to_map()
                st.rerun()
        with col3:
            is_last = st.session_state.scene_index >= len(SCENARIOS) - 1
            label = "🏁 Bilan final →" if is_last else "✅ Valider →"
            if st.button(label, use_container_width=True):
                advance_scene()
                st.rerun()
