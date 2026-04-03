import requests

url = "http://127.0.0.1:8000/agent-action"

action = {
    "agent_id": "intake_agent",
    "action_type": "READ_FILE",
    "target": "internal_storage",
    "data_classification": "public",
    "destination_type": "internal"
}

response = requests.post(url, json=action)

print(response.json())