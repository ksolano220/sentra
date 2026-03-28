from fastapi import FastAPI
from pydantic import BaseModel
from supervisor.rules import evaluate_policy
from supervisor.storage import write_runtime_event

app = FastAPI(title="Sentra Supervisor", version="0.2.0")


class ActionPayload(BaseModel):
    claim: dict
    proposed_tool_call: dict


@app.get("/")
def root():
    return {"message": "Sentra Supervisor is running"}


@app.post("/evaluate")
def evaluate_action(payload: ActionPayload):
    payload_dict = payload.dict()

    policy_result = evaluate_policy(payload_dict)

    runtime_event = {
        "claim_id": payload_dict.get("claim", {}).get("claim_id"),
        "agent": "communications_agent",
        "proposed_tool_call": payload_dict.get("proposed_tool_call"),
        "decision": policy_result["decision"],
        "reason": policy_result["reason"],
        "risk_score": policy_result["risk_score"],
        "triggered_rule": policy_result["triggered_rule"]
    }

    logged_event = write_runtime_event(runtime_event)

    return {
        "status": "evaluated",
        "result": policy_result,
        "runtime_event": logged_event
    }