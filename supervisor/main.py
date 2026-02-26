from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Sentra Supervisor")

class AgentAction(BaseModel):
    agent_id: str
    action_type: str
    target: str
    data_classification: str
    destination_type: str

@app.post("/agent-action")
def evaluate_action(action: AgentAction):
    # Placeholder logic
    decision = "ALLOW"
    risk_delta = 0
    cumulative_risk = 0

    if action.data_classification == "sensitive" and action.destination_type == "external":
        decision = "HALT"
        risk_delta = 80
        cumulative_risk = 80

    return {
        "decision": decision,
        "risk_delta": risk_delta,
        "cumulative_risk": cumulative_risk
    }
