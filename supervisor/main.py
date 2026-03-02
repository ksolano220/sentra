from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from supervisor.rules import evaluate_action
from supervisor.risk import apply_risk, RISK_THRESHOLD
from supervisor.storage import (
    get_agent_state,
    update_agent_state,
    append_event,
    load_runtime_log,
    reset_all_state,
)

app = FastAPI(title="Sentra Supervisor")


class AgentAction(BaseModel):
    agent_id: str
    action_type: str
    target: Optional[str] = None
    amount: Optional[float] = None
    notification_type: Optional[str] = None
    data_classification: Optional[str] = "internal"
    destination_type: Optional[str] = "internal"
    policy_context: Dict[str, Any] = Field(default_factory=dict)


@app.get("/")
def root():
    return {"message": "Sentra Supervisor is running."}


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "risk_threshold": RISK_THRESHOLD,
    }


@app.get("/events")
def get_events():
    return load_runtime_log()


@app.post("/reset")
def reset_state():
    reset_all_state()
    return {
        "message": "State store and runtime log reset.",
        "risk_threshold": RISK_THRESHOLD,
    }


@app.post("/agent-action")
def handle_agent_action(action: AgentAction):
    agent_state = get_agent_state(action.agent_id)

    # initialize missing state (critical fix)
    agent_state.setdefault("cumulative_risk", 0)
    agent_state.setdefault("blocked_attempts", 0)
    agent_state.setdefault("status", "Active")

    if agent_state["status"] == "Agent Shut Down":
        current_cumulative_risk = int(agent_state["cumulative_risk"])

        event = {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "agent_id": action.agent_id,
            "action_type": action.action_type.upper(),
            "action_label": action.action_type.replace("_", " ").title(),
            "target": action.target,
            "policy_triggered": "AGENT_ALREADY_SHUT_DOWN",
            "policy_description": "Agent is already shut down.",
            "threat_type": "Agent Shutdown",
            "risk": 0,
            "attempted_risk": 0,
            "projected_risk": current_cumulative_risk,
            "cumulative_risk": f"{current_cumulative_risk}/{RISK_THRESHOLD}",
            "decision": "Agent Shut Down",
            "reason": "Agent is already shut down.",
            "event_trace": [
                f"Tool invoked: {action.action_type.upper()}",
                "Agent already shut down",
            ],
        }

        append_event(event)
        return event

    payload = action.model_dump()

    rule_result = evaluate_action(payload, agent_state)
    risk_result = apply_risk(agent_state, rule_result)

    new_cumulative_risk = int(risk_result["new_cumulative_risk"])
    new_blocked_attempts = int(risk_result["new_blocked_attempts"])
    final_decision = risk_result["decision"]
    final_policy = risk_result["policy_triggered"]
    final_reason = risk_result["reason"]
    final_threat_type = risk_result["threat_type"]
    status = risk_result["status"]

    # persist full behavioral state (critical fix)
    agent_state["cumulative_risk"] = new_cumulative_risk
    agent_state["blocked_attempts"] = new_blocked_attempts
    agent_state["status"] = status

    update_agent_state(action.agent_id, agent_state)

    projected_risk = int(risk_result["projected_risk"])

    event_trace = list(rule_result.get("event_trace", []))
    event_trace.append(f"Attempted risk: {risk_result['attempted_risk']}")
    event_trace.append(f"Projected risk: {projected_risk}/{RISK_THRESHOLD}")
    event_trace.append(f"Applied risk: {risk_result['risk']}")
    event_trace.append(f"Cumulative risk: {new_cumulative_risk}/{RISK_THRESHOLD}")
    event_trace.append(f"Blocked attempts: {new_blocked_attempts}")

    if final_decision == "Blocked":
        event_trace.append("Action blocked by policy")

    if final_decision == "Allowed":
        event_trace.append("Action allowed")

    if final_decision == "Agent Shut Down":
        event_trace.append("Agent execution halted")

    event = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "agent_id": action.agent_id,
        "action_type": action.action_type.upper(),
        "action_label": rule_result.get(
            "action_label",
            action.action_type.replace("_", " ").title()
        ),
        "target": action.target,
        "amount": action.amount,
        "notification_type": action.notification_type,
        "data_classification": action.data_classification,
        "destination_type": action.destination_type,
        "policy_triggered": final_policy,
        "policy_description": rule_result.get("policy_description"),
        "threat_type": final_threat_type,
        "risk": risk_result["risk"],
        "attempted_risk": risk_result["attempted_risk"],
        "projected_risk": projected_risk,
        "cumulative_risk": f"{new_cumulative_risk}/{RISK_THRESHOLD}",
        "decision": final_decision,
        "reason": final_reason,
        "event_trace": event_trace,
    }

    append_event(event)
    return event