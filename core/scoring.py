from config import (
    RISK_LOW_THRESHOLD,
    RISK_MEDIUM_THRESHOLD,
)

# Score max = 16 × 7 = 112  |  Risk max = 16 × 6 = 96
SCORE_MAX = 112
RISK_MAX  = 96

# risk_delta in scenarios is already the exact contribution (6 for danger, 0 otherwise)
_RISK_SCALE = 1.0


def clamp(value: int, minimum: int = 0, maximum: int = 100) -> int:
    return max(minimum, min(maximum, value))


def apply_score_change(
    current_score: int,
    current_risk: int,
    score_delta: int,
    risk_delta: int,
) -> tuple[int, int, int]:
    new_score = clamp(current_score + score_delta, 0, SCORE_MAX)
    risk_contribution = max(0, round(risk_delta * _RISK_SCALE))
    new_risk = clamp(current_risk + risk_contribution, 0, RISK_MAX)
    return new_score, new_risk, risk_contribution


def get_player_profile(score: int, risk: int) -> dict:
    """Retourne le profil joueur (8 niveaux) selon le score et le risque final."""

    # Level 8 — score parfait ET risque nul
    if score >= SCORE_MAX and risk == 0:
        return {
            "level": 8,
            "badge": "👑",
            "title": "L'Élite Cyber",
            "comment": (
                "Score parfait, risque nul. Tu as déjoué chaque menace sans exception "
                "et sans compromis. Une maîtrise absolue des réflexes de sécurité. "
                "NovaCorp t'offre le poste de Référent Cybersécurité."
            ),
            "color": "#7C3AED",
            "bg": "linear-gradient(135deg,#F5F3FF,#EDE9FE)",
            "border": "#C4B5FD",
            "bar_color": "#7C3AED",
        }

    # Calculer le niveau de base selon le score
    pct = score / SCORE_MAX
    if pct >= 0.90:
        level = 7
    elif pct >= 0.80:
        level = 6
    elif pct >= 0.66:
        level = 5
    elif pct >= 0.51:
        level = 4
    elif pct >= 0.36:
        level = 3
    elif pct >= 0.20:
        level = 2
    else:
        level = 1

    # Le risque peut abaisser le niveau
    risk_pct = risk / RISK_MAX
    if risk_pct > 0.75:
        level = min(level, 1)
    elif risk_pct > 0.50:
        level = min(level, 2)

    _PROFILES = {
        7: {
            "badge": "🏰",
            "title": "Le Rempart Humain",
            "comment": (
                "Excellente performance. Tu constitues une barrière solide contre les cybermenaces. "
                "Quelques rares situations t'ont eu, mais tu restes un acteur clé "
                "de la sécurité de NovaCorp."
            ),
            "color": "#1D4ED8",
            "bg": "linear-gradient(135deg,#EFF6FF,#DBEAFE)",
            "border": "#93C5FD",
            "bar_color": "#2A52BE",
        },
        6: {
            "badge": "👁️",
            "title": "Le Gardien Averti",
            "comment": (
                "Très bonne vigilance. Tu détectes la grande majorité des menaces. "
                "Quelques angles morts subsistent mais le niveau est clairement au-dessus "
                "de la moyenne. Continue à progresser."
            ),
            "color": "#0E7490",
            "bg": "linear-gradient(135deg,#ECFEFF,#CFFAFE)",
            "border": "#67E8F9",
            "bar_color": "#0E7490",
        },
        5: {
            "badge": "🛡️",
            "title": "L'Employé Perfectible",
            "comment": (
                "Bonne base de vigilance. Tu reconnais les menaces courantes mais "
                "certaines situations complexes t'ont piégé. Une formation ciblée "
                "t'amènerait au niveau supérieur."
            ),
            "color": "#166534",
            "bg": "linear-gradient(135deg,#F0FDF4,#DCFCE7)",
            "border": "#86EFAC",
            "bar_color": "#16A34A",
        },
        4: {
            "badge": "🎲",
            "title": "L'Électron Libre",
            "comment": (
                "Résultat contrasté. Tes décisions sont parfois bonnes, parfois risquées "
                "sans logique apparente. Il te manque un cadre systématique pour identifier "
                "et réagir aux menaces."
            ),
            "color": "#92400E",
            "bg": "linear-gradient(135deg,#FFFBEB,#FEF3C7)",
            "border": "#FCD34D",
            "bar_color": "#F59E0B",
        },
        3: {
            "badge": "⚠️",
            "title": "Le Vecteur de Vulnérabilité",
            "comment": (
                "Résultat préoccupant. Tu as mordu à des pièges qui auraient pu être évités. "
                "NovaCorp t'inscrit en priorité au programme de sensibilisation renforcé."
            ),
            "color": "#B45309",
            "bg": "linear-gradient(135deg,#FFF7ED,#FFEDD5)",
            "border": "#FDBA74",
            "bar_color": "#EA580C",
        },
        2: {
            "badge": "🔥",
            "title": "Le Générateur d'Incidents",
            "comment": (
                "Résultat alarmant. Plusieurs de tes décisions ont mis NovaCorp en danger réel. "
                "Une remise à niveau urgente en cybersécurité s'impose immédiatement."
            ),
            "color": "#9A3412",
            "bg": "linear-gradient(135deg,#FFF7ED,#FED7AA)",
            "border": "#FB923C",
            "bar_color": "#DC2626",
        },
        1: {
            "badge": "💀",
            "title": "Le Fléau de NovaCorp",
            "comment": (
                "Résultat critique. Tu as mordu à presque tous les hameçons et exposé l'entreprise "
                "à des risques graves. Une formation complète et obligatoire est requise "
                "en urgence absolue."
            ),
            "color": "#991B1B",
            "bg": "linear-gradient(135deg,#FFF5F5,#FFE4E6)",
            "border": "#FCA5A5",
            "bar_color": "#EF4444",
        },
    }

    profile = _PROFILES[level]
    profile["level"] = level
    return profile


def get_risk_label(human_risk: int) -> str:
    if human_risk < RISK_LOW_THRESHOLD:
        return "🟢 Faible"
    if human_risk < RISK_MEDIUM_THRESHOLD:
        return "🟠 Moyen"
    return "🔴 Élevé"
