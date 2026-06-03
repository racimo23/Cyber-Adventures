APP_TITLE = "CyberOnboard Adventures"
APP_ICON = "🛡️"
COMPANY_NAME = "NovaCorp"

INITIAL_SECURITY_SCORE = 0
INITIAL_HUMAN_RISK = 0

# Risk thresholds (0–80 scale: weighted danger risk per scene, max 80)
RISK_LOW_THRESHOLD = 28
RISK_MEDIUM_THRESHOLD = 52

# Score values are weighted per scene (not uniform) — see scenarios.py
# Max score = 100, max risk = 80
SCORE_SUCCESS = 7  # reference only; actual values vary per scene
SCORE_NEUTRAL = 4  # reference only
SCORE_DANGER = 0

DEPARTMENTS = [
    "RH",
    "Finance",
    "Commercial",
    "IT",
    "Direction",
    "Juridique",
]
