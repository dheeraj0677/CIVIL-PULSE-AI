"""Tests for src.modeling."""

import numpy as np
import pandas as pd
import pytest
from src.data_loader import load_incidents, load_locations
from src.modeling import (
    ALL_FEATURES,
    create_pipeline,
    evaluate_predictions,
    get_chronological_splits,
    load_trained_model,
    prepare_dataset,
)


def test_prepare_dataset_no_leakage():
    """Verify feature matrix does not leak target, resolution flag, or IDs."""
    loc = load_locations()
    inc = load_incidents()

    X, y, full_df = prepare_dataset(inc, loc)

    # Only resolved incidents used
    assert len(X) == 7126
    assert len(y) == 7126

    # Leakage checks
    forbidden = ["resolution_hours", "resolved", "incident_id", "location_id", "timestamp"]
    for col in forbidden:
        assert col not in X.columns, f"Leakage column found in X: {col}"

    assert list(X.columns) == ALL_FEATURES


def test_chronological_split_ordering():
    """Verify temporal partitions do not overlap and maintain chronological order."""
    loc = load_locations()
    inc = load_incidents()

    X, y, full_df = prepare_dataset(inc, loc)
    splits = get_chronological_splits(X, y, full_df)

    assert len(splits["X_train"]) == 4988  # 70% of 7126
    assert len(splits["X_val"]) == 1069    # 15% of 7126
    assert len(splits["X_test"]) == 1069   # 15% of 7126 (4988 + 1069 + 1069 == 7126)

    train_max_ts = splits["train_range"][1]
    val_min_ts = splits["val_range"][0]
    val_max_ts = splits["val_range"][1]
    test_min_ts = splits["test_range"][0]

    assert train_max_ts <= val_min_ts
    assert val_max_ts <= test_min_ts


def test_pipeline_prediction_and_evaluation():
    """Verify pipeline trains, predicts finite values, and produces metric dictionary."""
    loc = load_locations()
    inc = load_incidents()

    X, y, full_df = prepare_dataset(inc, loc)
    splits = get_chronological_splits(X, y, full_df)

    pipe = create_pipeline("baseline")
    pipe.fit(splits["X_train"], splits["y_train"])
    preds = pipe.predict(splits["X_val"])

    assert len(preds) == len(splits["X_val"])
    assert np.isfinite(preds).all()

    metrics = evaluate_predictions(splits["y_val"], preds)
    assert "mae" in metrics
    assert "rmse" in metrics
    assert "r2" in metrics
    assert metrics["mae"] > 0


def test_load_trained_model_artifacts():
    """Verify saved artifacts load cleanly and can produce predictions."""
    pipeline, metadata, importance = load_trained_model()
    assert pipeline is not None
    assert metadata is not None
    assert importance is not None
    assert "test_metrics" in metadata
    assert len(importance) > 0

    # Test single-row inference
    sample_input = pd.DataFrame([{
        "incident_type": "Pothole",
        "severity": "High",
        "reported_by": "Citizen",
        "zone": "ZONE_01",
        "road_type": "Local",
        "road_condition": "Poor",
        "pedestrian_activity": "Medium",
        "injuries": 0,
        "near_school": 1,
        "near_hospital": 0,
        "population_density_per_km2": 8000,
        "hour": 14,
        "day_of_week": 2,
        "month": 5,
    }])
    pred = pipeline.predict(sample_input)
    assert len(pred) == 1
    assert np.isfinite(pred[0])
    assert pred[0] > 0

