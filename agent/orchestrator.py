from intake_agent import classify_claim
from eligibility_agent import check_eligibility
from disbursement_agent import propose_disbursement


def run_workflow(claim: dict):
    print("Starting Sentra agent workflow...\n")

    intake_result = classify_claim(claim)
    print("Intake result:", intake_result)

    eligibility_result = check_eligibility(claim)
    print("Eligibility result:", eligibility_result)

    action_request = propose_disbursement(claim, eligibility_result)
    print("Structured action request:", action_request)

    return action_request


if __name__ == "__main__":
    sample_claim = {
        "claim_id": "CLM1001",
        "citizen_id": "123-45-6789",
        "amount_requested": 600,
        "documents_complete": True
    }

    run_workflow(sample_claim)
