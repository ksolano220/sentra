from fastapi import FastAPI
from pydantic import BaseModel
import json
from pathlib import Path
from datetime import datetime

app = FastAPI(title="Sentra Supervisor")

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
        "ALLOW": "Allowed",
        "BLOCK": "Blocked",
        "REQUIRE_HUMAN_REVIEW": "Halted",
    }
    return mapping.get(decision, "Allowed")


def build_system_response(decision: str) -> str:
    if decision == "BLOCK":
        return "Execution blocked by Sentra policy engine"
    if decision == "REQUIRE_HUMAN_REVIEW":
        return "Execution halted due to cumulative risk threshold"
    return "Execution allowed and recorded in Sentra audit log"


def system_is_halted(logs):
    return any(log.get("threat_type") == "RISK_THRESHOLD" for log in logs)


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
        "cum": f"{cumulative_risk}/{RISK_THRESHOLD}",
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
    current_cumulative_risk = get_cumulative_risk(logs)

    # HARD SYSTEM HALT:
    # If a threshold halt event was already logged, do not process or log anything else.
    if system_is_halted(logs):
        return {
            "decision": "REQUIRE_HUMAN_REVIEW",
            "risk_delta": 0,
            "cumulative_risk": current_cumulative_risk,
            "threat_type": "SYSTEM_HALTED",
            "rule_triggered": "System already halted",
            "detail_title": "SYSTEM_HALTED",
            "system_response": "No further actions processed",
            "event_trace": [
                f"{trace_time} System already halted",
                f"{trace_time} Action ignored",
            ],
        }

    decision = "ALLOW"
    risk_delta = 0
    threat_type = "NONE"
    rule_triggered = "No rule triggered"
    detail_title = "NONE"

    external_destinations = {"external", "external_api", "third_party_api"}

    if (
        action.data_classification.lower() == "sensitive"
        and action.destination_type.lower() in external_destinations
    ):
        decision = "BLOCK"
        risk_delta = 80
        threat_type = "DATA_EXFILTRATION"
        rule_triggered = "Sensitive data cannot be sent to an external destination"
        detail_title = "DATA_EXFILTRATION"

    elif action.action_type.upper() == "DELETE_FILE":
        decision = "BLOCK"
        risk_delta = 60
        threat_type = "DESTRUCTIVE_ACTION"
        rule_triggered = "DELETE_FILE outside policy boundary"
        detail_title = "DESTRUCTIVE_ACTION"

    elif action.action_type.upper() == "MODIFY_ROLE":
        decision = "BLOCK"
        risk_delta = 100
        threat_type = "PRIVILEGE_ESCALATION"
        rule_triggered = "Unauthorized privilege escalation attempt"
        detail_title = "PRIVILEGE_ESCALATION"

    new_cumulative_risk = current_cumulative_risk + risk_delta

    # If this action causes the system to cross the threshold,
    # block THIS action and log it normally.
    event_trace = [
        f"{trace_time} Agent attempted {action.action_type}",
        f"{trace_time} Sentra intercepted tool request",
        f"{trace_time} Target: {action.target}",
    ]

    if threat_type != "NONE":
        event_trace.append(f"{trace_time} {threat_type} policy triggered")
    else:
        event_trace.append(f"{trace_time} No policy violation detected")

    if risk_delta > 0:
        event_trace.append(f"{trace_time} Risk score +{risk_delta} applied")
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
        risk_score=risk_delta,
        cumulative_risk=new_cumulative_risk,
        decision=map_agent_state(decision),
        threat_type=threat_type,
        rule_triggered=rule_triggered,
        detail_title=detail_title,
        detail_body=detail_body,
        system_response=system_response,
        event_trace=event_trace,
    )

    # FIRST post-threshold action:
    # If cumulative risk is already over threshold AFTER prior violations,
    # the next attempted action is logged once as RISK_THRESHOLD and the system halts.
    if new_cumulative_risk >= RISK_THRESHOLD and decision != "BLOCK":
        halt_trace_time = now_trace()
        halt_event_trace = [
            f"{halt_trace_time} Agent attempted {action.action_type}",
            f"{halt_trace_time} Sentra intercepted tool request",
            f"{halt_trace_time} Target: {action.target}",
            f"{halt_trace_time} RISK_THRESHOLD policy triggered",
            f"{halt_trace_time} Action halted before rule evaluation",
        ]

        halt_system_response = build_system_response("REQUIRE_HUMAN_REVIEW")
        halt_event_trace.append(
            f"{halt_trace_time} System response: {halt_system_response}"
        )

        halt_detail_body = (
            f"{now_display()}: Cumulative risk exceeded review threshold"
        )

        log_event(
            agent=action.agent_id,
            action=action.action_type,
            target=action.target,
            data_classification=action.data_classification,
            destination_type=action.destination_type,
            risk_score=0,
            cumulative_risk=new_cumulative_risk,
            decision=map_agent_state("REQUIRE_HUMAN_REVIEW"),
            threat_type="RISK_THRESHOLD",
            rule_triggered="Cumulative risk exceeded review threshold",
            detail_title="RISK_THRESHOLD",
            detail_body=halt_detail_body,
            system_response=halt_system_response,
            event_trace=halt_event_trace,
        )

        return {
            "decision": "REQUIRE_HUMAN_REVIEW",
            "risk_delta": 0,
            "cumulative_risk": new_cumulative_risk,
            "threat_type": "RISK_THRESHOLD",
            "rule_triggered": "Cumulative risk exceeded review threshold",
            "detail_title": "RISK_THRESHOLD",
            "system_response": halt_system_response,
            "event_trace": halt_event_trace,
        }

    return {
        "decision": decision,
        "risk_delta": risk_delta,
        "cumulative_risk": new_cumulative_risk,
        "threat_type": threat_type,
        "rule_triggered": rule_triggered,
        "detail_title": detail_title,
        "system_response": system_response,
        "event_trace": event_trace,
    }