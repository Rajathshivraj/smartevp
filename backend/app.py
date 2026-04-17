from flask import Flask, request, jsonify
from backend.core.logger import log
from backend.core import state as state_store
from backend.core.orchestrator import init_orchestrator, handle_emergency
from backend.mqtt.client import init_mqtt, publish, stop_mqtt
from backend.simulation.gps_simulator import start_simulation, stop_simulation, is_running

app = Flask(__name__)


def _bootstrap():
    init_mqtt(gps_callback=_on_gps_message)
    init_orchestrator(publish_fn=publish, start_simulation_fn=start_simulation)
    log("🚀 SmartEVP+ backend started — ready for emergency dispatch")


def _on_gps_message(data: dict):
    from backend.core.orchestrator import handle_gps_update
    handle_gps_update(data)


@app.route("/emergency", methods=["POST"])
def emergency():
    body = request.get_json(silent=True)
    if not body or "text" not in body:
        return jsonify({"error": "Missing 'text' field in request body"}), 400

    text = str(body["text"]).strip()
    if not text:
        return jsonify({"error": "'text' field cannot be empty"}), 400

    result = handle_emergency(text)

    return jsonify({
        "status": "dispatched" if result["decision"]["dispatch"] else "logged",
        "parsed": result["parsed"],
        "decision": result["decision"],
        "simulation_started": result["decision"]["dispatch"],
    }), 200


@app.route("/start", methods=["POST"])
def start():
    if is_running():
        return jsonify({"status": "already_running", "message": "Simulation is already active"}), 200

    active_case = state_store.get_state().get("active_case")
    if active_case is None:
        return jsonify({
            "status": "no_active_case",
            "message": "POST /emergency first to register a case before starting simulation",
        }), 400

    start_simulation(publish)
    return jsonify({"status": "started", "message": "GPS simulation started"}), 200


@app.route("/status", methods=["GET"])
def status():
    s = state_store.get_state()

    distance_m = s.get("distance_m")
    stage = s.get("stage", "IDLE")
    active_case = s.get("active_case")

    system_state = _derive_system_state(stage, s["signal_state"], is_running())

    return jsonify({
        "system_state": system_state,
        "stage": stage,
        "signal": {
            "state": s["signal_state"],
            "triggered_this_run": s.get("signal_triggered", False),
        },
        "vehicle": {
            "id": "AMB_001",
            "latest_gps": s["latest_gps"],
            "distance_to_intersection_m": distance_m,
            "simulation_running": is_running(),
        },
        "active_case": active_case,
        "intersection": {"lat": 12.9716, "lon": 77.5946},
    }), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "SmartEVP+"}), 200


def _derive_system_state(stage: str, signal_state: str, sim_running: bool) -> str:
    if stage == "IDLE":
        return "STANDBY"
    if stage == "DISPATCHED":
        return "AWAITING_GPS"
    if stage == "EN_ROUTE":
        return "TRACKING"
    if stage == "APPROACHING":
        return "PREDICTIVE_ACTIVE"
    if stage in ("SIGNAL_TRIGGERED", "ARRIVED"):
        return "INTERSECTION_CLEARED" if signal_state == "GREEN" else "COMPLETING"
    return "UNKNOWN"


if __name__ == "__main__":
    _bootstrap()
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
