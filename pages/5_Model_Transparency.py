"""Page 5: Model Transparency.
Rigorous, honest audit of the machine learning resolution pipeline.
"""

import streamlit as st
import pandas as pd

from src.modeling import load_trained_model
from src.visualization import (
    apply_custom_css,
    plot_feature_importance_bar,
    render_kpi_card,
)

apply_custom_css()

st.title("🔬 Machine Learning Transparency & Audit")
st.markdown("Honest, reproducible evaluation of the predictive resolution model against empirical baselines.")

pipeline, metadata, importance = load_trained_model()

if metadata is None or importance is None:
    st.error(
        "⚠️ Model metadata or feature importance artifacts not found in `artifacts/`. "
        "Please run `python train_model.py` to generate complete evaluation metrics."
    )
    st.stop()

# Methodology Overview Card
st.markdown(
    """
    <div class='disclaimer-banner'>
        <strong>Scientific Rigor in Datathon Evaluation:</strong> Rather than fitting a random k-fold split that leaks 
        temporal trends, CivicPulse AI enforces a strict chronological split (70% train, 15% validation, 15% test). 
        All models are benchmarked against a Dummy Median Regressor.
    </div>
    """,
    unsafe_allow_html=True,
)

# Chronological Split KPI Row
st.subheader("📅 Chronological Partition Breakdown")
s1, s2, s3, s4 = st.columns(4)
with s1:
    render_kpi_card("Target Variable", "resolution_hours", "Resolved incidents only (7,126)")
with s2:
    render_kpi_card(
        "Train Set (70%)",
        f"{metadata['train_rows']:,} rows",
        f"{metadata['train_date_range'][0][:10]} to {metadata['train_date_range'][1][:10]}",
    )
with s3:
    render_kpi_card(
        "Validation Set (15%)",
        f"{metadata['val_rows']:,} rows",
        f"{metadata['val_date_range'][0][:10]} to {metadata['val_date_range'][1][:10]}",
    )
with s4:
    render_kpi_card(
        "Held-Out Test (15%)",
        f"{metadata['test_rows']:,} rows",
        f"{metadata['test_date_range'][0][:10]} to {metadata['test_date_range'][1][:10]}",
    )

st.markdown("---")

# Validation Candidate Comparison Table
st.subheader("⚖️ Candidate Model Validation Comparison")
st.markdown(
    "Models evaluated strictly on the out-of-time validation partition. "
    "Notice how candidate architectures perform relative to the naive baseline:"
)

val_dict = metadata.get("validation_comparison", {})
val_rows = []
for model_name, metrics in val_dict.items():
    val_rows.append({
        "Candidate Model": model_name.replace("_", " ").title(),
        "Validation MAE": f"{metrics['mae']:.2f} hrs",
        "Validation MedAE": f"{metrics['medae']:.2f} hrs",
        "Validation RMSE": f"{metrics['rmse']:.2f} hrs",
        "Validation R²": f"{metrics['r2']:.4f}",
    })

val_df = pd.DataFrame(val_rows)
st.dataframe(val_df, width="stretch")

st.markdown("---")

# Test Set Results
st.subheader(f"🏆 Final Held-Out Test Set Performance (`{metadata['model_type']}`)")
test_m = metadata.get("test_metrics", {})
base_test_m = metadata.get("baseline_test_metrics", {})

t1, t2, t3, t4 = st.columns(4)
with t1:
    render_kpi_card("Test MAE", f"{test_m.get('mae', 0):.2f} hrs", f"Baseline: {base_test_m.get('mae', 0):.2f} hrs")
with t2:
    render_kpi_card("Test MedAE", f"{test_m.get('medae', 0):.2f} hrs", f"Baseline: {base_test_m.get('medae', 0):.2f} hrs")
with t3:
    render_kpi_card("Test RMSE", f"{test_m.get('rmse', 0):.2f} hrs", f"Baseline: {base_test_m.get('rmse', 0):.2f} hrs")
with t4:
    render_kpi_card("Test R² Score", f"{test_m.get('r2', 0):.4f}", "Variance explained")

st.markdown("---")

# Feature Importance
st.subheader("📈 Engineered Feature Importances")
st.markdown(
    "Relative importance of contextual and temporal features extracted from the trained model pipeline:"
)
fig_imp = plot_feature_importance_bar(importance, top_n=12)
st.plotly_chart(fig_imp, width="stretch")

st.markdown("---")

# Transparent Limitations Discussion
st.subheader("💡 Engineering Insights & Synthetic Data Limitations")
st.markdown(
    """
    ### 1. Why does R² hover near 0.0?
    In this synthetic benchmark dataset, `resolution_hours` was generated primarily with random exponential noise 
    rather than a strong functional dependence on incident attributes. In genuine municipal datasets, resolution times 
    are heavily driven by variables **not present in this dataset**, including:
    - Dedicated repair crew staffing availability and shift schedules
    - Work order parts and replacement inventory status
    - Inclement weather conditions on the day of repair
    - Contractor dispatch SLAs
    
    ### 2. Why Honest Reporting Matters for Datathon 2026
    Many entries might overfit or hallucinate artificial accuracy numbers by fitting on leaked target statistics or 
    non-chronological random splits. CivicPulse AI maintains uncompromising data integrity:
    - We report **exact, reproducible metrics**.
    - We demonstrate that standard regressors cannot magically extract signal where the underlying data generator used uniform random noise.
    
    ### 3. Decoupling Prioritization from Regression Uncertainty
    Because the regression model carries high variance, **CivicPulse AI does NOT use ML regression to decide which location to fix first.**
    Instead, our core product is the **Deterministic Multi-Criteria Priority Engine** (`priority_engine.py`), 
    which operates on verified physical facts: casualty counts, unresolved backlogs, public complaints, 
    and proximity to sensitive facilities like hospitals and schools.
    """
)
