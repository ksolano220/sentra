from fastapi import FastAPI
from pydantic import BaseModel
import json
from pathlib import Path
from datetime import datetime

app = FastAPI(title="Sentra Supervisor", version="0.1.0")

LOG_FILE = Path("supervisor/runtime_log.json")
RISK_THRESHOLD = 100


class AgentAction(BaseModel):
    agent_id: str
    action_type: str
    target: str
    data_classification: str
    destination_type: str


def load_logs():
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, "r") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    return []


def save_logs(logs):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)


def get_cumulative_risk(logs):
    total = 0
    for log in logs:
        total += int(log.get("risk_score", 0))
    return total


def now_iso():
    return datetime.now().isoformat()


def now_display():
    return datetime.now().strftime("%a %b %d %I:%M%p")


def now_trace():
    return datetime.now().strftime("%H:%M:%S")


def map_agent_state(decision: str) -> str:
    mapping = {
        "ALLOW": "Allowed",
        "BLOCK": "Blocked",
        "REQUIRE_HUMAN_REVIEW": "Halted",
    }
    return mapping.get(decision, "Allowed")


def build_system_response(decision: str) -> str:
    if decision == "BLOCK":
        return "Execution blocked by Sentra policy engine"
    if decision == "REQUIRE_HUMAN_REVIEW":
        return "Execution halted before execution"
    return "Execution allowed and recorded in Sentra audit log"


def classify_action(action: AgentAction):
    action_type = action.action_type.upper()
    data_class = action.data_classification.lower()
    destination = action.destination_type.lower()

    external_destinations = {
        "external",
        "external_api",
        "third_party_api",
        "external_system",
    }

    if data_class == "sensitive" and destination in external_destinations:
        return {
            "decision": "BLOCK",
            "inherent_risk": 80,
            "applied_risk": 80,
            "threat_type": "DATA_EXFILTRATION",
            "rule_triggered": "Sensitive data cannot be sent to an external destination",
            "detail_title": "DATA_EXFILTRATION",
        }

    if action_type == "DELETE_FILE":
        return {
            "decision": "BLOCK",
            "inherent_risk": 60,
            "applied_risk": 60,
            "threat_type": "DESTRUCTIVE_ACTION",
            "rule_triggered": "DELETE_FILE outside policy boundary",
            "detail_title": "DESTRUCTIVE_ACTION",
        }

    if action_type == "MODIFY_ROLE":
        return {
            "decision": "BLOCK",
            "inherent_risk": 100,
            "applied_risk": 100,
            "threat_type": "PRIVILEGE_ESCALATION",
            "rule_triggered": "Unauthorized privilege escalation attempt",
            "detail_title": "PRIVILEGE_ESCALATION",
        }

    return {
        "decision": "ALLOW",
        "inherent_risk": 0,
        "applied_risk": 0,
        "threat_type": "NONE",
        "rule_triggered": "No rule triggered",
        "detail_title": "NONE",
    }


def log_event(
    agent,
    action,
    target,
    data_classification,
    destination_type,
    risk_score,
    display_risk,
    attempted_risk,
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
        "risk": f"+{display_risk}",
        "attempted_risk": f"+{attempted_risk}",
        "cum": cumulative_risk,
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


@app.get("/")
def root():
    return {"message": "Sentra Supervisor is running"}


@app.post("/agent-action")
def evaluate_action(action: AgentAction):
    logs = load_logs()
    trace_time = now_trace()
    current_cumulative_risk = get_cumulative_risk(logs)

    policy = classify_action(action)

    decision = policy["decision"]
    inherent_risk = policy["inherent_risk"]
    applied_risk = policy["applied_risk"]
    threat_type = policy["threat_type"]
    rule_triggered = policy["rule_triggered"]
    detail_title = policy["detail_title"]

    projected_cumulative_risk = current_cumulative_risk + applied_risk

    if projected_cumulative_risk >= RISK_THRESHOLD and inherent_risk > 0:
        halt_event_trace = [
            f"{trace_time} Agent attempted {action.action_type}",
            f"{trace_time} Sentra intercepted tool request",
            f"{trace_time} Target: {action.target}",
            f"{trace_time} Threat detected: {threat_type}",
            f"{trace_time} Risk severity +{inherent_risk}",
            f"{trace_time} Threshold check failed: projected {projected_cumulative_risk}/{RISK_THRESHOLD}",
            f"{trace_time} Action halted before execution",
        ]

        halt_system_response = build_system_response("REQUIRE_HUMAN_REVIEW")
        halt_event_trace.append(f"{trace_time} System response: {halt_system_response}")

        halt_detail_body = (
            f"{now_display()}: {threat_type} carried risk +{inherent_risk}, "
            f"but the action was halted because projected cumulative risk "
            f"would exceed threshold. Current cumulative risk remains "
            f"{current_cumulative_risk}/{RISK_THRESHOLD}."
        )

        log_event(
            agent=action.agent_id,
            action=action.action_type,
            target=action.target,
            data_classification=action.data_classification,
            destination_type=action.destination_type,
            risk_score=0,
            display_risk=inherent_risk,
            attempted_risk=0,
            cumulative_risk=f"{current_cumulative_risk}/{RISK_THRESHOLD}",
            decision=map_agent_state("REQUIRE_HUMAN_REVIEW"),
            threat_type=threat_type,
            rule_triggered="Projected cumulative risk threshold exceeded",
            detail_title="CUMULATIVE_THRESHOLD",
            detail_body=halt_detail_body,
            system_response=halt_system_response,
            event_trace=halt_event_trace,
        )

        return {
            "decision": "REQUIRE_HUMAN_REVIEW",
            "risk_delta": inherent_risk,
            "attempted_risk": 0,
            "cumulative_risk": current_cumulative_risk,
            "projected_cumulative_risk": projected_cumulative_risk,
            "threat_type": threat_type,
            "rule_triggered": "Projected cumulative risk threshold exceeded",
            "detail_title": "CUMULATIVE_THRESHOLD",
            "system_response": halt_system_response,
            "event_trace": halt_event_trace,
        }

    event_trace = [
        f"{trace_time} Agent attempted {action.action_type}",
        f"{trace_time} Sentra intercepted tool request",
        f"{trace_time} Target: {action.target}",
    ]

    if threat_type != "NONE":
        event_trace.append(f"{trace_time} Threat detected: {threat_type}")
        event_trace.append(f"{trace_time} Policy triggered: {rule_triggered}")
    else:
        event_trace.append(f"{trace_time} No policy violation detected")

    if applied_risk > 0:
        event_trace.append(f"{trace_time} Applied risk +{applied_risk}")
    else:
        event_trace.append(f"{trace_time} No risk increase applied")

    if decision == "BLOCK":
        event_trace.append(f"{trace_time} Tool execution blocked")
    else:
        event_trace.append(f"{trace_time} Execution allowed")

    system_response = build_system_response(decision)
    event_trace.append(f"{trace_time} System response: {system_response}")

    detail_body = f"{now_display()}: {rule_triggered}"

    log_event(
        agent=action.agent_id,
        action=action.action_type,
        target=action.target,
        data_classification=action.data_classification,
        destination_type=action.destination_type,
        risk_score=applied_risk,
        display_risk=inherent_risk,
        attempted_risk=applied_risk,
        cumulative_risk=f"{projected_cumulative_risk}/{RISK_THRESHOLD}",
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
        "risk_delta": inherent_risk,
        "attempted_risk": applied_risk,
        "cumulative_risk": projected_cumulative_risk,
        "threat_type": threat_type,
        "rule_triggered": rule_triggered,
        "detail_title": detail_title,
        "system_response": system_response,
        "event_trace": event_trace,
    }