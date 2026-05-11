from config import (
    RISK_LOW_THRESHOLD,
    RISK_MEDIUM_THRESHOLD,
)


def clamp(value: int, minimum: int = 0, maximum: int = 100) -> int:
    "Empêche une valeur de dépasser une limite."
    return max(minimum, min(maximum, value))


def apply_score_change(
    current_score: int,
    current_risk: int,
    score_delta: int,
    risk_delta: int,
) -> tuple[int, int]:
    """
    Applique les changements de score et de risque après un choix joueur.
    """
    new_score = clamp(current_score + score_delta)
    new_risk = clamp(current_risk + risk_delta)
    return new_score, new_risk


def get_risk_label(human_risk: int) -> str:
    """
    Transforme un score de risque numérique en niveau lisible.
    """
    if human_risk < RISK_LOW_THRESHOLD:
        return "🟢 Faible"

    if human_risk < RISK_MEDIUM_THRESHOLD:
        return "🟠 Moyen"

    return "🔴 Élevé"