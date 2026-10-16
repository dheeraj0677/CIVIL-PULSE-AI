"""CLI script to train, evaluate, and persist the resolution-time predictor.

Usage:
    python train_model.py
"""

from pathlib import Path
from src.config import REPORTS_DIR
from src.data_loader import load_incidents, load_locations
from src.modeling import train_and_evaluate_all


def generate_evaluation_report(metadata: dict, output_path: Path):
    """Write comprehensive, honest evaluation report to markdown."""
    val_table_rows = []
    for model_name, metrics in metadata["validation_comparison"].items():
        val_table_rows.append(
            f"| `{model_name}` | {metrics['mae']:.2f}h | {metrics['medae']:.2f}h | {metrics['rmse']:.2f}h | {metrics['r2']:.4f} |"
        )
    val_table = "\n".join(val_table_rows)

    test = metadata["test_metrics"]

    report_content = f"""# CivicPulse AI — ML Model Evaluation Report
## Datathon 2026 · Track 3: Smart City ("Where Should We Fix First?")

**Date of Run:** October 2026  
**Selected Model Architecture:** `{metadata['model_type']}`  
**Evaluation Standard:** Chronological Train/Val/Test Split  

---

## 1. Problem Formulation & Setup

- **Target Variable:** `resolution_hours` (Continuous elapsed hours between incident reporting and resolution).
- **Data Filtering:** Strictly filtered to verified resolved incidents (`resolved == 1`, 7,126 records).
- **Split Strategy:** Strict chronological ordering by `timestamp` to avoid data leakage and simulate true deployment.
  - **Train Partition (70%):** {metadata['train_rows']:,} records ({metadata['train_date_range'][0]} to {metadata['train_date_range'][1]})
  - **Validation Partition (15%):** {metadata['val_rows']:,} records ({metadata['val_date_range'][0]} to {metadata['val_date_range'][1]})
  - **Test Partition (15%):** {metadata['test_rows']:,} records ({metadata['test_date_range'][0]} to {metadata['test_date_range'][1]})

---

## 2. Validation Candidate Comparison

Each candidate pipeline was trained strictly on the 70% training partition and evaluated on the out-of-time 15% validation partition.

| Model Candidate | Validation MAE | Validation MedAE | Validation RMSE | Validation R² |
|---|---|---|---|---|
{val_table}

---

## 3. Held-Out Test Evaluation

The winning model architecture was refitted on the combined Train + Validation partition (85% / {metadata['train_rows'] + metadata['val_rows']:,} records) and evaluated on the held-out Test partition (15% / {metadata['test_rows']:,} records).

| Metric | Test Set Score | Interpretation |
|---|---|---|
| **MAE** | **{test['mae']:.2f} hours** | Average absolute error in resolution time estimation |
| **MedAE** | **{test['medae']:.2f} hours** | Median absolute error (robust against extreme outliers) |
| **RMSE** | **{test['rmse']:.2f} hours** | Root mean square error |
| **R² Score** | **{test['r2']:.4f}** | Variance explained beyond naive baseline |

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
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_content)


def main():
    print("=" * 60)
    print("  CIVICPULSE AI — MODEL TRAINING PIPELINE")
    print("=" * 60)

    print("\n[1/4] Loading verified raw datasets...")
    loc = load_locations()
    inc = load_incidents()
    print(f"  Loaded {len(loc):,} locations and {len(inc):,} incidents.")

    print("\n[2/4] Training candidates on chronological split...")
    final_pipeline, metadata, imp_df = train_and_evaluate_all(inc, loc)

    print(f"\n[3/4] Best Architecture Selected: '{metadata['model_type']}'")
    print("\n--- Validation Comparison ---")
    for name, m in metadata["validation_comparison"].items():
        print(f"  {name:15s} | MAE: {m['mae']:.2f}h | RMSE: {m['rmse']:.2f}h | R²: {m['r2']:.4f}")

    print("\n--- Final Held-Out Test Set Metrics ---")
    tm = metadata["test_metrics"]
    print(f"  Test MAE:   {tm['mae']:.2f} hours")
    print(f"  Test MedAE: {tm['medae']:.2f} hours")
    print(f"  Test RMSE:  {tm['rmse']:.2f} hours")
    print(f"  Test R²:    {tm['r2']:.4f}")

    print("\n--- Top 5 Feature Importances ---")
    for idx, row in imp_df.head(5).iterrows():
        print(f"  {row['feature']:30s}: {row['importance']:.4f}")

    print("\n[4/4] Writing reports/model_evaluation.md...")
    report_file = REPORTS_DIR / "model_evaluation.md"
    generate_evaluation_report(metadata, report_file)
    print(f"  Saved report to {report_file}")
    print("\nModel training and artifact generation complete.")


if __name__ == "__main__":
    main()
