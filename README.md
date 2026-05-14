# AI-COMPASS — Compliance Automation Demo

A working Streamlit demonstration of the AI-COMPASS pipeline:
raw plant data → semantic harmonisation → regulation intelligence →
risk detection → **risk-to-regulation mapping (core)** → compliance
indicators → audit-ready reports.

---

## Quick start

Tested with Python 3.10+.

```bash
# 1. (optional) create a virtual environment
python -m venv .venv
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate           # Windows

# 2. install dependencies
pip install -r requirements.txt

# 3. run the app
streamlit run app.py
```

The browser opens at `http://localhost:8501`. Use the sidebar to walk
through pages **01 → 08**.

---

## Demo flow for a meeting

A natural 5–10 minute walkthrough:

| # | Page                       | What to say                                                                           |
|---|----------------------------|---------------------------------------------------------------------------------------|
| 1 | **Pipeline Overview**      | "Six layers, human-in-the-loop, this is what we are building."                       |
| 2 | **Data Streams**           | Upload a CSV or regenerate synthetic data with a controlled anomaly.                  |
| 3 | **Regulation Intelligence**| Show an extracted IED obligation — structured, traceable, expert-reviewed.            |
| 4 | **Risk Detection**         | Click *Run detection* — Isolation Forest + rules actually execute and find the anomaly. |
| 5 | **Mapping Engine**         | **The core contribution.** The data → risk → regulation → indicator → evidence chain. Confirm or reject the AI's proposal. |
| 6 | **Compliance Reports**     | Auto-drafted IED Q1 report with the incident embedded; export JSON/CSV.               |
| 7 | **Audit Trail**            | Every step hashed and traceable, from raw signal to submission.                       |
| 8 | **Privacy & Security**     | Data classification, PETs applied per class, GDPR posture, NIS2 events.               |

---

## File layout

```
ai-compass-demo/
├── app.py                              # 01 · Overview · main entry
├── lib.py                              # core library (single file)
│   ├── DataSimulator                   # synthetic data generator
│   ├── REGULATIONS                     # knowledge base (IED/ETS/WFD/EED/NIS2/GDPR)
│   ├── RiskEngine                      # IsolationForest + rule-engine
│   ├── MappingEngine                   # risk-to-regulation mapping (core)
│   ├── AuditTrail                      # SHA-256 hashed event log
│   ├── inject_css / kicker / lead      # styling helpers
│   └── init_session                    # shared state across pages
├── pages/
│   ├── 2_Data_Streams.py               # ingestion + harmonisation + upload
│   ├── 3_Regulation_Intelligence.py    # AB direktifleri, obligation extraction
│   ├── 4_Risk_Detection.py             # runs sklearn IsolationForest + rules
│   ├── 5_Mapping_Engine.py             # CORE — data→risk→reg→indicator→evidence
│   ├── 6_Reports.py                    # auto-drafted IED Q1 report
│   ├── 7_Audit_Trail.py                # hashed evidence chain
│   └── 8_Privacy_Security.py           # PETs, GDPR, NIS2
├── .streamlit/
│   └── config.toml                     # dark institutional theme
├── sample_data/
│   ├── emissions_sample.csv            # CEMS-style sample for upload
│   └── energy_sample.csv               # energy meter sample
├── requirements.txt
└── README.md                           # this file
```

---

## What the user can actually do

**Page 02 · Data Streams**
* Regenerate synthetic data with a custom seed and length.
* Toggle the controlled anomaly on or off.
* **Upload your own CSV** of CEMS-style emissions data — the whole
  pipeline re-runs on it.
* Download a CSV template from the current dataset.

**Page 04 · Risk Detection**
* Tune the contamination parameter for Isolation Forest.
* Click *Run detection* — `sklearn.ensemble.IsolationForest` actually
  fits on the current data and produces signals.
* Threshold rules from the knowledge base produce 100%-confident
  signals on real violations.

**Page 05 · Mapping Engine**
* Pick any detected case and inspect its full five-step chain.
* **Confirm** or **reject** the AI's proposed mapping — the decision
  flows to the report and audit trail.
* Inspect the machine-readable JSON output.

**Page 06 · Reports**
* Auto-generated Q1 IED report with all detected violations embedded.
* Download structured JSON or CSV summary.

**Page 07 · Audit Trail**
* Per-indicator evidence chain (raw signal → QAL2 → ontology →
  detector → mapping → human review).
* Global session audit log, downloadable as CSV.

---

## Required CSV format (for upload)

If you want to upload your own emissions data on page 02, use these
columns. Only `timestamp` and `no2_mg_nm3` are strictly required:

| Column         | Type      | Example       | Notes                            |
|----------------|-----------|---------------|----------------------------------|
| `timestamp`    | datetime  | `2026-03-14 14:22:00` | required                |
| `line`         | string    | `A` or `B`    | optional, defaults to `A`        |
| `no2_mg_nm3`   | float     | `218.0`       | required                         |
| `sox_mg_nm3`   | float     | `14.2`        | optional                         |
| `pm_mg_nm3`    | float     | `3.1`         | optional                         |
| `co_mg_nm3`    | float     | `28.4`        | optional                         |
| `o2_ref_pct`   | float     | `11.0`        | optional                         |
| `method`       | string    | `EN 14792`    | optional, free text              |

A working sample is included at `sample_data/emissions_sample.csv`.

---

## Extending the demo

* **New regulations** — add an entry to `REGULATIONS` in `lib.py`. Each
  obligation that has a `limit_field` matching a CEMS column will be
  picked up by the rule engine automatically and routed through the
  mapping engine.

* **New detectors** — add methods to `RiskEngine` that return
  `list[RiskSignal]` and call them from `detect_all`.

* **New data sources** — extend `DataSimulator` or simply replace
  `st.session_state.emissions_df` with anything that has the same
  schema.

* **New pages** — drop a new file into `pages/`. Streamlit picks it up
  on the next run.

---

## Notes

* All data is synthetic or user-provided. No real plant data is
  required to run the demo.
* `streamlit run app.py` is the only command needed. The pages directory
  is auto-discovered.
* This is a pilot UI for the AI-COMPASS proposal under
  **EU Horizon Europe · DIGITAL-2026-AI-DATA-10-COMPLIANCE**.
