from config import INTERSECTION, SIGNAL_TOPIC
from backend.ai.parser import parse_emergency
from backend.ai.decision import make_decision
from core import state as state_store
from backend.core.actions import trigger_signal
from backend.core.logger import log
from backend.utils.distance import haversine_meters

_publish_fn = None
_start_simulation_fn = None


def init_orchestrator(publish_fn, start_simulation_fn):
    global _publish_fn, _start_simulation_fn
    _publish_fn = publish_fn
    _start_simulation_fn = start_simulation_fn
    log("🎛️  Orchestrator initialized")


def handle_emergency(text: str) -> dict:
    log("━" * 52)
    log(f"🚨 [1/4] EMERGENCY CALL RECEIVED")
    log(f"       \"{text}\"")

    parsed = parse_emergency(text)
    log(
        f"🧠 [2/4] PARSED → severity={parsed['severity']}, "
        f"location={parsed['location']}, symptoms={parsed['symptoms']}"
    )

    initial_decision = {
        "dispatch": parsed["severity"] == "HIGH",
        "severity": parsed["severity"],
        "note": "Initial dispatch decision — GPS tracking not yet active",
    }

    log(
        f"🤖 [3/4] DECISION → dispatch={initial_decision['dispatch']}, "
        f"severity={parsed['severity']}"
    )

    state_store.clear_active_case()
    state_store.set_active_case(parsed)

    if initial_decision["dispatch"]:
        log("🚑 [4/4] UNIT DISPATCHED — AMB_001 en route, GPS tracking started")
        state_store.set_stage("EN_ROUTE")
        if _start_simulation_fn:
            _start_simulation_fn(_publish_fn)
    else:
        log(f"📋 [4/4] CASE LOGGED — severity={parsed['severity']}, no dispatch required")

    log("━" * 52)
    return {"parsed": parsed, "decision": initial_decision}


def handle_gps_update(data: dict):
    lat = data.get("lat")
    lon = data.get("lon")

    if lat is None or lon is None:
        log("⚠️  GPS update missing lat/lon — skipping", "warning")
        return

    coords = (float(lat), float(lon))
    state_store.set_latest_gps(coords)

    distance = haversine_meters(coords, INTERSECTION)
    state_store.set_distance(distance)

    active_case = state_store.get_state().get("active_case")
    if active_case is None:
        log("ℹ️  No active case — GPS update ignored")
        return

    decision = make_decision(active_case, distance)
    step = data.get("step", "?")
    total = data.get("total_steps", "?")

    if decision["arrived"]:
        _transition_stage("ARRIVED")
        log(f"🏁 [{step}/{total}] AMB_001 ARRIVED at intersection ({round(distance, 1)}m)")

    elif decision["hard_trigger"]:
        _transition_stage("SIGNAL_TRIGGERED")
        log(f"📍 [{step}/{total}] AMB_001 inside hard zone — {round(distance, 1)}m to intersection")
        trigger_signal(_publish_fn, SIGNAL_TOPIC)

    elif decision["predictive_trigger"]:
        _transition_stage("APPROACHING")
        log(
            f"⚡ [{step}/{total}] AMB_001 APPROACHING — {round(distance, 1)}m "
            f"(predictive zone, threshold={decision['predictive_threshold_m']}m)"
        )
        trigger_signal(_publish_fn, SIGNAL_TOPIC)

    else:
        _transition_stage("EN_ROUTE")
        log(f"🚑 [{step}/{total}] AMB_001 en route — {round(distance, 1)}m to intersection")


def _transition_stage(new_stage: str):
    current = state_store.get_state().get("stage")
    if current != new_stage:
        state_store.set_stage(new_stage)
        log(f"🔄 Stage transition: {current} → {new_stage}")
