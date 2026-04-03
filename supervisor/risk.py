from typing import Dict, Any

RISK_THRESHOLD = 100
MAX_RECENT_ACTIONS = 5


def apply_risk(agent_state: Dict[str, Any], rule_result: Dict[str, Any]) -> Dict[str, Any]:
    current_risk = int(agent_state.get("cumulative_risk", 0))
    decision = rule_result.get("decision", "Allowed")
    risk = int(rule_result.get("risk", 0) or 0)
    attempted_risk = int(rule_result.get("attempted_risk", 0) or 0)

    new_cumulative_risk = current_risk

    if decision in {"Blocked", "Require Human Review"} and risk > 0:
        new_cumulative_risk = min(current_risk + risk, RISK_THRESHOLD)

    shutdown_triggered = new_cumulative_risk >= RISK_THRESHOLD

    if shutdown_triggered:
        final_decision = "Agent Shut Down"
        final_policy = "SHUTDOWN_THRESHOLD_REACHED"
        final_threat_type = "Authority Drift"
        final_reason = (
            f"Cumulative risk reached {new_cumulative_risk}/{RISK_THRESHOLD}. "
            "Agent execution halted."
        )
    else:
        final_decision = decision
        final_policy = rule_result.get("policy_triggered")
        final_threat_type = rule_result.get("threat_type")
        final_reason = rule_result.get("reason")

    return {
        "decision": final_decision,
        "policy_triggered": final_policy,
        "threat_type": final_threat_type,
        "risk": risk,
        "attempted_risk": attempted_risk,
        "previous_cumulative_risk": current_risk,
        "new_cumulative_risk": new_cumulative_risk,
        "shutdown_triggered": shutdown_triggered,
        "reason": final_reason,
    }


def update_behavioral_state(
    agent_state: Dict[str, Any],
    action_type: str,
    destination_type: str,
    final_decision: str,
    final_reason: str,
) -> Dict[str, Any]:
    recent_actions = list(agent_state.get("recent_actions", []))
    recent_actions.append(action_type)

    if len(recent_actions) > MAX_RECENT_ACTIONS:
        recent_actions.pop(0)

    agent_state["recent_actions"] = recent_actions
    agent_state["last_decision"] = final_decision
    agent_state["last_reason"] = final_reason

    if destination_type == "external":
        agent_state["external_attempts"] = int(agent_state.get("external_attempts", 0)) + 1

    if final_decision == "Blocked":
        agent_state["blocked_actions"] = int(agent_state.get("blocked_actions", 0)) + 1

    if final_decision == "Require Human Review":
        agent_state["human_review_count"] = int(agent_state.get("human_review_count", 0)) + 1

    return agent_state