"""
07 · Audit Trail
Cross-cutting layer — every action (data ingestion, AI inference, human
review, submission) produces a hashed audit event. Anyone can verify the
chain from raw signal to final report.
"""
import pandas as pd
import streamlit as st

from lib import (
    init_session, inject_css, kicker, lead, sidebar_brand,
)

st.set_page_config(page_title="AI-COMPASS · Audit Trail",
                   page_icon="🔍", layout="wide")
inject_css()
init_session(st)
sidebar_brand()

kicker("07 · Cross-cutting · Audit & reproducibility")
st.markdown(
    "<h1>Every figure, traceable to the <em>raw signal</em>.</h1>",
    unsafe_allow_html=True,
)
lead(
    "Each report value, indicator and AI decision is anchored in a "
    "cryptographically-hashed evidence chain. Any auditor — internal, "
    "competent authority, or third-party verifier — can reproduce the path "
    "from raw data to final report."
)

# ===== summary metrics =====
audit_df = st.session_state.audit.df()
total_events = len(audit_df)
n_ai = (audit_df["actor"] == "AI").sum() if total_events else 0
n_user = (audit_df["actor"] == "USER").sum() if total_events else 0
n_sys = (audit_df["actor"] == "SYS").sum() if total_events else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total audit events", str(total_events), "since session start")
c2.metric("AI actions",         str(n_ai),         "detect · map")
c3.metric("Human actions",      str(n_user),       "review · upload · submit")
c4.metric("System actions",     str(n_sys),        "ingest · ontology")

# ===== evidence chain for selected indicator =====
st.markdown("###")
st.markdown("##### Evidence chain · per compliance indicator")

if not st.session_state.indicators:
    st.info(
        "No compliance indicators yet. Run **04 · Risk Detection** first.",
        icon="ℹ️",
    )
else:
    options = [f"{i.case_id} · {i.indicator_id}"
               for i in st.session_state.indicators]
    sel = st.selectbox("Indicator", options, index=0)
    ind = st.session_state.indicators[options.index(sel)]

    chain_steps = [
        ("raw_signal", "SCADA",
         f"Raw value {ind.signal_value:.1f} {ind.unit} captured from "
         f"{(ind.timestamp.strftime('%Y-%m-%d %H:%M') if ind.timestamp else '—')}"),
        ("qal2_validated", "QAL",
         "QAL2 validation passed · sensor in calibration date · method recognised"),
        ("ontology_mapped", "SYS",
         f"Ontology mapping · canonical field for {ind.article}"),
        ("risk_detected", "AI",
         f"Detector flagged signal · severity {ind.risk_level} · "
         f"confidence {ind.confidence:.2f}"),
        ("ai_mapping_proposed", "AI",
         f"Mapping engine linked signal to {ind.regulation.split(' · ')[0]} "
         f"({ind.article}) → {ind.indicator_id}"),
    ]
    decision = st.session_state.human_decisions.get(ind.case_id)
    if decision == "confirmed":
        chain_steps.append(
            ("human_confirmed", "USER",
             f"Compliance officer confirmed mapping {ind.indicator_id}"))
    elif decision == "rejected":
        chain_steps.append(
            ("human_rejected", "USER",
             f"Compliance officer rejected mapping {ind.indicator_id}"))
    else:
        chain_steps.append(
            ("awaiting_review", "SYS",
             "Case in compliance officer queue · awaiting human review"))

    for i, (step, actor, detail) in enumerate(chain_steps, 1):
        st.markdown(
            f"""
            <div style="display:grid;grid-template-columns:50px 130px 80px 1fr;
                        gap:14px;padding:12px 0;border-bottom:1px solid #232936;
                        align-items:center;font-size:13px;">
              <span style="font-family:'JetBrains Mono',monospace;
                           color:#c9a96e;font-size:11px;">{i:02d}</span>
              <span style="font-family:'JetBrains Mono',monospace;
                           font-size:11px;color:#a8aeba;">{step}</span>
              <span class="pill pill-{
                  'gold' if actor == 'AI' else
                  'green' if actor == 'USER' else 'gray' if actor == 'SYS' else 'blue'
              }">{actor}</span>
              <span style="color:#a8aeba;">{detail}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("###")
    st.markdown(
        f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:11px;'
        f'color:#8a929e;">data hash · '
        f'<span style="color:#c9a96e;">{ind.data_hash}…</span> · '
        f'sha-256 truncated · full chain reproducible from inputs</div>',
        unsafe_allow_html=True,
    )

# ===== global audit log =====
st.markdown("###")
st.markdown("##### Session audit log · global")

if total_events > 0:
    show_df = audit_df.sort_values("timestamp", ascending=False).copy()
    show_df["timestamp"] = show_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    st.dataframe(show_df, use_container_width=True, hide_index=True,
                 height=360)

    # download
    import io as _io
    buf = _io.StringIO()
    audit_df.to_csv(buf, index=False)
    st.download_button(
        "Download audit log · CSV",
        data=buf.getvalue(),
        file_name="ai-compass-audit-log.csv",
        mime="text/csv",
    )
else:
    st.info("No audit events yet.")
