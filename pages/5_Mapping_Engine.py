"""
05 · Risk-to-Regulation Mapping Engine — CORE
The central scientific contribution of AI-COMPASS. Takes a detected risk
signal and produces a machine-readable compliance indicator with explanation,
evidence chain and human review hooks.
"""
import json
import streamlit as st

from lib import (
    init_session, inject_css, kicker, lead, sidebar_brand,
)

st.set_page_config(page_title="AI-COMPASS · Mapping Engine",
                   page_icon="🔗", layout="wide")
inject_css()
init_session(st)
sidebar_brand()

kicker("05 · Layer 5 · Core scientific contribution")
st.markdown(
    "<h1>Risk-to-Regulation Mapping <em>Engine</em>.</h1>",
    unsafe_allow_html=True,
)
lead(
    "The bridge between detected operational risk and the regulatory world. "
    "For every signal, the engine identifies which obligation may be affected, "
    "which reporting field is at risk, generates a compliance indicator, and "
    "presents the full evidence chain — with confidence, explanation, and a "
    "human review checkpoint."
)

# ===== gate: run detection first =====
if not st.session_state.indicators:
    st.warning(
        "No compliance indicators yet. Go to **04 · Risk Detection** and click "
        "*Run detection* first. The mapping engine runs automatically after "
        "that step.",
        icon="⚠️",
    )
    st.stop()

# ===== indicator selector =====
inds = st.session_state.indicators
options = [f"{i.case_id} · {i.indicator_id} · "
           f"{'VIOLATION' if i.violation else 'within limits'}"
           for i in inds]
sel = st.selectbox("Inspect mapping case", options, index=0)
ind = inds[options.index(sel)]

# also pick out the matching signal so we can show source info
sig = next((s for s in st.session_state.signals if s.case_id == ind.case_id),
           None)

# ===== top action bar =====
c1, c2 = st.columns([3, 1.4])
with c1:
    pill_class = "pill-red" if ind.violation else "pill-amber"
    label = "VIOLATION" if ind.violation else "ANOMALY"
    st.markdown(
        f'<div style="margin:8px 0 6px;">'
        f'<span class="pill {pill_class}">● {label}</span>'
        f'<span class="pill pill-gold">{ind.indicator_id}</span>'
        f'<span class="pill pill-blue">conf {ind.confidence:.2f}</span>'
        f'<span class="pill pill-violet">{ind.regulation}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
with c2:
    decision = st.session_state.human_decisions.get(ind.case_id, "pending")
    b1, b2 = st.columns(2)
    if b1.button("✔ Confirm", use_container_width=True,
                 type="primary"):
        st.session_state.human_decisions[ind.case_id] = "confirmed"
        st.session_state.audit.log(
            "USER", "review",
            f"Mapping {ind.indicator_id} (case {ind.case_id}) confirmed by user",
            obj_id=ind.indicator_id, obj_hash=ind.data_hash)
        st.rerun()
    if b2.button("✕ Reject", use_container_width=True):
        st.session_state.human_decisions[ind.case_id] = "rejected"
        st.session_state.audit.log(
            "USER", "review",
            f"Mapping {ind.indicator_id} (case {ind.case_id}) rejected by user",
            obj_id=ind.indicator_id, obj_hash=ind.data_hash)
        st.rerun()

if decision == "confirmed":
    st.success(f"Case {ind.case_id} confirmed and added to the evidence chain.")
elif decision == "rejected":
    st.error(f"Case {ind.case_id} rejected. Marked for model retraining.")

# ===== the five-step chain =====
st.markdown("###")
st.markdown("##### Mapping chain · five steps")

c1, c2, c3, c4, c5 = st.columns(5, gap="small")

with c1:
    st.markdown(
        f"""
        <div class="chain-node">
          <div class="chain-node-label">01 · Data</div>
          <div style="font-family:'Fraunces',serif;font-style:italic;
                      font-size:22px;color:#c9a96e;margin:6px 0;">∰</div>
          <div class="chain-node-title">CEMS reading</div>
          <div class="chain-node-detail">
            Time: <strong>{ind.timestamp.strftime('%d %b %H:%M') if ind.timestamp else '—'}</strong><br>
            Source: <strong>{sig.source if sig else '—'}</strong><br>
            Field: <strong>{sig.field if sig else '—'}</strong><br>
            Value: <strong>{ind.signal_value:.1f} {ind.unit}</strong>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        f"""
        <div class="chain-node">
          <div class="chain-node-label">02 · Risk</div>
          <div style="font-family:'Fraunces',serif;font-style:italic;
                      font-size:22px;color:#c9a96e;margin:6px 0;">⚠</div>
          <div class="chain-node-title">Detected</div>
          <div class="chain-node-detail">
            Type: <strong>{'Limit violation' if ind.violation else 'Multivariate anomaly'}</strong><br>
            Severity: <strong>{ind.risk_level}</strong><br>
            Detector: <strong>{sig.detector if sig else '—'}</strong><br>
            Confidence: <strong>{ind.confidence:.2f}</strong>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        f"""
        <div class="chain-node">
          <div class="chain-node-label">03 · Obligation</div>
          <div style="font-family:'Fraunces',serif;font-style:italic;
                      font-size:22px;color:#c9a96e;margin:6px 0;">§</div>
          <div class="chain-node-title">Regulation</div>
          <div class="chain-node-detail">
            Source: <strong>{ind.regulation.split(' · ')[0]}</strong><br>
            Article: <strong>{ind.article}</strong><br>
            Limit: <strong>{ind.limit_value} {ind.unit}</strong><br>
            Window: <strong>daily mean</strong>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c4:
    over_pct = ((ind.signal_value - ind.limit_value) / ind.limit_value * 100
                if (ind.limit_value and ind.violation) else 0)
    st.markdown(
        f"""
        <div class="chain-node">
          <div class="chain-node-label">04 · Indicator</div>
          <div style="font-family:'Fraunces',serif;font-style:italic;
                      font-size:22px;color:#c9a96e;margin:6px 0;">⊕</div>
          <div class="chain-node-title">Generated</div>
          <div class="chain-node-detail">
            ID: <strong>{ind.indicator_id}</strong><br>
            Violation: <strong>{'YES (+%.0f%%)' % over_pct if ind.violation else 'NO'}</strong><br>
            Risk: <strong>{ind.risk_level}</strong><br>
            Deadline: <strong>{'+48h notice' if ind.violation else '—'}</strong>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c5:
    st.markdown(
        f"""
        <div class="chain-node">
          <div class="chain-node-label">05 · Evidence</div>
          <div style="font-family:'Fraunces',serif;font-style:italic;
                      font-size:22px;color:#c9a96e;margin:6px 0;">✎</div>
          <div class="chain-node-title">Audit packet</div>
          <div class="chain-node-detail">
            Hash: <strong style="font-family:'JetBrains Mono',monospace;
                       font-size:10px;">{ind.data_hash}…</strong><br>
            Validation: <strong>QAL2 cert.</strong><br>
            Cross-check: <strong>SCADA</strong><br>
            Steps: <strong>{len(ind.evidence_chain)}</strong>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ===== AI vs human comparison =====
st.markdown("###")
st.markdown("##### Mapping proposal · AI versus human review")

c1, c2 = st.columns(2)
with c1:
    st.markdown(
        f"""
        <div class="chain-node" style="border-color:rgba(201,169,110,0.3);">
          <div class="chain-node-label">AI · automatic</div>
          <div class="chain-node-title">Mapping proposal</div>
          <div class="chain-node-detail">
            <strong>Why this obligation:</strong><br>
            {ind.explanation}
          </div>
          <div style="margin-top:12px;">
            <span class="pill pill-gold">● conf {ind.confidence:.2f}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    if decision == "confirmed":
        body = (
            "<strong>Decision:</strong> Mapping <em>confirmed</em>. The "
            "exceedance is real; corrective action initiated. Q1 report will "
            "include this incident with a root-cause narrative."
        )
        pill = "pill-green"; pill_label = "● confirmed"
    elif decision == "rejected":
        body = (
            "<strong>Decision:</strong> Mapping <em>rejected</em>. The "
            "reviewer believes this is a sensor-side issue rather than a true "
            "regulatory exceedance. Case forwarded to model-retraining queue."
        )
        pill = "pill-red"; pill_label = "● rejected"
    else:
        body = (
            "<strong>Decision:</strong> <em>Pending review.</em> The "
            "compliance officer will confirm or reject the AI's mapping. "
            "Until then the indicator stays in <em>provisional</em> state and "
            "no automatic notification is sent."
        )
        pill = "pill-amber"; pill_label = "● awaiting review"

    st.markdown(
        f"""
        <div class="chain-node" style="border-color:rgba(107,155,122,0.3);">
          <div class="chain-node-label">Human · in the loop</div>
          <div class="chain-node-title">Validation</div>
          <div class="chain-node-detail">{body}</div>
          <div style="margin-top:12px;">
            <span class="pill {pill}">{pill_label}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ===== machine-readable output =====
st.markdown("###")
st.markdown("##### Machine-readable compliance indicator · output")
lead(
    "Every confirmed indicator is exported as a structured payload that can be "
    "ingested by downstream reporting systems, regulators' APIs or XBRL "
    "exporters."
)

payload = {
    "case_id": ind.case_id,
    "indicator_id": ind.indicator_id,
    "obligation": {
        "regulation": ind.regulation,
        "article": ind.article,
        "limit": ind.limit_value,
        "unit": ind.unit,
    },
    "signal": {
        "source": sig.source if sig else None,
        "field": sig.field if sig else None,
        "value": ind.signal_value,
        "timestamp": (ind.timestamp.isoformat()
                      if ind.timestamp else None),
        "data_hash": ind.data_hash,
    },
    "violation": ind.violation,
    "risk_level": ind.risk_level,
    "confidence": round(ind.confidence, 3),
    "human_validated": (decision == "confirmed"),
    "decision": decision,
    "evidence_chain": ind.evidence_chain,
}
st.code(json.dumps(payload, indent=2, default=str), language="json")
