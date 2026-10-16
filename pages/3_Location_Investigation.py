"""Page 3: Location Investigation.
Comprehensive deep-dive audit for individual city locations.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from src.data_loader import load_all_data
from src.feature_engineering import build_location_features
from src.priority_engine import rank_locations
from src.visualization import (
    apply_custom_css,
    plot_component_breakdown,
    plot_location_map,
    render_kpi_card,
)

apply_custom_css()

st.title("🔍 Location Investigation & Audit")
st.markdown("Detailed forensic investigation of individual infrastructure nodes, incident logs, and citizen grievances.")

@st.cache_data
def get_investigation_data():
    loc, inc, comp = load_all_data()
    feats = build_location_features(loc, inc, comp)
    ranked = rank_locations(feats)
    return loc, inc, comp, feats, ranked

loc, inc, comp, feats, ranked = get_investigation_data()

# Location Selector
loc_list = ranked["location_id"].tolist()
default_idx = 0
selected_id = st.selectbox(
    "Select Location ID to Audit:",
    options=loc_list,
    index=default_idx,
    format_func=lambda x: f"{x} (Rank #{int(ranked[ranked['location_id']==x]['priority_rank'].iloc[0])} · Score: {ranked[ranked['location_id']==x]['priority_score'].iloc[0]:.1f})",
)

loc_row = ranked[ranked["location_id"] == selected_id].iloc[0]
loc_incidents = inc[inc["location_id"] == selected_id].sort_values("timestamp", ascending=False)
loc_complaints = comp[comp["location_id"] == selected_id].sort_values("created_at", ascending=False)

# Top KPI row for this location
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    render_kpi_card("Priority Rank", f"#{int(loc_row['priority_rank'])}", "of 1,000 citywide")
with c2:
    render_kpi_card("Priority Score", f"{loc_row['priority_score']:.1f}", "Scale: 0 - 100")
with c3:
    render_kpi_card("Total Incidents", f"{len(loc_incidents):,}", f"{int(loc_row['unresolved_incidents'])} open")
with c4:
    render_kpi_card("Total Complaints", f"{len(loc_complaints):,}", f"{int(loc_row['active_complaints'])} active")
with c5:
    render_kpi_card("Casualties", f"{int(loc_row['total_injuries']):,}", "Injuries recorded")

st.markdown("---")

# Infrastructure Context & Component Breakdown
row_col1, row_col2 = st.columns([1, 1])

with row_col1:
    st.subheader("📋 Infrastructure & Built Environment Profile")
    st.markdown(
        f"""
        - **Zone:** `{loc_row['zone']}`
        - **Road Classification:** `{loc_row['road_type']}`
        - **Road Condition:** `{loc_row['road_condition']}`
        - **Pedestrian Activity Level:** `{loc_row['pedestrian_activity']}`
        - **Population Density:** `{int(loc_row['population_density_per_km2']):,} residents/km²`
        - **Adjacent to School:** `{'Yes 🏫 (Enhanced Caution)' if loc_row['near_school'] == 1 else 'No'}`
        - **Adjacent to Hospital:** `{'Yes 🏥 (Critical Access Corridor)' if loc_row['near_hospital'] == 1 else 'No'}`
        - **Coordinates:** `Lat {loc_row['latitude']:.5f}, Lon {loc_row['longitude']:.5f}`
        """
    )
    st.info(f"**Evidence & Rationale:** {loc_row['evidence_summary']}")

with row_col2:
    st.subheader("📊 Priority Dimension Profile")
    fig_comp = plot_component_breakdown(loc_row)
    st.plotly_chart(fig_comp, width="stretch")

st.markdown("---")

# Geospatial Cluster View
st.subheader("📍 Geospatial Node Context")
fig_map = plot_location_map(ranked, highlight_id=selected_id)
st.plotly_chart(fig_map, width="stretch")

st.markdown("---")

# Detailed Incident Log Table
st.subheader(f"⚠️ Recorded Incidents History ({len(loc_incidents)} records)")
if not loc_incidents.empty:
    st.dataframe(
        loc_incidents[[
            "incident_id",
            "timestamp",
            "incident_type",
            "severity",
            "injuries",
            "reported_by",
            "resolved",
            "resolution_hours",
        ]],
        width="stretch",
        column_config={
            "incident_id": "Incident ID",
            "timestamp": "Reported Time",
            "incident_type": "Type",
            "severity": "Severity",
            "injuries": "Injuries",
            "reported_by": "Reporting Source",
            "resolved": st.column_config.CheckboxColumn("Resolved"),
            "resolution_hours": st.column_config.NumberColumn("Resolution Hours", format="%.1fh"),
        },
    )
else:
    st.info("No incidents recorded for this location.")

# Detailed Citizen Complaints Table
st.subheader(f"📣 Citizen Complaints & 311 Tickets ({len(loc_complaints)} records)")
if not loc_complaints.empty:
    st.dataframe(
        loc_complaints[[
            "complaint_id",
            "created_at",
            "category",
            "priority_reported",
            "status",
            "days_to_resolution",
        ]],
        width="stretch",
        column_config={
            "complaint_id": "Ticket ID",
            "created_at": "Logged Time",
            "category": "Category",
            "priority_reported": "Citizen Priority",
            "status": "Ticket Status",
            "days_to_resolution": st.column_config.NumberColumn("Days Elapsed", format="%.1fd"),
        },
    )
else:
    st.info("No citizen complaints recorded for this location.")
