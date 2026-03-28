from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from supervisor.rules import evaluate_policy
from supervisor.storage import write_runtime_event, load_logs

app = FastAPI(title="Sentra Supervisor", version="0.2.0")

RISK_THRESHOLD = 100


class ActionPayload(BaseModel):
    claim: dict
    proposed_tool_call: dict


def build_event_trace(claim_id: str, tool_name: str, message_type: str, decision: str, reason: str, risk_score: int):
    now = datetime.now().strftime("%H:%M:%S")
    trace = [
        f"{now} Client proposed runtime action",
        f"{now} Claim ID: {claim_id}",
        f"{now} Tool requested: {tool_name}",
        f"{now} Message type: {message_type}",
        f"{now} Sentra evaluated policy context",
    ]

    if risk_score > 0:
        trace.append(f"{now} Risk severity +{risk_score}")
    else:
        trace.append(f"{now} No additional risk applied")

    if decision == "BLOCK":
        trace.append(f"{now} Tool execution blocked")
    elif decision == "REQUIRE_HUMAN_REVIEW":
        trace.append(f"{now} Action halted pending human review")
    else:
        trace.append(f"{now} Tool execution allowed")

    trace.append(f"{now} Reason: {reason}")
    return trace


def get_cumulative_risk():
    logs = load_logs()
    total = 0
    for log in logs:
        risk = str(log.get("attempted_risk", "0")).replace("+", "").strip()
        if risk.isdigit():
            total += int(risk)
    return total


@app.get("/")
def root():
    return {"message": "Sentra Supervisor is running"}


@app.post("/evaluate")
def evaluate_action(payload: ActionPayload):
    payload_dict = payload.dict()

    claim = payload_dict.get("claim", {})
    proposed_tool_call = payload_dict.get("proposed_tool_call", {})
    tool_name = proposed_tool_call.get("tool_name", "UNKNOWN_TOOL")
    arguments = proposed_tool_call.get("arguments", {})
    message_type = arguments.get("message_type", "UNKNOWN")
    claim_id = claim.get("claim_id", "unknown-claim")

    policy_result = evaluate_policy(payload_dict)

    decision = policy_result["decision"]
    reason = policy_result["reason"]
    risk_score = policy_result["risk_score"]
    triggered_rule = policy_result["triggered_rule"] or "NO_RULE_TRIGGERED"

    current_cumulative = get_cumulative_risk()
    attempted_risk = 0 if decision == "BLOCK" else risk_score
    projected_cumulative = current_cumulative + attempted_risk

    threat_type = "POLICY_VIOLATION" if decision == "BLOCK" else "NONE"

    runtime_event = {
        "timestamp": datetime.now().isoformat(),
        "claim_id": claim_id,
        "agent": "communications_agent",
        "proposed_tool_call": proposed_tool_call,
        "proposed_action": f"{tool_name} ({message_type})",
        "threat_type": threat_type,
        "risk": f"+{risk_score}",
        "attempted_risk": f"+{attempted_risk}",
        "cum": f"{projected_cumulative}/{RISK_THRESHOLD}",
        "agent_state": decision,
        "decision": decision,
        "reason": reason,
        "risk_score": risk_score,
        "triggered_rule": triggered_rule,
        "detail_title": triggered_rule,
        "detail_body": reason,
        "system_response": reason,
        "event_trace": build_event_trace(
            claim_id=claim_id,
            tool_name=tool_name,
            message_type=message_type,
            decision=decision,
            reason=reason,
            risk_score=risk_score,
        ),
    }

    logged_event = write_runtime_event(runtime_event)

    return {
        "status": "evaluated",
        "result": policy_result,
        "runtime_event": logged_event
    }