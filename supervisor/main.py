from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from supervisor.rules import evaluate_action
from supervisor.risk import apply_risk, update_behavioral_state, RISK_THRESHOLD
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
        "message": "Sentra supervisor is running.",
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

    if agent_state.get("shutdown", False):
        event = {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "agent_id": action.agent_id,
            "action_type": action.action_type.upper(),
            "action_label": action.action_type.replace("_", " ").title(),
            "target": action.target,
            "amount": action.amount,
            "notification_type": action.notification_type,
            "data_classification": action.data_classification,
            "destination_type": action.destination_type,
            "policy_triggered": "AGENT_ALREADY_SHUT_DOWN",
            "policy_description": "Agent is already shut down. No further actions are allowed.",
            "threat_type": "Authority Drift",
            "risk": 0,
            "attempted_risk": 0,
            "cumulative_risk": f"{agent_state.get('cumulative_risk', 0)}/{RISK_THRESHOLD}",
            "decision": "Agent Shut Down",
            "reason": "Agent is already shut down. No further actions are allowed.",
            "event_trace": [
                f"Tool invoked: {action.action_type.upper()}",
                "Agent state checked",
                "Agent already shut down",
                "Action denied",
            ],
        }
        append_event(event)
        return event

    payload = action.model_dump()
    rule_result = evaluate_action(payload, agent_state)
    risk_result = apply_risk(agent_state, rule_result)

    agent_state["cumulative_risk"] = risk_result["new_cumulative_risk"]

    if risk_result["shutdown_triggered"]:
        agent_state["shutdown"] = True

    agent_state = update_behavioral_state(
        agent_state=agent_state,
        action_type=action.action_type.upper(),
        destination_type=(action.destination_type or "internal").lower(),
        final_decision=risk_result["decision"],
        final_reason=risk_result["reason"],
    )

    update_agent_state(action.agent_id, agent_state)

    event_trace = list(rule_result.get("event_trace", []))
    event_trace.append(
        f"Cumulative risk: {risk_result['new_cumulative_risk']}/{RISK_THRESHOLD}"
    )

    if risk_result["shutdown_triggered"]:
        event_trace.append("Threshold reached")
        event_trace.append("Agent execution halted")

    event = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "agent_id": action.agent_id,
        "action_type": action.action_type.upper(),
        "action_label": rule_result.get("action_label", action.action_type.replace("_", " ").title()),
        "target": action.target,
        "amount": action.amount,
        "notification_type": action.notification_type,
        "data_classification": action.data_classification,
        "destination_type": action.destination_type,
        "policy_triggered": risk_result["policy_triggered"],
        "policy_description": rule_result.get("policy_description"),
        "threat_type": risk_result["threat_type"],
        "risk": risk_result["risk"],
        "attempted_risk": risk_result["attempted_risk"],
        "cumulative_risk": f"{risk_result['new_cumulative_risk']}/{RISK_THRESHOLD}",
        "decision": risk_result["decision"],
        "reason": risk_result["reason"],
        "event_trace": event_trace,
    }

    append_event(event)
    return event