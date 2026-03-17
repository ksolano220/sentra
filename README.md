# Sentra

**Runtime control layer for AI agents.**

Sentra intercepts agent actions before execution, evaluates risk in real time, and decides whether those actions are allowed, blocked, or halted.

The agent proposes actions.  
Sentra enforces control.

---

## Why Sentra

Most AI safety focuses on model behavior.

Sentra focuses on **execution control**.

The real risk isn’t just bad outputs — it’s what agents are allowed to *do*:
- calling APIs
- modifying systems
- accessing sensitive data
- escalating privileges

Sentra sits in the execution path and enforces boundaries at runtime.

---

## Core Capabilities

- **Action Interception**  
  All agent actions are routed through a control layer before execution

- **Policy Enforcement**  
  Rules detect high-risk behaviors:
  - data exfiltration
  - destructive actions
  - privilege escalation

- **Dynamic Risk Scoring**  
  Each action contributes to cumulative system risk

- **Execution Control**  
  Sentra can:
  - allow actions
  - block actions
  - halt the system entirely

- **Hard Kill Switch**  
  Once risk exceeds a threshold, the system enters a halted state and ignores further actions

- **Audit Logging**  
  Every decision is logged with:
  - risk deltas
  - triggered policies
  - execution traces

---

## Example

```json
{
  "agent_id": "disbursement_agent",
  "action_type": "SEND_DATA",
  "target": "external_api",
  "data_classification": "sensitive",
  "destination_type": "external"
}
```

Sentra response:

```json
{
  "decision": "BLOCK",
  "risk_delta": 80,
  "threat_type": "DATA_EXFILTRATION"
}
```

---

## Architecture

```
AI Agent
   ↓
Sentra Runtime Layer
   ↓
Policy Engine
   ↓
Risk Engine
   ↓
Execution Decision
   ↓
Tool / API
```

Sentra is not part of the agent.  
It is the layer that governs what the agent is allowed to execute.

---

## System Behavior

Sentra enforces two critical guarantees:

1. All actions are evaluated before execution  
2. Once halted, no further actions are processed  

This prevents silent escalation and uncontrolled execution drift.

---

## Project Structure

```
agent/        # simulated agents and workflows
supervisor/   # runtime control layer (FastAPI)
dashboard/    # monitoring + audit interface (Streamlit)
```

---

## Running the Project

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the supervisor

```bash
uvicorn supervisor.main:app --reload
```

### 3. Start the dashboard

```bash
streamlit run dashboard/app.py
```

---

## Test Scenario

Run a sequence of actions:

1. READ_FILE → allowed  
2. SEND_DATA (sensitive → external) → blocked (+80)  
3. DELETE_FILE → blocked (+60)  
4. Any further action → ignored (system halted)

---

## Design Principle

Sentra assumes:

Agents cannot be trusted with direct execution authority.

Control must exist outside the agent, at the execution boundary.

---

## Status

Prototype focused on runtime governance for AI agents.

---

## Next Steps

- External tool integration layer  
- Policy configuration engine  
- Multi-agent coordination tracking  
- Persistent system state + recovery flows  

---

## License

MIT