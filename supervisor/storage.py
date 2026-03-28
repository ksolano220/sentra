import json
from pathlib import Path
from datetime import datetime

LOG_FILE = Path("supervisor/runtime_log.json")


def load_logs():
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, "r") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    return []


def write_runtime_event(event: dict) -> dict:
    logs = load_logs()

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        **event
    }

    logs.append(log_entry)

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)

    return log_entry