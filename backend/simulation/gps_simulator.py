import json
import time
import threading
from config import GPS_TOPIC
from backend.core.logger import log

ROUTE = [
    (12.9550, 77.5700),
    (12.9570, 77.5720),
    (12.9590, 77.5745),
    (12.9610, 77.5770),
    (12.9630, 77.5795),
    (12.9650, 77.5810),
    (12.9665, 77.5830),
    (12.9680, 77.5855),
    (12.9695, 77.5880),
    (12.9700, 77.5900),
    (12.9705, 77.5920),
    (12.9710, 77.5935),
    (12.9714, 77.5942),
    (12.9716, 77.5946),
    (12.9718, 77.5950),
]

_sim_thread = None
_stop_event = threading.Event()


def _run_simulation(publish_fn):
    log("🚑 GPS simulation started — ambulance en route")
    for idx, (lat, lon) in enumerate(ROUTE):
        if _stop_event.is_set():
            log("🛑 GPS simulation stopped early")
            return
        payload = json.dumps({
            "vehicle_id": "AMB_001",
            "lat": lat,
            "lon": lon,
            "step": idx + 1,
            "total_steps": len(ROUTE),
        })
        publish_fn(GPS_TOPIC, payload)
        log(f"📍 GPS step {idx + 1}/{len(ROUTE)}: ({lat}, {lon})")
        time.sleep(1)
    log("✅ GPS simulation complete — ambulance reached destination")


def start_simulation(publish_fn):
    global _sim_thread, _stop_event

    if _sim_thread and _sim_thread.is_alive():
        log("⚠️  Simulation already running", "warning")
        return

    _stop_event.clear()
    _sim_thread = threading.Thread(
        target=_run_simulation,
        args=(publish_fn,),
        daemon=True,
        name="GPSSimulator",
    )
    _sim_thread.start()


def stop_simulation():
    global _stop_event
    _stop_event.set()
    log("🛑 Simulation stop requested")


def is_running() -> bool:
    return _sim_thread is not None and _sim_thread.is_alive()
