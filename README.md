# Sentra

Sentra is a prototype runtime supervision layer for AI agents.

The system demonstrates how a control layer can intercept agent actions, evaluate risk, and determine whether those actions should be allowed to execute.

Instead of allowing agents to directly call tools or APIs, Sentra introduces an inline runtime layer that monitors behavior and enforces safety policies.

The agent proposes actions.
Sentra decides whether they execute.


# Project Goal

This project explores runtime governance for autonomous AI agents.

The prototype demonstrates how a control layer can:

- intercept agent tool calls
- apply policy rules
- calculate risk scores
- decide whether actions should execute

The system focuses on detecting unsafe sequences such as:

- large financial transfers
- unauthorized data access
- data exfiltration attempts


# System Architecture

Execution pipeline:

AI Agent
↓
Sentra Runtime Interceptor
↓
Policy Rules
↓
Risk Engine
↓
Execution Decision
↓
Tool Environment
↓
Monitoring Dashboard

The AI agent generates actions as part of a workflow.
Sentra intercepts those actions before they reach external systems.


# Repository Structure

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


# Agent Workflow

The agent simulates a public-service processing pipeline.

1. Intake Agent
   receives applicant data

2. Eligibility Agent
   evaluates eligibility conditions

3. Disbursement Agent
   proposes financial actions

Example action output:

{
  "agent": "disbursement_agent",
  "action": "transfer_funds",
  "amount": 5000
}

These actions are intercepted by the Sentra runtime layer.


# Threat Model

The system focuses on detecting risky agent behavior such as:

- excessive financial transfers
- unauthorized data access
- data exfiltration
- unsafe multi-step action sequences

The runtime layer assigns risk scores and determines whether actions should be blocked.

See docs/threat_model.md for more details.


# Monitoring

All agent actions and runtime decisions are logged to a monitoring dashboard.

The dashboard provides visibility into:

- agent behavior
- risk scores
- rule violations
- execution decisions


# Prototype Scope

This project demonstrates the feasibility of runtime supervision for AI agents.

It is not intended to be a full governance platform.
The objective is to prove that an inline runtime layer can intercept and control agent tool usage.


# IBM AI Experiential Learning Lab

This project is being developed as part of the IBM SkillsBuild AI Experiential Learning Lab.

The prototype demonstrates how runtime controls can improve the safety of autonomous AI systems.
