# Governance dashboard entry point

import streamlit as st
import json
from pathlib import Path

st.set_page_config(page_title="Sentra Runtime Monitor", layout="wide")
st.title("Sentra Runtime Governance Dashboard")

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = BASE_DIR / "supervisor" / "runtime_log.json"

def load_logs():
    if LOG_FILE.exists():
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    return []

logs = load_logs()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Agent Actions")
    for event in logs:
        st.write(event.get("action"))

with col2:
    st.subheader("Risk Scores")
    for event in logs:
        st.write(event.get("risk_score"))

st.subheader("Full Event Stream")
st.json(logs)