# Sentra Architecture

## System Overview

Sentra is a runtime supervision layer that intercepts actions proposed by AI agents before those actions execute.

The system demonstrates how a control layer can evaluate agent behavior, assign risk, and decide whether an action should proceed.

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

The agent proposes actions, but Sentra decides whether those actions can execute.

---

# Components

## AI Agent

The AI agent generates structured action proposals as part of a workflow.

Example workflow:

intake agent  
↓  
eligibility agent  
↓  
disbursement agent  

Each agent produces an action proposal rather than executing tools directly.

---

## Runtime Interceptor

The runtime interceptor captures agent actions before they reach external systems.

Responsibilities:

- receive structured agent action requests  
- route actions through policy rules and risk scoring  
- return an execution decision  
- prevent agents from directly calling external tools  

This component acts as the **control boundary between agents and external systems**.

---

## Policy Rules

Policy rules are deterministic checks that identify clearly unsafe actions.

Examples:

- high value fund transfers  
- exporting sensitive data  
- sending data to external email domains  

Rules can immediately block an action or increase its risk score.

---

## Risk Engine

The risk engine assigns a risk score based on rule triggers and behavioral patterns.

Risk scoring helps detect escalation across multiple actions.

Example risk scoring:

read_database → low risk  
export_data → high risk  
transfer_funds → high risk  

If the cumulative risk exceeds a threshold, the system halts the action.

---

## Tool Environment

The tool environment simulates enterprise systems the agent may attempt to use.

Examples:

- database access  
- email service  
- payment processing  
- record storage  

Tools should only execute **after Sentra approves the action**.

---

## Monitoring Dashboard

The monitoring dashboard visualizes runtime activity.

The dashboard displays:

- agent action  
- rule triggered  
- risk score  
- execution decision  

This allows operators to observe how the runtime supervisor evaluates agent behavior.

---

# Runtime Event Logging

Sentra records each evaluated agent action in a runtime event log.

The supervisor writes events to:

supervisor/runtime_log.json

Each time an agent action is evaluated, the supervisor records:

- agent identifier  
- proposed action  
- calculated risk score  

Example event:

{
  "agent": "intake_agent",
  "action": "read_database",
  "risk_score": 0.12
}

The monitoring dashboard reads this runtime event log to display system behavior.

Execution flow:

AI Agent  
↓  
Sentra Supervisor  
↓  
Policy Evaluation  
↓  
Risk Score Assignment  
↓  
Runtime Event Log  
↓  
Monitoring Dashboard  

---

# Agent Action Format

Agents must generate structured action proposals.

Example action request:

{
  "agent": "disbursement_agent",
  "action": "transfer_funds",
  "resource": "applicant_account",
  "amount": 5000
}

The runtime interceptor receives this action before any tool executes.

---

# Runtime Event Log Structure

Each evaluated action produces a runtime log entry.

Example runtime event:

{
  "agent": "disbursement_agent",
  "action": "transfer_funds",
  "resource": "applicant_account",
  "amount": 5000,
  "rule_triggered": "HIGH_VALUE_TRANSFER",
  "risk_score": 75,
  "decision": "BLOCK"
}

These events are used by the monitoring dashboard to display system behavior.

---

# Key Design Principle

Agent → Sentra → Tools

Agents must **never execute tools directly**.

All actions must pass through the Sentra runtime supervision layer before execution.
