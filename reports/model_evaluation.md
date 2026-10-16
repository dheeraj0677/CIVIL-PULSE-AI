# CivicPulse AI — ML Model Evaluation Report
## Datathon 2026 · Track 3: Smart City ("Where Should We Fix First?")

**Date of Run:** October 2026  
**Selected Model Architecture:** `random_forest`  
**Evaluation Standard:** Chronological Train/Val/Test Split  

---

## 1. Problem Formulation & Setup

- **Target Variable:** `resolution_hours` (Continuous elapsed hours between incident reporting and resolution).
- **Data Filtering:** Strictly filtered to verified resolved incidents (`resolved == 1`, 7,126 records).
- **Split Strategy:** Strict chronological ordering by `timestamp` to avoid data leakage and simulate true deployment.
  - **Train Partition (70%):** 4,988 records (2025-01-01 00:29:00 to 2025-09-13 08:31:00)
  - **Validation Partition (15%):** 1,069 records (2025-09-13 08:32:00 to 2025-11-05 11:58:00)
  - **Test Partition (15%):** 1,069 records (2025-11-05 12:50:00 to 2025-12-31 23:11:00)

---

## 2. Validation Candidate Comparison

Each candidate pipeline was trained strictly on the 70% training partition and evaluated on the out-of-time 15% validation partition.

| Model Candidate | Validation MAE | Validation MedAE | Validation RMSE | Validation R² |
|---|---|---|---|---|
| `baseline` | 16.52h | 12.80h | 22.64h | -0.0715 |
| `linear` | 17.00h | 14.81h | 21.95h | -0.0077 |
| `decision_tree` | 16.87h | 14.10h | 21.95h | -0.0071 |
| `random_forest` | 16.97h | 14.63h | 21.95h | -0.0069 |

---

## 3. Held-Out Test Evaluation

The winning model architecture was refitted on the combined Train + Validation partition (85% / 6,057 records) and evaluated on the held-out Test partition (15% / 1,069 records).

| Metric | Test Set Score | Interpretation |
|---|---|---|
| **MAE** | **16.38 hours** | Average absolute error in resolution time estimation |
| **MedAE** | **13.94 hours** | Median absolute error (robust against extreme outliers) |
| **RMSE** | **21.27 hours** | Root mean square error |
| **R² Score** | **0.0008** | Variance explained beyond naive baseline |

---

## 4. Transparent Discussion of Results & Synthetic Data Characteristics

### Key Engineering Insights:
1. **Low Signal-to-Noise Ratio in Resolution Time:**  
   Across all tested architectures (Linear Ridge, Decision Tree, Random Forest, Dummy Median), the R² score hovers around 0.0, and MAE remains around 16.5 to 17.0 hours.
2. **Root Cause Analysis:**  
   In this benchmark synthetic dataset, `resolution_hours` was generated primarily with a uniform/exponential random noise component rather than a deterministic linear or tree relationship with incident type or location.
3. **Product Design Implication:**  
   - CivicPulse AI **does not** rely on this ML regression model for critical prioritization.
   - The primary decision engine is the **Multi-Criteria Priority Engine** (`priority_engine.py`), which uses verified structural aggregates, casualty burdens, backlog counts, and public urgency.
   - The regression model is provided in the **Resolution Estimator** tool with explicit confidence bounds and transparent disclaimer notices for dispatchers.
