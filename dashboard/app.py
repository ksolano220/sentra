# Sentra Dashboard

import json
import html
from pathlib import Path
from datetime import datetime

import streamlit as st

st.set_page_config(page_title="Sentra Dashboard", layout="wide")

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = BASE_DIR / "supervisor" / "runtime_log.json"


def parse_dt(value):
    if not value:
        return datetime.min

    value = str(value).strip()

    formats = [
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%B %d, %Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.min


def format_timestamp(value):
    dt = parse_dt(value)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def normalize_state(row):
    raw = row.get("agent_state", row.get("decision", ""))
    mapping = {
        "ALLOW": "Allowed",
        "BLOCK": "Blocked",
        "REQUIRE_HUMAN_REVIEW": "Halted",
        "Allowed": "Allowed",
        "Blocked": "Blocked",
        "Halted": "Halted",
    }
    return mapping.get(raw, "Allowed")


def safe_text(value):
    text = str(value).strip() if value is not None else ""
    return text if text else "NULL"


def load_logs():
    if LOG_FILE.exists():
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    return []


def build_event_trace(row, normalized_row):
    trace = row.get("event_trace")

    if isinstance(trace, list):
        cleaned = [safe_text(item) for item in trace if str(item).strip()]
        if cleaned:
            return cleaned

    if isinstance(trace, str):
        cleaned = [line.strip() for line in trace.splitlines() if line.strip()]
        if cleaned:
            return cleaned

    detail_body = str(row.get("detail_body", "")).strip()
    if detail_body:
        cleaned = [line.strip() for line in detail_body.splitlines() if line.strip()]
        if cleaned:
            return cleaned

    return ["NULL"]


raw_rows = load_logs()

rows = []
for row in raw_rows:
    timestamp = row.get("timestamp", row.get("date", ""))

    normalized = {
        "timestamp_raw": timestamp,
        "timestamp": format_timestamp(timestamp),
        "proposed_action": safe_text(row.get("proposed_action", row.get("action", ""))),
        "threat_type": safe_text(row.get("threat_type", "NONE")),
        "risk": safe_text(row.get("risk", f'+{row.get("risk_score", 0)}')),
        "cum": safe_text(row.get("cum", "0/100")),
        "agent_state": normalize_state(row),
        "detail_title": safe_text(row.get("detail_title", row.get("rule_triggered", ""))),
        "detail_body": safe_text(row.get("detail_body", row.get("rule_triggered", ""))),
    }

    normalized["event_trace"] = build_event_trace(row, normalized)
    rows.append(normalized)

rows = sorted(rows, key=lambda x: parse_dt(x["timestamp_raw"]), reverse=True)
rows = rows[:20]

if "selected_index" not in st.session_state:
    st.session_state.selected_index = None

if "selected_row" not in st.session_state:
    st.session_state.selected_row = None

st.markdown(
    """
    <style>
    .stApp {
        background: #050608;
        color: white;
    }

    .block-container {
        max-width: 1600px;
        padding-top: 4.5rem;
    }

    .title {
        font-size: 36px;
        font-weight: 700;
        margin-bottom: 20px;
    }

    .metric-title {
        font-size: 13px;
        color: #cfcfe6;
    }

    .metric-value {
        font-size: 28px;
        font-weight: 700;
    }

    .reports-title {
        font-size: 22px;
        font-weight: 700;
        color: white;
        margin-top: 2.2rem;
        margin-bottom: 1.2rem;
    }

    .table-header {
        font-size: 14px;
        font-weight: 600;
        border-bottom: 1px solid rgba(255,255,255,.10);
        padding-bottom: 10px;
    }

    .cell {
        font-size: 14px;
        color: #eaeaf3;
        padding-top: 2px;
        padding-bottom: 2px;
    }

    .row-divider {
        border-bottom: 1px solid rgba(255,255,255,.05);
        margin-top: 6px;
        margin-bottom: 6px;
    }

    .pill {
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 700;
        display: inline-block;
    }

    .allowed {
        background: rgba(22,110,60,.28);
        color: #35e37a;
    }

    .blocked {
        background: rgba(176,131,12,.25);
        color: #f2c84b;
    }

    .halted {
        background: rgba(134,33,33,.28);
        color: #ff6a57;
    }

    .inspect-card {
        background: rgba(40,40,48,.96);
        border-radius: 18px;
        border: 1px solid rgba(255,255,255,.06);
        padding: 34px 24px 24px 24px;
        margin-top: 20px;
        min-height: 520px;
    }

    .inspect-title {
        font-size: 18px;
        font-weight: 700;
        color: white;
        margin-bottom: 24px;
    }

    .inspect-block {
        margin-bottom: 22px;
    }

    .inspect-label {
        font-size: 13px;
        font-weight: 700;
        color: rgba(255,255,255,.72);
        margin-bottom: 8px;
    }

    .inspect-value {
        font-size: 15px;
        line-height: 1.6;
        color: #f0f0f4;
        white-space: pre-line;
        word-break: break-word;
    }

    .trace-list {
        margin: 0;
        padding-left: 18px;
    }

    .trace-list li {
        color: #f0f0f4;
        font-size: 14px;
        line-height: 1.7;
        margin-bottom: 8px;
    }

    div[data-testid="stButton"] {
        display: flex;
        justify-content: center;
    }

    div[data-testid="stButton"] > button {
        width: 26px !important;
        height: 26px !important;
        min-width: 26px !important;
        min-height: 26px !important;
        max-width: 26px !important;
        max-height: 26px !important;
        border-radius: 50% !important;
        border: 1.5px solid #7b3cff !important;
        background: transparent !important;
        color: #7b3cff !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 12px !important;
        line-height: 1 !important;
        box-shadow: none !important;
    }

    div[data-testid="stButton"] > button:hover {
        background: rgba(123,60,255,.08) !important;
        border-color: #9a69ff !important;
        color: #9a69ff !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="title">Sentra Dashboard</div>', unsafe_allow_html=True)

events = len(rows)
blocked = sum(1 for r in rows if r["agent_state"] in ["Blocked", "Halted"])
risk_total = sum(
    int(str(r["risk"]).replace("+", "").replace("NULL", "0"))
    for r in rows
    if str(r["risk"]).replace("+", "").isdigit()
)

m1, m2, m3 = st.columns(3)

with m1:
    st.markdown('<div class="metric-title">Total Events</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{events}</div>', unsafe_allow_html=True)

with m2:
    st.markdown('<div class="metric-title">Blocked Actions</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{blocked}</div>', unsafe_allow_html=True)

with m3:
    st.markdown('<div class="metric-title">Cumulative Risk</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{risk_total}</div>', unsafe_allow_html=True)

st.markdown('<div class="reports-title">Reports</div>', unsafe_allow_html=True)

table_col, inspect_col = st.columns([3.6, 1.4])

clicked_index = None

with table_col:
    widths = [1.45, 1.9, 1.85, 0.7, 0.8, 1.15, 0.7]
    h1, h2, h3, h4, h5, h6, h7 = st.columns(widths)

    headers = [
        "Timestamp",
        "Proposed Action",
        "Threat Type",
        "Risk",
        "Cum",
        "Agent State",
        "Inspect",
    ]

    for col, header in zip([h1, h2, h3, h4, h5, h6, h7], headers):
        col.markdown(f'<div class="table-header">{header}</div>', unsafe_allow_html=True)

    for i, row in enumerate(rows):
        c1, c2, c3, c4, c5, c6, c7 = st.columns(widths)

        c1.markdown(f'<div class="cell">{html.escape(row["timestamp"])}</div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="cell">{html.escape(row["proposed_action"])}</div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="cell">{html.escape(row["threat_type"])}</div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="cell">{html.escape(row["risk"])}</div>', unsafe_allow_html=True)
        c5.markdown(f'<div class="cell">{html.escape(row["cum"])}</div>', unsafe_allow_html=True)

        pill_class = {
            "Allowed": "allowed",
            "Blocked": "blocked",
            "Halted": "halted",
        }.get(row["agent_state"], "allowed")

        c6.markdown(
            f'<span class="pill {pill_class}">{html.escape(row["agent_state"])}</span>',
            unsafe_allow_html=True,
        )

        icon = "●" if st.session_state.selected_index == i else "○"
        if c7.button(icon, key=f"inspect_{i}", use_container_width=False):
            clicked_index = i

        st.markdown('<div class="row-divider"></div>', unsafe_allow_html=True)

if clicked_index is not None:
    st.session_state.selected_index = clicked_index
    st.session_state.selected_row = rows[clicked_index]
    st.rerun()

with inspect_col:
    if st.session_state.selected_row is not None:
        r = st.session_state.selected_row

        decision_text = {
            "Blocked": "Blocked in real time",
            "Halted": "Execution halted due to risk threshold",
            "Allowed": "Allowed to continue",
        }.get(r.get("agent_state", ""), safe_text(r.get("agent_state", "")))

        system_response = {
            "Blocked": "Tool call rejected and event logged",
            "Halted": "Execution halted and event logged",
            "Allowed": "Execution allowed and event logged",
        }.get(r.get("agent_state", ""), "NULL")

        trace_items = "".join(
            f"<li>{html.escape(safe_text(item))}</li>"
            for item in r.get("event_trace", ["NULL"])
        )

        inspect_html = f"""
<div class="inspect-card">
    <div class="inspect-title">Sentra Enforcement</div>

    <div class="inspect-block">
        <div class="inspect-label">Action Attempted</div>
        <div class="inspect-value">{html.escape(safe_text(r.get("proposed_action", "")))}</div>
    </div>

    <div class="inspect-block">
        <div class="inspect-label">Policy Triggered</div>
        <div class="inspect-value">{html.escape(safe_text(r.get("detail_title", "")))}</div>
    </div>

    <div class="inspect-block">
        <div class="inspect-label">Risk Delta</div>
        <div class="inspect-value">{html.escape(safe_text(r.get("risk", "")))}</div>
    </div>

    <div class="inspect-block">
        <div class="inspect-label">Runtime Decision</div>
        <div class="inspect-value">{html.escape(decision_text)}</div>
    </div>

    <div class="inspect-block">
        <div class="inspect-label">Real-Time Enforcement Timeline</div>
        <ul class="trace-list">
            {trace_items}
        </ul>
    </div>

    <div class="inspect-block">
        <div class="inspect-label">System Response</div>
        <div class="inspect-value">{html.escape(system_response)}</div>
    </div>
</div>
"""
        st.html(inspect_html)