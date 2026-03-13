from fastapi import FastAPI
from pydantic import BaseModel
import json
from pathlib import Path
from datetime import datetime

app = FastAPI(title="Sentra Supervisor")

LOG_FILE = Path("supervisor/runtime_log.json")


class AgentAction(BaseModel):
    agent_id: str
    action_type: str
    target: str
    data_classification: str
    destination_type: str


def load_logs():
    if LOG_FILE.exists():
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    return []


def save_logs(logs):
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)


def get_cumulative_risk(agent_id, logs):
    total = 0
    for log in logs:
        if log["agent"] == agent_id:
            total += log["risk_score"]
    return total


def log_event(agent, action, risk_score, cumulative_risk, decision, threat_type, rule_triggered):
    event = {
        "agent": agent,
        "action": action,
        "risk_score": risk_score,
        "timestamp": datetime.now().isoformat(),
        "proposed_action": action,
        "threat_type": threat_type,
        "risk": f"+{risk_score}",
        "cum": f"{cumulative_risk}/100",
        "agent_state": decision,
        "rule_triggered": rule_triggered,
        "detail_title": f"Rule Triggered for {action}",
        "detail_body": f"{datetime.now().strftime('%a %b %d %I:%M%p')}: {rule_triggered}"
    }

    logs = load_logs()
    logs.append(event)
    save_logs(logs)


@app.post("/agent-action")
def evaluate_action(action: AgentAction):
    logs = load_logs()

    decision = "ALLOW"
    risk_delta = 0
    threat_type = "NONE"
    rule_triggered = "No rule triggered"

    if action.data_classification == "sensitive" and action.destination_type == "external":
        decision = "BLOCK"
        risk_delta = 80
        threat_type = "DATA_EXFILTRATION"
        rule_triggered = "Sensitive data cannot be sent to an external destination"

    elif action.action_type == "DELETE_FILE":
        decision = "BLOCK"
        risk_delta = 60
        threat_type = "DESTRUCTIVE_ACTION"
        rule_triggered = "DELETE_FILE outside policy boundary"

    cumulative_risk = get_cumulative_risk(action.agent_id, logs) + risk_delta

    if cumulative_risk >= 100 and decision == "ALLOW":
        decision = "REQUIRE_HUMAN_REVIEW"
        threat_type = "RISK_THRESHOLD"
        rule_triggered = "Cumulative risk exceeded review threshold"

    log_event(
        agent=action.agent_id,
        action=action.action_type,
        risk_score=risk_delta,
        cumulative_risk=cumulative_risk,
        decision=decision,
        threat_type=threat_type,
        rule_triggered=rule_triggered
    )

    return {
        "decision": decision,
        "risk_delta": risk_delta,
        "cumulative_risk": cumulative_risk,
        "threat_type": threat_type,
        "rule_triggered": rule_triggered
    }
