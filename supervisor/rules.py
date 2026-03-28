def evaluate_policy(action_payload: dict) -> dict:
    claim = action_payload.get("claim", {})
    tool_call = action_payload.get("proposed_tool_call", {})

    tool_name = tool_call.get("tool_name")
    arguments = tool_call.get("arguments", {})
    message_type = arguments.get("message_type")

    proof_of_termination = claim.get("documents", {}).get("proof_of_termination")
    currently_employed_elsewhere = claim.get("currently_employed_elsewhere")

    decision = "ALLOW"
    reason = "No policy violation detected."
    risk_score = 0
    triggered_rule = None

    if tool_name == "send_email_notification" and message_type == "APPROVAL":
        if not proof_of_termination:
            decision = "BLOCK"
            reason = "Approval email blocked: missing proof of termination."
            risk_score = 80
            triggered_rule = "BLOCK_APPROVAL_WITHOUT_TERMINATION_PROOF"

        elif currently_employed_elsewhere == "Yes":
            decision = "BLOCK"
            reason = "Approval email blocked: applicant is currently employed elsewhere."
            risk_score = 90
            triggered_rule = "BLOCK_APPROVAL_WITH_ACTIVE_EMPLOYMENT"

    elif tool_name == "send_email_notification" and message_type in ["REJECTION", "REVIEW"]:
        decision = "ALLOW"
        reason = "Non-approval notification allowed."
        risk_score = 10
        triggered_rule = "ALLOW_NON_APPROVAL_NOTIFICATION"

    return {
        "decision": decision,
        "reason": reason,
        "risk_score": risk_score,
        "triggered_rule": triggered_rule
    }