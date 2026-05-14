"""
06 · Compliance Reports
Layer 6 — generates auto-drafted regulatory reports from the compliance
indicators produced by the mapping engine. Reports are exportable as JSON
(stand-in for XBRL) and human-readable summaries.
"""
import io
import json
import pandas as pd
import streamlit as st

from lib import (
    init_session, inject_css, kicker, lead, sidebar_brand,
)

st.set_page_config(page_title="AI-COMPASS · Compliance Reports",
                   page_icon="📋", layout="wide")
inject_css()
init_session(st)
sidebar_brand()

kicker("06 · Layer 6 · Reporting")
st.markdown(
    "<h1>Auto-drafted, <em>auditable</em> regulatory reports.</h1>",
    unsafe_allow_html=True,
)
lead(
    "For every regime AI-COMPASS produces a structured draft — "
    "machine-readable (XBRL/JSON/XML) and a human-readable view — with the "
    "full evidence chain attached. The compliance officer only reviews, "
    "edits, and submits."
)

# ===== status cards =====
df_em = st.session_state.emissions_df
violations = [i for i in st.session_state.indicators if i.violation]

c1, c2, c3 = st.columns(3)
with c1:
    pill = ("pill-red" if violations else "pill-amber")
    label = ("● draft · violations flagged" if violations
             else "● draft · clean")
    st.markdown(
        f"""
        <div class="chain-node">
          <div class="chain-node-label">Q1 · IED report</div>
          <div class="chain-node-title">Industrial Emissions</div>
          <div class="chain-node-detail">
            Completeness: <strong>94%</strong><br>
            Incidents flagged: <strong>{len(violations)}</strong><br>
            Deadline: <strong>in 18 days</strong><br>
            Regime: <strong>Monthly + Quarterly</strong>
          </div>
          <div style="margin-top:12px;"><span class="pill {pill}">{label}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        """
        <div class="chain-node">
          <div class="chain-node-label">2025 · ETS verification</div>
          <div class="chain-node-title">EU ETS · annual MRV</div>
          <div class="chain-node-detail">
            Verified emissions: <strong>412,308 tCO₂e</strong><br>
            Verifier: <strong>Accredited body</strong><br>
            Submitted: <strong>2026-03-28</strong><br>
            Status: <strong>signed &amp; archived</strong>
          </div>
          <div style="margin-top:12px;"><span class="pill pill-green">● signed</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        """
        <div class="chain-node">
          <div class="chain-node-label">Q1 · WFD waste</div>
          <div class="chain-node-title">Waste tonnages</div>
          <div class="chain-node-detail">
            Completeness: <strong>76%</strong><br>
            Missing: <strong>8 EWC codes</strong><br>
            Deadline: <strong>in 32 days</strong><br>
            Regime: <strong>Quarterly</strong>
          </div>
          <div style="margin-top:12px;"><span class="pill pill-amber">● draft</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ===== full report preview =====
st.markdown("###")
st.markdown("##### Q1 IED report · auto-generated draft")

# Compute aggregate emission stats per pollutant
def stats(df, col, limit, unit):
    s = df[col].dropna()
    if s.empty:
        return None
    return {
        "Parameter": col.split("_")[0].upper(),
        "Limit": f"{limit} {unit}",
        "Average": f"{s.mean():.1f}",
        "Maximum": f"{s.max():.1f}",
        "Exceedances": int((s > limit).sum()),
    }

rows = []
for col, limit, unit in [
    ("no2_mg_nm3", 200, "mg/Nm³"),
    ("sox_mg_nm3", 50, "mg/Nm³"),
    ("pm_mg_nm3", 10, "mg/Nm³"),
    ("co_mg_nm3", 50, "mg/Nm³"),
]:
    s = stats(df_em, col, limit, unit)
    if s:
        rows.append(s)
report_df = pd.DataFrame(rows)

period_start = df_em["timestamp"].min().strftime("%Y-%m-%d")
period_end = df_em["timestamp"].max().strftime("%Y-%m-%d")

st.markdown(
    f"""
    <div style="background:rgba(255,255,255,0.02);border:1px solid #232936;
                border-radius:6px;padding:32px 36px;
                font-family:'Fraunces',serif;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:10px;
                  color:#8a929e;letter-spacing:0.16em;text-transform:uppercase;
                  margin-bottom:16px;">
        REPORT R-2026-Q1-IED · v0.7 · DRAFT
      </div>
      <h2 style="font-weight:500;font-size:24px;letter-spacing:-0.02em;
                 margin-bottom:6px;">
        Industrial Emissions Report
      </h2>
      <div style="font-style:italic;color:#a8aeba;font-size:14px;
                  margin-bottom:24px;">
        Waste-to-energy facility · Operator permit ref. ·
        Competent authority: national env. body
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Reporting period",   f"{period_start} → {period_end}")
c2.metric("Net electricity exported", "61,920 MWh", "Q1 2026")
c3.metric("Plant capacity",     "≈ 600 kt/year",   "2 lines")
c4.metric("Incidents",          str(len(violations)),
          "from mapping engine")

st.markdown("##### § 1 · Emissions summary")
st.dataframe(report_df, use_container_width=True, hide_index=True)

if violations:
    st.markdown("##### § 2 · Reported incidents")
    inc_rows = []
    for ind in violations:
        inc_rows.append({
            "Case": ind.case_id,
            "Indicator": ind.indicator_id,
            "When": (ind.timestamp.strftime("%Y-%m-%d %H:%M")
                     if ind.timestamp else "—"),
            "Value": f"{ind.signal_value:.1f} {ind.unit}",
            "Limit": f"{ind.limit_value} {ind.unit}",
            "Article": ind.article,
            "Validated": (
                "✓" if (st.session_state.human_decisions.get(ind.case_id)
                        == "confirmed") else "pending"
            ),
        })
    st.dataframe(pd.DataFrame(inc_rows),
                 use_container_width=True, hide_index=True)

# ===== export =====
st.markdown("###")
st.markdown("##### Export")

# build JSON export
export_payload = {
    "report_id": "R-2026-Q1-IED",
    "version": "0.7-draft",
    "period": {"start": period_start, "end": period_end},
    "regime": "IED 2010/75/EU",
    "emissions_summary": rows,
    "incidents": [
        {
            "case_id": i.case_id,
            "indicator": i.indicator_id,
            "article": i.article,
            "timestamp": (i.timestamp.isoformat()
                          if i.timestamp else None),
            "value": i.signal_value,
            "limit": i.limit_value,
            "unit": i.unit,
            "violation": i.violation,
            "risk_level": i.risk_level,
            "confidence": round(i.confidence, 3),
            "human_validated": (
                st.session_state.human_decisions.get(i.case_id) == "confirmed"
            ),
            "data_hash": i.data_hash,
            "evidence_chain": i.evidence_chain,
        }
        for i in violations
    ],
}
export_json = json.dumps(export_payload, indent=2, default=str)

# CSV summary
csv_buf = io.StringIO()
report_df.to_csv(csv_buf, index=False)

c1, c2, c3 = st.columns(3)
with c1:
    st.download_button("Download · JSON (structured)", export_json,
                       file_name="R-2026-Q1-IED.json",
                       mime="application/json",
                       use_container_width=True)
with c2:
    st.download_button("Download · CSV summary", csv_buf.getvalue(),
                       file_name="R-2026-Q1-IED_summary.csv",
                       mime="text/csv",
                       use_container_width=True)
with c3:
    if st.button("Sign &amp; submit (simulated)", type="primary",
                 use_container_width=True):
        st.session_state.audit.log(
            "USER", "submit",
            "R-2026-Q1-IED submitted to competent authority (simulated)")
        st.success("Submission logged in audit trail.")
