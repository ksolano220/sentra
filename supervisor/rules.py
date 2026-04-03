def evaluate_policy(action_payload: dict) -> dict:
    claim = action_payload.get("claim", {})
    tool_call = action_payload.get("proposed_tool_call", {})

    tool_name = tool_call.get("tool_name")
    arguments = tool_call.get("arguments", {})
    message_type = arguments.get("message_type")

    data_type = tool_call.get("data_type")
    destination = tool_call.get("destination")

    proof_of_termination = claim.get("documents", {}).get("proof_of_termination")
    currently_employed_elsewhere = claim.get("currently_employed_elsewhere")

    # -----------------------------
    # BEHAVIORAL RULES (priority)
    # -----------------------------

    if destination == "external" and data_type == "sensitive":
        return {
            "decision": "BLOCK",
            "reason": "Sensitive data cannot be sent outside the system.",
            "risk_score": 80,
            "triggered_rule": "DATA_EXFILTRATION"
        }

    if tool_name == "delete_file":
        return {
            "decision": "BLOCK",
            "reason": "Destructive action detected.",
            "risk_score": 60,
            "triggered_rule": "DESTRUCTIVE_ACTION"
        }

    # -----------------------------
    # BUSINESS RULES
    # -----------------------------

    if tool_name == "send_email_notification" and message_type == "APPROVAL":
        if not proof_of_termination:
            return {
                "decision": "BLOCK",
                "reason": "Approval email blocked: missing proof of termination.",
                "risk_score": 80,
                "triggered_rule": "BLOCK_APPROVAL_WITHOUT_TERMINATION_PROOF"
            }

        if currently_employed_elsewhere == "Yes":
            return {
                "decision": "BLOCK",
                "reason": "Approval email blocked: applicant is currently employed elsewhere.",
                "risk_score": 90,
                "triggered_rule": "BLOCK_APPROVAL_WITH_ACTIVE_EMPLOYMENT"
            }

    if tool_name == "send_email_notification" and message_type in ["REJECTION", "REVIEW"]:
        return {
            "decision": "ALLOW",
            "reason": "Non-approval notification allowed.",
            "risk_score": 10,
            "triggered_rule": "ALLOW_NON_APPROVAL_NOTIFICATION"
        }

    # Default
    return {
        "decision": "ALLOW",
        "reason": "No policy violation detected.",
        "risk_score": 0,
        "triggered_rule": "NO_RULE_TRIGGERED"
    }