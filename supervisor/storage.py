import json
import os
from typing import Dict, Any, List

BASE_DIR = os.path.dirname(__file__)
STATE_PATH = os.path.join(BASE_DIR, "state_store.json")
RUNTIME_LOG_PATH = os.path.join(BASE_DIR, "runtime_log.json")


def _read_json_file(path: str, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write_json_file(path: str, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_all_state() -> Dict[str, Any]:
    return _read_json_file(STATE_PATH, {})


def save_all_state(state: Dict[str, Any]) -> None:
    _write_json_file(STATE_PATH, state)


def get_agent_state(agent_id: str) -> Dict[str, Any]:
    state = load_all_state()

    if agent_id not in state:
        state[agent_id] = {
            "cumulative_risk": 0,
            "shutdown": False,
            "external_attempts": 0,
            "blocked_actions": 0,
            "human_review_count": 0,
            "recent_actions": [],
            "last_decision": None,
            "last_reason": None,
        }
        save_all_state(state)

    return state[agent_id]


def update_agent_state(agent_id: str, agent_state: Dict[str, Any]) -> None:
    state = load_all_state()
    state[agent_id] = agent_state
    save_all_state(state)


def load_runtime_log() -> List[Dict[str, Any]]:
    return _read_json_file(RUNTIME_LOG_PATH, [])


def save_runtime_log(events: List[Dict[str, Any]]) -> None:
    _write_json_file(RUNTIME_LOG_PATH, events)


def append_event(event: Dict[str, Any]) -> None:
    events = load_runtime_log()
    events.append(event)
    save_runtime_log(events)


def reset_all_state() -> None:
    save_all_state({})
    save_runtime_log([])