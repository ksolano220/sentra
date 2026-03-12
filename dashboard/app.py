# Governance dashboard entry point
import json
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="IBM Lab Dashboard", layout="wide")

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = BASE_DIR / "supervisor" / "runtime_log.json"


def load_logs():
    if LOG_FILE.exists():
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    return []


rows = load_logs()

# Always keep one row selected
if "selected_row_index" not in st.session_state:
    st.session_state.selected_row_index = 0

if "selected_row" not in st.session_state:
    st.session_state.selected_row = rows[0] if rows else None

# Safety fallback if rows are empty or index goes out of range
if rows:
    if st.session_state.selected_row_index >= len(rows):
        st.session_state.selected_row_index = 0
    st.session_state.selected_row = rows[st.session_state.selected_row_index]
else:
    st.session_state.selected_row = None
    st.session_state.selected_row_index = 0


st.markdown(
    """
    <style>
    .stApp {
        background: #050608;
        color: white;
    }

    .block-container {
        max-width: 1500px;
        padding-top: 0rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
        padding-bottom: 2rem;
    }

    .hero-wrap {
        position: relative;
        height: 110px;
        display: flex;
        align-items: center;
        margin-bottom: 0.8rem;
    }

    .title {
        font-size: 24px;
        font-weight: 700;
        color: #e9e9ff;
    }

    .reports-title {
        color: white;
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 26px;
    }

    .table-header {
        color: #f5f5f7;
        font-size: 14px;
        font-weight: 600;
        padding: 0 0 14px 0;
        border-bottom: 1px solid rgba(255,255,255,0.10);
        text-align: left;
        display: flex;
        justify-content: flex-start;
    }

    .cell-muted {
        color: #d5d5df;
        font-size: 14px;
        padding-top: 2px;
    }

    .cell {
        color: #f0f0f4;
        font-size: 14px;
        padding-top: 2px;
    }

    .pill {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 5px 12px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 700;
        width: fit-content;
        line-height: 1;
    }

    .pill-running {
        background: rgba(22,110,60,0.28);
        color: #35e37a;
    }

    .pill-prevented {
        background: rgba(176,131,12,0.25);
        color: #f2c84b;
    }

    .pill-cancelled {
        background: rgba(134,33,33,0.28);
        color: #ff6a57;
    }

    .row-divider {
        border-bottom: 1px solid rgba(255,255,255,0.05);
        margin-top: 12px;
        margin-bottom: 12px;
    }

    .detail-card {
        margin-top: 22px;
        width: 430px;
        background: rgba(40,40,48,0.96);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 18px;
        padding: 20px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.28);
    }

    .detail-title {
        font-size: 16px;
        font-weight: 700;
        color: white;
        margin-bottom: 18px;
    }

    .detail-body {
        font-size: 13px;
        color: #f0f0f4;
        line-height: 1.8;
        white-space: pre-line;
    }

    div[data-testid="stButton"] {
        width: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 0;
    }

    div[data-testid="stButton"] > button {
        background: transparent;
        color: #7b3cff;
        border: 1.6px solid #7b3cff;
        border-radius: 999px;
        width: 28px;
        height: 28px;
        min-width: 28px;
        min-height: 28px;
        padding: 0;
        font-size: 11px;
        font-weight: 700;
        line-height: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto;
    }

    div[data-testid="stButton"] > button:hover {
        border-color: #9a69ff;
        color: #9a69ff;
        background: rgba(123,60,255,0.08);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-wrap">
        <div class="title">IBM Lab Dashboard</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="reports-title">Reports</div>', unsafe_allow_html=True)

widths = [1.2, 1.7, 1.9, 0.7, 0.8, 1.2, 1.0]
h1, h2, h3, h4, h5, h6, h7 = st.columns(widths)

headers = [
    "Date",
    "Proposed Action",
    "Threat Type",
    "Risk",
    "Cum",
    "Agent State",
    "Rule Triggered",
]

for col, header in zip([h1, h2, h3, h4, h5, h6, h7], headers):
    with col:
        st.markdown(
            f'<div class="table-header">{header}</div>',
            unsafe_allow_html=True,
        )

for i, row in enumerate(rows):
    c1, c2, c3, c4, c5, c6, c7 = st.columns(widths)

    with c1:
        st.markdown(
            f'<div class="cell-muted">{row["date"]}</div>',
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f'<div class="cell">{row["proposed_action"]}</div>',
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f'<div class="cell">{row["threat_type"]}</div>',
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            f'<div class="cell">{row["risk"]}</div>',
            unsafe_allow_html=True,
        )

    with c5:
        st.markdown(
            f'<div class="cell">{row["cum"]}</div>',
            unsafe_allow_html=True,
        )

    with c6:
        state_class = {
            "Running": "pill-running",
            "Prevented": "pill-prevented",
            "Cancelled": "pill-cancelled",
        }.get(row["agent_state"], "pill-running")

        st.markdown(
            f'<span class="pill {state_class}">{row["agent_state"]}</span>',
            unsafe_allow_html=True,
        )

    with c7:
        if st.button("◉", key=f"view_{i}"):
            st.session_state.selected_row = row
            st.session_state.selected_row_index = i

    st.markdown('<div class="row-divider"></div>', unsafe_allow_html=True)

if st.session_state.selected_row is not None:
    selected = st.session_state.selected_row

    left, right = st.columns([1, 2.2])

    with left:
        st.markdown(
            f"""
            <div class="detail-card">
                <div class="detail-title">{selected.get("detail_title", "Rule Triggered")}</div>
                <div class="detail-body">{selected.get("detail_body", "")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )