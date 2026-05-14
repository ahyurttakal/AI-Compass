"""
03 · Regulation Intelligence
Layer 3 — extracting machine-readable obligations from EU regulatory texts
(LLM + RAG + Legal NLP). For the demo the knowledge base is curated, but
the UI mimics what an automated extraction interface looks like.
"""
import streamlit as st
import pandas as pd

from lib import (
    init_session, inject_css, kicker, lead, sidebar_brand, REGULATIONS,
)

st.set_page_config(page_title="AI-COMPASS · Regulation Intelligence",
                   page_icon="📜", layout="wide")
inject_css()
init_session(st)
sidebar_brand()

kicker("03 · Layer 3 · Regulation Intelligence")
st.markdown(
    "<h1>EU directives — <em>parsed</em> into machine-readable obligations.</h1>",
    unsafe_allow_html=True,
)
lead(
    "Legal NLP plus retrieval-augmented LLMs read EUR-Lex texts and extract "
    "structured obligations: required fields, frequency, thresholds, evidence. "
    "Every extraction is traceable to the source article and reviewed by a "
    "domain expert."
)

# ===== regulation cards (3 per row) =====
reg_codes = list(REGULATIONS.keys())

if "selected_reg" not in st.session_state:
    st.session_state.selected_reg = "IED"

for row_start in range(0, len(reg_codes), 3):
    cols = st.columns(3, gap="medium")
    for col, code in zip(cols, reg_codes[row_start:row_start + 3]):
        reg = REGULATIONS[code]
        is_sel = (st.session_state.selected_reg == code)
        border = "#c9a96e" if is_sel else "#232936"
        bg = "rgba(201,169,110,0.04)" if is_sel else "rgba(255,255,255,0.02)"
        with col:
            st.markdown(
                f"""
                <div style="border:1px solid {border};border-radius:6px;
                            padding:18px;background:{bg};min-height:200px;">
                  <div style="font-family:'JetBrains Mono',monospace;font-size:10px;
                              color:#c9a96e;letter-spacing:0.12em;">
                    {reg['id']}
                  </div>
                  <div style="font-family:'Fraunces',serif;font-weight:500;
                              font-size:16px;margin-top:6px;letter-spacing:-0.01em;
                              line-height:1.3;">
                    {reg['name']}
                  </div>
                  <div style="color:#a8aeba;font-size:12px;line-height:1.5;
                              margin-top:10px;">
                    {reg['summary']}
                  </div>
                  <div style="margin-top:14px;">
                    <span class="pill pill-gold">● {len(reg['obligations'])} obligations</span>
                    <span class="pill pill-blue">{reg['frequency']}</span>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(f"Inspect {code}", key=f"sel_{code}",
                         use_container_width=True):
                st.session_state.selected_reg = code
                st.session_state.audit.log(
                    "USER", "inspect",
                    f"User opened regulation {reg['id']} ({code})")
                st.rerun()

# ===== extraction view =====
st.markdown("###")
reg = REGULATIONS[st.session_state.selected_reg]

st.markdown("##### Auto-extracted obligation view")

hdr_left, hdr_right = st.columns([2.5, 1])
with hdr_left:
    st.markdown(
        f"""
        <div style="font-family:'JetBrains Mono',monospace;font-size:10px;
                    color:#8a929e;text-transform:uppercase;
                    letter-spacing:0.14em;margin-bottom:6px;">
          selected · auto-extracted from EUR-Lex
        </div>
        <div style="font-family:'Fraunces',serif;font-weight:500;font-size:22px;
                    letter-spacing:-0.01em;">
          {reg['id']} · {reg['name']}
        </div>
        <div style="color:#a8aeba;font-size:13px;margin-top:6px;">
          {reg['summary']}
        </div>
        """,
        unsafe_allow_html=True,
    )

with hdr_right:
    st.metric("Frequency", reg["frequency"])
    st.metric("Authority",  reg["authority"])

# Quote (only for IED, demonstrative)
if st.session_state.selected_reg == "IED":
    st.markdown(
        """
        <div class="quote">
          "The permit shall include <span class="hl">emission limit values</span>
          for polluting substances [...]. The permit shall also include
          <span class="hl">monitoring requirements</span>, specifying measurement
          methodology and <span class="hl">frequency</span>, evaluation procedure
          and an obligation to supply the competent authority with the data
          required for checking compliance with the permit."
          <div style="font-family:'JetBrains Mono',monospace;font-size:10px;
                      color:#8a929e;margin-top:10px;letter-spacing:0.12em;">
            ─ Directive 2010/75/EU · Article 14
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ----- obligations table -----
st.markdown("##### Structured obligations · extracted")

ob_rows = []
for ob in reg["obligations"]:
    ob_rows.append({
        "Obligation ID": ob["id"],
        "Article": ob["article"],
        "Field": ob["limit_field"] or "—",
        "Limit": (f"{ob['limit_value']} {ob['unit']}"
                  if ob["limit_value"] is not None else "—"),
        "Averaging": ob["averaging"],
        "Evidence": ob["evidence"],
    })
st.dataframe(pd.DataFrame(ob_rows),
             use_container_width=True, hide_index=True)

# ----- extraction confidence / human review -----
st.markdown("###")
c1, c2 = st.columns(2)
with c1:
    st.markdown(
        """
        <div class="chain-node">
          <div class="chain-node-label">AI extraction</div>
          <div class="chain-node-title">Obligation parser</div>
          <div class="chain-node-detail">
            Pipeline: <strong>EUR-Lex source → text normalisation →
            named entity recognition → obligation pattern matching → 
            structured JSON</strong>.<br><br>
            Models combined: <strong>BERT-Legal-NER</strong> for entities,
            <strong>LLM with RAG</strong> for relation extraction over
            article context.
          </div>
          <div style="margin-top:12px;">
            <span class="pill pill-gold">● confidence 0.92</span>
            <span class="pill pill-blue">{} obligations</span>
          </div>
        </div>
        """.format(len(reg["obligations"])),
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        """
        <div class="chain-node">
          <div class="chain-node-label">Human-in-the-loop</div>
          <div class="chain-node-title">Domain expert validation</div>
          <div class="chain-node-detail">
            Every extracted obligation is reviewed by a domain expert before
            being added to the knowledge base. The reviewer can:<br>
            • Confirm or correct the threshold<br>
            • Refine averaging window or O₂ reference basis<br>
            • Add jurisdiction-specific notes<br>
            • Reject if the AI misclassified
          </div>
          <div style="margin-top:12px;">
            <span class="pill pill-green">● confirmed</span>
            <span class="pill pill-violet">expert reviewer</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
