"""
AI-COMPASS — Core library
=========================

Synthetic data generation, regulation knowledge base, risk detection,
risk-to-regulation mapping engine, audit trail and styling helpers.

All pages of the Streamlit demo import from this module.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Optional, Any

import numpy as np
import pandas as pd


# =====================================================================
# 1. Synthetic data generator
# =====================================================================

class DataSimulator:
    """Generates realistic-looking operational data for a waste-to-energy plant.

    All series are deterministic given a seed so demos are reproducible.
    The simulator can inject a controlled anomaly (NOx exceedance on line B)
    to make the downstream risk / mapping pipeline produce a visible result.
    """

    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)

    # ---- emissions (CEMS) ------------------------------------------------
    def emissions(self, days: int = 30, freq_hours: int = 24,
                  inject_anomaly: bool = True) -> pd.DataFrame:
        end = datetime.now().replace(minute=0, second=0, microsecond=0)
        start = end - timedelta(days=days)
        idx = pd.date_range(start, end, freq=f"{freq_hours}h")
        n = len(idx)

        rows = []
        for line in ("A", "B"):
            base_nox = 135 if line == "A" else 145
            nox = base_nox + 18 * np.sin(np.arange(n) / 3) + self.rng.normal(0, 12, n)
            sox = 13 + 4 * np.sin(np.arange(n) / 2) + self.rng.normal(0, 3, n)
            pm = 3.0 + 0.8 * np.sin(np.arange(n) / 5) + self.rng.normal(0, 0.6, n)
            co = 28 + 4 * np.sin(np.arange(n) / 4) + self.rng.normal(0, 5, n)
            o2 = 11 + self.rng.normal(0, 0.4, n)

            # inject a controlled exceedance on line B around day 14
            if line == "B" and inject_anomaly and n > 16:
                nox[14] = 218.0
                nox[15] = 195.0

            for i, ts in enumerate(idx):
                rows.append({
                    "timestamp": ts,
                    "line": line,
                    "no2_mg_nm3": round(max(0.0, float(nox[i])), 1),
                    "sox_mg_nm3": round(max(0.0, float(sox[i])), 1),
                    "pm_mg_nm3": round(max(0.0, float(pm[i])), 2),
                    "co_mg_nm3": round(max(0.0, float(co[i])), 1),
                    "o2_ref_pct": round(float(o2[i]), 1),
                    "method": "EN 14792",
                })
        return (pd.DataFrame(rows)
                  .sort_values("timestamp")
                  .reset_index(drop=True))

    # ---- energy ----------------------------------------------------------
    def energy(self, days: int = 30) -> pd.DataFrame:
        end = datetime.now().replace(minute=0, second=0, microsecond=0)
        start = end - timedelta(days=days)
        idx = pd.date_range(start, end, freq="D")
        n = len(idx)
        base = 700 + 60 * np.sin(np.arange(n) / 4) + self.rng.normal(0, 35, n)
        weekday_factor = np.array([1.0 if d.weekday() < 5 else 0.86 for d in idx])
        delivered = base * weekday_factor
        return pd.DataFrame({
            "timestamp": idx,
            "energy_delivered_mwh": np.round(delivered, 1),
            "energy_consumed_mwh": np.round(delivered * 0.08, 1),
        })

    # ---- waste -----------------------------------------------------------
    def waste(self, days: int = 30) -> pd.DataFrame:
        end = datetime.now().replace(minute=0, second=0, microsecond=0)
        start = end - timedelta(days=days)
        idx = pd.date_range(start, end, freq="D")
        codes = [
            ("20 03 01", "Mixed municipal waste"),
            ("19 12 12", "Residues from mechanical treatment"),
            ("20 02 01", "Biodegradable waste"),
        ]
        rows = []
        for ts in idx:
            for code, desc in codes:
                share = (self.rng.uniform(0.35, 0.55) if code == "20 03 01"
                         else self.rng.uniform(0.10, 0.30))
                rows.append({
                    "timestamp": ts,
                    "ewc_code": code,
                    "description": desc,
                    "tonnes": round(1840 * share, 1),
                })
        return pd.DataFrame(rows)


# =====================================================================
# 2. Regulation knowledge base
# =====================================================================
# In a production system this is the output of the Regulation Intelligence
# layer (LLM + RAG over EUR-Lex). For the demo it is curated by hand so the
# Mapping Engine has a clean target to match against.

REGULATIONS: dict[str, dict[str, Any]] = {
    "IED": {
        "id": "2010/75/EU",
        "name": "Industrial Emissions Directive",
        "summary": (
            "Integrated pollution prevention and control. Sets emission limit "
            "values and monitoring obligations for industrial installations "
            "including waste incineration."
        ),
        "frequency": "Monthly + quarterly",
        "authority": "National environmental authority",
        "obligations": [
            {"id": "NOx", "article": "Annex VI · NOx limit",
             "limit_field": "no2_mg_nm3", "limit_value": 200.0,
             "averaging": "daily_mean", "unit": "mg/Nm³ @ 11% O₂",
             "evidence": "CEMS · QAL2 certified"},
            {"id": "SOx", "article": "Annex VI · SOx limit",
             "limit_field": "sox_mg_nm3", "limit_value": 50.0,
             "averaging": "daily_mean", "unit": "mg/Nm³",
             "evidence": "CEMS"},
            {"id": "PM",  "article": "Annex VI · Particulate matter",
             "limit_field": "pm_mg_nm3", "limit_value": 10.0,
             "averaging": "daily_mean", "unit": "mg/Nm³",
             "evidence": "CEMS"},
            {"id": "CO",  "article": "Annex VI · CO limit",
             "limit_field": "co_mg_nm3", "limit_value": 50.0,
             "averaging": "daily_mean", "unit": "mg/Nm³",
             "evidence": "CEMS"},
        ],
    },
    "ETS": {
        "id": "2003/87/EC",
        "name": "EU Emissions Trading System",
        "summary": "MRV — monitoring, reporting and verification — of greenhouse gas emissions.",
        "frequency": "Annual",
        "authority": "National ETS authority + accredited verifier",
        "obligations": [
            {"id": "MRV", "article": "Art. 14 · annual emission report",
             "limit_field": None, "limit_value": None,
             "averaging": "annual_total", "unit": "tCO₂e/year",
             "evidence": "Verified by accredited body"},
        ],
    },
    "WFD": {
        "id": "2008/98/EC",
        "name": "Waste Framework Directive",
        "summary": "Waste hierarchy, EWC classification, recovery and disposal reporting.",
        "frequency": "Quarterly + annual",
        "authority": "National waste authority",
        "obligations": [
            {"id": "EWC", "article": "Art. 35 · record-keeping by waste operators",
             "limit_field": None, "limit_value": None,
             "averaging": "per_event", "unit": "tonnes / EWC code",
             "evidence": "Weighbridge + EWC classification"},
        ],
    },
    "EED": {
        "id": "2023/1791",
        "name": "Energy Efficiency Directive (recast)",
        "summary": "Annual energy use and efficiency reporting.",
        "frequency": "Annual",
        "authority": "National energy authority",
        "obligations": [
            {"id": "Art8", "article": "Art. 8 · energy audits / annual reporting",
             "limit_field": None, "limit_value": None,
             "averaging": "annual_total", "unit": "MWh",
             "evidence": "Validated metering"},
        ],
    },
    "NIS2": {
        "id": "2022/2555",
        "name": "NIS2 Directive",
        "summary": "Cybersecurity risk management and incident reporting.",
        "frequency": "Continuous + 24h / 72h",
        "authority": "National CSIRT",
        "obligations": [
            {"id": "INC", "article": "Art. 23 · incident notification",
             "limit_field": None, "limit_value": None,
             "averaging": "per_event", "unit": "events",
             "evidence": "SIEM · forensic chain"},
        ],
    },
    "GDPR": {
        "id": "2016/679",
        "name": "General Data Protection Regulation",
        "summary": "Personal data processing, security of processing, breach notification.",
        "frequency": "Continuous",
        "authority": "Data Protection Authority",
        "obligations": [
            {"id": "Art32", "article": "Art. 32 · security of processing",
             "limit_field": None, "limit_value": None,
             "averaging": "continuous", "unit": "controls",
             "evidence": "DPIA + TOMs"},
        ],
    },
}


# =====================================================================
# 3. Risk detection engine
# =====================================================================

@dataclass
class RiskSignal:
    case_id: str
    timestamp: datetime
    source: str
    field: str
    value: float
    detector: str
    severity: str           # LOW / MEDIUM / HIGH
    confidence: float
    description: str
    raw_index: Optional[int] = None


class RiskEngine:
    """Combines rule-based threshold checks with unsupervised anomaly detection.

    Two detectors are wired in:
      * rule-engine — deterministic IED threshold violations (always 100% confident)
      * isolation-forest — unsupervised multivariate anomalies (probabilistic)
    """

    def __init__(self):
        self._case_counter = 0

    def _next_case_id(self) -> str:
        self._case_counter += 1
        return f"A-{datetime.now().year}-{self._case_counter:03d}"

    # ---- deterministic threshold checks ---------------------------------
    def detect_thresholds(self, df: pd.DataFrame) -> list[RiskSignal]:
        signals: list[RiskSignal] = []
        for ob in REGULATIONS["IED"]["obligations"]:
            field_name = ob["limit_field"]
            limit = ob["limit_value"]
            if field_name is None or field_name not in df.columns:
                continue
            violations = df[df[field_name] > limit]
            for idx, row in violations.iterrows():
                signals.append(RiskSignal(
                    case_id=self._next_case_id(),
                    timestamp=row.get("timestamp", datetime.now()),
                    source=f"CEMS · Line {row.get('line', '?')}",
                    field=field_name,
                    value=float(row[field_name]),
                    detector="rule-engine · IED",
                    severity="HIGH",
                    confidence=1.0,
                    description=(f"{field_name} = {row[field_name]:.1f} {ob['unit']} "
                                 f"exceeds limit {limit}"),
                    raw_index=int(idx),
                ))
        return signals

    # ---- isolation forest -----------------------------------------------
    def detect_anomalies_iforest(self, df: pd.DataFrame,
                                 contamination: float = 0.05) -> list[RiskSignal]:
        try:
            from sklearn.ensemble import IsolationForest
        except ImportError:
            return []

        numeric_cols = [c for c in
                        ("no2_mg_nm3", "sox_mg_nm3", "pm_mg_nm3", "co_mg_nm3")
                        if c in df.columns]
        if not numeric_cols or len(df) < 20:
            return []

        X = df[numeric_cols].fillna(df[numeric_cols].mean()).values
        iso = IsolationForest(contamination=contamination, random_state=42)
        iso.fit(X)
        labels = iso.predict(X)
        scores = -iso.score_samples(X)

        signals: list[RiskSignal] = []
        for i, (lab, sc) in enumerate(zip(labels, scores)):
            if lab != -1:
                continue
            row = df.iloc[i]
            # identify which field deviates most → "responsible" field
            deviations = {c: abs(row[c] - df[c].mean()) / (df[c].std() + 1e-6)
                          for c in numeric_cols}
            top_field = max(deviations, key=deviations.get)
            conf = float(min(0.99, 0.5 + sc / 2))
            signals.append(RiskSignal(
                case_id=self._next_case_id(),
                timestamp=row.get("timestamp", datetime.now()),
                source=f"CEMS · Line {row.get('line', '?')}",
                field=top_field,
                value=float(row[top_field]),
                detector="isolation-forest",
                severity="MEDIUM",
                confidence=conf,
                description=(f"Multivariate anomaly · {top_field} = "
                             f"{row[top_field]:.1f}"),
                raw_index=i,
            ))
        return signals

    # ---- combined --------------------------------------------------------
    def detect_all(self, df: pd.DataFrame) -> list[RiskSignal]:
        rule_signals = self.detect_thresholds(df)
        flagged = {s.raw_index for s in rule_signals}
        iforest_signals = [s for s in self.detect_anomalies_iforest(df)
                           if s.raw_index not in flagged]
        return rule_signals + iforest_signals


# =====================================================================
# 4. Risk-to-Regulation mapping engine
# =====================================================================

@dataclass
class ComplianceIndicator:
    indicator_id: str
    case_id: str
    regulation: str
    article: str
    violation: bool
    risk_level: str
    confidence: float
    explanation: str
    evidence_chain: list[str] = field(default_factory=list)
    data_hash: str = ""
    signal_value: float = 0.0
    limit_value: Optional[float] = None
    unit: str = ""
    timestamp: Optional[datetime] = None


class MappingEngine:
    """Maps detected risk signals to regulatory obligations and produces
    machine-readable compliance indicators with explanations."""

    def map_signal(self, signal: RiskSignal) -> Optional[ComplianceIndicator]:
        for reg_code, reg in REGULATIONS.items():
            for ob in reg["obligations"]:
                if ob["limit_field"] != signal.field:
                    continue
                violation = (ob["limit_value"] is not None
                             and signal.value > ob["limit_value"])
                indicator_id = f"CI-{reg_code}-{ob['id']}"
                explanation = self._explain(signal, reg, ob, violation)
                data_hash = hashlib.sha256(
                    f"{signal.case_id}{signal.timestamp}{signal.value}".encode()
                ).hexdigest()[:12]
                return ComplianceIndicator(
                    indicator_id=indicator_id,
                    case_id=signal.case_id,
                    regulation=f"{reg['id']} · {reg['name']}",
                    article=ob["article"],
                    violation=violation,
                    risk_level=signal.severity,
                    confidence=signal.confidence,
                    explanation=explanation,
                    evidence_chain=[
                        "raw_signal", "qal2_validated", "ontology_mapped",
                        "risk_detected", "ai_mapping_proposed",
                        "awaiting_human_review",
                    ],
                    data_hash=data_hash,
                    signal_value=signal.value,
                    limit_value=ob["limit_value"],
                    unit=ob["unit"],
                    timestamp=signal.timestamp,
                )
        return None

    @staticmethod
    def _explain(signal: RiskSignal, reg: dict, ob: dict, violation: bool) -> str:
        if violation:
            return (
                f"Observed {signal.field} = {signal.value:.1f} {ob['unit']} at "
                f"{signal.timestamp}. This exceeds the regulatory limit of "
                f"{ob['limit_value']} set by {reg['name']} ({ob['article']}). "
                f"Reference O₂ basis confirmed; measurement method recognised. "
                f"Recommend incident notification to {reg['authority']}."
            )
        return (
            f"Observed {signal.field} = {signal.value:.1f} {ob['unit']} flagged "
            f"as unusual by {signal.detector}. Within {reg['name']} regulatory "
            f"limits but worth investigating to ensure data quality."
        )

    def map_all(self, signals: list[RiskSignal]) -> list[ComplianceIndicator]:
        out = []
        for s in signals:
            ind = self.map_signal(s)
            if ind:
                out.append(ind)
        return out


# =====================================================================
# 5. Audit trail
# =====================================================================

@dataclass
class AuditEvent:
    timestamp: datetime
    actor: str
    action: str
    detail: str
    obj_id: str = ""
    obj_hash: str = ""


class AuditTrail:
    def __init__(self):
        self.events: list[AuditEvent] = []

    def log(self, actor: str, action: str, detail: str,
            obj_id: str = "", obj_hash: str = ""):
        self.events.append(AuditEvent(
            timestamp=datetime.now(),
            actor=actor, action=action, detail=detail,
            obj_id=obj_id, obj_hash=obj_hash,
        ))

    def df(self) -> pd.DataFrame:
        if not self.events:
            return pd.DataFrame(columns=["timestamp", "actor", "action",
                                         "detail", "obj_id", "obj_hash"])
        return pd.DataFrame([asdict(e) for e in self.events])


# =====================================================================
# 6. Styling helpers
# =====================================================================

def inject_css():
    """Inject custom typography and palette into Streamlit."""
    import streamlit as st
    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,400;0,500;0,600;1,500&family=IBM+Plex+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
        <style>
        :root {
            --gold: #c9a96e;
            --gold-dim: #8c764a;
            --green: #6b9b7a;
            --amber: #d4a574;
            --red: #c14b54;
            --blue: #6b8ec9;
            --violet: #a08bc4;
        }
        html, body, .stApp, [class*="css"] {
            font-family: "IBM Plex Sans", -apple-system, system-ui, sans-serif;
        }
        h1, h2, h3, h4 {
            font-family: "Fraunces", Georgia, serif !important;
            font-weight: 500 !important;
            letter-spacing: -0.02em;
        }
        h1 { font-size: 2.6rem !important; line-height: 1.1; }
        h1 em, h2 em { color: var(--gold); font-style: italic; }
        .kicker {
            font-family: "JetBrains Mono", monospace;
            font-size: 0.7rem;
            color: var(--gold);
            text-transform: uppercase;
            letter-spacing: 0.18em;
            margin-bottom: 0.5rem;
        }
        .lead {
            color: #a8aeba;
            font-size: 1rem;
            line-height: 1.65;
            max-width: 760px;
            margin-bottom: 1.4rem;
        }
        .pill {
            display: inline-block;
            font-family: "JetBrains Mono", monospace;
            font-size: 0.68rem;
            padding: 0.22rem 0.6rem;
            border-radius: 3px;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            margin-right: 0.45rem;
            font-weight: 500;
        }
        .pill-green { background: rgba(107,155,122,.14); color: var(--green); }
        .pill-amber { background: rgba(212,165,116,.14); color: var(--amber); }
        .pill-red   { background: rgba(193,75,84,.14);   color: var(--red);   }
        .pill-blue  { background: rgba(107,142,201,.14); color: var(--blue);  }
        .pill-gold  { background: rgba(201,169,110,.14); color: var(--gold);  }
        .pill-violet{ background: rgba(160,139,196,.14); color: var(--violet);}
        [data-testid="stMetricValue"] {
            font-family: "Fraunces", Georgia, serif !important;
            font-weight: 500 !important;
        }
        [data-testid="stMetricLabel"] {
            font-family: "JetBrains Mono", monospace !important;
            font-size: 0.7rem !important;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: #8a929e !important;
        }
        .chain-node {
            background: rgba(255,255,255,0.02);
            border: 1px solid #2a3140;
            border-radius: 6px;
            padding: 16px;
            margin-bottom: 8px;
            min-height: 200px;
        }
        .chain-node-label {
            font-family: "JetBrains Mono", monospace;
            font-size: 0.65rem;
            color: var(--gold);
            text-transform: uppercase;
            letter-spacing: 0.16em;
        }
        .chain-node-title {
            font-family: "Fraunces", Georgia, serif;
            font-weight: 500;
            font-size: 1rem;
            margin: 8px 0;
        }
        .chain-node-detail { font-size: 0.85rem; color: #a8aeba; line-height: 1.55; }
        .chain-node-detail strong { color: #e7e9ec; }
        .quote {
            border-left: 3px solid var(--gold);
            padding: 12px 16px;
            font-family: "Fraunces", Georgia, serif;
            font-style: italic;
            color: #a8aeba;
            background: rgba(255,255,255,0.02);
            margin: 12px 0;
        }
        .quote .hl {
            background: rgba(201,169,110,0.20);
            color: #e7e9ec;
            font-style: normal;
            padding: 0 3px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def kicker(text: str):
    import streamlit as st
    st.markdown(f'<div class="kicker">{text}</div>', unsafe_allow_html=True)


def lead(text: str):
    import streamlit as st
    st.markdown(f'<div class="lead">{text}</div>', unsafe_allow_html=True)


def sidebar_brand():
    """Re-usable sidebar header shown on every page."""
    import streamlit as st
    with st.sidebar:
        st.markdown("""
        <div style="padding: 8px 0 16px;">
          <div style="font-family:'Fraunces',serif;font-style:italic;font-size:30px;
                      color:#c9a96e;font-weight:500;line-height:1;">A/C</div>
          <div style="font-family:'Fraunces',serif;font-size:22px;font-weight:600;
                      letter-spacing:-0.02em;margin-top:4px;">AI-COMPASS</div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:10px;
                      color:#8a929e;text-transform:uppercase;
                      letter-spacing:0.16em;margin-top:6px;">Demo · v0.4</div>
        </div>
        <div style="border-top:1px solid #232936;padding-top:12px;">
          <div style="font-family:'JetBrains Mono',monospace;font-size:10px;
                      color:#8a929e;text-transform:uppercase;
                      letter-spacing:0.14em;margin-bottom:6px;">Active pilot</div>
          <div style="font-size:13px;">Waste-to-energy facility</div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:11px;
                      color:#8a929e;margin-top:4px;">1,840 t/day · 6 reporting regimes</div>
        </div>
        """, unsafe_allow_html=True)


# =====================================================================
# 7. Session state initialiser
# =====================================================================

def init_session(st):
    """Initialise shared session state. Call at the top of every page."""
    if "simulator" not in st.session_state:
        st.session_state.simulator = DataSimulator(seed=42)
    if "emissions_df" not in st.session_state:
        st.session_state.emissions_df = (
            st.session_state.simulator.emissions(days=30))
    if "energy_df" not in st.session_state:
        st.session_state.energy_df = st.session_state.simulator.energy(days=30)
    if "waste_df" not in st.session_state:
        st.session_state.waste_df = st.session_state.simulator.waste(days=30)
    if "data_source" not in st.session_state:
        st.session_state.data_source = "synthetic"
    if "risk_engine" not in st.session_state:
        st.session_state.risk_engine = RiskEngine()
    if "mapping_engine" not in st.session_state:
        st.session_state.mapping_engine = MappingEngine()
    if "audit" not in st.session_state:
        st.session_state.audit = AuditTrail()
        st.session_state.audit.log(
            "SYS", "init",
            "Session initialised · synthetic emissions data generated (30 days)")
    if "signals" not in st.session_state:
        st.session_state.signals = []
    if "indicators" not in st.session_state:
        st.session_state.indicators = []
    if "human_decisions" not in st.session_state:
        st.session_state.human_decisions = {}


# =====================================================================
# 8. Plotly defaults
# =====================================================================

def plotly_layout(**overrides) -> dict:
    """Common dark plotly layout used across pages."""
    base = dict(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Sans", color="#a8aeba", size=11),
        xaxis=dict(showgrid=False, color="#8a929e"),
        yaxis=dict(showgrid=True, gridcolor="#232936", color="#8a929e"),
        margin=dict(l=10, r=10, t=20, b=10),
        legend=dict(orientation="h", y=1.12, bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(font_family="JetBrains Mono",
                        bgcolor="#131720", bordercolor="#c9a96e"),
    )
    base.update(overrides)
    return base


# Colour palette exposed for charts
PALETTE = {
    "gold": "#c9a96e",
    "green": "#6b9b7a",
    "amber": "#d4a574",
    "red": "#c14b54",
    "blue": "#6b8ec9",
    "violet": "#a08bc4",
    "muted": "#8a929e",
}
