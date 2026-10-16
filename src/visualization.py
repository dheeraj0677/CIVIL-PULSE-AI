"""Visualization and UI rendering components for CivicPulse AI.

Provides unified Plotly chart builders, custom CSS injections,
and reusable card components following the clean cyan-accent design system.
"""

from typing import Dict, List, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.config import PALETTE


def apply_custom_css():
    """Inject modern, clean CSS styling with cyan accents and crisp cards."""
    st.markdown(
        f"""
        <style>
        /* Main background & typography */
        .stApp {{
            color: {PALETTE['text']};
            background-color: {PALETTE['background']};
        }}

        /* Header accents */
        h1, h2, h3 {{
            color: #0F172A !important;
            font-weight: 700 !important;
        }}
        
        .civic-badge {{
            display: inline-block;
            background: linear-gradient(135deg, rgba(6, 182, 212, 0.12), rgba(8, 145, 178, 0.18));
            color: {PALETTE['primary_dark']};
            border: 1px solid rgba(6, 182, 212, 0.3);
            border-radius: 9999px;
            padding: 4px 14px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 0.75rem;
            letter-spacing: 0.03em;
        }}

        .kpi-card {{
            background: {PALETTE['card_bg']};
            border: 1px solid {PALETTE['border']};
            border-radius: 12px;
            padding: 18px 20px;
            margin-bottom: 12px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }}
        .kpi-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(6, 182, 212, 0.12);
            border-color: rgba(6, 182, 212, 0.4);
        }}
        .kpi-title {{
            font-size: 0.82rem;
            color: {PALETTE['text_muted']};
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 6px;
        }}
        .kpi-value {{
            font-size: 1.85rem;
            font-weight: 800;
            color: #0F172A;
            line-height: 1.1;
        }}
        .kpi-subtitle {{
            font-size: 0.78rem;
            color: {PALETTE['text_muted']};
            margin-top: 5px;
        }}

        .disclaimer-banner {{
            background-color: #FEF3C7;
            border-left: 4px solid #F59E0B;
            padding: 12px 16px;
            border-radius: 6px;
            color: #92400E;
            font-size: 0.88rem;
            margin: 12px 0 20px 0;
        }}

        .priority-badge-critical {{
            background-color: #FEE2E2;
            color: #B91C1C;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 6px;
        }}
        .priority-badge-high {{
            background-color: #FFEDD5;
            color: #C2410C;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 6px;
        }}
        .priority-badge-medium {{
            background-color: #FEF3C7;
            color: #B45309;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 6px;
        }}
        .priority-badge-low {{
            background-color: #D1FAE5;
            color: #047857;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 6px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_card(title: str, value: str, subtitle: str = ""):
    """Render an HTML KPI card."""
    sub_html = f"<div class='kpi-subtitle'>{subtitle}</div>" if subtitle else ""
    card_html = f"""
    <div class='kpi-card'>
        <div class='kpi-title'>{title}</div>
        <div class='kpi-value'>{value}</div>
        {sub_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def plot_top_locations_bar(ranked_df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Horizontal bar chart of top priority locations."""
    top_df = ranked_df.head(top_n).sort_values("priority_score", ascending=True)
    fig = px.bar(
        top_df,
        x="priority_score",
        y="location_id",
        orientation="h",
        color="priority_score",
        color_continuous_scale=["#67E8F9", "#0891B2", "#0E7490", "#DC2626"],
        title=f"Top {top_n} Priority Action Locations",
        labels={"priority_score": "Priority Score (0-100)", "location_id": "Location ID"},
        hover_data=["zone", "road_type", "total_incidents", "total_complaints", "evidence_summary"],
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=20, r=20, t=40, b=20),
        coloraxis_showscale=False,
        height=380,
    )
    fig.update_xaxes(range=[0, 100], gridcolor="#F1F5F9")
    fig.update_yaxes(categoryorder="total ascending")
    return fig


def plot_severity_donut(incidents_df: pd.DataFrame) -> go.Figure:
    """Donut chart showing incident severity distribution."""
    sev_counts = incidents_df["severity"].value_counts()
    order = ["Critical", "High", "Medium", "Low"]
    labels = [s for s in order if s in sev_counts]
    values = [sev_counts[s] for s in labels]
    colors = [PALETTE["critical"], PALETTE["high"], PALETTE["medium"], PALETTE["low"]]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                marker=dict(colors=colors),
                textinfo="label+percent",
                hoverinfo="label+value+percent",
            )
        ]
    )
    fig.update_layout(
        title="Incident Severity Breakdown",
        showlegend=True,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=10, t=40, b=10),
        height=320,
    )
    return fig


def plot_incident_type_bar(incidents_df: pd.DataFrame) -> go.Figure:
    """Bar chart of incident counts by type."""
    counts = incidents_df["incident_type"].value_counts().reset_index()
    counts.columns = ["incident_type", "count"]
    fig = px.bar(
        counts,
        x="count",
        y="incident_type",
        orientation="h",
        title="Incidents by Category",
        color_discrete_sequence=[PALETTE["primary_dark"]],
        labels={"count": "Incident Count", "incident_type": "Incident Type"},
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=20, r=20, t=40, b=20),
        height=320,
    )
    fig.update_xaxes(gridcolor="#F1F5F9")
    fig.update_yaxes(categoryorder="total ascending")
    return fig


def plot_component_breakdown(row: pd.Series) -> go.Figure:
    """Bar chart breakdown of the 5 component scores for an individual location."""
    labels = [
        "Severity Burden",
        "Unresolved Backlog",
        "Citizen Urgency",
        "Recurrence Volume",
        "Context Vulnerability",
    ]
    values = [
        float(row.get("component_severity", 0)),
        float(row.get("component_unresolved", 0)),
        float(row.get("component_complaints", 0)),
        float(row.get("component_recurrence", 0)),
        float(row.get("component_context", 0)),
    ]
    colors = ["#EF4444", "#F97316", "#F59E0B", "#06B6D4", "#8B5CF6"]

    fig = go.Figure(
        data=[
            go.Bar(
                x=labels,
                y=values,
                marker=dict(color=colors),
                text=[f"{v:.1f}" for v in values],
                textposition="auto",
            )
        ]
    )
    fig.update_layout(
        title=f"MCDA Component Profile for {row.get('location_id', 'Location')}",
        yaxis=dict(range=[0, 100], title="Component Percentile (0-100)", gridcolor="#F1F5F9"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=20, r=20, t=40, b=20),
        height=320,
    )
    return fig


def plot_location_map(ranked_df: pd.DataFrame, highlight_id: Optional[str] = None) -> go.Figure:
    """Scatter map of locations with cyan/red priority gradient."""
    df = ranked_df.copy()
    if highlight_id:
        df["is_selected"] = df["location_id"] == highlight_id
        df["size"] = df["is_selected"].map({True: 18, False: 8})
    else:
        df["size"] = 9

    fig = px.scatter_map(
        df,
        lat="latitude",
        lon="longitude",
        color="priority_score",
        size="size",
        color_continuous_scale=["#67E8F9", "#0891B2", "#EA580C", "#DC2626"],
        range_color=[0, 100],
        hover_name="location_id",
        hover_data={
            "priority_rank": True,
            "priority_score": ":.1f",
            "zone": True,
            "total_incidents": True,
            "total_complaints": True,
            "latitude": False,
            "longitude": False,
            "size": False,
        },
        zoom=10,
        title="Geospatial Priority Heatmap (1,000 Verified City Locations)",
    )
    fig.update_layout(
        map_style="carto-positron",
        margin=dict(l=0, r=0, t=40, b=0),
        height=520,
    )
    return fig


def plot_feature_importance_bar(importance_df: pd.DataFrame, top_n: int = 12) -> go.Figure:
    """Bar chart of model feature importances."""
    top = importance_df.head(top_n).sort_values("importance", ascending=True)
    fig = px.bar(
        top,
        x="importance",
        y="feature",
        orientation="h",
        color="importance",
        color_continuous_scale=["#A5F3FC", "#06B6D4", "#0891B2"],
        title=f"Top {top_n} Predictive Feature Importances",
        labels={"importance": "Importance Metric", "feature": "Engineered Feature"},
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        coloraxis_showscale=False,
        margin=dict(l=20, r=20, t=40, b=20),
        height=380,
    )
    fig.update_xaxes(gridcolor="#F1F5F9")
    return fig
