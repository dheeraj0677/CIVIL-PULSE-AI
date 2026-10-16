"""Tests for src.feature_engineering."""

import pandas as pd
import pytest
from src.data_loader import load_all_data
from src.feature_engineering import (
    aggregate_incidents,
    aggregate_complaints,
    build_location_features,
)


def test_aggregation_and_reconciliation():
    """Verify aggregation on full actual dataset preserves totals."""
    loc, inc, comp = load_all_data()

    loc_features = build_location_features(loc, inc, comp)

    # Must preserve exactly 1000 locations
    assert len(loc_features) == 1000
    assert loc_features["location_id"].nunique() == 1000

    # Exact reconciliation against raw inputs
    assert loc_features["total_incidents"].sum() == 10000
    assert loc_features["total_complaints"].sum() == 8000
    assert loc_features["total_injuries"].sum() == inc["injuries"].sum()
    assert (
        loc_features["resolved_incidents"].sum()
        + loc_features["unresolved_incidents"].sum()
        == 10000
    )


def test_zero_event_handling():
    """Verify behavior when a location has zero incidents and zero complaints."""
    # Synthetic 2-location dataset
    loc = pd.DataFrame([
        {
            "location_id": "L0001",
            "zone": "ZONE_1",
            "road_type": "Local",
            "road_condition": "Good",
            "population_density_per_km2": 5000,
            "near_school": 0,
            "near_hospital": 0,
            "pedestrian_activity": "Low",
            "latitude": 16.5,
            "longitude": 80.5,
        },
        {
            "location_id": "L0002",
            "zone": "ZONE_1",
            "road_type": "Arterial",
            "road_condition": "Poor",
            "population_density_per_km2": 12000,
            "near_school": 1,
            "near_hospital": 0,
            "pedestrian_activity": "High",
            "latitude": 16.6,
            "longitude": 80.6,
        },
    ])

    # Only L0001 has an incident and complaint; L0002 has none
    inc = pd.DataFrame([
        {
            "incident_id": "I001",
            "location_id": "L0001",
            "timestamp": "2025-01-01 10:00:00",
            "incident_type": "Pothole",
            "severity": "High",
            "injuries": 1,
            "reported_by": "Citizen",
            "resolved": 1,
            "resolution_hours": 12.0,
        }
    ])

    comp = pd.DataFrame([
        {
            "complaint_id": "C001",
            "location_id": "L0001",
            "created_at": "2025-01-01 10:00:00",
            "category": "Road damage",
            "priority_reported": "High",
            "status": "Open",
            "days_to_resolution": 2.0,
        }
    ])

    features = build_location_features(loc, inc, comp)
    assert len(features) == 2

    # L0002 should have 0s, not NaNs
    l2 = features[features["location_id"] == "L0002"].iloc[0]
    assert l2["total_incidents"] == 0
    assert l2["total_complaints"] == 0
    assert l2["total_injuries"] == 0
    assert l2["weighted_severity_burden"] == 0
    assert not pd.isna(l2["avg_resolution_hours"])
