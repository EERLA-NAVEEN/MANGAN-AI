# MANGAN-AI — Reserve-to-Production Intelligence

**Smart India Hackathon (SIH 2026) Prototype**  
**Problem Statement SIH26009:** *Using AI/ML and Space Technology to Prioritize Manganese Exploration and Overcome Production Shortfalls.*

---

## ⚠️ Important Terminology, Scientific Scope & Compliance Disclaimers

1. **Exploration Favorability Prioritization:** Satellite multispectral imagery (NDVI, Bare Soil Index) and terrain geomorphology serve strictly as **surface/outcrop and environmental proxies**. They do **NOT** directly detect, delineate, or certify subsurface manganese mineral deposits beneath soil, alluvium, or hanging-wall waste rock.
2. **Confirmatory Drilling Mandatory:** The exploration module performs **"AI-based exploration-favorability mapping and drilling prioritization"**. Confirmatory diamond core drilling, stratigraphic logging, and certified geological validation are mandatory before mineral reserve classification or mine investment.
3. **Operational Decision Support:** The system is an operational decision-support tool. It is **NOT** an autonomous mining-control system. All operational interventions and candidate recommendations require supervisory human review and authorization.
4. **Synthetic Demonstration Data:** All datasets, boreholes, concession boundaries, fleet logs, and assays provided in this prototype are **synthetic demonstration records** designed to validate algorithmic flows and decision workflows offline without proprietary or real MOIL data.

---

## 🏛️ System Architecture

```text
mangan-ai/
├── app.py                     # Main Streamlit application entrypoint & navigation
├── requirements.txt           # Python dependencies
├── README.md                  # System architecture, schemas, and execution guide
├── config/
│   └── thresholds.yaml        # Configurable risk thresholds and model parameters
├── data/
│   ├── demo/                  # Synthetic demonstration datasets
│   │   ├── production.csv     # Historical operational logs (Mine A & Mine B)
│   │   ├── equipment.csv      # Fleet operating hours & downtime logs
│   │   ├── blasting.csv       # Blast schedules, execution times, and delays
│   │   ├── drill_holes.csv    # Borehole collar coordinates & depths (60 holes)
│   │   ├── assays.csv         # Core interval geochemistry (Mn%, Fe%, SiO2%)
│   │   ├── satellite_features.csv # Multispectral surface proxies & weather logs
│   │   ├── mine_boundary.geojson  # Dynamic permit boundaries (4 concession blocks)
│   │   └── geology.geojson    # Regional stratigraphic formations (7 geological units)
│   ├── raw/                   # Ingestion directory for raw datasets
│   └── processed/             # Cached feature matrices
├── models/                    # Model artifacts & checkpoints
├── src/
│   ├── __init__.py
│   ├── data_loader.py         # Data loading, validation, and auto-bootstrapping
│   ├── validation.py          # Synthetic Demo Data Quality scoring engine
│   ├── feature_engineering.py # Cross-domain temporal & operational feature extraction
│   ├── exploration_model.py   # Multi-criteria exploration-favorability & priority engine
│   ├── production_model.py    # Random Forest realization ratio model & horizon forecaster
│   ├── explainability.py      # Scenario sensitivity & model feature attribution
│   ├── rules.py               # Configurable operational & exploration rule engine
│   ├── recommendations.py     # Scoped candidate action state & approval audit manager
│   └── app_state.py           # Pipeline caching & session state coordinator
├── pages/
│   ├── overview.py            # Executive KPI dashboard & cross-module health
│   ├── exploration.py         # Multi-layer concession map, assays & priority zones
│   ├── production.py          # Production trajectory, validation metrics & diagnostics
│   └── recommendations.py     # Decision-support dashboard & isolated human approval
└── assets/
    └── style.css              # Custom mining intelligence theme styling
```

---

## 🚀 Quickstart & Local Execution

### 1. Prerequisites
Python 3.10+ (tested on Python 3.14).

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch Streamlit Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 📊 Core Features & Model Methodology

### 1. Production Realization Model (Leak-Free ML)
* **Target Variable:** Operational Realization Ratio ($\text{Actual Tonnes} / \text{Planned Tonnes}$), safe from target-scale leakage (`planned_tonnes` is strictly excluded from predictive features).
* **Validation Methodology:** Per-section chronological holdout (75% train / 25% validation), preventing future information leakage and evaluating out-of-sample across all concession sections.
* **Benchmark Comparison:** Evaluated against historical training mean realization ratio.
* **Future Forecast Layer:** Produces a genuine day-by-day forecast trajectory across the designated horizon (7, 14, or 30 days) with an empirical prediction interval derived from validation residuals.

### 2. Multi-Criteria Exploration Favorability
* **Dynamic Spatial Extent:** Concession bounding boxes and grid bounds are dynamically computed from `mine_boundary.geojson` polygons for both Mine A (North Block, South Pit) and Mine B (East Ridge, Deep West).
* **Evidence Synthesis:** Synthesizes lithological formation favorability (Gondite Series, Mansar Schist, etc.), Inverse Distance Weighting (IDW) of borehole assays, proximity confidence distance, and terrain context.
* **Transparent Prioritization:** Identifies candidate confirmatory drilling step-out targets requiring geological validation.

### 3. Model Explainability & Attribution
* **Sensitivity Estimation:** Decomposes predicted shortfall into operational domains (equipment, precipitation, blasting, grade dilution) derived mathematically from model feature importances and scenario counterfactual sensitivity.
* **Non-Causal Framing:** Clearly disclaimed as model sensitivity rather than physical causal proof.

### 4. Human-in-the-Loop Governance
* **Candidate Interventions:** Rule engine evaluates configurable thresholds from `config/thresholds.yaml` and extracts live operational bottlenecks dynamically from equipment and blasting logs.
* **Isolated Session State:** Decision approvals (Approved, Deferred, Rejected) are scoped per mine concession and section to prevent state cross-talk.
* **Audit Trail Export:** Signed decision register exportable as CSV.

---

## 🔒 Known Limitations & Roadmap

### Current Prototype Scope:
* Utilizes synthetic demonstration datasets to validate algorithmic decision pipelines offline.
* Spatial modeling uses 2D planar projection and inverse-distance weighted assay interpolation.
* Rules are evaluated against threshold configurations defined in `config/thresholds.yaml`.

### Future Development Roadmap:
1. **Satellite Remote Sensing Integration:** Ingest Sentinel-2 and Landsat multispectral bands via STAC APIs (with offline caching) for surface alteration and lineament extraction.
2. **Geological Block Modelling:** Extend borehole intervals into 3D voxel wireframes to model mineral strike, dip, and structural faulting.
3. **Automated Fleet Telematics Connector:** Ingest haul truck cycle times and shovel payload sensors via industrial MQTT/REST protocols.
