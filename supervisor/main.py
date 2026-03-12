from fastapi import FastAPI
from pydantic import BaseModel
import json
from pathlib import Path

app = FastAPI(title="Sentra Supervisor")

# Log file used by the governance dashboard
LOG_FILE = Path("supervisor/runtime_log.json")


class AgentAction(BaseModel):
    agent_id: str
    action_type: str
    target: str
    data_classification: str
    destination_type: str


def log_event(agent, action, risk_score):
    """
    Writes evaluated agent actions to runtime_log.json.
    The Streamlit governance dashboard reads this file to display
    agent behavior and associated risk scores.
    """

    event = {
        "agent": agent,
        "action": action,
        "risk_score": risk_score
    }

    logs = []
    if LOG_FILE.exists():
        logs = json.load(open(LOG_FILE))

    logs.append(event)

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)


@app.post("/agent-action")
def evaluate_action(action: AgentAction):

    decision = "ALLOW"
    risk_delta = 0
    cumulative_risk = 0

    # Example policy rule
    if action.data_classification == "sensitive" and action.destination_type == "external":
        decision = "HALT"
        risk_delta = 80
        cumulative_risk = 80

    # Log the evaluated action so the dashboard can monitor runtime behavior
    log_event(action.agent_id, action.action_type, risk_delta)

    return {
        "decision": decision,
        "risk_delta": risk_delta,
        "cumulative_risk": cumulative_risk
    }
