import random

import streamlit as st
import streamlit.components.v1 as components

from core.scoring import apply_score_change, get_player_profile, SCORE_MAX
from core.game_state import set_outcome, advance_scene, return_to_map, reset_game_progress
from data.scenarios import SCENARIOS, resolve_scenario, _resolve_cached
from ui.cards import (
    hero_card_html,
    artifact_html,
    scene_card_html,
    dialogue_html,
    render_score_card,
    render_consequence,
    render_lesson,
)


# ── Helpers ───────────────────────────────────────────────────────



@st.cache_data(show_spinner=False)
def _cached_left_col_html(scene_index: int, company: str, player: str, gender: str = "f") -> str:
    """Scène card + dialogues en un seul bloc HTML — calculé une fois par scène/utilisateur."""
    s = _resolve_cached(scene_index, company, player, gender)
    html = scene_card_html(s["scene_card"]["title"], s["scene_card"]["body"])
    for d in s["dialogues"]:
        html += dialogue_html(d["speaker"], d["text"], d.get("avatar", "💬"))
    return html


@st.cache_data(show_spinner=False)
def _cached_artifact_html(scene_index: int, company: str, player: str, gender: str = "f") -> str:
    """HTML de l'artefact (email/fichier/…) — calculé une fois par scène/utilisateur."""
    s = _resolve_cached(scene_index, company, player, gender)
    return artifact_html(s["artifact"])


@st.cache_data(show_spinner=False)
def _cached_hero_html(scene_index: int, company: str, player: str, gender: str = "f") -> str:
    s = _resolve_cached(scene_index, company, player, gender)
    return hero_card_html(s["hero"], s["day"], s["difficulty"])


def _get_shuffled_choices(choices: list) -> list:
    key = f"choices_order_{st.session_state.scene_index}"
    if key not in st.session_state:
        order = list(range(len(choices)))
        random.shuffle(order)
        st.session_state[key] = order
    return [choices[i] for i in st.session_state[key]]



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
    _OUTCOME_STYLE = {
        "success": {"bg": "#F0FDF4", "border": "#86EFAC", "icon": "✅", "badge": "BONNE RÉPONSE",
                    "label_color": "#14532D", "justif_color": "#166534"},
        "danger":  {"bg": "#FFF5F5", "border": "#FCA5A5", "icon": "🚨", "badge": "MAUVAIS CHOIX",
                    "label_color": "#7F1D1D", "justif_color": "#991B1B"},
        "neutral": {"bg": "#FFFBEB", "border": "#FCD34D", "icon": "ℹ️",  "badge": "RISQUÉ",
                    "label_color": "#78350F", "justif_color": "#92400E"},
    }

    _FONT = "font-family:'Inter',sans-serif;"
    _SIZE = "font-size:14px;line-height:1.55;"

    items_html = ""
    for choice in choices:
        s = _OUTCOME_STYLE.get(choice["outcome"], _OUTCOME_STYLE["neutral"])
        is_chosen = choice["label"] == chosen_label
        border_w  = "2px" if is_chosen else "1.5px"

        badge_html = (
            f'<span style="display:inline-block;{_FONT}font-size:10px;font-weight:700;'
            f'text-transform:uppercase;letter-spacing:.5px;padding:2px 8px;border-radius:99px;'
            f'background:rgba(0,0,0,0.08);color:{s["label_color"]};white-space:nowrap;">'
            f'{s["badge"]}</span>'
        ) if is_chosen else ""

        justification = choice.get("feedback", "")
        justif_html = (
            f'<div style="margin-top:6px;margin-left:28px;padding:5px 10px;'
            f'background:rgba(0,0,0,0.04);border-radius:6px;">'
            f'<span style="{_FONT}{_SIZE}font-weight:400;color:{s["justif_color"]};">'
            f'{justification}</span>'
            f'</div>'
        ) if justification else ""

        items_html += (
            f'<div style="display:block;background:{s["bg"]};border:{border_w} solid {s["border"]};'
            f'border-radius:10px;padding:11px 14px;margin-bottom:8px;">'
            f'<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">'
            f'<span style="font-size:16px;flex-shrink:0;">{s["icon"]}</span>'
            f'<span style="{_FONT}{_SIZE}font-weight:600;color:{s["label_color"]};flex:1;">'
            f'{choice["label"]}</span>'
            f'{badge_html}'
            f'</div>'
            f'{justif_html}'
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
                /* Boutons de navigation à ignorer */
                var NAV = ['carte', 'rejouer', 'retour', 'valider', 'bilan',
                           'quitter', 'indices', 'connecter', 'loin', 'compte'];
                var allBtns = Array.from(window.parent.document.querySelectorAll('button'));
                var choiceBtn = allBtns.find(function(b) {{
                    if (b.disabled) return false;
                    var t = b.textContent.trim().toLowerCase();
                    if (!t) return false;
                    return !NAV.some(function(n) {{ return t.indexOf(n) >= 0; }});
                }});
                if (choiceBtn) choiceBtn.click();
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


# ── Certificate ───────────────────────────────────────────────────

def _generate_certificate(display_name: str, company: str, score: int,
                           nb_missions: int, nb_success: int,
                           profile_title: str) -> bytes:
    from fpdf import FPDF
    from datetime import date
    from pathlib import Path

    FONTS = Path(__file__).parent.parent / "fonts"
    W, H = 297, 210  # A4 paysage mm

    # ── Couleurs ──────────────────────────────────────────────────────
    NAVY   = (11,  29,  82)   # #0B1D52
    BLUE   = (42,  82,  190)  # #2A52BE
    GOLD   = (245, 158, 11)   # #F59E0B
    WHITE  = (255, 255, 255)
    LIGHT  = (239, 246, 255)  # #EFF6FF
    GRAY   = (100, 116, 139)
    DARK   = (30,  41,  59)
    FAINT  = (203, 213, 225)

    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(False)
    pdf.add_page()

    # Polices UTF-8
    pdf.add_font("Sans",     "", str(FONTS / "DejaVuSans.ttf"))
    pdf.add_font("Sans",     "B", str(FONTS / "DejaVuSans-Bold.ttf"))

    # ── Fond blanc ────────────────────────────────────────────────────
    pdf.set_fill_color(*WHITE)
    pdf.rect(0, 0, W, H, "F")

    # ── Panneau gauche navy ───────────────────────────────────────────
    PW = 82   # largeur panneau gauche
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, PW, H, "F")

    # Bande dorée sur le bord gauche
    pdf.set_fill_color(*GOLD)
    pdf.rect(0, 0, 4, H, "F")

    # Bouclier géométrique
    cx, cy = PW / 2, 50
    sw, sh = 26, 30
    sx = cx - sw / 2
    # Corps du bouclier (rectangle arrondi approché)
    pdf.set_fill_color(*WHITE)
    pdf.set_draw_color(*WHITE)
    pdf.rect(sx, cy - sh / 2, sw, sh * 0.72, "F")
    # Pointe basse du bouclier
    pdf.polygon(
        [(sx, cy - sh / 2 + sh * 0.72),
         (sx + sw, cy - sh / 2 + sh * 0.72),
         (cx, cy - sh / 2 + sh)],
        style="F",
    )
    # Lettre centrale
    pdf.set_font("Sans", "B", 14)
    pdf.set_text_color(*NAVY)
    pdf.set_xy(0, cy - 7)
    pdf.cell(PW, 10, "CA", align="C")

    # Nom de l'app
    pdf.set_font("Sans", "B", 13)
    pdf.set_text_color(*WHITE)
    pdf.set_xy(0, 76)
    pdf.cell(PW, 8, "CyberOnboard", align="C")

    pdf.set_font("Sans", "", 9)
    pdf.set_text_color(147, 197, 253)   # bleu clair
    pdf.set_xy(0, 85)
    pdf.cell(PW, 6, "Adventures", align="C")

    # Séparateur doré court
    pdf.set_draw_color(*GOLD)
    pdf.set_line_width(0.8)
    sep_x = (PW - 30) / 2
    pdf.line(sep_x, 95, sep_x + 30, 95)

    # Tagline
    pdf.set_font("Sans", "", 7.5)
    pdf.set_text_color(148, 163, 184)
    pdf.set_xy(0, 98)
    pdf.cell(PW, 5, "Sensibilisation", align="C")
    pdf.set_xy(0, 104)
    pdf.cell(PW, 5, "à la cybersécurité", align="C")

    # Stats verticales dans le panneau gauche
    left_stats = [
        (f"{score}/100", "Score"),
        (f"{nb_missions}/16", "Missions"),
        (str(nb_success), "Réussites"),
    ]
    sy = 122
    for val, lbl in left_stats:
        pdf.set_font("Sans", "B", 16)
        pdf.set_text_color(*GOLD)
        pdf.set_xy(0, sy)
        pdf.cell(PW, 9, val, align="C")
        pdf.set_font("Sans", "", 7)
        pdf.set_text_color(148, 163, 184)
        pdf.set_xy(0, sy + 9)
        pdf.cell(PW, 5, lbl.upper(), align="C")
        sy += 20

    # Date en bas du panneau
    pdf.set_font("Sans", "", 7)
    pdf.set_text_color(100, 116, 139)
    pdf.set_xy(0, H - 14)
    pdf.cell(PW, 5, date.today().strftime("%d/%m/%Y"), align="C")

    # ── Panneau droit (contenu principal) ─────────────────────────────
    RX = PW + 10   # x de départ du contenu droit
    RW = W - RX    # largeur disponible

    # Filigrane décoratif (cercles en haut à droite)
    for i in range(4):
        r = 18 + i * 14
        pdf.set_draw_color(*FAINT)
        pdf.set_line_width(0.3)
        pdf.circle(W - r / 2, -r / 2, r, "D")

    # CERTIFICAT
    pdf.set_font("Sans", "B", 32)
    pdf.set_text_color(*BLUE)
    pdf.set_xy(RX, 28)
    pdf.cell(RW - 10, 18, "CERTIFICAT", align="L")

    # Ligne dorée épaisse sous CERTIFICAT
    pdf.set_draw_color(*GOLD)
    pdf.set_line_width(1.2)
    pdf.line(RX, 48, RX + 90, 48)

    # Sous-titre
    pdf.set_font("Sans", "", 9.5)
    pdf.set_text_color(*GRAY)
    pdf.set_xy(RX, 52)
    pdf.cell(RW - 10, 7, "FORMATION SENSIBILISATION À LA CYBERSÉCURITÉ", align="L")

    # "Décerné à"
    pdf.set_font("Sans", "", 10)
    pdf.set_text_color(*GRAY)
    pdf.set_xy(RX, 70)
    pdf.cell(RW - 10, 7, "Décerné à", align="L")

    # Nom complet
    pdf.set_font("Sans", "B", 28)
    pdf.set_text_color(*DARK)
    pdf.set_xy(RX, 78)
    pdf.cell(RW - 10, 16, display_name, align="L")

    # Ligne dorée sous le nom
    nw = pdf.get_string_width(display_name)
    pdf.set_draw_color(*GOLD)
    pdf.set_line_width(0.6)
    pdf.line(RX, 96, RX + min(nw + 4, RW - 14), 96)

    # Entreprise
    pdf.set_font("Sans", "", 11)
    pdf.set_text_color(*GRAY)
    pdf.set_xy(RX, 100)
    pdf.cell(RW - 10, 7, f"au sein de  {company}", align="L")

    # Profil badge
    pdf.set_font("Sans", "B", 10)
    pdf.set_text_color(*BLUE)
    badge_y = 113
    pdf.set_fill_color(*LIGHT)
    pdf.set_draw_color(*BLUE)
    pdf.set_line_width(0.3)
    badge_w = pdf.get_string_width(f"  {profile_title}  ") + 6
    pdf.rect(RX, badge_y, badge_w, 8, "FD")
    pdf.set_xy(RX, badge_y)
    pdf.cell(badge_w, 8, f"  {profile_title}", align="L")

    # Message de validation
    pdf.set_font("Sans", "", 8.5)
    pdf.set_text_color(*GRAY)
    pdf.set_xy(RX, 130)
    pdf.multi_cell(RW - 14, 5,
        "Ce certificat atteste que la personne mentionnée ci-dessus a complété\n"
        "avec succès le parcours de sensibilisation à la cybersécurité\n"
        "CyberOnboard Adventures.",
        align="L"
    )

    # Ligne de signature
    sig_y = H - 28
    pdf.set_draw_color(*FAINT)
    pdf.set_line_width(0.4)
    pdf.line(RX, sig_y, RX + 55, sig_y)
    pdf.line(RX + 80, sig_y, RX + 135, sig_y)

    pdf.set_font("Sans", "", 7.5)
    pdf.set_text_color(*GRAY)
    pdf.set_xy(RX, sig_y + 2)
    pdf.cell(55, 5, "Responsable formation", align="C")
    pdf.set_xy(RX + 80, sig_y + 2)
    pdf.cell(55, 5, "Responsable cybersécurité", align="C")

    return bytes(pdf.output())


# ── End game ──────────────────────────────────────────────────────

def _render_endgame() -> None:
    score     = st.session_state.score
    profile   = get_player_profile(score)
    completed = len(st.session_state.completed_scenes)

    outcomes   = [v["outcome"] for v in st.session_state.completed_scenes.values()]
    nb_success = outcomes.count("success")
    nb_neutral = outcomes.count("neutral")
    nb_danger  = outcomes.count("danger")
    score_pct  = round(score / SCORE_MAX * 100)

    st.html(
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
        f'</div>'
        f'<div class="endgame-stats">'
        f'<div><div class="endgame-stat-label">Missions</div><div class="endgame-stat-value">{completed}/{len(SCENARIOS)}</div></div>'
        f'<div><div class="endgame-stat-label">Succès</div><div class="endgame-stat-value" style="color:#15803D;">✅ {nb_success}</div></div>'
        f'<div><div class="endgame-stat-label">Risqués</div><div class="endgame-stat-value" style="color:#B45309;">⚠️ {nb_neutral}</div></div>'
        f'<div><div class="endgame-stat-label">Échecs</div><div class="endgame-stat-value" style="color:#991B1B;">🚨 {nb_danger}</div></div>'
        f'</div>'
        f'</div>'
    )

    # ── Certificat PDF ─────────────────────────────────────────────
    display_name = st.session_state.get("display_name") or "Participant"
    company      = st.session_state.get("company_name") or "NovaCorp"
    pdf_bytes    = _generate_certificate(
        display_name, company, score, completed, nb_success, profile["title"]
    )
    st.html("<div style='height:16px'></div>")
    st.download_button(
        label="📄 Télécharger mon certificat (PDF)",
        data=pdf_bytes,
        file_name=f"certificat_{display_name.replace(' ','_')}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

    st.html("<div style='height:8px'></div>")
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
    st.session_state.score = apply_score_change(
        st.session_state.score,
        choice["score_delta"],
    )
    set_outcome(
        outcome=choice["outcome"],
        feedback=choice["feedback"],
        consequence_title=choice["consequence_title"],
        consequence_story=choice["consequence_story"],
        lesson=choice["lesson"],
        chosen_label=choice["label"],
        score_delta=choice["score_delta"],
    )


# ── Main view ─────────────────────────────────────────────────────

def render_game_view() -> None:
    if st.session_state.scene_index >= len(SCENARIOS):
        _render_endgame()
        return

    idx       = st.session_state.scene_index
    company   = st.session_state.get("company_name") or "NovaCorp"
    player    = st.session_state.get("display_name") or "Alice"
    gender    = st.session_state.get("gender", "f")
    scenario  = _resolve_cached(idx, company, player, gender)
    total     = len(SCENARIOS)
    completed = len(st.session_state.completed_scenes)

    # Breadcrumb navigation
    _render_breadcrumb(scenario)

    # Progression — un seul st.html() pour le texte + barre native
    st.html(
        f"<div style='color:#64748B;font-size:13px;margin:10px 0 4px;"
        f"font-family:Inter,sans-serif;'>{completed} / {total} scènes terminées</div>"
    )
    st.progress(completed / total)

    # Hero banner (cached HTML → 1 appel)
    st.html(_cached_hero_html(idx, company, player, gender))

    # Score — 1 seul score card (risque supprimé)
    render_score_card("Score sécurité", f"{st.session_state.score} / {SCORE_MAX}")

    left_col, right_col = st.columns([1.2, 1])
    with left_col:
        # Scène card + dialogues fusionnés en 1 appel HTML caché
        st.html(_cached_left_col_html(idx, company, player, gender))
    with right_col:
        # Artefact en 1 appel HTML caché
        st.html(_cached_artifact_html(idx, company, player, gender))
        if not st.session_state.answered and not st.session_state.get("viewing_completed"):
            _render_indices(scenario.get("indices", []))

    _render_interactive(scenario)


@st.fragment
def _render_interactive(scenario: dict) -> None:
    """Fragment indépendant : seule cette zone se recharge à chaque interaction."""

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
                st.button(
                    choice["label"],
                    use_container_width=True,
                    key=f"choice_{idx}",
                    on_click=handle_choice,
                    args=(choice,),
                )

        # Dès qu'un choix est enregistré, déclenche un rerun complet
        # pour mettre à jour les scores affichés hors du fragment.
        if st.session_state.answered:
            st.rerun()

    # ── Résultat (après réponse) ───────────────────────────────────
    else:
        is_review = st.session_state.get("viewing_completed", False)

        if is_review:
            st.html(
                '<div style="background:#EFF6FF;border:1.5px solid #93C5FD;border-radius:12px;'
                'padding:10px 16px;margin-bottom:16px;font-family:Inter,sans-serif;'
                'display:flex;align-items:center;gap:10px;">'
                '<span style="font-size:18px;">👁️</span>'
                '<div><div style="font-size:13px;font-weight:700;color:#1D4ED8;">Mode révision</div>'
                '<div style="font-size:12px;color:#3B82F6;">Tu consultes ta réponse passée — '
                'elle ne peut pas être modifiée.</div></div>'
                '</div>'
            )

        # En mode révision, afficher les choix dans l'ordre original (sans mélange)
        choices_to_display = scenario["choices"] if is_review else _get_shuffled_choices(scenario["choices"])

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
        _render_choices_recap(choices_to_display, st.session_state.chosen_label)

        st.markdown("<br>", unsafe_allow_html=True)
        if is_review:
            if st.button("🗺️ Retour à la carte", use_container_width=True, key="back_map_review"):
                return_to_map()
                st.rerun()
        else:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗺️ Retour à la carte", use_container_width=True, key="back_map_bottom"):
                    return_to_map()
                    st.rerun()
            with col2:
                is_last = st.session_state.scene_index >= len(SCENARIOS) - 1
                label = "🏁 Bilan final →" if is_last else "✅ Valider →"
                if st.button(label, use_container_width=True):
                    advance_scene()
                    st.rerun()
