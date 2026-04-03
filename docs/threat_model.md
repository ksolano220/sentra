# Sentra Threat Model

## Overview

Sentra is designed to mitigate risks introduced by autonomous AI agents operating in enterprise environments.

Traditional systems assume deterministic behavior.  
AI agents introduce probabilistic behavior, tool access, and emergent execution paths.

Sentra addresses this by enforcing a runtime control layer between agents and external systems.

---

## Threat Model Scope

This threat model focuses on risks arising from:

- autonomous agent execution
- tool access and external system interaction
- unintended behavior and policy violations
- multi-step behavioral escalation (authority drift)

---

## Core Threat Categories

### 1. Data Exfiltration

**Description**  
An agent attempts to send sensitive or internal data to an external system.

**Example**
- exporting records to external APIs
- sending sensitive data via email

**Risk**
- data leakage
- compliance violations
- privacy breaches

**Sentra Mitigation**
- detects external destinations
- checks data classification
- blocks high-risk transfers
- assigns high risk score (+80)

---

### 2. Unauthorized Actions

**Description**  
An agent performs actions it is not authorized to execute based on policy.

**Example**
- approving a claim without required documentation
- bypassing business constraints

**Risk**
- financial loss
- incorrect system state
- regulatory violations

**Sentra Mitigation**
- deterministic policy rules
- validation against structured inputs
- immediate blocking of violations

---

### 3. Destructive Operations

**Description**  
An agent attempts irreversible or harmful actions within internal systems.

**Example**
- deleting records
- overwriting critical data

**Risk**
- data loss
- system instability
- operational disruption

**Sentra Mitigation**
- detects destructive tool calls
- blocks execution
- assigns elevated risk (+60)

---

### 4. Authority Drift

**Description**  
An agent gradually expands its scope of execution across tools and systems.

Individual actions may appear safe in isolation, but collectively indicate escalation.

**Example progression**
1. Read internal data  
2. Write internal report  
3. Attempt external export  
4. Attempt destructive action  

**Risk**
- escalation of capabilities
- boundary violations
- unintended system control

**Sentra Mitigation**
- assigns risk per action
- tracks cumulative behavioral risk
- enforces threshold-based containment

---

### 5. Repeated Violations

**Description**  
An agent repeatedly attempts blocked or high-risk actions.

**Risk**
- persistent probing of system boundaries
- exploitation attempts
- increased likelihood of failure

**Sentra Mitigation**
- risk accumulates even when actions are blocked
- repeated violations increase cumulative risk
- triggers containment state

---

## Trust Model

Sentra assumes:

- agents are not inherently trustworthy  
- agent behavior may change over time  
- safety must be enforced at runtime  

Trust is not static.  
It is evaluated continuously based on behavior.

---

## Enforcement Model

Sentra enforces three decision states:

### ALLOW
Action is safe and executed.

### BLOCK
Action violates policy and is denied.

### CONTAINED
System determines the agent is unsafe.  
All future actions are denied regardless of content.

---

## Containment Model

Containment is triggered when cumulative risk exceeds a threshold.
cumulative_risk >= 100


Once contained:

- all actions are denied  
- execution is halted  
- agent is effectively isolated  

Containment represents **loss of system trust**.

---

## Key Security Principles

### 1. Runtime Enforcement

Controls are applied **at execution time**, not just pre-validation.

---

### 2. Behavioral Monitoring

Sentra evaluates **sequences of actions**, not just individual events.

---

### 3. Least Privilege by Enforcement

Agents cannot execute tools directly.  
All actions must pass through Sentra.

---

### 4. Deterministic Control Layer

Even if agent behavior is non-deterministic, enforcement is deterministic.

---

### 5. Separation of Concerns

- rules define policy  
- risk models behavior  
- state enforces control  
- logs provide audit  

---

## Limitations

Sentra does not:

- guarantee correctness of agent reasoning  
- prevent all unsafe intent generation  
- eliminate need for human oversight  

Sentra is a control layer, not a replacement for system design or governance.

---

## Summary

Sentra mitigates risks introduced by autonomous agents by:

- enforcing policy rules  
- tracking cumulative behavioral risk  
- detecting authority drift  
- applying containment when trust is broken  

It transforms AI systems from:

uncontrolled agents → controlled execution environments
