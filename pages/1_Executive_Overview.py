"""Page 1: Executive Overview.
Citywide operational KPIs, distributions, and top priority targets.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.data_loader import load_all_data
from src.feature_engineering import build_location_features
from src.priority_engine import rank_locations
from src.visualization import (
    apply_custom_css,
    plot_incident_type_bar,
    plot_location_map,
    plot_severity_donut,
    plot_top_locations_bar,
    render_kpi_card,
)

apply_custom_css()

st.title("📊 Executive Operational Overview")
st.markdown("High-level performance monitoring, hazard distributions, and top action locations.")

@st.cache_data
def get_overview_data():
    loc, inc, comp = load_all_data()
    feats = build_location_features(loc, inc, comp)
    ranked = rank_locations(feats)
    return loc, inc, comp, feats, ranked

loc, inc, comp, feats, ranked = get_overview_data()

# 6 Core KPIs
k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1:
    render_kpi_card("Locations", f"{len(loc):,}", "Monitored zones")
with k2:
    render_kpi_card("Total Incidents", f"{len(inc):,}", "Reported in 2025")
with k3:
    render_kpi_card("Complaints", f"{len(comp):,}", "Public 311 tickets")
with k4:
    inj = int(inc["injuries"].sum())
    render_kpi_card("Casualties", f"{inj:,}", "Injuries across events")
with k5:
    res_rate = (inc["resolved"] == 1).mean() * 100
    render_kpi_card("Resolution Rate", f"{res_rate:.1f}%", f"{int((inc['resolved']==1).sum()):,} resolved")
with k6:
    avg_hours = inc[inc["resolved"] == 1]["resolution_hours"].mean()
    render_kpi_card("Avg Turnaround", f"{avg_hours:.1f}h", "Resolved events")

st.markdown("---")

# Visual distributions
row1_col1, row1_col2 = st.columns([1, 1])
with row1_col1:
    fig_top = plot_top_locations_bar(ranked, top_n=10)
    st.plotly_chart(fig_top, width="stretch")

with row1_col2:
    fig_sev = plot_severity_donut(inc)
    st.plotly_chart(fig_sev, width="stretch")

row2_col1, row2_col2 = st.columns([1, 1])
with row2_col1:
    fig_type = plot_incident_type_bar(inc)
    st.plotly_chart(fig_type, width="stretch")

with row2_col2:
    # Complaints status breakdown
    status_counts = comp["status"].value_counts().reset_index()
    status_counts.columns = ["status", "count"]
    fig_status = px.pie(
        status_counts,
        names="status",
        values="count",
        hole=0.55,
        title="Public Complaint Resolution Status",
        color_discrete_sequence=["#10B981", "#06B6D4", "#64748B", "#F59E0B", "#EF4444"],
    )
    fig_status.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=10, t=40, b=10),
        height=320,
    )
    st.plotly_chart(fig_status, width="stretch")

st.markdown("---")

# Geospatial Overview
st.subheader("🗺️ Citywide Hazard & Priority Map")
st.markdown("Locations sized by incident volume and color-graded by MCDA priority score.")
fig_map = plot_location_map(ranked)
st.plotly_chart(fig_map, width="stretch")

st.markdown("---")

# Zone-Level Aggregation Table
st.subheader("🏢 Zone-Level Operational Summary")
zone_summary = ranked.groupby("zone").agg(
    locations=("location_id", "count"),
    total_incidents=("total_incidents", "sum"),
    unresolved_incidents=("unresolved_incidents", "sum"),
    total_complaints=("total_complaints", "sum"),
    active_complaints=("active_complaints", "sum"),
    total_injuries=("total_injuries", "sum"),
    mean_priority_score=("priority_score", "mean"),
    max_priority_score=("priority_score", "max"),
).reset_index()

zone_summary["mean_priority_score"] = zone_summary["mean_priority_score"].round(1)
zone_summary["max_priority_score"] = zone_summary["max_priority_score"].round(1)
zone_summary = zone_summary.sort_values("mean_priority_score", ascending=False).reset_index(drop=True)

st.dataframe(
    zone_summary,
    width="stretch",
    column_config={
        "zone": st.column_config.TextColumn("Zone"),
        "locations": st.column_config.NumberColumn("Locations"),
        "total_incidents": st.column_config.NumberColumn("Incidents"),
        "unresolved_incidents": st.column_config.NumberColumn("Open Incidents"),
        "total_complaints": st.column_config.NumberColumn("Complaints"),
        "active_complaints": st.column_config.NumberColumn("Active Complaints"),
        "total_injuries": st.column_config.NumberColumn("Casualties"),
        "mean_priority_score": st.column_config.ProgressColumn("Mean Priority", min_value=0, max_value=100, format="%.1f"),
        "max_priority_score": st.column_config.NumberColumn("Peak Priority"),
    },
)
