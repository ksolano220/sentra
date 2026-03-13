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
        if log.get("agent") == agent_id:
            total += log.get("risk_score", 0)
    return total


def now_iso():
    return datetime.now().isoformat()


def now_display():
    return datetime.now().strftime("%a %b %d %I:%M%p")


def now_trace():
    return datetime.now().strftime("%H:%M:%S")


def map_agent_state(decision: str) -> str:
    mapping = {
        "ALLOW": "Running",
        "BLOCK": "Prevented",
        "REQUIRE_HUMAN_REVIEW": "Cancelled",
    }
    return mapping.get(decision, "Running")


def build_system_response(decision: str) -> str:
    if decision == "BLOCK":
        return "Execution blocked by Sentra policy engine"
    if decision == "REQUIRE_HUMAN_REVIEW":
        return "Execution halted pending human review"
    return "Execution allowed and recorded in Sentra audit log"


def log_event(
    agent,
    action,
    target,
    data_classification,
    destination_type,
    risk_score,
    cumulative_risk,
    decision,
    threat_type,
    rule_triggered,
    detail_title,
    detail_body,
    system_response,
    event_trace,
):
    event = {
        "agent": agent,
        "action": action,
        "target": target,
        "data_classification": data_classification,
        "destination_type": destination_type,
        "risk_score": risk_score,
        "timestamp": now_iso(),
        "proposed_action": action,
        "threat_type": threat_type,
        "risk": f"+{risk_score}",
        "cum": f"{cumulative_risk}/100",
        "agent_state": decision,
        "rule_triggered": rule_triggered,
        "detail_title": detail_title,
        "detail_body": detail_body,
        "system_response": system_response,
        "event_trace": event_trace,
    }

    logs = load_logs()
    logs.append(event)
    save_logs(logs)


@app.post("/agent-action")
def evaluate_action(action: AgentAction):
    logs = load_logs()
    trace_time = now_trace()

    decision = "ALLOW"
    risk_delta = 0
    threat_type = "NONE"
    rule_triggered = "NULL"
    detail_title = "NULL"

    event_trace = [
        f"{trace_time} Agent attempted {action.action_type}",
        f"{trace_time} Sentra intercepted tool request",
        f"{trace_time} Target: {action.target}",
    ]

    # Rule evaluation
    if action.data_classification == "sensitive" and action.destination_type == "external":
        decision = "BLOCK"
        risk_delta = 80
        threat_type = "DATA_EXFILTRATION"
        rule_triggered = "Sensitive data cannot be sent to an external destination"
        detail_title = "DATA_EXFILTRATION"

    elif action.action_type == "DELETE_FILE":
        decision = "BLOCK"
        risk_delta = 60
        threat_type = "DESTRUCTIVE_ACTION"
        rule_triggered = "DELETE_FILE outside policy boundary"
        detail_title = "DESTRUCTIVE_ACTION"

    # Trace policy outcome
    if threat_type != "NONE":
        event_trace.append(f"{trace_time} {threat_type} policy triggered")
    else:
        event_trace.append(f"{trace_time} No policy violation detected")

    # Risk trace
    if risk_delta > 0:
        event_trace.append(f"{trace_time} Risk score +{risk_delta} applied")
    else:
        event_trace.append(f"{trace_time} No risk increase applied")

    cumulative_risk = get_cumulative_risk(action.agent_id, logs) + risk_delta

    # Cumulative threshold review
    if cumulative_risk >= 100 and decision == "ALLOW":
        decision = "REQUIRE_HUMAN_REVIEW"
        threat_type = "RISK_THRESHOLD"
        rule_triggered = "Cumulative risk exceeded review threshold"
        detail_title = "RISK_THRESHOLD"
        event_trace.append(f"{trace_time} RISK_THRESHOLD policy triggered")
        event_trace.append(f"{trace_time} Escalated to human review")

    elif decision == "BLOCK":
        event_trace.append(f"{trace_time} Tool execution blocked")

    elif decision == "ALLOW":
        event_trace.append(f"{trace_time} Execution allowed")

    system_response = build_system_response(decision)
    event_trace.append(f"{trace_time} System response: {system_response}")

    detail_body = (
        f"{now_display()}: {rule_triggered}"
        if rule_triggered != "NULL"
        else f"{now_display()}: No rule triggered"
    )

    log_event(
        agent=action.agent_id,
        action=action.action_type,
        target=action.target,
        data_classification=action.data_classification,
        destination_type=action.destination_type,
        risk_score=risk_delta,
        cumulative_risk=cumulative_risk,
        decision=map_agent_state(decision),
        threat_type=threat_type,
        rule_triggered=rule_triggered,
        detail_title=detail_title,
        detail_body=detail_body,
        system_response=system_response,
        event_trace=event_trace,
    )

    return {
        "decision": decision,
        "risk_delta": risk_delta,
        "cumulative_risk": cumulative_risk,
        "threat_type": threat_type,
        "rule_triggered": rule_triggered,
        "detail_title": detail_title,
        "system_response": system_response,
        "event_trace": event_trace,
    }