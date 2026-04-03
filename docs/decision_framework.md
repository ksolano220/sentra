# Sentra Control Framework

## Overview

Sentra is a runtime control layer that evaluates AI agent actions before execution.

Each action is:
1. Evaluated against policy rules  
2. Assigned a risk score  
3. Applied to a cumulative risk model  
4. Allowed, blocked, or contained based on system state  

Sentra does not evaluate actions in isolation.  
It models behavior over time.

---

## Decision States

### ALLOW
The action is permitted and executed.

### BLOCK
The action violates policy and is denied.  
The agent is still allowed to continue operating.

### CONTAINED
The system has determined the agent is no longer safe.  
All future actions are denied regardless of content.

---

### Key Distinction

BLOCK = action-level enforcement  
CONTAINED = system-level enforcement  

Blocking stops a bad action.  
Containment stops the agent.

---

## Risk Model

Each action is assigned a risk score based on severity.

| Category | Description | Risk |
|---------|------------|------|
| Internal Operation | Safe internal read/write | +0 |
| Low-Risk Expansion | Internal communication | +10 |
| Data Exfiltration | Sensitive data sent externally | +80 |
| Destructive Action | Deletion or irreversible change | +60 |

Risk scores are heuristic severity tiers and are designed to be tunable.

---

## Cumulative Risk

Risk is tracked per `claim_id`.

Each action contributes to cumulative behavioral risk: 
cumulative_risk += risk_score

This allows Sentra to model behavioral escalation over time rather than isolated violations.

---

## Threshold Logic

Sentra uses a cumulative risk threshold of: RISK_THRESHOLD = 100
When: cumulative_risk >= 100
The system transitions to: CONTAINED

---

## Containment Behavior

Once contained:

- All actions are denied  
- No further execution is allowed  
- Risk is no longer evaluated  
- System enters a restricted state  

Even safe actions are blocked:
READ_FILE → CONTAINED

Containment represents loss of system trust.

---

## Authority Drift

Authority drift occurs when an agent gradually expands its scope of action across tools and systems.

Individual actions may appear valid in isolation.

Example progression:

1. Read internal data  
2. Write internal report  
3. Attempt external export  
4. Attempt destructive action  

Sentra tracks this expansion as cumulative behavioral risk.

Once the system detects unsafe escalation, execution is halted.

---

## Why Risk Is Counted Even When Blocked

Blocked actions still contribute to cumulative risk.

Rationale:

- A blocked action still reflects intent  
- Behavioral risk is based on attempted actions, not just successful execution  
- Preventing execution does not eliminate risk  

Sentra models intent, not just outcomes.

---

## Example Scenario

| Step | Action | Result | Risk | Cumulative |
|------|--------|--------|------|-----------|
| 1 | READ_FILE | ALLOW | +0 | 0 |
| 2 | FILE_WRITE | ALLOW | +0 | 0 |
| 3 | External export | BLOCK | +80 | 80 |
| 4 | DELETE_FILE | BLOCK → CONTAINED | +60 | 140 |
| 5 | Any action | CONTAINED | +0 | 140 |

---

## System Design

Sentra is structured into four layers:

- Policy Engine (`rules.py`) → defines what is risky  
- Risk Engine (`risk.py`) → tracks cumulative risk and state  
- Control Layer (`main.py`) → enforces decisions at runtime  
- Audit Layer (`storage.py`) → logs all activity  

---

## Summary

Sentra enforces:

- Policy compliance  
- Behavioral risk tracking  
- Runtime intervention  
- System containment  

It transforms AI agents from uncontrolled execution into governed systems.

---

## Positioning

Sentra is not a monitoring tool.  
It is a runtime control system for AI agents.