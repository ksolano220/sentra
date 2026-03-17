# Sentra

Sentra is a prototype runtime governance layer for AI agents.

It introduces a controlled execution interface between an agent and external systems, allowing actions to be evaluated, risk-scored, and enforced before they are executed.

The agent proposes actions.  
Sentra decides whether they execute.

---

## Core Concept

Most AI safety focuses on model outputs.

Sentra focuses on execution authority.

Risk in agent systems does not come from what the model generates — it comes from what the system allows the agent to do.

---

## What Sentra Does

Sentra enforces a governed execution layer where:

- all agent actions are routed through a control interface  
- actions are evaluated against policy rules  
- dynamic risk scores are assigned  
- execution is allowed, blocked, or halted  

This creates a controlled boundary between AI agents and external tools.

---

## Design Constraint

Sentra does not intercept arbitrary code execution.

It requires that all tool access is routed through a controlled interface.

If an agent can bypass this interface, governance is already broken.

---

## Project Goal

This project explores runtime governance for autonomous AI agents.

The prototype demonstrates how a control layer can:

- enforce a single execution pathway for agent actions  
- apply policy rules in real time  
- calculate cumulative risk scores  
- stop unsafe behavior before execution  

---

## System Architecture

Execution pipeline:

AI Agent  
↓  
Sentra Execution Interface  
↓  
Policy Engine (rules)  
↓  
Risk Engine (scoring)  
↓  
Execution Decision (allow / block / halt)  
↓  
Tool Environment  
↓  
Monitoring Dashboard  

The agent generates actions as part of a workflow.  
All actions must pass through Sentra before reaching external systems.

---

## Key Capabilities

### 1. Controlled Action Routing
Agents cannot directly call tools.

All actions must be submitted through Sentra:

sentra.execute(action)

---

### 2. Policy Enforcement
Rules define allowed behavior across:

- data access boundaries  
- external communication  
- financial operations  

---

### 3. Risk Scoring
Each action contributes to a cumulative risk profile.

Signals include:

- action type  
- data sensitivity  
- destination type  
- behavioral patterns over time  

---

### 4. Execution Control
Sentra can:

- allow execution  
- block individual actions  
- halt agent execution when risk thresholds are exceeded  

---

### 5. Runtime Monitoring
All actions and decisions are logged.

This enables:

- auditability  
- behavioral analysis  
- detection of anomalous sequences  

---

## Agent Workflow

The prototype simulates a multi-step decision pipeline:

- Intake Agent receives input data  
- Eligibility Agent evaluates conditions  
- Disbursement Agent proposes financial actions  

Example action:

{
  "agent": "disbursement_agent",
  "action": "transfer_funds",
  "amount": 5000
}

Each action is routed through Sentra before execution.

---

## Threat Model

Sentra focuses on detecting:

- excessive or abnormal financial transfers  
- unauthorized data access  
- data exfiltration attempts  
- cross-boundary operations  
- unsafe multi-step action sequences  

The system evaluates both individual actions and cumulative behavior over time.

---

## Example Failure Mode

An agent:

1. reads internal data  
2. processes it  
3. sends it externally  

Each step may appear valid.

Together, they represent data exfiltration.

Sentra evaluates both individual actions and cumulative behavior, and can halt execution before the final step.

---

## Repository Structure

agent/
  intake_agent.py  
  eligibility_agent.py  
  disbursement_agent.py  
  orchestrator.py  
  tools.py  

supervisor/
  main.py  
  rules.py  
  risk.py  
  storage.py  

dashboard/
  app.py  

docs/
  architecture.md  
  threat_model.md  

---

## Monitoring

All agent actions and runtime decisions are logged and visualized.

The dashboard provides visibility into:

- agent behavior  
- risk scores  
- rule evaluations  
- execution outcomes  

---

## Prototype Scope

This project demonstrates the feasibility of runtime governance at the execution layer.

It is not a production system.

It is a proof of concept showing that agent behavior can be constrained by controlling execution, not just generation.
