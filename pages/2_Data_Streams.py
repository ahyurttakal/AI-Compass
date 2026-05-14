"""
02 · Data Streams
Layer 1 + 2 — ingestion and semantic harmonisation.
Allows the user to upload their own CSV or work with synthetic data.
"""
import io
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import (
    init_session, inject_css, kicker, lead, sidebar_brand,
    plotly_layout, PALETTE, DataSimulator,
)

st.set_page_config(page_title="AI-COMPASS · Data Streams",
                   page_icon="📡", layout="wide")
inject_css()
init_session(st)
sidebar_brand()

# --------------------------------------------------------------------- page
kicker("02 · Layer 1 + 2 · Data Ingestion & Harmonisation")
st.markdown(
    "<h1>A <em>single</em>, harmonised view of plant operations.</h1>",
    unsafe_allow_html=True,
)
lead(
    "Bring your own CSV or work with the built-in synthetic dataset. "
    "Multiple heterogeneous sources are pulled, cleaned, unit-converted "
    "and aligned to a common compliance ontology before anything else "
    "happens downstream."
)

# ===== data source controls =====
left, right = st.columns([1.4, 1])

with left:
    st.markdown("##### Data source")
    src_choice = st.radio(
        "Choose data source",
        ["Synthetic (built-in)", "Upload my own CSV"],
        index=0,
        horizontal=True,
        label_visibility="collapsed",
    )

    if src_choice == "Synthetic (built-in)":
        c1, c2, c3 = st.columns([1, 1, 1.4])
        with c1:
            days = st.number_input("Days", min_value=7, max_value=180,
                                   value=30, step=1)
        with c2:
            seed = st.number_input("Random seed", min_value=0, max_value=9999,
                                   value=42, step=1)
        with c3:
            inject = st.toggle("Inject anomaly on Line B", value=True,
                               help="Forces a NOx exceedance around day 14 "
                                    "so the downstream pipeline produces a "
                                    "visible violation.")
        if st.button("Regenerate synthetic data", type="primary"):
            sim = DataSimulator(seed=int(seed))
            st.session_state.emissions_df = sim.emissions(days=int(days),
                                                          inject_anomaly=inject)
            st.session_state.energy_df = sim.energy(days=int(days))
            st.session_state.waste_df = sim.waste(days=int(days))
            st.session_state.data_source = "synthetic"
            # invalidate any prior risk/mapping results
            st.session_state.signals = []
            st.session_state.indicators = []
            st.session_state.audit.log(
                "USER", "regenerate",
                f"Synthetic data regenerated · {days}d · seed={seed} · "
                f"anomaly={'on' if inject else 'off'}")
            st.success("Synthetic data regenerated. Risk/mapping reset.")
            st.rerun()
    else:
        uploaded = st.file_uploader(
            "Upload an emissions CSV",
            type=["csv"],
            help="Required columns: timestamp, line, no2_mg_nm3, sox_mg_nm3, "
                 "pm_mg_nm3, co_mg_nm3, o2_ref_pct. Optional: method.",
        )
        if uploaded is not None:
            try:
                df = pd.read_csv(uploaded)
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                required = {"timestamp", "no2_mg_nm3"}
                missing = required - set(df.columns)
                if missing:
                    st.error(f"Missing required columns: {missing}")
                else:
                    if "line" not in df.columns:
                        df["line"] = "A"
                    for col in ("sox_mg_nm3", "pm_mg_nm3",
                                "co_mg_nm3", "o2_ref_pct"):
                        if col not in df.columns:
                            df[col] = np.nan
                    if "method" not in df.columns:
                        df["method"] = "user-provided"
                    st.session_state.emissions_df = df.reset_index(drop=True)
                    st.session_state.data_source = "user-uploaded"
                    st.session_state.signals = []
                    st.session_state.indicators = []
                    st.session_state.audit.log(
                        "USER", "upload",
                        f"User CSV uploaded · {len(df)} rows · "
                        f"{df['timestamp'].min()} → {df['timestamp'].max()}")
                    st.success(f"Loaded {len(df)} rows. "
                               f"Go to 04 · Risk Detection to re-run.")
            except Exception as e:
                st.error(f"Could not parse CSV: {e}")

with right:
    st.markdown("##### Sample CSV")
    df = st.session_state.emissions_df.head(60)
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        "Download a template CSV",
        data=csv_buf.getvalue(),
        file_name="emissions_template.csv",
        mime="text/csv",
        help="60 rows from the current dataset — use as a column template "
             "for your own data.",
    )
    label = ("synthetic" if st.session_state.data_source == "synthetic"
             else "user-uploaded")
    st.markdown(
        f'<div style="margin-top:14px;">'
        f'<span class="pill pill-gold">● {label}</span>'
        f'<span class="pill pill-blue">{len(st.session_state.emissions_df)} rows</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

# ===== headline metrics =====
st.markdown("###")
df_em = st.session_state.emissions_df
df_en = st.session_state.energy_df

m1, m2, m3, m4 = st.columns(4)
m1.metric("Active sources",
          "7" if st.session_state.data_source == "synthetic" else "1",
          "all healthy")
m2.metric("Records · emissions", f"{len(df_em):,}", "within nominal range")
m3.metric("Data quality score", "92 %", "▲ 4 pts last week")
m4.metric("Harmonised fields", "146", "mapped to ontology")

# ===== charts =====
st.markdown("###")
c1, c2 = st.columns(2)

with c1:
    st.markdown("##### Electrical energy delivered to grid")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_en["timestamp"], y=df_en["energy_delivered_mwh"],
        name="MWh/day",
        line=dict(color=PALETTE["gold"], width=2.2),
        fill="tozeroy", fillcolor="rgba(201,169,110,0.08)",
    ))
    fig.update_layout(**plotly_layout(height=300))
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.markdown("##### Stack emissions · NOx vs IED limit")
    df_b = df_em[df_em["line"] == "B"].copy() if "line" in df_em.columns else df_em
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_b["timestamp"], y=df_b["no2_mg_nm3"],
        name="NOx (Line B)",
        line=dict(color=PALETTE["amber"], width=2.2),
        mode="lines+markers",
        marker=dict(size=4),
    ))
    fig.add_hline(y=200, line_dash="dash", line_color=PALETTE["red"],
                  annotation_text="IED limit · 200 mg/Nm³",
                  annotation_position="top right",
                  annotation_font_color=PALETTE["red"])
    fig.update_layout(**plotly_layout(height=300))
    st.plotly_chart(fig, use_container_width=True)

# ===== source table =====
st.markdown("###")
st.markdown("##### Connected data sources · ontology mapping")

src_data = [
    ("CEMS · Line A", "Continuous Emissions Monitor",
     "emission.no2 → IED.field_4.b", "96%", "● live", "pill-green"),
    ("CEMS · Line B", "Continuous Emissions Monitor",
     "emission.no2 → IED.field_4.b", "88%", "● drift", "pill-amber"),
    ("SCADA · plant", "Process control",
     "temp/flow/pressure → ops.*", "99%", "● live", "pill-green"),
    ("Energy meter", "Net export & consumption",
     "power_kWh → energy.delivered", "97%", "● live", "pill-green"),
    ("Waste tracking", "Tonnage & EWC classification",
     "waste.code → EWC list", "84%", "● live", "pill-green"),
    ("ERP · maintenance", "Manual + scheduled",
     "incident → ops.event", "72%", "● gaps", "pill-amber"),
    ("SIEM logs", "Security events (NIS2)",
     "cyber.event → nis2.*", "95%", "● live", "pill-green"),
]
src_df = pd.DataFrame(src_data, columns=[
    "Source", "Type", "Ontology mapping (canonical)",
    "Quality", "Status", "_pill"])
st.dataframe(
    src_df.drop(columns=["_pill"]),
    use_container_width=True,
    hide_index=True,
)

# ===== harmonisation example =====
st.markdown("###")
st.markdown("##### Semantic harmonisation · live example")
lead(
    "Different EGF subsystems use different field names for the same "
    "regulatory concept. The harmonisation layer resolves them to a "
    "single canonical field using ontology + embedding similarity."
)
st.code(
    "# source fields detected across systems\n"
    "scada.kpi.elec_out_mw         → canonical: energy.delivered_to_grid.kWh   "
    "# confidence 0.94\n"
    "erp.report.power_kWh          → canonical: energy.delivered_to_grid.kWh   "
    "# confidence 0.91\n"
    "meter.A1.total_energy_use     → canonical: energy.delivered_to_grid.kWh   "
    "# confidence 0.88 · unit converted MWh→kWh\n"
    "\n"
    "# mapped to obligation field\n"
    "energy.delivered_to_grid.kWh  → obligation: 'EED Art. 8 · annual energy "
    "reporting'\n"
    "                              → reporting field: 'net_electricity_delivered'",
    language="python",
)

# ===== raw data preview =====
with st.expander("Raw emissions data · preview"):
    st.dataframe(df_em.head(200), use_container_width=True, hide_index=True)
