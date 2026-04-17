import json
import requests
from config import OLLAMA_URL, OLLAMA_MODEL
from backend.core.logger import log

FALLBACK_RESPONSE = {
    "location": "unknown",
    "severity": "HIGH",
    "symptoms": "unknown",
    "raw_text": "",
}

PROMPT_TEMPLATE = """You are an emergency dispatch AI. Extract structured data from the following emergency report.

Return ONLY a valid JSON object with these exact keys:
- "location": string (place name or address)
- "severity": one of "LOW", "MEDIUM", "HIGH"
- "symptoms": string (brief description)

Emergency report: "{text}"

JSON only. No explanation. No markdown. No extra text."""


def parse_emergency(text: str) -> dict:
    prompt = PROMPT_TEMPLATE.format(text=text)
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        raw_output = data.get("response", "").strip()

        start = raw_output.find("{")
        end = raw_output.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON object found in Ollama response")

        json_str = raw_output[start:end]
        parsed = json.loads(json_str)

        result = {
            "location": str(parsed.get("location", "unknown")),
            "severity": str(parsed.get("severity", "HIGH")).upper(),
            "symptoms": str(parsed.get("symptoms", "unknown")),
            "raw_text": text,
        }

        if result["severity"] not in ("LOW", "MEDIUM", "HIGH"):
            result["severity"] = "HIGH"

        log(f"🧠 Parser → location={result['location']}, severity={result['severity']}, symptoms={result['symptoms']}")
        return result

    except requests.exceptions.ConnectionError:
        log("⚠️  Ollama not reachable — using fallback parser response", "warning")
    except requests.exceptions.Timeout:
        log("⚠️  Ollama request timed out — using fallback", "warning")
    except (json.JSONDecodeError, ValueError) as e:
        log(f"⚠️  Parser JSON error: {e} — using fallback", "warning")
    except Exception as e:
        log(f"⚠️  Parser unexpected error: {e} — using fallback", "warning")

    fallback = dict(FALLBACK_RESPONSE)
    fallback["raw_text"] = text
    return fallback
