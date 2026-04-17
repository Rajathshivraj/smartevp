import json
from backend.core.logger import log
from core import state as state_store


def trigger_signal(publish_fn, signal_topic: str) -> bool:
    if state_store.is_signal_triggered():
        log("🔒 Signal already triggered this run — skipping duplicate publish")
        return False

    payload = json.dumps({"action": "GREEN", "source": "SmartEVP+", "vehicle": "AMB_001"})
    publish_fn(signal_topic, payload)
    state_store.mark_signal_triggered()
    log("🚦 ═══════════════════════════════════════")
    log("🚦  SIGNAL → GREEN  |  INTERSECTION CLEARED")
    log("🚦 ═══════════════════════════════════════")
    return True


def reset_signal(publish_fn, signal_topic: str):
    payload = json.dumps({"action": "RED", "source": "SmartEVP+", "vehicle": "AMB_001"})
    publish_fn(signal_topic, payload)
    state_store.set_signal_state("RED")
    log("🚦 SIGNAL RESET to RED")
