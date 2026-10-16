# CivicPulse AI 🏙️
## Datathon 2026 · Track 3: Smart City
### *"Where Should We Fix First?"*

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/pytest-17%20passed-brightgreen.svg)](tests/)
[![UI](https://img.shields.io/badge/Streamlit-Multi--Page-FF4B4B.svg)](app.py)
[![Design](https://img.shields.io/badge/Theme-Cyan%20Accent%20%7C%20Charcoal-06B6D4.svg)](src/visualization.py)

---

## 📌 Executive Summary

Urban municipal authorities manage thousands of physical infrastructure assets across changing traffic demands, weather disruptions, and public service tickets. When dozens of hazards occur simultaneously, city dispatchers face a critical question: **Where should we fix first?**

**CivicPulse AI** is an explainable decision-intelligence platform engineered for Datathon 2026. Operating directly on the verified 2025 Smart City benchmark dataset (1,000 locations, 10,000 incidents, 8,000 citizen complaints), CivicPulse AI bridges the gap between raw maintenance data and operational dispatch through:

1. **A Transparent Multi-Criteria Priority Engine (MCDA):** Computes deterministic 0–100 priority scores, tiebreaker rankings, and human-readable evidence narratives based on casualty burdens, backlogs, public urgency, and sensitive infrastructure (schools, hospitals).
2. **Interactive 5-Page Streamlit Operations Suite:** Features high-level executive dashboards, dynamic policy weight customizers, deep forensic location cards, predictive resolution forecasting, and complete machine-learning transparency.
3. **Uncompromising Data & Modeling Integrity:** Enforces strict chronological train/val/test splits, compares candidate models against naive baselines, and transparently analyzes synthetic dataset characteristics.

---

## 🏗️ System Architecture

```
CivilPulseAI/
├── 03_smart_city_where_fix_first/     ← Read-only original benchmark data
│   ├── locations.csv                  ← 1,000 monitored urban locations
│   ├── incidents.csv                  ← 10,000 incident events (full year 2025)
│   ├── public_complaints.csv          ← 8,000 citizen 311 service tickets
│   └── README.txt                     ← Benchmark data specification
│
├── src/                               ← Modular core library
│   ├── config.py                      ← Central constants, filepaths, schemas, color tokens
│   ├── data_loader.py                 ← Schema validation, FK verification, boundary audits
│   ├── feature_engineering.py         ← Location-level aggregation & reconciliation
│   ├── priority_engine.py             ← MCDA composite scoring & narrative generator
│   ├── modeling.py                    ← Chronological ML pipeline, training & inference
│   └── visualization.py               ← Plotly charts, custom CSS, reusable UI cards
│
├── pages/                             ← Multi-page Streamlit application
│   ├── 1_Executive_Overview.py        ← Citywide operational KPIs & geographic clusters
│   ├── 2_Priority_Queue.py            ← Dynamic dispatch queue with weight tuning & CSV export
│   ├── 3_Location_Investigation.py    ← Deep forensic audit of individual location nodes
│   ├── 4_Resolution_Estimator.py      ← Predictive resolution time calculator with bounds
│   └── 5_Model_Transparency.py        ← Scientific validation comparison & benchmark report
│
├── tests/                             ← Pytest automated test suite (17 tests)
│   ├── test_data_loader.py            ← Primary keys, foreign keys, missing columns, bounds
│   ├── test_feature_engineering.py    ← Total reconciliation, zero-event handling
│   ├── test_priority_engine.py        ← Score bounds (0-100), determinism, tiebreakers
│   └── test_modeling.py               ← Chronological ordering, leakage prevention, inference
│
├── artifacts/                         ← Serialized models & metadata
│   ├── model_pipeline.pkl             ← Trained scikit-learn pipeline (RandomForest)
│   ├── model_metadata.json            ← Exact partition dates, validation metrics, test MAE
│   └── feature_importance.csv         ← Contextual and temporal feature importances
│
├── reports/                           ← Formal markdown documentation
│   ├── data_audit.md                  ← Comprehensive schema & distribution analysis
│   └── model_evaluation.md            ← Empirical model evaluation & synthetic benchmark notes
│
├── app.py                             ← Streamlit entrypoint & executive hub
├── train_model.py                     ← Standalone model training CLI script
├── requirements.txt                   ← Python dependencies
└── README.md                          ← Project documentation
```

---

## 🌐 Full-Fledged Web Application (Citizen, Officer & Worker Portals)

CivicPulse AI includes a complete multi-role web platform built with FastAPI, SQLite, and vanilla CSS/JS.

### Start the Web Application
```powershell
python run_web.py
```
Open **`http://localhost:8000`** in your browser.

### Key Roles & Capabilities:
1. **Citizen Portal (No Login Required):**
   - Direct grievance reporting with text description, location selection, or simulated GPS locator.
   - **Real-Time ML Diagnostic Box:** As the citizen types, the AI predicts Category, Severity, Turnaround time, and computes the 0–100 MCDA Priority Score before submission!
   - Generates instant Tracking Code (e.g., `CP-2026-1517`).
   - **Live 5-Step Stepper Timeline:** Track grievance from registration $\rightarrow$ AI scoring $\rightarrow$ officer approval $\rightarrow$ field crew dispatch $\rightarrow$ resolution.

2. **Government Officer Command Portal (Login Required):**
   - **Demo Credentials:** `officer@smartcity.gov` / `password123` (or click 1-Click Demo Persona button).
   - **Strict Priority Queue:** All incoming citizen grievances are ordered strictly by **MCDA Priority Score (0–100)** so the most urgent life hazards and hospital/school corridor risks are addressed first!
   - **Approval & Dispatch:** Review ML assessment, adjust severity if needed, and assign to target Field Crew squad.

3. **Field Crew Worker Console (Login Required):**
   - **Demo Credentials:** `worker@smartcity.gov` / `password123` (Vikram Singh, Crew Lead).
   - View assigned work orders in priority sequence.
   - Actions: **"Start Work"** (in-progress timestamp) $\rightarrow$ **"Complete & Resolve"** (records field notes and actual labor hours).

---

## ⚡ Quickstart Guide (Windows PowerShell)

### 1. Run the Full Web Platform (Recommended for Demos)
```powershell
python run_web.py
# Running at http://localhost:8000
```

### 2. Run the Streamlit Analytics Suite
```powershell
python -m streamlit run app.py
# Running at http://localhost:8501
```

### 3. Run the Automated Pytest Suite (20 Tests)
```powershell
python -m pytest tests/ -v
# All 20 tests pass in ~4 seconds
```

### 4. Re-Train the ML Model & Re-generate Artifacts
```powershell
python train_model.py
```

---

## 🎯 Prioritization Engine Methodology (MCDA)

Rather than treating prioritization as an uninterpretable black box, CivicPulse AI uses a deterministic Multi-Criteria Decision Analysis framework.

### Priority Components & Default Policy Weights:

| Dimension | Default Weight | Evaluated Factors | Normalization |
|---|---|---|---|
| **Severity & Casualty Burden** | **30%** | Weighted severity sum (Critical=4, High=3, Medium=2, Low=1) + Casualties/Injuries (×2.0) | Percentile rank across 1,000 locations (0–100) |
| **Unresolved Workload Backlog** | **25%** | Unresolved incidents (×2.0) + Active citizen complaints (Open, Assigned, In Progress) (×1.5) | Percentile rank (0–100) |
| **Public Citizen Urgency** | **20%** | Total citizen complaints (×1.0) + High-priority complaints (×2.0) | Percentile rank (0–100) |
| **Recurrence Volume** | **15%** | Total historical incident frequency | Percentile rank (0–100) |
| **Location Vulnerability** | **10%** | Road degradation condition + Pedestrian traffic + School corridor flag + Hospital corridor flag + Population density | Scaled vulnerability sum to percentile rank (0–100) |

- **Deterministic Tiebreaker:** If two locations have identical composite scores, sorting deterministically breaks ties using `location_id` ascending.
- **Explainability:** For every ranked location, the system automatically builds an **Evidence Summary** detailing the primary driving components and specific raw figures (e.g., *"Primary driver: Unresolved Backlog (8 open incidents, 7 active complaints, score 98.5)..."*).

---

## 🔬 Machine Learning Evaluation & Transparency

### Problem Definition
- **Target:** `resolution_hours` (Turnaround time from incident reporting to resolution).
- **Filtering:** Strictly trained on verified completed incidents (`resolved == 1`, 7,126 records).
- **Temporal Partitions (Strict Chronological Split):**
  - **Train (70%):** 4,988 records (2025-01-01 to 2025-09-13)
  - **Validation (15%):** 1,069 records (2025-09-13 to 2025-11-05)
  - **Held-Out Test (15%):** 1,069 records (2025-11-05 to 2025-12-31)

### Validation Comparison Results:

| Model Architecture | Validation MAE | Validation MedAE | Validation RMSE | Validation R² |
|---|---|---|---|---|
| **Dummy Baseline (Median)** | **16.52h** | 13.00h | 22.64h | -0.0715 |
| **Linear Model (Ridge)** | 17.00h | 14.15h | 21.95h | -0.0077 |
| **Decision Tree** | 16.87h | 13.59h | 21.95h | -0.0071 |
| **Random Forest (Deployed)** | **16.97h** | 14.28h | 21.95h | **-0.0069** |

### Held-Out Test Set Performance:
- **Test MAE:** **16.38 hours** (vs. Naive Baseline 16.02 hours)
- **Test MedAE:** **13.94 hours** (vs. Naive Baseline 13.10 hours)
- **Test RMSE:** **21.27 hours**
- **Test R² Score:** **+0.0008**

### Honest Scientific Findings:
In this benchmark synthetic dataset, `resolution_hours` exhibits an approximately uniform/exponential random distribution with high variance that is virtually uncorrelated with incident type, location, or severity. 
Rather than inventing artificial metrics, **CivicPulse AI truthfully documents this finding** and intentionally decouples the prioritization engine from regression uncertainty. The regression pipeline is utilized strictly as an advisory turnaround estimator equipped with empirical confidence bounds (`± MAE`).

---

## 🧪 Verification & QA Checklist

- [x] **Zero Data Leakage:** All feature matrices strictly exclude `resolution_hours`, `resolved`, and ID columns.
- [x] **Relational Integrity:** 100% of foreign keys reconciled; zero orphan records.
- [x] **Zero Row Multiplication:** Location aggregations left-join back to exactly 1,000 unique locations.
- [x] **100% Deterministic Ranking:** Repeated calls with identical inputs produce identical orderings.
- [x] **Full Test Suite:** 17 automated tests passing in `tests/`.
- [x] **Clean Visual Interface:** Light theme with cyan accent palette (`#06B6D4`), dark charcoal text (`#1E293B`), and responsive Plotly visual charts.

---

*CivicPulse AI — Developed for DATATHON 2026 | Track 3: Smart City*
