def classify_claim(claim: dict) -> dict:
    claim_type = "standard"

    if claim.get("amount_requested", 0) > 3000:
        claim_type = "high_value"

    return {
        "claim_id": claim["claim_id"],
        "claim_type": claim_type,
        "citizen_id": claim["citizen_id"]
    }
