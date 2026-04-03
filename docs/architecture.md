# Sentra Architecture

## System Overview

Sentra is a runtime supervision layer that intercepts actions proposed
by AI agents before those actions execute.

The system evaluates agent behavior, assigns risk, maintains cumulative
state, and determines whether an action should proceed.

Execution pipeline:

AI Agent ↓ Sentra Runtime Interceptor ↓ Policy Rules ↓ Risk Engine ↓
Execution Decision ↓ Tool Environment ↓ Monitoring Dashboard

The agent proposes actions, but Sentra determines whether those actions
can execute.

------------------------------------------------------------------------

## Execution Model

Sentra does not evaluate actions in isolation.

Each action is: 1. Evaluated against policy rules 2. Assigned a risk
score 3. Applied to a cumulative risk model 4. Evaluated against system
state 5. Allowed, blocked, or contained

Execution decisions are stateful and persist across multiple actions.

------------------------------------------------------------------------

# Components

## AI Agent

The AI agent generates structured action proposals as part of a
workflow.

Example workflow:

intake agent ↓ eligibility agent ↓ disbursement agent

Each agent produces an action proposal rather than executing tools
directly.

------------------------------------------------------------------------

## Runtime Interceptor

The runtime interceptor captures agent actions before they reach
external systems.

Responsibilities:

-   receive structured agent action requests
-   route actions through policy rules and risk evaluation
-   enforce execution decisions
-   prevent agents from directly calling external tools

This component acts as the control boundary between agents and external
systems.

------------------------------------------------------------------------

## Policy Rules

Policy rules are deterministic checks that identify clearly unsafe
actions.

Examples:

-   exporting sensitive data externally
-   destructive operations (e.g., deleting records)
-   invalid approval actions based on missing requirements

Rules can:

-   block an action immediately
-   assign a risk score

------------------------------------------------------------------------

## Risk Engine

The risk engine assigns a risk score to each action and tracks
cumulative behavioral risk over time.

Risk is tracked per entity (e.g., claim_id) and persists across multiple
actions.

Example risk scoring:

read_database → +0 internal_write → +0 export_data → +80 delete_file →
+60

Cumulative risk is updated after each action:

cumulative_risk += risk_score

When cumulative risk exceeds a defined threshold, the system transitions
into a containment state.

This enables Sentra to detect behavioral escalation rather than isolated
violations.

------------------------------------------------------------------------

## State Management

Sentra maintains persistent state per entity (e.g., claim_id).

Each entity has:

-   cumulative_risk
-   status (ACTIVE or CONTAINED)

Example:

{ "claim_id": "CLM-001", "cumulative_risk": 140, "status": "CONTAINED" }

State is updated after every evaluated action.

Once an entity enters CONTAINED state:

-   all future actions are denied
-   no further execution is allowed

This ensures Sentra enforces system-level containment, not just
action-level filtering.

------------------------------------------------------------------------

## Execution Decisions

Sentra produces three possible outcomes:

ALLOW → action executes BLOCK → action denied, system continues
CONTAINED → system denies all future actions

Key distinction:

BLOCK = action-level enforcement CONTAINED = system-level enforcement

------------------------------------------------------------------------

## Tool Environment

The tool environment simulates enterprise systems the agent may attempt
to use.

Examples:

-   database access
-   email service
-   payment processing
-   record storage

Tools only execute after Sentra approves the action.

------------------------------------------------------------------------

## Monitoring Dashboard

The monitoring dashboard visualizes runtime activity.

The dashboard displays:

-   proposed action
-   rule triggered
-   risk score
-   cumulative risk
-   execution decision
-   event trace

------------------------------------------------------------------------

## Runtime Event Logging

Sentra records each evaluated agent action in a runtime event log.

Events are written to:

supervisor/runtime_log.json

Each log entry includes:

-   claim_id
-   proposed action
-   triggered rule
-   risk score
-   cumulative risk
-   execution decision

Example:

{ "claim_id": "CLM-001", "proposed_action": "file_write", "risk_score":
"+80", "cumulative_risk": "80/100", "decision": "BLOCK",
"triggered_rule": "DATA_EXFILTRATION" }

Execution flow:

AI Agent ↓ Sentra Supervisor ↓ Policy Evaluation ↓ Risk Update ↓ State
Evaluation ↓ Runtime Event Log ↓ Monitoring Dashboard

------------------------------------------------------------------------

## Agent Action Format

Agents generate structured action proposals.

Example:

{ "claim": { "claim_id": "CLM-001" }, "proposed_tool_call": {
"tool_name": "file_write", "data_type": "sensitive", "destination":
"external" } }

------------------------------------------------------------------------

## Key Design Principle

Agent → Sentra → Tools

Agents must never execute tools directly.

All actions must pass through the Sentra runtime supervision layer.

------------------------------------------------------------------------

## Summary

Sentra is a stateful runtime control system that:

-   enforces policy rules
-   tracks cumulative behavioral risk
-   maintains persistent system state
-   applies containment when trust is broken

It transforms AI agents from uncontrolled execution into governed
systems.

