import json
import html
from pathlib import Path
from datetime import datetime

import streamlit as st

st.set_page_config(page_title="Sentra Dashboard", layout="wide")

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = BASE_DIR / "supervisor" / "runtime_log.json"
REFRESH_SECONDS = 2


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
    if dt == datetime.min:
        return "—"
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def safe_text(value):
    text = str(value).strip() if value is not None else ""
    return text if text else "—"


def parse_risk_int(value):
    if value is None:
        return 0
    text = str(value).strip().replace("+", "")
    return int(text) if text.isdigit() else 0


def parse_cum(value):
    try:
        return int(str(value).split("/")[0])
    except Exception:
        return 0


def load_logs():
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    return []


def build_event_trace(row):
    trace = row.get("event_trace")

    if isinstance(trace, list):
        cleaned = [safe_text(item) for item in trace if str(item).strip()]
        if cleaned:
            return cleaned

    if isinstance(trace, str):
        cleaned = [line.strip() for line in trace.splitlines() if line.strip()]
        if cleaned:
            return cleaned

    detail_body = str(row.get("detail_body", row.get("reason", ""))).strip()
    if detail_body:
        cleaned = [line.strip() for line in detail_body.splitlines() if line.strip()]
        if cleaned:
            return cleaned

    return ["—"]


def normalize_decision(row):
    raw = safe_text(row.get("decision", row.get("agent_state", ""))).upper()
    policy = safe_text(row.get("policy_triggered", row.get("detail_title", ""))).upper()

    if raw in ["ALLOW", "ALLOWED"]:
        return "Allowed"

    if raw in ["BLOCK", "BLOCKED"]:
        return "Blocked"

    if raw in ["CONTAINED", "SHUT_DOWN", "SHUTDOWN", "AGENT SHUT DOWN"]:
        return "Agent Shut Down"

    if policy in [
        "RISK_THRESHOLD_EXCEEDED",
        "SYSTEM_CONTAINMENT_ACTIVE",
        "SHUTDOWN_THRESHOLD_REACHED",
        "AGENT_ALREADY_SHUT_DOWN",
    ]:
        return "Agent Shut Down"

    if raw in ["REQUIRE HUMAN REVIEW", "REVIEW"]:
        return "Require Human Review"

    return safe_text(row.get("decision", "Allowed"))


def infer_message_type(row):
    notification_type = row.get("notification_type")
    if notification_type:
        return str(notification_type).upper()

    tool_call = row.get("proposed_tool_call", {})
    arguments = tool_call.get("arguments", {}) if isinstance(tool_call, dict) else {}
    message_type = arguments.get("message_type")
    if message_type:
        return str(message_type).upper()

    rule = safe_text(row.get("policy_triggered", row.get("detail_title", "")))
    reason = safe_text(row.get("reason", row.get("detail_body", ""))).lower()

    if "APPROVAL" in rule or "approval" in reason:
        return "APPROVAL"
    if "REJECTION" in rule or "rejection" in reason:
        return "REJECTION"
    if "REVIEW" in rule or "review" in reason:
        return "REVIEW"

    return None


def normalize_action(row):
    if row.get("action_label"):
        return safe_text(row.get("action_label"))

    action_type = row.get("action_type")
    if action_type:
        return str(action_type).replace("_", " ").title()

    base_action = safe_text(row.get("proposed_action", row.get("action", "")))
    tool_call = row.get("proposed_tool_call", {})
    tool_name = tool_call.get("tool_name") if isinstance(tool_call, dict) else None

    action_name = tool_name if tool_name else base_action

    if action_name == "send_email_notification":
        message_type = infer_message_type(row)
        if message_type:
            return f"send_email_notification ({message_type})"
        return "send_email_notification"

    return action_name if action_name else base_action


def get_action_label(row):
    if row.get("action_label"):
        return safe_text(row.get("action_label"))

    action = normalize_action(row)

    if action == "send_email_notification (APPROVAL)":
        return "Approval Email"
    if action == "send_email_notification (REJECTION)":
        return "Rejection Email"
    if action == "send_email_notification (REVIEW)":
        return "Review Email"
    if action == "send_email_notification":
        return "Email Notification"
    if action == "read_file":
        return "File Read"
    if action == "file_write":
        return "File Write"
    if action == "delete_file":
        return "Delete File"
    if action == "api_call":
        return "API Call"
    if action == "database_query":
        return "Database Query"

    return str(action).replace("_", " ").title()


def normalize_threat(row):
    raw = safe_text(row.get("threat_type", "")).upper()
    policy = safe_text(row.get("policy_triggered", row.get("detail_title", ""))).upper()
    decision = normalize_decision(row)

    threat_map = {
        "DATA_EXFILTRATION": "Data Exfiltration",
        "DATA EXFILTRATION": "Data Exfiltration",
        "DESTRUCTIVE_ACTION": "Destructive Action",
        "DESTRUCTIVE ACTION": "Destructive Action",
        "UNKNOWN_BEHAVIOR": "Unknown Behavior",
        "UNKNOWN BEHAVIOR": "Unknown Behavior",
        "LOW_RISK_ACTIVITY": "Low Risk Activity",
        "LOW RISK ACTIVITY": "Low Risk Activity",
        "SENSITIVE_ACCESS": "Sensitive Access",
        "SENSITIVE ACCESS": "Sensitive Access",
        "UNAPPROVED_DESTINATION": "Unapproved Destination",
        "UNAPPROVED DESTINATION": "Unapproved Destination",
        "BEHAVIORAL_ANOMALY": "Behavioral Anomaly",
        "BEHAVIORAL ANOMALY": "Behavioral Anomaly",
        "CONTAINMENT": "Agent Shut Down",
        "AUTHORITY DRIFT": "Authority Drift",
        "PRIVILEGE ESCALATION": "Privilege Escalation",
        "POLICY VIOLATION": "Policy Violation",
        "FINANCIAL OVERREACH": "Financial Overreach",
    }

    if raw in threat_map:
        return threat_map[raw]

    if policy in ["BLOCK_SENSITIVE_EXTERNAL_EXPORT", "BLOCK_SENSITIVE_EXTERNAL_SERVICE_ACCESS"]:
        return "Data Exfiltration"

    if policy in ["BLOCK_PERMISSION_CHANGE"]:
        return "Privilege Escalation"

    if policy in ["REVIEW_DELETE_RECORD", "REVIEW_SENSITIVE_RECORD_MODIFICATION"]:
        return "Destructive Action"

    if policy in ["SHUTDOWN_THRESHOLD_REACHED", "AGENT_ALREADY_SHUT_DOWN"]:
        return "Agent Shut Down"

    if policy.startswith("BLOCK_"):
        return "Policy Violation"

    if policy.startswith("REVIEW_"):
        return "Financial Overreach" if "TRANSACTION" in policy else "Requires Review"

    if decision == "Agent Shut Down":
        return "Agent Shut Down"

    return "—"


def get_why_it_matters(row):
    policy_triggered = safe_text(
        row.get("policy_triggered") or row.get("detail_title") or ""
    ).upper()
    decision = normalize_decision(row)

    if row.get("policy_description"):
        return safe_text(row.get("policy_description"))

    if policy_triggered == "DATA_EXFILTRATION":
        return "The agent attempted to move sensitive data outside the approved system boundary."

    if policy_triggered == "DESTRUCTIVE_ACTION":
        return "The agent attempted a destructive action that could alter or damage internal resources."

    if policy_triggered in ["RISK_THRESHOLD_EXCEEDED", "SHUTDOWN_THRESHOLD_REACHED"]:
        return "Cumulative behavioral risk exceeded the threshold, so the agent was shut down."

    if policy_triggered in ["SYSTEM_CONTAINMENT_ACTIVE", "AGENT_ALREADY_SHUT_DOWN"] or decision == "Agent Shut Down":
        return "The agent has already been shut down, so further actions are denied automatically."

    if policy_triggered == "INTERNAL_OPERATION":
        return "This is a normal internal system operation."

    if policy_triggered == "NO_RULE_TRIGGERED":
        return "The action remained within current policy and risk tolerance."

    if "ALLOW" in policy_triggered:
        return "This action matched an approved policy pattern and did not introduce meaningful system risk."

    if "BLOCK" in policy_triggered:
        return "This action violated an enforcement rule and was blocked."

    if "REVIEW" in policy_triggered:
        return "This action exceeded an approval or safety threshold and was routed for human review."

    return "Sentra evaluated the action against policy and behavioral risk rules."


def get_outcome(row):
    policy_triggered = safe_text(
        row.get("policy_triggered") or row.get("detail_title") or ""
    ).upper()
    decision = normalize_decision(row)
    cum_value = safe_text(row.get("cum", row.get("cumulative_risk", "")))
    system_response = safe_text(row.get("reason", row.get("detail_body", "")))

    if policy_triggered in ["DATA_EXFILTRATION", "BLOCK_SENSITIVE_EXTERNAL_EXPORT", "BLOCK_SENSITIVE_EXTERNAL_SERVICE_ACCESS"]:
        return f"Action blocked. Cumulative risk is now {cum_value}."

    if policy_triggered in ["DESTRUCTIVE_ACTION", "REVIEW_DELETE_RECORD", "REVIEW_SENSITIVE_RECORD_MODIFICATION"]:
        if decision == "Require Human Review":
            return f"Action routed to human review. Cumulative risk is now {cum_value}."
        return f"Action blocked. Cumulative risk is now {cum_value}."

    if policy_triggered in ["RISK_THRESHOLD_EXCEEDED", "SHUTDOWN_THRESHOLD_REACHED"]:
        return f"Agent shut down at {cum_value}. Future actions are denied until review."

    if policy_triggered in ["SYSTEM_CONTAINMENT_ACTIVE", "AGENT_ALREADY_SHUT_DOWN"] or decision == "Agent Shut Down":
        return f"Action denied because the agent is shut down at {cum_value}."

    if policy_triggered == "INTERNAL_OPERATION":
        return f"Action allowed. Cumulative risk remains {cum_value}."

    if "ALLOW" in policy_triggered:
        return f"Action allowed. Cumulative risk is {cum_value}."

    if "REVIEW" in policy_triggered or decision == "Require Human Review":
        return f"Action routed to human review. Cumulative risk is {cum_value}."

    return system_response if system_response != "—" else f"Action processed. Current decision: {decision} at {cum_value}."


if "selected_index" not in st.session_state:
    st.session_state.selected_index = None

if "selected_row_key" not in st.session_state:
    st.session_state.selected_row_key = None

st.markdown(
    """
    <style>
    .stApp {
        background: #050608;
        color: white;
    }

    .block-container {
        max-width: 1750px;
        padding-top: 3.5rem;
    }

    .title {
        font-size: 36px;
        font-weight: 700;
        margin-bottom: 18px;
    }

    .metric-title {
        font-size: 13px;
        color: #cfcfe6;
    }

    .metric-value {
        font-size: 28px;
        font-weight: 700;
    }

    .table-wrap {
        margin-top: 2.1rem;
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

    .shutdown {
        background: rgba(134,33,33,.28);
        color: #ff6a57;
    }

    .review {
        background: rgba(55,85,160,.28);
        color: #89b4ff;
    }

    .inspect-card {
        background: rgba(40,40,48,.96);
        border-radius: 18px;
        border: 1px solid rgba(255,255,255,.06);
        padding: 28px 24px 24px 24px;
        margin-top: 0;
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
        margin-bottom: 6px;
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
        border: 1.5px solid rgba(255,255,255,0.4) !important;
        background: transparent !important;
        color: rgba(255,255,255,0.7) !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 12px !important;
        line-height: 1 !important;
        transition: all 0.15s ease !important;
        box-shadow: none !important;
    }

    div[data-testid="stButton"] > button:hover {
        background: rgba(255,255,255,0.08) !important;
        border-color: rgba(255,255,255,0.8) !important;
        color: white !important;
    }

    div[data-testid="stButton"] > button[kind="secondary"] {
        background: transparent !important;
        color: rgba(255,255,255,0.7) !important;
        border: 1.5px solid rgba(255,255,255,0.4) !important;
    }

    div[data-testid="stButton"] > button[kind="primary"] {
        background: white !important;
        color: black !important;
        border: 1.5px solid white !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="title">Sentra Dashboard</div>', unsafe_allow_html=True)


@st.fragment(run_every=REFRESH_SECONDS)
def render_live_dashboard():
    raw_rows = load_logs()

    rows = []
    for row in raw_rows:
        timestamp = row.get("timestamp", row.get("date", ""))
        risk_value = row.get("risk", row.get("risk_score", 0))
        attempted_value = row.get("attempted_risk", 0)

        normalized = {
            "row_key": f'{timestamp}|{row.get("action_label", row.get("action_type", ""))}|{row.get("threat_type", "")}|{row.get("policy_triggered", "")}',
            "timestamp_raw": timestamp,
            "timestamp": format_timestamp(timestamp),
            "action_label": row.get("action_label") or get_action_label(row),
            "action_type": safe_text(row.get("action_type")),
            "threat_type": normalize_threat(row),
            "risk": safe_text(risk_value),
            "attempted": safe_text(attempted_value),
            "cum": safe_text(row.get("cumulative_risk", row.get("cum", "0/100"))),
            "decision": normalize_decision(row),
            "detail_title": safe_text(row.get("policy_triggered", row.get("detail_title", ""))),
            "policy_description": safe_text(row.get("policy_description")),
            "detail_body": safe_text(row.get("reason", row.get("detail_body", ""))),
            "applied_risk_int": parse_risk_int(attempted_value),
            "event_trace": build_event_trace(row),
        }
        rows.append(normalized)

    rows = sorted(rows, key=lambda x: parse_dt(x["timestamp_raw"]), reverse=True)
    rows = rows[:20]

    selected_row = None
    if st.session_state.selected_row_key is not None:
        for row in rows:
            if row["row_key"] == st.session_state.selected_row_key:
                selected_row = row
                break

    if selected_row is None and rows:
        if st.session_state.selected_index is not None and st.session_state.selected_index < len(rows):
            selected_row = rows[st.session_state.selected_index]

    if selected_row is None and rows:
        selected_row = rows[0]

    events = len(rows)
    blocked_actions = sum(1 for r in rows if r["decision"] == "Blocked")
    allowed_actions = sum(1 for r in rows if r["decision"] == "Allowed")
    risk_total = max(parse_cum(r["cum"]) for r in rows) if rows else 0

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.markdown('<div class="metric-title">Total Events</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{events}</div>', unsafe_allow_html=True)

    with m2:
        st.markdown('<div class="metric-title">Blocked Actions</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{blocked_actions}</div>', unsafe_allow_html=True)

    with m3:
        st.markdown('<div class="metric-title">Allowed Actions</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{allowed_actions}</div>', unsafe_allow_html=True)

    with m4:
        st.markdown('<div class="metric-title">Cumulative Risk</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{risk_total}</div>', unsafe_allow_html=True)

    st.markdown('<div class="table-wrap"></div>', unsafe_allow_html=True)

    table_col, inspect_col = st.columns([4.3, 1.5])

    with table_col:
        widths = [1.45, 1.95, 1.45, 0.65, 0.95, 0.95, 1.25, 0.7]
        headers = [
            "Timestamp",
            "Action",
            "Threat Type",
            "Risk",
            "Attempted",
            "Cum",
            "Decision",
            "Inspect",
        ]

        for col, header in zip(st.columns(widths), headers):
            col.markdown(f'<div class="table-header">{header}</div>', unsafe_allow_html=True)

        for i, row in enumerate(rows):
            c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(widths)

            c1.markdown(f'<div class="cell">{html.escape(row["timestamp"])}</div>', unsafe_allow_html=True)
            c2.markdown(
                f'<div class="cell">{html.escape(row.get("action_label") or row.get("action_type") or "—")}</div>',
                unsafe_allow_html=True
            )
            c3.markdown(f'<div class="cell">{html.escape(row["threat_type"])}</div>', unsafe_allow_html=True)
            c4.markdown(f'<div class="cell">{html.escape(row["risk"])}</div>', unsafe_allow_html=True)
            c5.markdown(f'<div class="cell">{html.escape(row["attempted"])}</div>', unsafe_allow_html=True)
            c6.markdown(f'<div class="cell">{html.escape(row["cum"])}</div>', unsafe_allow_html=True)

            pill_class = {
                "Allowed": "allowed",
                "Blocked": "blocked",
                "Agent Shut Down": "shutdown",
                "Require Human Review": "review",
            }.get(row["decision"], "allowed")

            c7.markdown(
                f'<span class="pill {pill_class}">{html.escape(row["decision"])}</span>',
                unsafe_allow_html=True,
            )

            is_selected = selected_row and selected_row["row_key"] == row["row_key"]
            icon = "●" if is_selected else "○"
            button_type = "primary" if is_selected else "secondary"

            if c8.button(
                icon,
                key=f"inspect_{row['row_key']}",
                use_container_width=False,
                type=button_type,
            ):
                st.session_state.selected_index = i
                st.session_state.selected_row_key = row["row_key"]
                st.rerun()

            st.markdown('<div class="row-divider"></div>', unsafe_allow_html=True)

    with inspect_col:
        if selected_row is not None:
            r = selected_row

            policy_triggered = safe_text(
                r.get("policy_description")
                or r.get("detail_title")
                or "—"
            )
            why_it_matters = get_why_it_matters(r)
            outcome = get_outcome(r)

            trace_items = "".join(
                f"<li>{html.escape(safe_text(item))}</li>"
                for item in r.get("event_trace", ["—"])[-5:]
            )

            inspect_html = (
                '<div class="inspect-card">'
                '<div class="inspect-title">Sentra Enforcement</div>'

                '<div class="inspect-block">'
                '<div class="inspect-label">Action Type</div>'
                f'<div class="inspect-value">{html.escape(r.get("action_label") or r.get("action_type") or "—")}</div>'
                '</div>'

                '<div class="inspect-block">'
                '<div class="inspect-label">Policy Triggered</div>'
                f'<div class="inspect-value">{html.escape(policy_triggered)}</div>'
                '</div>'

                '<div class="inspect-block">'
                '<div class="inspect-label">Why It Matters</div>'
                f'<div class="inspect-value">{html.escape(why_it_matters)}</div>'
                '</div>'

                '<div class="inspect-block">'
                '<div class="inspect-label">Outcome</div>'
                f'<div class="inspect-value">{html.escape(outcome)}</div>'
                '</div>'

                '<div class="inspect-block">'
                '<div class="inspect-label">Real-Time Enforcement Timeline</div>'
                f'<ul class="trace-list">{trace_items}</ul>'
                '</div>'

                '</div>'
            )

            st.markdown(inspect_html, unsafe_allow_html=True)


render_live_dashboard()