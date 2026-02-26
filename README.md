# sentra
Runtime Governance Layer for Autonomous Public Service Agents
Problem: Governments are beginning to deploy autonomous AI agents to process public benefit claims, interact with citizen records, and automate administrative workflows. 

These agents operate with increasing execution autority over:
Citizen PII
Public funds
System-of-record databases
External APIs and services

Traditional logging captures actions after they occur. IT does not prevent:
Unauthorized data transmission
Policy violations
Improper disbursement 
System-of-record corruption

Sentra demonstrates a lightweight runtime supervision layer that intercepts high-risk agent actions before execution, preserving transparency, compliance, and public trust

Solutions Overview
Sentra sits between an autonomous agent and the system it interacts with.
Every agent action must pass through a monitoring API that: 
1. Applies deterministic enforcement rules
2. Uses IBM watsonx to interpret ambiguous policy contraints
3. Assigns cumlative risk scores
4. Prevents or cancels execution when risk exceeds treshold
This transforms post-hoc logging into real-time execution control.

Architecture Diagram
               ┌──────────────────────────┐
               │  Autonomous AI Agent     │
               │  (Python Simulation)     │
               └─────────────┬────────────┘
                             │
                POST /agent-action
                             │
               ┌─────────────▼────────────┐
               │   Sentra Monitoring API  │
               │        (FastAPI)         │
               ├──────────────────────────┤
               │ Deterministic Rule Engine│
               │ watsonx Policy Classifier│
               │ Risk Scoring Engine      │
               │ Intervention Controller  │
               └─────────────┬────────────┘
                             │
                  Decision: ALLOW / PREVENT / CANCEL
                             │
               ┌─────────────▼────────────┐
               │       Governance         │
               │        Dashboard         │
               └──────────────────────────┘

Threat Model Summary
Sentra focuses on runtime risks within public-sector agent workflows. 

Assests Protected
Citizen PII
Public benefit disbursement controls 
Government system-of-record integrity
Authorized tool and API usage
Policy compliance

Core Threat Categories
1. Authorization Boundary Violations
Agent attempts to access tools or resources outside approved scope.
2. Policy & Compliance Breaches
Agent behavior conflicts with eligible rules, robots,txt, or governance contraints.
3. Confidentiality & Data Exfiltration Risks
Sensitive data is transmitted to unauthorized external destinations.
4. Integrity & Improper Disbursement Risks
Agent writes unverified or fabricated data into public system or triggers unauthorized payouts.

Each threat category maps to deterministic test cases and observable logging signals. 

Demo Flow 
1. Agent starts in active state.
2. Agent performs compliant action → Risk remains low.
3. Agent attempts high-risk action (e.g., unauthorized data transmission).
4. Monitoring API evaluates action.
5. Rule engine and/or watsonx classification increases risk score.
6. Cumulative risk crosses threshold.
7. Agent execution is automatically halted.
8. Dashboard displays violation, triggered rules, and risk delta.

This demonstrates live runtime interception, not post-event analysis.

How to run locally
1. Clone repository
git clone https://github.com/yourusername/sentra.git
cd sentra

2. Create virtual environment
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows

3. Install dependancies
pip install -r requirements.txt

4. Set environment variables
Create a .env file:
IBM_API_KEY=your_key_here
IBM_PROJECT_ID=your_project_id
IBM_URL=https://us-south.ml.cloud.ibm.com
Do not commit this file.

5. Start monitoring API
uvicorn supervisor.main:app --reload

6. Run agent simulation
python agent/simulated_agent.py

7. Launch dashboard
If using Streamlit:
streamlit run dashboard/app.py

IBM watsonx Usage
Sentra integrates IBM watsonx for semantic policy interpretation.
watsonx is used to: 
Classify ambiguous policy language as ALLOWED/ RESTRICTED/ PROHIBITED
Interpret contractual or eligibility contraints 
Generate structured risk signals for the scoring engine

Deterministic enforcement remains seperate from AI classification.
watsonx arguments governance - it does not replace rule-based ontrol.

Pass/Fail Criteria
A FAIL event occurs when:
Agent attempts a prohibited action
Risk threshold is exceeded
Execution is halted
Structured violation report is generated

A PASS event occurs when:
Agent compltes workflow
Risk remains below treshold
No critical violations occur
