# Sentra

<<<<<<< HEAD
Sentra is a Python prototype for runtime supervision of AI agent actions.

It provides a control layer that evaluates proposed agent actions before execution, applies policy rules, assigns risk scores, and determines whether those actions should proceed.

Rather than giving agents unrestricted access to tools or external systems, Sentra is designed around a controlled execution path.

The agent proposes actions. Sentra evaluates whether they should execute.

---

## Overview

As AI agents gain the ability to interact with tools, APIs, files, and internal systems, the main risk is no longer only what the model generates. The main risk is what the system allows the agent to do.

Sentra explores this problem at the execution layer.

The prototype demonstrates how agent actions can be routed through a runtime supervision layer that:

- evaluates actions against policy rules
- assigns dynamic risk scores
- blocks or halts unsafe actions
- logs execution decisions for monitoring and review

---

## What Sentra Does

Sentra provides a supervised execution layer for agent workflows.

For each proposed action, the system can:

- inspect the action metadata
- evaluate applicable policy rules
- calculate a risk score
- decide whether to allow, block, or halt execution
- record the decision in a structured runtime log

This makes it possible to test how runtime controls can reduce unsafe agent behavior in multi-step workflows.

---

## Important Scope Constraint

Sentra does not claim to control arbitrary agent behavior at the operating-system or model level.

It works when agent actions are routed through the Sentra control layer.

In other words, Sentra governs actions that pass through its supervised execution path. If an agent can bypass that path, those actions are outside Sentra’s control.

---

## Project Goal

This project explores runtime governance for AI agents.

The prototype is designed to show that a control layer can sit within an agent workflow and make execution decisions before risky actions reach external systems.

Specifically, Sentra demonstrates how to:

- route agent actions through a single supervision point
- apply policy rules in real time
- score execution risk dynamically
- stop unsafe actions before they execute
- monitor behavior across an entire workflow

---

## System Architecture

Execution flow:

AI Agent
↓
Sentra Supervision Layer
↓
Policy Rules
↓
Risk Scoring
↓
Execution Decision
↓
Tool or External System
↓
Monitoring Dashboard

In this design, the agent does not execute actions directly. Instead, actions are submitted to the Sentra supervision layer for evaluation first.

---

## Core Capabilities

### 1. Runtime Action Evaluation

Sentra inspects each proposed action before execution.

This includes fields such as:

- agent identity
- action type
- target
- data classification
- destination type

### 2. Policy Rule Enforcement

Sentra applies predefined rules to identify unsafe or restricted behaviors.

These rules can be used to detect patterns such as:

- unauthorized data access
- high-risk external calls
- sensitive actions involving restricted data
- risky combinations of action type and destination

### 3. Dynamic Risk Scoring

Each action is assigned a risk score based on its characteristics and context.

This allows the system to distinguish between lower-risk and higher-risk actions during execution.

### 4. Execution Control

Based on rule evaluation and risk score, Sentra can:

- allow execution
- block a specific action
- halt execution when a defined threshold is exceeded

### 5. Structured Logging and Monitoring

Sentra records runtime decisions in a structured log for downstream inspection and dashboard monitoring.

This provides visibility into:

- proposed actions
- assigned risk scores
- rule triggers
- execution outcomes

---

## Example Agent Workflow

The prototype simulates a multi-step public-service style workflow:

- Intake Agent receives applicant data
- Eligibility Agent evaluates conditions
- Disbursement Agent proposes financial actions

An example proposed action might look like:

```python
action = {
    "agent_id": "disbursement_agent",
    "action_type": "transfer_funds",
    "target": "external_bank_api",
    "data_classification": "restricted",
    "destination_type": "external"
}
```

Sentra evaluates the action before execution and determines whether it should proceed.

---

## Threat Model Focus

Sentra is designed to detect and control high-risk behaviors such as:

- unauthorized access to sensitive data
- external transmission of restricted information
- abnormal or high-risk financial actions
- unsafe system actions
- risky multi-step action sequences

The emphasis is not only on individual actions, but also on how risky behavior can emerge during a workflow.

---

## Example Failure Pattern

A sequence like the following may appear harmless when viewed step by step:

1. read internal data
2. process or transform that data
3. send the result to an external destination

Individually, each action may appear acceptable.
Taken together, the sequence may represent exfiltration or policy breach.

Sentra is intended to support evaluation at the point of execution so that unsafe actions can be blocked before completion.

---

## Repository Structure

```text
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
```

---

## Monitoring

Runtime decisions are logged and surfaced through a dashboard.

The dashboard is intended to provide visibility into:

- agent behavior
- risk scores
- policy rule triggers
- blocked or halted actions
- execution history across workflows

---

## Current Scope

Sentra is an early prototype.

It is intended to demonstrate the feasibility of runtime supervision for AI agent workflows, not to serve as a complete production governance platform.

The project currently focuses on:

- supervised execution of agent actions
- policy-based evaluation
- risk scoring
- blocking and halting decisions
- structured runtime monitoring

---

## Design Principle

Sentra is based on a simple principle:

Do not rely only on what an agent is asked to do.
Control what the agent is allowed to execute.

---

## Status

Early Python prototype focused on runtime supervision, execution control, and monitoring for simulated agent workflows.
=======
AI agents shouldn’t have unrestricted execution.

Sentra is a runtime control layer that sits between agents and the tools they use.

Every action is intercepted before it executes.

Sentra decides:

* allow
* block
* halt

---

## The problem

Agents don’t just generate text.

They:

* call APIs
* move data
* modify systems

Most systems evaluate outputs.

Very few control what actually gets executed.

---

## What Sentra does

Sentra turns every action into a decision.

* intercepts tool calls
* applies policy rules
* assigns risk scores
* tracks cumulative behavior
* stops execution when the system becomes unsafe

---

## Example

READ_FILE → allowed
SEND_DATA (sensitive → external) → blocked (+80)
DELETE_FILE → blocked (+60)
NEXT ACTION → halted

The last action isn’t dangerous.

The system is.

---

## Model

Sentra introduces two layers of enforcement:

Action-level

* Allowed
* Blocked

System-level

* Halted when cumulative risk exceeds threshold

---

## Architecture

Agent → Sentra → Policy → Risk → Decision → Execution

Sentra sits directly in the execution path.

---

## Why this exists

Agent failures are rarely single events.

They emerge over sequences of actions.

Sentra models that with cumulative risk and stops execution before escalation.

---

## Quickstart

git clone https://github.com/YOUR_USERNAME/sentra.git
cd sentra

pip install -r requirements.txt

uvicorn supervisor.main:app --reload
streamlit run dashboard/app.py

---

## Status

Prototype.

Designed to explore execution control for AI systems.
>>>>>>> f3b5f04 (Update README)
