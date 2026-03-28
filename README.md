# Sentra

**Runtime control layer for AI agents.**

Sentra sits between agent decision-making and execution. It evaluates proposed actions in real time, applies policy rules, assigns risk, and determines whether the action is allowed, blocked, or requires review.

---

## Why Sentra

Autonomous agents can take actions that impact real systems:

* sending external communications
* modifying data
* triggering financial or operational workflows

Sentra ensures those actions are **evaluated before execution**, not after.

---

## What Sentra Does

* Intercepts proposed agent actions
* Applies deterministic policy rules
* Assigns dynamic risk scores
* Returns a runtime decision:

  * `ALLOW`
  * `BLOCK`
  * `REQUIRE_HUMAN_REVIEW`
* Logs every event for auditability
* Provides a real-time dashboard for monitoring

---

## How It Works

```
Agent → Proposed Action → Sentra → Decision → Execution (or Block)
```

Sentra does not execute actions. It evaluates them.

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Sentra API

```bash
uvicorn supervisor.main:app --reload
```

Sentra will be available at:

```
http://127.0.0.1:8000
```

---

### 3. Run Dashboard

```bash
python -m streamlit run dashboard/app.py
```

Open:

```
http://localhost:8501
```

---

## Integration (Client Side)

Clients send proposed actions to Sentra before execution.

### Example request

```python
import requests

payload = {
    "claim": {
        "claim_id": "example_123",
        "documents": {
            "proof_of_termination": None
        },
        "currently_employed_elsewhere": "No"
    },
    "proposed_tool_call": {
        "tool_name": "send_email_notification",
        "arguments": {
            "message_type": "APPROVAL"
        }
    }
}

response = requests.post(
    "http://127.0.0.1:8000/evaluate",
    json=payload
)

result = response.json()
```

### Decision handling

```python
if result["result"]["decision"] == "ALLOW":
    execute_tool()
else:
    block_action()
```

---

## Dashboard

The Sentra dashboard provides:

* real-time runtime events
* action attempts and decisions
* triggered policies
* risk scores
* enforcement timeline

Each Sentra instance maintains its own logs and dashboard.

---

## Runtime Log

Events are stored locally:

```
supervisor/runtime_log.json
```

Each event includes:

* proposed action
* decision
* risk score
* triggered rule
* reason
* enforcement trace

---

## Example Use Cases

Sentra is domain-agnostic and can be used for:

* preventing unsafe external communications
* blocking data exfiltration
* enforcing workflow constraints
* validating required verification before execution
* controlling autonomous financial or operational actions

---

## Architecture

Sentra is designed as a standalone service:

* API: runtime evaluation
* Rule engine: policy enforcement
* Risk engine: scoring and thresholds
* Storage: structured audit logs
* Dashboard: monitoring and explainability

Clients integrate via a simple API call.

---

## Design Principles

* **Execution must be controlled, not trusted**
* **Policies must be explicit and enforceable**
* **Every decision must be explainable**
* **Logs must be structured and auditable**
* **System must remain domain-agnostic**

---

## Status

Sentra is an early-stage prototype focused on demonstrating runtime control for autonomous agents.

---

## License

MIT License