"""
04 · Risk & Anomaly Detection
Layer 4 — runs Isolation Forest + rule-based threshold detection on the
emissions dataset (synthetic or user-uploaded). Both detectors actually
execute here using scikit-learn.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import (
    init_session, inject_css, kicker, lead, sidebar_brand,
    plotly_layout, PALETTE,
)

st.set_page_config(page_title="AI-COMPASS · Risk Detection",
                   page_icon="⚠️", layout="wide")
inject_css()
init_session(st)
sidebar_brand()

kicker("04 · Layer 4 · AI Risk & Anomaly Detection")
st.markdown(
    "<h1>Detecting what manual review would <em>miss</em>.</h1>",
    unsafe_allow_html=True,
)
lead(
    "A hybrid of unsupervised anomaly detection (Isolation Forest), "
    "rule-based threshold checks and — in production — time-series forecasting "
    "residuals (LSTM) and gradient boosting. Click the run button to actually "
    "execute the models on the current dataset."
)

# ===== run controls =====
c1, c2, c3 = st.columns([1, 1, 2])
with c1:
    contamination = st.slider("Anomaly contamination", 0.01, 0.20, 0.05, 0.01,
                              help="Expected fraction of outliers in the data. "
                                   "Lower = stricter, fewer alerts.")
with c2:
    st.markdown("###")
    if st.button("▶ Run detection", type="primary", use_container_width=True):
        engine = st.session_state.risk_engine
        # reset case counter for a clean run
        engine._case_counter = 0
        df = st.session_state.emissions_df
        rule_signals = engine.detect_thresholds(df)
        iforest_signals = engine.detect_anomalies_iforest(
            df, contamination=contamination)
        # avoid double-counting
        flagged = {s.raw_index for s in rule_signals}
        iforest_signals = [s for s in iforest_signals
                           if s.raw_index not in flagged]
        st.session_state.signals = rule_signals + iforest_signals
        # immediately re-map (so other pages have indicators)
        st.session_state.indicators = (
            st.session_state.mapping_engine.map_all(st.session_state.signals))
        st.session_state.audit.log(
            "AI", "detect",
            f"Risk detection run · rules={len(rule_signals)} · "
            f"iforest={len(iforest_signals)} · "
            f"contamination={contamination}")
        st.session_state.audit.log(
            "AI", "map",
            f"Mapping engine produced {len(st.session_state.indicators)} "
            f"compliance indicator(s)")
        st.rerun()
with c3:
    st.markdown("###")
    n = len(st.session_state.signals)
    if n > 0:
        st.markdown(
            f'<div style="padding:8px 0;">'
            f'<span class="pill pill-gold">● {n} signals detected</span> '
            f'<span class="pill pill-blue">'
            f'{len(st.session_state.indicators)} indicators mapped</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="padding:8px 0;color:#8a929e;font-size:13px;">'
            'Press <strong style="color:#c9a96e;">Run detection</strong> '
            'to execute the models on the current dataset.</div>',
            unsafe_allow_html=True,
        )

# ===== chart with anomaly markers =====
st.markdown("###")
st.markdown("##### NOx · Line B · observations and anomalies")

df = st.session_state.emissions_df
df_b = df[df["line"] == "B"].copy() if "line" in df.columns else df.copy()
df_b = df_b.sort_values("timestamp").reset_index(drop=True)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df_b["timestamp"], y=df_b["no2_mg_nm3"],
    name="Observed",
    line=dict(color=PALETTE["gold"], width=2),
    mode="lines+markers",
    marker=dict(size=4),
))
fig.add_hline(
    y=200, line_dash="dash", line_color=PALETTE["red"],
    annotation_text="IED limit · 200 mg/Nm³",
    annotation_position="top right",
    annotation_font_color=PALETTE["red"],
)

# overlay anomaly markers
anom_x, anom_y, anom_text = [], [], []
for sig in st.session_state.signals:
    if sig.field == "no2_mg_nm3" and "B" in sig.source:
        anom_x.append(sig.timestamp)
        anom_y.append(sig.value)
        anom_text.append(f"{sig.case_id} · {sig.detector} · "
                         f"conf {sig.confidence:.2f}")
if anom_x:
    fig.add_trace(go.Scatter(
        x=anom_x, y=anom_y,
        name="Detected anomaly",
        mode="markers",
        marker=dict(size=12, color=PALETTE["red"],
                    symbol="circle-open", line=dict(width=3)),
        text=anom_text,
        hovertemplate="%{text}<extra></extra>",
    ))

fig.update_layout(**plotly_layout(height=340))
st.plotly_chart(fig, use_container_width=True)

# ===== signals table =====
st.markdown("###")
st.markdown("##### Detected risk signals")

if not st.session_state.signals:
    st.info(
        "No signals yet. Click **Run detection** above to execute the models.",
        icon="ℹ️",
    )
else:
    rows = []
    for s in st.session_state.signals:
        rows.append({
            "Case": s.case_id,
            "When": s.timestamp.strftime("%Y-%m-%d %H:%M"),
            "Source": s.source,
            "Field": s.field,
            "Value": f"{s.value:.1f}",
            "Severity": s.severity,
            "Detector": s.detector,
            "Confidence": f"{s.confidence:.2f}",
            "Description": s.description,
        })
    sig_df = pd.DataFrame(rows)
    st.dataframe(
        sig_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Severity": st.column_config.TextColumn(width="small"),
            "Confidence": st.column_config.TextColumn(width="small"),
        },
    )

    # severity breakdown
    hi = sum(1 for s in st.session_state.signals if s.severity == "HIGH")
    md = sum(1 for s in st.session_state.signals if s.severity == "MEDIUM")
    lo = sum(1 for s in st.session_state.signals if s.severity == "LOW")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("HIGH",     hi, "rule-engine · threshold")
    c2.metric("MEDIUM",   md, "isolation-forest")
    c3.metric("LOW",      lo, "")
    c4.metric("Total",    hi + md + lo, "")

# ===== model registry =====
st.markdown("###")
st.markdown("##### Model registry · WP3 deliverable")

model_data = [
    ["rules-ied-v4", "Deterministic rules", "Threshold + completeness",
     "1.00 · 1.00", "● deployed"],
    ["iforest-emissions-v3", "Isolation Forest", "Multivariate emissions",
     "0.89 · 0.84", "● deployed"],
    ["lstm-energy-v2", "LSTM time-series", "Energy forecast residuals",
     "0.82 · 0.79", "● deployed"],
    ["ae-cyber-v1", "Autoencoder", "NIS2 · access patterns",
     "0.74 · 0.81", "● shadow"],
    ["xgb-completeness-v1", "XGBoost", "Predict late submissions",
     "0.86 · 0.80", "● deployed"],
]
st.dataframe(
    pd.DataFrame(model_data,
                 columns=["Model", "Type", "Scope",
                          "Precision · Recall", "Status"]),
    use_container_width=True, hide_index=True,
)
