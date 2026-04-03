import json
import os

STATE_FILE = "supervisor/state_store.json"
RISK_THRESHOLD = 100


def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_state(claim_id):
    state = load_state()
    return state.get(claim_id, {
        "cumulative_risk": 0,
        "status": "ACTIVE"
    })


def apply_risk(claim_id, risk_score):
    state = load_state()

    current = state.get(claim_id, {
        "cumulative_risk": 0,
        "status": "ACTIVE"
    })

    new_total = current["cumulative_risk"] + risk_score

    status = "ACTIVE"
    if new_total >= RISK_THRESHOLD:
        status = "CONTAINED"

    updated = {
        "cumulative_risk": new_total,
        "status": status
    }

    state[claim_id] = updated
    save_state(state)

    return updated


def reset_state(claim_id):
    state = load_state()
    state[claim_id] = {
        "cumulative_risk": 0,
        "status": "ACTIVE"
    }
    save_state(state)