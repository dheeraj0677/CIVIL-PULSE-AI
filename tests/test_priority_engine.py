"""Tests for src.priority_engine."""

import pytest
import pandas as pd
from src.data_loader import load_all_data
from src.feature_engineering import build_location_features
from src.priority_engine import (
    normalize_weights,
    compute_component_scores,
    rank_locations,
)


def test_normalize_weights():
    """Verify weight validation and normalization."""
    # Default weights sum to 1.0
    w_def = normalize_weights()
    assert pytest.approx(sum(w_def.values())) == 1.0

    # Custom weights normalization
    custom = {
        "severity_injury": 10,
        "unresolved_workload": 10,
        "complaint_urgency": 10,
        "recurrence_volume": 10,
        "location_vulnerability": 10,
    }
    w_norm = normalize_weights(custom)
    for v in w_norm.values():
        assert pytest.approx(v) == 0.2

    # Negative weights raise
    with pytest.raises(ValueError, match="must be non-negative"):
        bad = custom.copy()
        bad["severity_injury"] = -1
        normalize_weights(bad)

    # Missing keys raise
    with pytest.raises(ValueError, match="Missing required priority weight keys"):
        normalize_weights({"severity_injury": 1.0})


def test_rank_locations_bounds_and_determinism():
    """Verify 0-100 bounds, complete ranking, and deterministic outputs."""
    loc, inc, comp = load_all_data()
    features = build_location_features(loc, inc, comp)

    ranked1 = rank_locations(features)
    ranked2 = rank_locations(features)

    # Exactly 1000 locations
    assert len(ranked1) == 1000
    assert ranked1["priority_rank"].iloc[0] == 1
    assert ranked1["priority_rank"].iloc[-1] == 1000

    # Strict determinism
    pd.testing.assert_frame_equal(ranked1, ranked2)

    # Score bounds [0, 100]
    assert (ranked1["priority_score"] >= 0.0).all()
    assert (ranked1["priority_score"] <= 100.0).all()

    # Component score bounds
    for col in [
        "component_severity",
        "component_unresolved",
        "component_complaints",
        "component_recurrence",
        "component_context",
    ]:
        assert (ranked1[col] >= 0.0).all()
        assert (ranked1[col] <= 100.0).all()

    # Evidence summary is populated
    assert ranked1["evidence_summary"].str.len().min() > 10
    assert "Primary driver:" in ranked1["evidence_summary"].iloc[0]


def test_tiebreaking():
    """Verify deterministic tiebreaker uses location_id ascending."""
    df = pd.DataFrame([
        {
            "location_id": "L0002",
            "weighted_severity_burden": 10,
            "total_injuries": 0,
            "unresolved_incidents": 2,
            "active_complaints": 2,
            "total_complaints": 5,
            "high_priority_complaints": 1,
            "total_incidents": 5,
            "road_condition": "Good",
            "pedestrian_activity": "Low",
            "population_density_per_km2": 5000,
            "near_school": 0,
            "near_hospital": 0,
        },
        {
            "location_id": "L0001",
            "weighted_severity_burden": 10,
            "total_injuries": 0,
            "unresolved_incidents": 2,
            "active_complaints": 2,
            "total_complaints": 5,
            "high_priority_complaints": 1,
            "total_incidents": 5,
            "road_condition": "Good",
            "pedestrian_activity": "Low",
            "population_density_per_km2": 5000,
            "near_school": 0,
            "near_hospital": 0,
        },
    ])

    ranked = rank_locations(df)
    # Both have identical attributes -> equal scores, but L0001 should be rank 1 due to tiebreaker
    assert ranked.iloc[0]["location_id"] == "L0001"
    assert ranked.iloc[1]["location_id"] == "L0002"
