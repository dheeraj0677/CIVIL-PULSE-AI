"""Page 2: Priority Queue.
Interactive, explainable multi-criteria priority queue and dispatch engine.
"""

import streamlit as st
import pandas as pd

from src.config import DEFAULT_PRIORITY_WEIGHTS
from src.data_loader import load_all_data
from src.feature_engineering import build_location_features
from src.priority_engine import rank_locations
from src.visualization import (
    apply_custom_css,
    plot_component_breakdown,
)

apply_custom_css()

st.title("🎯 Municipal Priority Action Queue")
st.markdown("Deterministic, transparent prioritization of city infrastructure repair and hazard mitigation.")

# Explanatory banner
st.markdown(
    """
    <div class='disclaimer-banner'>
        <strong>Prioritization Standard:</strong> Priority scores (0–100) are computed deterministically via 
        Multi-Criteria Decision Analysis (MCDA). Scores reflect objective severity weights, injury burdens, 
        active backlogs, public urgency, and vulnerable facilities (schools, hospitals). 
        Adjust weights below to evaluate alternative dispatch strategies.
    </div>
    """,
    unsafe_allow_html=True,
)

@st.cache_data
def get_base_features():
    loc, inc, comp = load_all_data()
    return build_location_features(loc, inc, comp)

feats = get_base_features()

# Sidebar: Interactive Weight Configuration
st.sidebar.subheader("⚖️ MCDA Weight Customizer")
st.sidebar.caption("Adjust policy weights to evaluate priority rebalancing.")

w_sev = st.sidebar.slider("Severity & Injury Burden", 0.0, 1.0, DEFAULT_PRIORITY_WEIGHTS["severity_injury"], 0.05)
w_unres = st.sidebar.slider("Unresolved Backlog", 0.0, 1.0, DEFAULT_PRIORITY_WEIGHTS["unresolved_workload"], 0.05)
w_comp = st.sidebar.slider("Citizen Complaint Urgency", 0.0, 1.0, DEFAULT_PRIORITY_WEIGHTS["complaint_urgency"], 0.05)
w_rec = st.sidebar.slider("Recurrence Volume", 0.0, 1.0, DEFAULT_PRIORITY_WEIGHTS["recurrence_volume"], 0.05)
w_ctx = st.sidebar.slider("Location Vulnerability", 0.0, 1.0, DEFAULT_PRIORITY_WEIGHTS["location_vulnerability"], 0.05)

raw_sum = w_sev + w_unres + w_comp + w_rec + w_ctx
if raw_sum <= 0:
    st.sidebar.error("At least one weight must be greater than zero.")
    active_weights = DEFAULT_PRIORITY_WEIGHTS
else:
    active_weights = {
        "severity_injury": w_sev,
        "unresolved_workload": w_unres,
        "complaint_urgency": w_comp,
        "recurrence_volume": w_rec,
        "location_vulnerability": w_ctx,
    }

# Compute ranked locations with active weights
ranked_df = rank_locations(feats, weights=active_weights)

# Filter Controls
with st.expander("🔍 Filter & Search Queue", expanded=True):
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    with f_col1:
        search_id = st.text_input("Search Location ID", placeholder="e.g. L0001, L0428").strip().upper()
    with f_col2:
        all_zones = sorted(ranked_df["zone"].unique())
        selected_zones = st.multiselect("Filter Zones", options=all_zones, default=[])
    with f_col3:
        road_types = sorted(ranked_df["road_type"].unique())
        selected_road_types = st.multiselect("Road Type", options=road_types, default=[])
    with f_col4:
        min_score = st.slider("Min Priority Score", 0.0, 100.0, 0.0, 5.0)

# Apply filters
filtered_df = ranked_df.copy()
if search_id:
    filtered_df = filtered_df[filtered_df["location_id"].str.contains(search_id, case=False, na=False)]
if selected_zones:
    filtered_df = filtered_df[filtered_df["zone"].isin(selected_zones)]
if selected_road_types:
    filtered_df = filtered_df[filtered_df["road_type"].isin(selected_road_types)]
if min_score > 0:
    filtered_df = filtered_df[filtered_df["priority_score"] >= min_score]

st.markdown(f"**Showing {len(filtered_df):,} of {len(ranked_df):,} locations**")

# Display columns
display_cols = [
    "priority_rank",
    "location_id",
    "zone",
    "road_type",
    "priority_score",
    "total_incidents",
    "unresolved_incidents",
    "active_complaints",
    "total_injuries",
    "evidence_summary",
]

st.dataframe(
    filtered_df[display_cols],
    width="stretch",
    height=420,
    column_config={
        "priority_rank": st.column_config.NumberColumn("Rank", format="#%d"),
        "location_id": st.column_config.TextColumn("Location"),
        "zone": st.column_config.TextColumn("Zone"),
        "road_type": st.column_config.TextColumn("Road"),
        "priority_score": st.column_config.ProgressColumn(
            "Priority Score", min_value=0, max_value=100, format="%.1f"
        ),
        "total_incidents": st.column_config.NumberColumn("Incidents"),
        "unresolved_incidents": st.column_config.NumberColumn("Open Incidents"),
        "active_complaints": st.column_config.NumberColumn("Active Complaints"),
        "total_injuries": st.column_config.NumberColumn("Casualties"),
        "evidence_summary": st.column_config.TextColumn("Primary Justification", width="large"),
    },
)

# Export CSV
csv_data = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="📥 Export Filtered Queue to CSV",
    data=csv_data,
    file_name="civicpulse_priority_queue.csv",
    mime="text/csv",
)

st.markdown("---")

# Quick Location Profile Inspector
st.subheader("🔎 Instant Location Profile")
loc_options = filtered_df["location_id"].tolist()
if loc_options:
    chosen_loc = st.selectbox("Select Location to Inspect Component Breakdown:", options=loc_options, index=0)
    selected_row = filtered_df[filtered_df["location_id"] == chosen_loc].iloc[0]

    p_col1, p_col2 = st.columns([1, 1])
    with p_col1:
        st.markdown(f"### Location: `{selected_row['location_id']}`")
        st.markdown(f"**Current Priority Rank:** `#{int(selected_row['priority_rank'])}` of 1,000")
        st.markdown(f"**Priority Score:** `{selected_row['priority_score']:.1f} / 100`")
        st.markdown(f"**Zone & Road:** {selected_row['zone']} · {selected_row['road_type']} ({selected_row['road_condition']} condition)")
        st.markdown(f"**Sensitive Features:** Near School: {'Yes 🏫' if selected_row['near_school']==1 else 'No'} | Near Hospital: {'Yes 🏥' if selected_row['near_hospital']==1 else 'No'}")
        st.info(selected_row["evidence_summary"])

    with p_col2:
        fig_profile = plot_component_breakdown(selected_row)
        st.plotly_chart(fig_profile, width="stretch")
else:
    st.info("No locations match the current filter criteria.")
