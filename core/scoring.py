SCORE_MAX = 100


def clamp(value: int, minimum: int = 0, maximum: int = 100) -> int:
    return max(minimum, min(maximum, value))


def apply_score_change(current_score: int, score_delta: int) -> int:
    return clamp(current_score + score_delta, 0, SCORE_MAX)


def get_player_profile(score: int) -> dict:
    pct = score / SCORE_MAX

    if score >= SCORE_MAX:
        return {
            "level": 8,
            "badge": "👑",
            "title": "L'Élite Cyber",
            "comment": (
                "Score parfait, zéro erreur. Tu as déjoué chaque menace sans exception "
                "et sans compromis. Une maîtrise absolue des réflexes de sécurité."
            ),
            "color": "#7C3AED",
            "bg": "linear-gradient(135deg,#F5F3FF,#EDE9FE)",
            "border": "#C4B5FD",
            "bar_color": "#7C3AED",
        }

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

    _PROFILES = {
        7: {
            "badge": "🏰",
            "title": "Le Rempart Humain",
            "comment": (
                "Excellente performance. Tu constitues une barrière solide contre les cybermenaces. "
                "Quelques rares situations t'ont eu, mais tu restes un acteur clé de la sécurité."
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
                "Quelques angles morts subsistent mais le niveau est clairement au-dessus de la moyenne."
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
                "certaines situations complexes t'ont piégé."
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
                "sans logique apparente."
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
                "Une formation renforcée s'impose."
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
                "Résultat alarmant. Plusieurs de tes décisions ont mis l'entreprise en danger réel. "
                "Une remise à niveau urgente en cybersécurité s'impose."
            ),
            "color": "#9A3412",
            "bg": "linear-gradient(135deg,#FFF7ED,#FED7AA)",
            "border": "#FB923C",
            "bar_color": "#DC2626",
        },
        1: {
            "badge": "💀",
            "title": "Le Fléau",
            "comment": (
                "Résultat critique. Tu as mordu à presque tous les hameçons et exposé l'entreprise "
                "à des risques graves. Une formation complète et obligatoire est requise."
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
