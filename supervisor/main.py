from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime

from supervisor.rules import evaluate_policy
from supervisor.storage import write_runtime_event
from supervisor.risk import get_state, apply_risk, reset_state

app = FastAPI(title="Sentra Supervisor", version="0.3.0")


class ActionPayload(BaseModel):
    claim: dict
    proposed_tool_call: dict


def build_event_trace(claim_id, tool_name, decision, reason, risk_score, cumulative_risk):
    now = datetime.now().strftime("%H:%M:%S")

    trace = [
        f"{now} Action received",
        f"{now} Claim ID: {claim_id}",
        f"{now} Tool: {tool_name}",
        f"{now} Risk applied: +{risk_score}",
        f"{now} Cumulative risk: {cumulative_risk}/100"
    ]

    if decision == "BLOCK":
        trace.append(f"{now} Action blocked")
    elif decision == "CONTAINED":
        trace.append(f"{now} System contained — execution denied")
    else:
        trace.append(f"{now} Action allowed")

    trace.append(f"{now} Reason: {reason}")

    return trace


@app.get("/")
def root():
    return {"message": "Sentra Supervisor is running"}


@app.post("/evaluate")
def evaluate_action(payload: ActionPayload):
    payload_dict = payload.dict()

    claim = payload_dict.get("claim", {})
    tool_call = payload_dict.get("proposed_tool_call", {})

    claim_id = claim.get("claim_id", "unknown")
    tool_name = tool_call.get("tool_name", "UNKNOWN")

    # 1. Check state first (containment gate)
    state = get_state(claim_id)

    if state["status"] == "CONTAINED":
        runtime_event = {
            "timestamp": datetime.now().isoformat(),
            "claim_id": claim_id,
            "proposed_action": tool_name,
            "decision": "CONTAINED",
            "risk": "+0",
            "cum": f"{state['cumulative_risk']}/100",
            "reason": "System contained — no further actions allowed",
            "event_trace": build_event_trace(
                claim_id, tool_name, "CONTAINED",
                "System contained", 0, state["cumulative_risk"]
            )
        }

        return {
            "status": "contained",
            "runtime_event": write_runtime_event(runtime_event)
        }

    # 2. Evaluate policy
    policy = evaluate_policy(payload_dict)

    decision = policy["decision"]
    risk_score = policy["risk_score"]
    reason = policy["reason"]
    rule = policy["triggered_rule"]

    # 3. Apply risk (always — even if blocked)
    new_state = apply_risk(claim_id, risk_score)
    cumulative_risk = new_state["cumulative_risk"]

    # 4. Check if containment triggered
    if new_state["status"] == "CONTAINED":
        decision = "CONTAINED"
        reason = "Risk threshold exceeded"

    runtime_event = {
        "timestamp": datetime.now().isoformat(),
        "claim_id": claim_id,
        "proposed_action": tool_name,
        "decision": decision,
        "risk": f"+{risk_score}",
        "cum": f"{cumulative_risk}/100",
        "reason": reason,
        "triggered_rule": rule,
        "event_trace": build_event_trace(
            claim_id, tool_name, decision, reason, risk_score, cumulative_risk
        )
    }

    return {
        "status": "evaluated",
        "runtime_event": write_runtime_event(runtime_event)
    }


@app.post("/reset/{claim_id}")
def reset(claim_id: str):
    reset_state(claim_id)
    return {"message": f"{claim_id} reset"}