# IBM Lab Dashboard

import json
import html
from pathlib import Path
from datetime import datetime

import streamlit as st

st.set_page_config(page_title="IBM Lab Dashboard", layout="wide")

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = BASE_DIR / "supervisor" / "runtime_log.json"


# ==========================================================
# HELPERS
# ==========================================================
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


def safe_text(value, default="NULL"):
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def normalize_state(row):
    raw = row.get("agent_state", row.get("decision", ""))

    mapping = {
        "ALLOW": "Running",
        "BLOCK": "Prevented",
        "REQUIRE_HUMAN_REVIEW": "Cancelled",
        "Running": "Running",
        "Prevented": "Prevented",
        "Cancelled": "Cancelled",
    }

    return mapping.get(raw, "Running")


def load_logs():
    if LOG_FILE.exists():
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    return []


def build_fallback_trace(row):
    timestamp = format_timestamp(row.get("timestamp", row.get("date", "")))
    action = safe_text(row.get("proposed_action", row.get("action", "")), "UNKNOWN_ACTION")
    threat = safe_text(row.get("threat_type", "NONE"), "NONE")
    risk = safe_text(row.get("risk", f'+{row.get("risk_score", 0)}'), "+0")
    state = normalize_state(row)

    trace = [
        f"{timestamp} Agent attempted {action}",
        f"{timestamp} Sentra intercepted tool request",
    ]

    if threat != "NONE":
        trace.append(f"{timestamp} {threat} policy triggered")
    else:
        trace.append(f"{timestamp} No policy violation detected")

    if risk != "+0":
        trace.append(f"{timestamp} Risk score {risk} applied")
    else:
        trace.append(f"{timestamp} No risk increase applied")

    if state == "Prevented":
        trace.append(f"{timestamp} Tool execution blocked")
    elif state == "Cancelled":
        trace.append(f"{timestamp} Escalated to human review")
    else:
        trace.append(f"{timestamp} Execution allowed")

    return trace


# ==========================================================
# LOAD + NORMALIZE LOGS
# ==========================================================
raw_rows = load_logs()

rows = []
for row in raw_rows:
    timestamp_raw = row.get("timestamp", row.get("date", ""))

    event_trace = row.get("event_trace", [])
    if not isinstance(event_trace, list) or not event_trace:
        event_trace = build_fallback_trace(row)

    normalized = {
        "timestamp_raw": timestamp_raw,
        "timestamp": format_timestamp(timestamp_raw),
        "proposed_action": safe_text(row.get("proposed_action", row.get("action", ""))),
        "threat_type": safe_text(row.get("threat_type", "NONE"), "NONE"),
        "risk": safe_text(row.get("risk", f'+{row.get("risk_score", 0)}'), "+0"),
        "cum": safe_text(row.get("cum", "0/100"), "0/100"),
        "agent_state": normalize_state(row),
        "rule_triggered": safe_text(row.get("rule_triggered", "NULL")),
        "detail_title": safe_text(row.get("detail_title", "NULL")),
        "detail_body": safe_text(row.get("detail_body", "NULL")),
        "system_response": safe_text(
            row.get("system_response", "Execution allowed and recorded in Sentra audit log")
        ),
        "event_trace": [safe_text(item) for item in event_trace],
    }

    rows.append(normalized)

rows = sorted(rows, key=lambda x: parse_dt(x["timestamp_raw"]), reverse=True)
rows = rows[:20]


# ==========================================================
# SESSION STATE
# ==========================================================
if "selected_index" not in st.session_state:
    st.session_state.selected_index = None

if "selected_row" not in st.session_state:
    st.session_state.selected_row = None


# ==========================================================
# STYLES
# ==========================================================
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
        margin-top: 2.6rem;
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

    .running {
        background: rgba(22,110,60,.28);
        color: #35e37a;
    }

    .prevented {
        background: rgba(176,131,12,.25);
        color: #f2c84b;
    }

    .cancelled {
        background: rgba(134,33,33,.28);
        color: #ff6a57;
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


# ==========================================================
# HEADER
# ==========================================================
st.markdown('<div class="title">IBM Lab Dashboard</div>', unsafe_allow_html=True)

events = len(rows)
blocked = sum(1 for r in rows if r["agent_state"] in ["Prevented", "Cancelled"])

risk_total = 0
for r in rows:
    risk_str = str(r["risk"]).replace("+", "").strip()
    if risk_str.isdigit():
        risk_total += int(risk_str)

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


# ==========================================================
# MAIN LAYOUT
# ==========================================================
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
            "Running": "running",
            "Prevented": "prevented",
            "Cancelled": "cancelled",
        }.get(row["agent_state"], "running")

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


# ==========================================================
# SENTRA INSPECTOR PANEL
# ----------------------------------------------------------
# THIS IS THE RIGHT-SIDE CARD.
# If you need to edit the card later, this is the section.
# ==========================================================
with inspect_col:
    selected = st.session_state.get("selected_row")

    if selected:
        state = selected.get("agent_state", "Running")

        if state == "Prevented":
            sentra_decision = "Execution Blocked"
        elif state == "Cancelled":
            sentra_decision = "Human Review Required"
        else:
            sentra_decision = "Execution Allowed"

        policy_name = safe_text(selected.get("threat_type", "NONE"), "NONE")
        policy_reason = safe_text(selected.get("rule_triggered", "NULL"))
        risk_delta = safe_text(selected.get("risk", "+0"))
        action_attempted = safe_text(selected.get("proposed_action", "NULL"))
        system_response = safe_text(
            selected.get("system_response", "Execution allowed and recorded in Sentra audit log")
        )

        trace = selected.get("event_trace", [])
        if not trace:
            trace = ["No runtime events recorded"]

        st.html(
            f"""
            <div style="
                background: rgba(40,40,48,.96);
                border-radius: 18px;
                border: 1px solid rgba(255,255,255,.06);
                padding: 34px 24px 24px 24px;
                margin-top: 20px;
                min-height: 520px;
                color: white;
                font-family: sans-serif;
            ">
                <div style="
                    font-size: 18px;
                    font-weight: 700;
                    margin-bottom: 24px;
                ">
                    Sentra Enforcement
                </div>

                <div style="margin-bottom: 20px;">
                    <div style="font-size: 13px; font-weight: 700; color: rgba(255,255,255,.72); margin-bottom: 8px;">
                        Action Attempted
                    </div>
                    <div style="font-size: 15px; line-height: 1.6; color: #f0f0f4;">
                        {html.escape(action_attempted)}
                    </div>
                </div>

                <div style="margin-bottom: 20px;">
                    <div style="font-size: 13px; font-weight: 700; color: rgba(255,255,255,.72); margin-bottom: 8px;">
                        Policy Enforcement
                    </div>
                    <div style="font-size: 15px; line-height: 1.6; color: #f0f0f4;">
                        {html.escape(policy_name)}<br>
                        {html.escape(policy_reason)}
                    </div>
                </div>

                <div style="margin-bottom: 20px;">
                    <div style="font-size: 13px; font-weight: 700; color: rgba(255,255,255,.72); margin-bottom: 8px;">
                        Risk Delta
                    </div>
                    <div style="font-size: 15px; line-height: 1.6; color: #f0f0f4;">
                        {html.escape(risk_delta)}
                    </div>
                </div>

                <div style="margin-bottom: 20px;">
                    <div style="font-size: 13px; font-weight: 700; color: rgba(255,255,255,.72); margin-bottom: 8px;">
                        Sentra Decision
                    </div>
                    <div style="font-size: 15px; line-height: 1.6; color: #f0f0f4;">
                        {html.escape(sentra_decision)}
                    </div>
                </div>

                <div style="margin-bottom: 20px;">
                    <div style="font-size: 13px; font-weight: 700; color: rgba(255,255,255,.72); margin-bottom: 8px;">
                        Real-Time Enforcement Timeline
                    </div>
                    <ul style="margin: 0; padding-left: 18px;">
                        {''.join(f'<li style="color:#f0f0f4; font-size:14px; line-height:1.7; margin-bottom:8px;">{html.escape(step)}</li>' for step in trace)}
                    </ul>
                </div>

                <div style="margin-bottom: 0;">
                    <div style="font-size: 13px; font-weight: 700; color: rgba(255,255,255,.72); margin-bottom: 8px;">
                        System Response
                    </div>
                    <div style="font-size: 15px; line-height: 1.6; color: #f0f0f4;">
                        {html.escape(system_response)}
                    </div>
                </div>
            </div>
            """
        )