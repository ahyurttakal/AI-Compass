"""
08 · Privacy & Security
Cross-cutting layer — data classification, PET applied per class, GDPR
posture, NIS2 incident log. In production this is wired to the privacy and
cybersecurity partners' deliverables (PETs + secure-by-design audits).
"""
import pandas as pd
import streamlit as st

from lib import (
    init_session, inject_css, kicker, lead, sidebar_brand,
)

st.set_page_config(page_title="AI-COMPASS · Privacy & Security",
                   page_icon="🔒", layout="wide")
inject_css()
init_session(st)
sidebar_brand()

kicker("08 · Cross-cutting · Privacy & Security")
st.markdown(
    "<h1>Privacy-preserving by design, <em>secure</em> by construction.</h1>",
    unsafe_allow_html=True,
)
lead(
    "Privacy-enhancing technologies (PETs) are applied at the data layer; "
    "the system's cybersecurity posture is independently validated. "
    "Sensitive operator, personnel and commercial data never leave their "
    "classification boundary."
)

# ===== data classification table =====
st.markdown("##### Data classification & PET applied")

class_data = [
    ("Stack emissions (CEMS)",       "~14 GB/yr",
     "none required · operational data",   "negligible", "open",        "pill-green"),
    ("Operator / personnel logs",    "~2.1 GB/yr",
     "k-anonymity + pseudonymisation",     "low",        "protected",   "pill-violet"),
    ("Maintenance & access logs",    "~0.6 GB/yr",
     "pseudonymisation + RBAC",            "residual",   "protected",   "pill-violet"),
    ("Training datasets (multi-site)", "~28 GB",
     "synthetic data (PET-grade)",          "near-zero",  "synthetic",   "pill-violet"),
    ("Commercial throughput data",   "~3.4 GB/yr",
     "aggregation + role-based access",     "residual",   "restricted",  "pill-violet"),
]
class_df = pd.DataFrame(class_data, columns=[
    "Data class", "Volume", "Technique applied",
    "Re-identification risk", "Status", "_pill"]).drop(columns=["_pill"])
st.dataframe(class_df, use_container_width=True, hide_index=True)

# ===== security + GDPR posture =====
st.markdown("###")
c1, c2 = st.columns(2)

with c1:
    st.markdown("##### Security validation")
    st.markdown(
        """
        <div class="chain-node">
          <div class="chain-node-detail" style="line-height:2;">
            Last pen-test:              <strong style="float:right;font-family:'JetBrains Mono',monospace;">2026-05-08</strong><br>
            Critical findings:          <strong style="float:right;color:#6b9b7a;font-family:'JetBrains Mono',monospace;">0</strong><br>
            High findings (resolved):   <strong style="float:right;font-family:'JetBrains Mono',monospace;">2 / 2</strong><br>
            Secure-by-design audit:     <strong style="float:right;color:#6b9b7a;">✓ passed</strong><br>
            NIS2 readiness:             <strong style="float:right;color:#6b9b7a;font-family:'JetBrains Mono',monospace;">93%</strong><br>
            SBOM up to date:            <strong style="float:right;color:#6b9b7a;">✓ verified</strong>
          </div>
          <div style="margin-top:14px;"><span class="pill pill-green">● green</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown("##### GDPR posture")
    st.markdown(
        """
        <div class="chain-node">
          <div class="chain-node-detail" style="line-height:2;">
            Lawful basis (operational):   <strong style="float:right;">Art. 6(1)(c)</strong><br>
            DPIA completed:               <strong style="float:right;color:#6b9b7a;">✓ WP4</strong><br>
            Data minimisation:            <strong style="float:right;color:#6b9b7a;">enforced</strong><br>
            PET applied to PII:           <strong style="float:right;color:#6b9b7a;font-family:'JetBrains Mono',monospace;">100%</strong><br>
            DPO sign-off:                 <strong style="float:right;">current</strong><br>
            Personal-data incidents:      <strong style="float:right;color:#6b9b7a;font-family:'JetBrains Mono',monospace;">0 in pilot</strong>
          </div>
          <div style="margin-top:14px;"><span class="pill pill-green">● compliant</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ===== NIS2 events =====
st.markdown("###")
st.markdown("##### NIS2 · security event log · last 7 days")

events = [
    ["12 May · 02:14", "Login attempt outside working hours",
     "reporting-console", "anomaly · low", "Awaiting review"],
    ["11 May · 09:08", "API rate-limit triggered",
     "api.gateway",       "expected",       "Auto-throttled"],
    ["10 May · 17:20", "Certificate rotation completed",
     "pki",               "ok",             "Scheduled"],
    ["09 May · 11:55", "Failed login (5×) · same user",
     "sso",               "anomaly",        "Lockout · resolved with user"],
    ["08 May · 14:00", "Penetration-test campaign closed",
     "security-team",     "closed",         "Report archived"],
]
st.dataframe(pd.DataFrame(events, columns=[
    "Time", "Event", "Source", "Classification", "Action"]),
    use_container_width=True, hide_index=True)

# ===== PET techniques explained =====
st.markdown("###")
st.markdown("##### Privacy-Enhancing Techniques · in use")

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(
        """
        <div class="chain-node">
          <div class="chain-node-label">technique</div>
          <div class="chain-node-title">k-Anonymity</div>
          <div class="chain-node-detail">
            Each record indistinguishable from at least <strong>k−1</strong>
            others on quasi-identifiers. Used on personnel and operator logs
            so individual shift workers can't be re-identified from
            ostensibly anonymised data.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        """
        <div class="chain-node">
          <div class="chain-node-label">technique</div>
          <div class="chain-node-title">Synthetic data</div>
          <div class="chain-node-detail">
            Statistical properties preserved; individual records are
            <strong>generated, not original</strong>. Used for cross-site
            model training so no real PII or commercial data ever leaves the
            operator's environment.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        """
        <div class="chain-node">
          <div class="chain-node-label">technique</div>
          <div class="chain-node-title">Pseudonymisation + RBAC</div>
          <div class="chain-node-detail">
            Identifiers replaced with reversible tokens held in a separate
            key vault. Combined with role-based access control, only
            authorised roles see the mapping. Suitable for access and
            maintenance logs.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
