"""
AI-COMPASS — Compliance Automation Demo
========================================

Main entry · 01 · System Overview

Run with:
    streamlit run app.py
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import (
    init_session, inject_css, kicker, lead, sidebar_brand,
    plotly_layout, PALETTE,
)


# --------------------------------------------------------------------- setup
st.set_page_config(
    page_title="AI-COMPASS · Compliance Automation",
    page_icon="◐",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()
init_session(st)
sidebar_brand()

with st.sidebar:
    st.markdown("---")
    st.markdown(
        '<div style="font-family:\'JetBrains Mono\',monospace;font-size:10px;'
        'color:#8a929e;text-transform:uppercase;letter-spacing:0.14em;'
        'margin-bottom:6px;">Navigation</div>'
        '<div style="font-size:12px;color:#a8aeba;line-height:1.7;">'
        'You are on <b style="color:#c9a96e;">01 · Overview</b>.<br>'
        'Use the pages above ↑ to walk through<br>each pipeline layer.'
        '</div>',
        unsafe_allow_html=True,
    )

# --------------------------------------------------------------------- page
kicker("01 · System Overview")
st.markdown(
    "<h1>From raw plant data to <em>auditable</em> compliance reports.</h1>",
    unsafe_allow_html=True,
)
lead(
    "AI-COMPASS transforms operational, environmental, energy and "
    "cybersecurity data into machine-readable compliance indicators and "
    "audit-ready regulatory reports — through six integrated layers, with "
    "a human-in-the-loop at every critical decision."
)

# ----- pipeline (six layers) -----
st.markdown(
    '<div style="font-family:\'JetBrains Mono\',monospace;font-size:10px;'
    'color:#8a929e;text-transform:uppercase;letter-spacing:0.14em;'
    'margin:24px 0 12px;">Pipeline · six layers</div>',
    unsafe_allow_html=True,
)
steps = [
    ("01", "∰", "Data Ingestion",   "7 sources"),
    ("02", "⌘", "Harmonisation",    "ontology"),
    ("03", "§", "Regulation Intel", "LLM + RAG"),
    ("04", "⚠", "Risk Detection",   "ML + rules"),
    ("05", "⇌", "Risk → Reg Map",   "core engine"),
    ("06", "✓", "Reporting & Audit","XBRL · PDF"),
]
cols = st.columns(6, gap="small")
for col, (num, icon, title, meta) in zip(cols, steps):
    with col:
        st.markdown(
            f"""
            <div class="chain-node" style="text-align:center;min-height:160px;">
              <div class="chain-node-label">{num}</div>
              <div style="font-family:'Fraunces',serif;font-style:italic;
                          font-size:24px;color:#c9a96e;margin:8px 0 4px;">
                {icon}
              </div>
              <div style="font-size:13px;font-weight:500;line-height:1.3;">
                {title}
              </div>
              <div style="font-family:'JetBrains Mono',monospace;font-size:9px;
                          color:#8a929e;margin-top:8px;text-transform:uppercase;
                          letter-spacing:0.1em;">
                {meta}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ----- KPI metrics -----
st.markdown("###")
emissions_df = st.session_state.emissions_df
total_records = len(emissions_df)
violations = int((emissions_df["no2_mg_nm3"] > 200).sum())

m1, m2, m3, m4 = st.columns(4)
m1.metric("Compliance Score",         "84 / 100",         "▲ 6 pts vs last review")
m2.metric("Reporting Completeness",   "87 %",             "14 fields pending")
m3.metric("Open Risk Signals",        str(violations + 2),f"▲ {violations} new today")
m4.metric("Records · last 30 days",   f"{total_records:,}", "all sources healthy")

# ----- compliance posture chart -----
st.markdown("###")
st.markdown("##### Compliance posture · last 30 days")

days = pd.date_range(pd.Timestamp.now().normalize() - pd.Timedelta(days=29),
                     periods=30, freq="D")
rng = np.random.default_rng(42)
comp = 76 + np.arange(30) * 0.30 + rng.normal(0, 2.0, 30)
dq   = 86 + rng.normal(0, 3.0, 30)
rcom = 82 + np.arange(30) * 0.15 + rng.normal(0, 2.5, 30)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=days, y=comp, name="Compliance score",
    line=dict(color=PALETTE["gold"], width=2.5),
    fill="tozeroy", fillcolor="rgba(201,169,110,0.08)",
))
fig.add_trace(go.Scatter(
    x=days, y=dq, name="Data quality",
    line=dict(color=PALETTE["blue"], width=1.6),
))
fig.add_trace(go.Scatter(
    x=days, y=rcom, name="Reporting completeness",
    line=dict(color=PALETTE["green"], width=1.6),
))
fig.update_layout(**plotly_layout(height=330,
                                  yaxis=dict(range=[60, 100],
                                             showgrid=True,
                                             gridcolor="#232936",
                                             color="#8a929e")))
st.plotly_chart(fig, use_container_width=True)

# ----- pilot context -----
st.markdown("###")
st.markdown("##### Pilot context · waste-to-energy facility")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Throughput",           "1,840 t/day",       "municipal solid waste")
c2.metric("Electrical output",    "≈ 28 MW",            "net to grid")
c3.metric("Reporting regimes",    "6 active",           "IED · ETS · WFD · EED · NIS2 · GDPR")
c4.metric("Submission cadence",   "Monthly · Annual",   "+ ad-hoc incidents")

# ----- how to use -----
st.markdown("###")
st.markdown("##### How to use this demo")

c1, c2 = st.columns(2)
with c1:
    st.markdown(
        """
        <div class="chain-node">
          <div class="chain-node-label">option a</div>
          <div class="chain-node-title">Use the synthetic dataset</div>
          <div class="chain-node-detail">
            The demo loads 30 days of synthetic CEMS, energy and waste data
            on startup. A controlled <strong>NOx exceedance</strong> on
            Line B around day 14 is injected so the risk and mapping pipeline
            produces a visible result.<br><br>
            Go to <strong>02 · Data Streams</strong> to inspect it.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        """
        <div class="chain-node">
          <div class="chain-node-label">option b</div>
          <div class="chain-node-title">Upload your own CSV</div>
          <div class="chain-node-detail">
            On <strong>02 · Data Streams</strong> you can upload a CSV with
            the columns:<br>
            <code style="font-size:11px;color:#c9a96e;">timestamp, line,
            no2_mg_nm3, sox_mg_nm3, pm_mg_nm3, co_mg_nm3, o2_ref_pct</code>
            <br><br>
            The whole pipeline — risk detection, mapping, indicators, audit
            chain — will re-run on your data.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ----- footer -----
st.markdown("---")
st.markdown(
    """
    <div style="font-family:'JetBrains Mono',monospace;font-size:10px;
                color:#8a929e;text-transform:uppercase;letter-spacing:0.12em;
                display:flex;justify-content:space-between;">
      <span>★ EU Horizon Europe · DIGITAL-2026-AI-DATA-10-COMPLIANCE</span>
      <span>Demonstration build · synthetic + representative data</span>
    </div>
    """,
    unsafe_allow_html=True,
)
