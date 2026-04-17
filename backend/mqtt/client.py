import json
import threading
import paho.mqtt.client as mqtt
from config import MQTT_BROKER, MQTT_PORT, GPS_TOPIC
from backend.core.logger import log

_client = None
_lock = threading.Lock()
_gps_callback = None


def _on_connect(client, userdata, flags, rc):
    if rc == 0:
        log(f"✅ MQTT connected to {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(GPS_TOPIC)
        log(f"📡 Subscribed to topic: {GPS_TOPIC}")
    else:
        log(f"❌ MQTT connection failed with code {rc}", "error")


def _on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        log(f"📩 MQTT message on [{msg.topic}]: {payload}")
        if _gps_callback:
            _gps_callback(payload)
    except json.JSONDecodeError as e:
        log(f"⚠️  MQTT message decode error: {e}", "warning")


def _on_disconnect(client, userdata, rc):
    if rc != 0:
        log(f"⚠️  MQTT disconnected unexpectedly (rc={rc})", "warning")


def init_mqtt(gps_callback=None):
    global _client, _gps_callback
    _gps_callback = gps_callback

    with _lock:
        _client = mqtt.Client(client_id="SmartEVP_Backend")
        _client.on_connect = _on_connect
        _client.on_message = _on_message
        _client.on_disconnect = _on_disconnect

        try:
            _client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            _client.loop_start()
            log("🔌 MQTT client loop started")
        except Exception as e:
            log(f"❌ MQTT init error: {e}", "error")


def publish(topic: str, payload: str):
    with _lock:
        if _client is None:
            log("⚠️  MQTT client not initialized — skipping publish", "warning")
            return
        try:
            result = _client.publish(topic, payload)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                log(f"📤 Published to [{topic}]: {payload}")
            else:
                log(f"⚠️  Publish failed (rc={result.rc})", "warning")
        except Exception as e:
            log(f"❌ MQTT publish error: {e}", "error")


def stop_mqtt():
    with _lock:
        if _client:
            _client.loop_stop()
            _client.disconnect()
            log("🔌 MQTT client stopped")
