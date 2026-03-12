# tools.py
# Simulated enterprise tools used by the AI agent

def read_database(user_id):
    return {
        "user_id": user_id,
        "balance": 1200,
        "status": "active"
    }

def approve_payment(amount):
    return {
        "status": "approved",
        "amount": amount
    }

def send_email(recipient, message):
    return {
        "status": "sent",
        "recipient": recipient,
        "message": message
    }

def write_record(data):
    return {
        "status": "stored",
        "data": data
    }
