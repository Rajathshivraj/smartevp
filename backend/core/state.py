import threading

_lock = threading.Lock()

_state = {
    "latest_gps": None,
    "signal_state": "RED",
    "signal_triggered": False,
    "active_case": None,
    "distance_m": None,
    "stage": "IDLE",
}

STAGES = ("IDLE", "DISPATCHED", "EN_ROUTE", "APPROACHING", "SIGNAL_TRIGGERED", "ARRIVED")


def get_state():
    with _lock:
        return dict(_state)


def set_latest_gps(coords: tuple):
    with _lock:
        _state["latest_gps"] = coords


def set_signal_state(state: str):
    with _lock:
        _state["signal_state"] = state


def mark_signal_triggered():
    with _lock:
        _state["signal_triggered"] = True
        _state["signal_state"] = "GREEN"


def is_signal_triggered() -> bool:
    with _lock:
        return _state["signal_triggered"]


def set_distance(distance: float):
    with _lock:
        _state["distance_m"] = round(distance, 2)


def set_stage(stage: str):
    if stage not in STAGES:
        return
    with _lock:
        _state["stage"] = stage


def set_active_case(case: dict):
    with _lock:
        _state["active_case"] = case
        _state["stage"] = "DISPATCHED"


def clear_active_case():
    with _lock:
        _state["active_case"] = None
        _state["signal_state"] = "RED"
        _state["signal_triggered"] = False
        _state["latest_gps"] = None
        _state["distance_m"] = None
        _state["stage"] = "IDLE"
