"""CivicPulse AI — Streamlit Entrypoint and Hub.
Datathon 2026 | Track 3: Smart City ("Where Should We Fix First?")
"""

import streamlit as st

st.set_page_config(
    page_title="CivicPulse AI | Smart City Intelligence",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.data_loader import load_all_data
from src.feature_engineering import build_location_features
from src.priority_engine import rank_locations
from src.modeling import load_trained_model
from src.visualization import apply_custom_css, render_kpi_card

apply_custom_css()

# Cache core data
@st.cache_data
def get_cached_data():
    loc, inc, comp = load_all_data()
    feats = build_location_features(loc, inc, comp)
    ranked = rank_locations(feats)
    return loc, inc, comp, feats, ranked

loc, inc, comp, feats, ranked = get_cached_data()
pipeline, metadata, importance = load_trained_model()

# Header
st.markdown("<span class='civic-badge'>DATATHON 2026 · TRACK 3 · SMART CITY INFRASTRUCTURE</span>", unsafe_allow_html=True)
st.title("🏙️ CivicPulse AI: Where Should We Fix First?")
st.markdown(
    "**An explainable decision intelligence platform for municipal resource allocation, "
    "hazard mitigation, and public service responsiveness.**"
)

# Notice banner
st.markdown(
    """
    <div class='disclaimer-banner'>
        <strong>Data Transparency Notice:</strong> Operating on the verified 2025 Smart City synthetic benchmark dataset. 
        All metrics, severity burdens, and location rankings are deterministically computed on verified primary records (1,000 locations, 10,000 incidents, 8,000 citizen complaints).
    </div>
    """,
    unsafe_allow_html=True,
)

# Top KPIs
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    render_kpi_card("City Locations", f"{len(loc):,}", "Active monitoring grid")
with col2:
    render_kpi_card("Reported Incidents", f"{len(inc):,}", "Full year 2025 records")
with col3:
    render_kpi_card("Citizen Complaints", f"{len(comp):,}", "Public 311 service tickets")
with col4:
    total_injuries = int(inc["injuries"].sum())
    render_kpi_card("Casualties / Injuries", f"{total_injuries:,}", "Reported across incidents")
with col5:
    unresolved_total = int((inc["resolved"] == 0).sum()) + int(comp["status"].isin(["Open", "Assigned", "In progress"]).sum())
    render_kpi_card("Active Backlog", f"{unresolved_total:,}", "Open incidents & complaints")

st.markdown("---")

# Quick Navigation Section
st.subheader("🧭 System Modules")
nav_col1, nav_col2, nav_col3 = st.columns(3)

with nav_col1:
    st.markdown(
        """
        ### 📊 [1. Executive Overview](Executive_Overview)
        High-level municipal operations pulse:
        - Citywide operational health KPIs
        - Severity & incident type breakdowns
        - Top-10 urgent priority locations
        - Geospatial priority cluster preview
        """
    )
    st.markdown(
        """
        ### 🎯 [2. Priority Queue](Priority_Queue)
        Transparent decision engine:
        - Deterministic multi-criteria 0-100 ranking
        - Interactive weight tuning
        - Zone and severity filters
        - Full CSV export for maintenance crews
        """
    )

with nav_col2:
    st.markdown(
        """
        ### 🔍 [3. Location Investigation](Location_Investigation)
        Deep-dive audit per location:
        - 360-degree profile for any `location_id`
        - Component score breakdown
        - Complete incident and complaint histories
        - Vulnerability indicators (schools, hospitals)
        """
    )
    st.markdown(
        """
        ### ⏱️ [4. Resolution Estimator](Resolution_Estimator)
        Predictive turnaround time:
        - Interactive incident dispatcher tool
        - Resolution-time ML regression model
        - Empirical confidence intervals
        - Operational turnaround guidance
        """
    )

with nav_col3:
    st.markdown(
        """
        ### 🔬 [5. Model Transparency](Model_Transparency)
        Honest, rigorous machine learning audit:
        - Chronological train/val/test methodology
        - Baseline vs. candidate model comparison
        - Feature importance rankings
        - Synthetic benchmark analysis & limitations
        """
    )

st.markdown("---")

# Architecture / Core Workflow
st.subheader("⚙️ How CivicPulse AI Works")
st.markdown(
    """
    ```
    ┌─────────────────────────┐     ┌─────────────────────────┐     ┌─────────────────────────┐
    │  locations.csv (1,000)  │     │ incidents.csv (10,000)  │     │ complaints.csv (8,000)  │
    └───────────┬─────────────┘     └───────────┬─────────────┘     └───────────┬─────────────┘
                │                               │                               │
                └───────────────────────┬───────┴───────────────────────────────┘
                                        ▼
                        ┌───────────────────────────────┐
                        │ Location Aggregation Pipeline │
                        │  (Reconciled 1,000 rows)      │
                        └───────────────┬───────────────┘
                                        ▼
                 ┌──────────────────────────────────────────────┐
                 │ Multi-Criteria Priority Engine (MCDA 0-100)  │
                 │  • Severity & Casualties (30%)               │
                 │  • Unresolved Workload (25%)                 │
                 │  • Citizen Complaints (20%)                  │
                 │  • Recurrence Volume (15%)                   │
                 │  • Location Vulnerability (10%)              │
                 └──────────────────────┬───────────────────────┘
                                        ▼
                 ┌──────────────────────────────────────────────┐
                 │  Actionable Dispatch Queue & Transparency    │
                 │  Ranked list, geospatial map, and audit logs │
                 └──────────────────────────────────────────────┘
    ```
    """
)

# Footer info
st.sidebar.title("🏙️ CivicPulse AI")
st.sidebar.markdown("**Track 3: Smart City**")
st.sidebar.markdown(f"**Version:** 1.0.0")
st.sidebar.markdown(f"**Data Status:** Validated ({len(loc)} locations)")
model_status = "Trained & Loaded ✅" if pipeline is not None else "Not Trained ⚠️"
st.sidebar.markdown(f"**ML Engine:** {model_status}")
