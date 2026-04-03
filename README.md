# Sentra

Runtime control layer for AI agents.

Sentra sits between agent decision-making and execution. It evaluates proposed actions in real time, applies policy rules, assigns risk, and determines whether the action is allowed, blocked, or results in agent shutdown.

---

## Why Sentra

Autonomous agents can take actions that impact real systems:

- sending external communications  
- modifying data  
- triggering financial or operational workflows  

Sentra ensures those actions are evaluated before execution, not after.

---

## What Sentra Does

- intercepts proposed agent actions  
- applies deterministic policy rules  
- assigns attempted risk scores  
- evaluates cumulative risk and behavioral state  
- enforces runtime decisions:

  - ALLOW  
  - BLOCK  
  - AGENT SHUT DOWN  

- logs every event for auditability  
- provides a real-time monitoring dashboard  

---

## How It Works

Agent → Proposed Action → Sentra → Decision → Execution (or Block)

Sentra does not execute actions. It evaluates them.

---

## Decision Model

Sentra enforces three outcomes:

### ALLOW
- action executes  
- risk is applied to cumulative risk  

### BLOCK
- action is denied  
- risk is not applied  
- blocked_attempts increments  

### AGENT SHUT DOWN
- triggered after repeated blocked actions (3-strike rule)  
- all future actions are denied  

---

## Risk Model

Each action has:

- attempted_risk  
- applied_risk (only if allowed)  
- cumulative_risk (stateful)  

Key rules:

- only allowed actions increase cumulative risk  
- blocked actions do not change cumulative risk  
- threshold prevents escalation, not execution history  

---

## Threshold Logic

RISK_THRESHOLD = 100

If an action would exceed the threshold:

- the action is blocked  
- cumulative risk remains unchanged  

Example:

40 + 80 → 120  
→ BLOCK  
→ cumulative remains 40  

---

## Behavioral Enforcement

Sentra tracks unsafe intent through blocked attempts.

blocked_attempts >= 3 → AGENT SHUT DOWN

This separates:

- executed behavior (risk)  
- unsafe intent (blocked attempts)  

---

## Quick Start

### 1. Install dependencies

pip install -r requirements.txt

### 2. Run Sentra API

uvicorn supervisor.main:app --reload

Sentra will be available at:

http://127.0.0.1:8000

---

### 3. Run Dashboard

python -m streamlit run dashboard/app.py

Open:

http://localhost:8501

---

## Integration (Client Side)

Clients send proposed actions to Sentra before execution.

### Example request

```python
import requests

payload = {
    "agent_id": "agent_1",
    "action_type": "SEND_NOTIFICATION",
    "notification_type": "approval",
    "policy_context": {
        "approval_requires_verified_eligibility": True,
        "eligibility_verified": False
    }
}

response = requests.post(
    "http://127.0.0.1:8000/agent-action",
    json=payload
)

result = response.json()
```

### Decision handling

```python
if result["decision"] == "Allowed":
    execute_tool()
elif result["decision"] == "Blocked":
    block_action()
else:
    shutdown_agent()
```

---

## Dashboard

The Sentra dashboard provides:

- real-time events  
- action attempts and decisions  
- triggered policies  
- attempted vs applied risk  
- cumulative risk  
- enforcement timeline  

The dashboard reflects backend decisions and does not recompute logic.

---

## Runtime Log

Events are stored locally:

supervisor/runtime_log.json

Each event includes:

- agent_id  
- action  
- attempted_risk  
- cumulative_risk  
- decision  
- policy_triggered  
- reason  

---

## Example Use Cases

Sentra is domain-agnostic and can be used for:

- preventing unsafe external communications  
- blocking data exfiltration  
- enforcing workflow constraints  
- validating required verification before execution  
- controlling financial or operational actions  

---

## Architecture

Sentra is designed as a standalone service:

- API: runtime evaluation  
- Policy engine: rule enforcement  
- Risk engine: stateful scoring  
- Storage: audit logs  
- Dashboard: monitoring  

Clients integrate via a simple API call.

---

## Design Principles

- execution must be controlled, not trusted  
- policies must be explicit and enforceable  
- decisions must be explainable  
- logs must be structured and auditable  
- system must remain domain-agnostic  

---

## Status

Sentra is a prototype demonstrating runtime control for autonomous agents.

---

## License

MIT License
