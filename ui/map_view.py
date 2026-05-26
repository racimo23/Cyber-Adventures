import streamlit as st

from core.game_state import select_scene
from core.scoring import get_risk_label, SCORE_MAX, RISK_MAX
from data.scenarios import SCENARIOS

_NODES_PER_ROW = 4

_OUTCOME_STYLE = {
    "success": {"bg": "#F0FDF4", "border": "#86EFAC", "icon": "✅", "label": "Succès"},
    "neutral": {"bg": "#FFFBEB", "border": "#FCD34D", "icon": "⚠️", "label": "Risqué"},
    "danger":  {"bg": "#FFF5F5", "border": "#FCA5A5", "icon": "🚨", "label": "Échec"},
}

_DIFF_COLORS = {
    "Facile":    ("#DCFCE7", "#166534"),
    "Moyen":     ("#FEF3C7", "#92400E"),
    "Difficile": ("#FFE4E6", "#9F1239"),
}


def _chunks(lst: list, n: int):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


# ── Header ─────────────────────────────────────────────────────────

def _render_map_header() -> None:
    completed = len(st.session_state.completed_scenes)
    total = len(SCENARIOS)
    score = st.session_state.score
    risk = st.session_state.risk
    all_done = completed == total

    successes = sum(
        1 for v in st.session_state.completed_scenes.values()
        if v["outcome"] == "success"
    )

    title = "🎉 Toutes les missions accomplies !" if all_done else "🗺️ Sélectionne ta mission"
    desc = (
        "Tu as complété toutes les scènes. Consulte ton bilan ou rejoue pour améliorer ton score."
        if all_done
        else "Clique sur une scène débloquée pour commencer. Chaque mission terminée ouvre la suivante."
    )

    st.markdown(f"""
    <div class="map-header-card">
        <div class="map-header-top">
            <div>
                <div class="map-header-title">{title}</div>
                <div class="map-header-desc">{desc}</div>
            </div>
        </div>
        <div class="map-header-stats">
            <div class="map-stat-pill">
                <span class="map-stat-icon">🎯</span>
                <span class="map-stat-text">{completed}/{total} scènes terminées</span>
            </div>
            <div class="map-stat-pill">
                <span class="map-stat-icon">✅</span>
                <span class="map-stat-text">{successes} succès</span>
            </div>
            <div class="map-stat-pill">
                <span class="map-stat-icon">⭐</span>
                <span class="map-stat-text">Score : {score} / {SCORE_MAX}</span>
            </div>
            <div class="map-stat-pill">
                <span class="map-stat-icon">🛡️</span>
                <span class="map-stat-text">Risque : {get_risk_label(risk)}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if all_done:
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        if st.button("🏆 Voir mon bilan final", use_container_width=True):
            st.session_state.current_scene = len(SCENARIOS)
            st.session_state.scene_index = len(SCENARIOS)
            st.rerun()


# ── Score bar ──────────────────────────────────────────────────────

def _render_score_bar() -> None:
    score = st.session_state.score
    pct = round(score / SCORE_MAX * 100)
    color = "#27AE60" if pct >= 60 else "#E67E22" if pct >= 30 else "#E74C3C"
    st.markdown(f"""
    <div class="map-score-bar-wrap">
        <div class="map-score-bar-label">Progression globale — {score}/{SCORE_MAX} pts</div>
        <div class="map-score-bar-track">
            <div class="map-score-bar-fill" style="width:{pct}%;background:{color};"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Single node ────────────────────────────────────────────────────

def _render_node(scene_idx: int, scenario: dict) -> None:
    scene_id   = scenario["id"]
    max_unlocked   = st.session_state.max_unlocked_scene
    completed_data = st.session_state.completed_scenes.get(scene_id)

    is_completed = completed_data is not None
    is_unlocked  = scene_idx <= max_unlocked
    is_next      = scene_idx == max_unlocked and not is_completed

    diff_bg, diff_color = _DIFF_COLORS.get(scenario["difficulty"], ("#F1F5F9", "#64748B"))
    emoji      = scenario["hero"]["emoji"]
    day        = scenario["day"]
    title      = scenario["title"]
    difficulty = scenario["difficulty"]

    if is_completed:
        outcome  = completed_data["outcome"]
        label = (
            f"{emoji}\n\n"
            f"Jour {day} · {difficulty}\n\n"
            f"**{title}**"
        )
        st.markdown(f'<div class="nbm nbm-{outcome}"></div>', unsafe_allow_html=True)
        if st.button(label, key=f"map_btn_{scene_idx}", use_container_width=True):
            select_scene(scene_idx)
            st.rerun()

    elif is_unlocked:
        state    = "active" if is_next else "available"
        prefix   = "▶ " if is_next else ""
        label = (
            f"{emoji}\n\n"
            f"{prefix}Jour {day} · {difficulty}\n\n"
            f"**{title}**"
        )
        st.markdown(f'<div class="nbm nbm-{state}"></div>', unsafe_allow_html=True)
        if st.button(label, key=f"map_btn_{scene_idx}", use_container_width=True):
            select_scene(scene_idx)
            st.rerun()

    else:
        # Locked — HTML card only, not clickable
        has_timer = "timer" in scenario
        timer_html = '<div class="node-timer-badge">⏱ Chrono</div>' if has_timer else ""
        node_html = (
            f'<div class="map-node node-locked" style="background:#F8FAFC;border-color:#E2E8F0;height:190px;">'
            f'<div style="font-size:14px;color:#CBD5E1;align-self:flex-end;margin-bottom:-4px;">🔒</div>'
            f'<div style="font-size:32px;line-height:1;margin:2px 0 6px;">{emoji}</div>'
            f'<div class="node-day">Jour {day}</div>'
            f'<div class="node-title" style="color:#94A3B8;">{title}</div>'
            f'<div class="node-diff" style="background:{diff_bg};color:{diff_color};opacity:.7;">{difficulty}</div>'
            f'{timer_html}'
            f'</div>'
        )
        st.markdown(node_html, unsafe_allow_html=True)


# ── Horizontal connector (arrow between nodes in a row) ───────────

def _render_h_connector(unlocked: bool) -> None:
    color = "#93C5FD" if unlocked else "#CBD5E1"
    st.markdown(f"""
    <div class="map-node-connector-h">
        <div class="connector-h-line" style="background:{color};"></div>
        <div class="connector-h-arrow" style="color:{color};">▶</div>
    </div>
    """, unsafe_allow_html=True)


# ── Vertical connector (bridge between rows) ──────────────────────

def _render_v_connector(row_idx: int, rows: list) -> None:
    # Determine if the last node of the previous row is unlocked
    prev_row     = rows[row_idx - 1]
    last_prev    = prev_row[-1][0]  # scene_idx of last node in prev row
    is_visible   = last_prev < st.session_state.max_unlocked_scene

    line_color  = "#93C5FD" if is_visible else "#E2E8F0"
    arrow_color = "#2A52BE" if is_visible else "#CBD5E1"

    st.markdown(f"""
    <div class="map-row-v-connector">
        <div class="v-connector-line" style="background:{line_color};"></div>
        <div class="v-connector-arrow" style="color:{arrow_color};">↓</div>
        <div class="v-connector-line" style="background:{line_color};"></div>
    </div>
    """, unsafe_allow_html=True)


# ── Main render ────────────────────────────────────────────────────

def render_map() -> None:
    _render_map_header()
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    _render_score_bar()
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    indexed = list(enumerate(SCENARIOS))
    rows    = list(_chunks(indexed, _NODES_PER_ROW))

    for row_idx, row in enumerate(rows):
        # Vertical connector between rows
        if row_idx > 0:
            _render_v_connector(row_idx, rows)

        # Build alternating column widths: [node, arrow, node, arrow, node, ...]
        n = len(row)
        col_widths = []
        for i in range(n):
            col_widths.append(5)
            if i < n - 1:
                col_widths.append(1)

        cols     = st.columns(col_widths)
        col_iter = iter(cols)

        for i, (scene_idx, scenario) in enumerate(row):
            with next(col_iter):
                _render_node(scene_idx, scenario)

            if i < n - 1:
                # Arrow connector column
                right_scene_idx = row[i + 1][0]
                is_conn_active  = right_scene_idx <= st.session_state.max_unlocked_scene
                with next(col_iter):
                    _render_h_connector(is_conn_active)
