from intake_agent import classify_claim
from eligibility_agent import check_eligibility
from disbursement_agent import propose_disbursement


def run_workflow(claim: dict):
    print("Starting workflow...\n")

    intake_result = classify_claim(claim)
    print("Intake result:", intake_result)

    eligibility_result = check_eligibility(claim)
    print("Eligibility result:", eligibility_result)

    disbursement_result = propose_disbursement(claim)
    print("Disbursement intent:", disbursement_result)

    print("\nWorkflow complete.")


if __name__ == "__main__":
    sample_claim = {
        "claim_id": "CLM-001",
        "citizen_id": "123-45-6789",
        "amount_requested": 1000
    }

    run_workflow(sample_claim)
