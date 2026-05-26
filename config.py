APP_TITLE = "CyberOnboard Adventures"
APP_ICON = "🛡️"
COMPANY_NAME = "NovaCorp"

INITIAL_SECURITY_SCORE = 0
INITIAL_HUMAN_RISK = 0

# Risk thresholds (0–96 scale: 16 scenes × 6 max risk each)
RISK_LOW_THRESHOLD = 34
RISK_MEDIUM_THRESHOLD = 62

# Each scene: success = +7 pts, neutral = +4 pts, danger = +0 pts
# 16 scenes × 7 pts max = 112
SCORE_SUCCESS = 7
SCORE_NEUTRAL = 4
SCORE_DANGER = 0

DEPARTMENTS = [
    "RH",
    "Finance",
    "Commercial",
    "IT",
    "Direction",
    "Juridique",
]
