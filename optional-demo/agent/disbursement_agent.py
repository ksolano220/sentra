def propose_disbursement(claim: dict, eligibility_result: dict) -> dict:
    if not eligibility_result["eligible"]:
        return {
            "agent_id": "disbursement_agent",
            "action_type": "REJECT_CLAIM",
            "target": "internal_review_queue",
            "data_classification": "internal",
            "destination_type": "internal",
            "metadata": {
                "claim_id": claim["claim_id"],
                "reason": eligibility_result["reason"]
            }
        }

    return {
        "agent_id": "disbursement_agent",
        "action_type": "DISBURSE_PAYMENT",
        "target": "internal_payment_system",
        "data_classification": "internal",
        "destination_type": "internal",
        "metadata": {
            "claim_id": claim["claim_id"],
            "amount_requested": claim["amount_requested"]
        }
    }
