from config import DISTANCE_THRESHOLD, PREDICTIVE_MULTIPLIER, ARRIVED_THRESHOLD
from backend.core.logger import log

PREDICTIVE_THRESHOLD = DISTANCE_THRESHOLD * PREDICTIVE_MULTIPLIER


def make_decision(parsed_data: dict, distance: float) -> dict:
    severity = parsed_data.get("severity", "HIGH").upper()

    dispatch = severity == "HIGH"
    predictive_trigger = distance < PREDICTIVE_THRESHOLD
    hard_trigger = distance < DISTANCE_THRESHOLD
    arrived = distance < ARRIVED_THRESHOLD

    decision = {
        "dispatch": dispatch,
        "trigger_signal": predictive_trigger,
        "predictive_trigger": predictive_trigger,
        "hard_trigger": hard_trigger,
        "arrived": arrived,
        "severity": severity,
        "distance_m": round(distance, 2),
        "predictive_threshold_m": PREDICTIVE_THRESHOLD,
        "hard_threshold_m": DISTANCE_THRESHOLD,
    }

    zone = (
        "ARRIVED" if arrived
        else "INSIDE_HARD_THRESHOLD" if hard_trigger
        else "INSIDE_PREDICTIVE_ZONE" if predictive_trigger
        else "EN_ROUTE"
    )

    log(
        f"🤖 Decision → severity={severity}, zone={zone}, "
        f"dispatch={dispatch}, trigger_signal={predictive_trigger}, distance={round(distance, 2)}m"
    )
    return decision
