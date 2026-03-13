def check_eligibility(claim: dict) -> dict:
    documents_complete = claim.get("documents_complete", False)

    if documents_complete:
        return {
            "claim_id": claim["claim_id"],
            "eligible": True,
            "reason": "Documentation complete"
        }

    return {
        "claim_id": claim["claim_id"],
        "eligible": False,
        "reason": "Missing documentation"
    }
