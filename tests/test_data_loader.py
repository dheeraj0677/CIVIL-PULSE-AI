"""Tests for src.data_loader."""

from pathlib import Path
import pytest
import pandas as pd
from src.data_loader import (
    load_locations,
    load_incidents,
    load_complaints,
    load_all_data,
)


def test_load_locations_success():
    """Verify loading the actual locations dataset."""
    df = load_locations()
    assert len(df) == 1000
    assert df["location_id"].nunique() == 1000
    assert not df.isnull().any().any()
    assert "latitude" in df.columns
    assert "longitude" in df.columns


def test_load_incidents_success():
    """Verify loading the actual incidents dataset with FK check."""
    locations = load_locations()
    valid_ids = set(locations["location_id"])
    df = load_incidents(valid_location_ids=valid_ids)
    assert len(df) == 10000
    assert df["incident_id"].nunique() == 10000
    assert not df.isnull().any().any()
    assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])


def test_load_complaints_success():
    """Verify loading the actual complaints dataset with FK check."""
    locations = load_locations()
    valid_ids = set(locations["location_id"])
    df = load_complaints(valid_location_ids=valid_ids)
    assert len(df) == 8000
    assert df["complaint_id"].nunique() == 8000
    assert not df.isnull().any().any()
    assert pd.api.types.is_datetime64_any_dtype(df["created_at"])


def test_load_all_data():
    """Verify load_all_data convenience helper."""
    locs, incs, comps = load_all_data()
    assert len(locs) == 1000
    assert len(incs) == 10000
    assert len(comps) == 8000


def test_missing_file_raises():
    """Verify FileNotFoundError on non-existent path."""
    with pytest.raises(FileNotFoundError):
        load_locations(Path("non_existent_file.csv"))


def test_missing_column_raises(tmp_path):
    """Verify ValueError when required column is missing."""
    bad_csv = tmp_path / "bad_locations.csv"
    bad_csv.write_text("location_id,zone\nL0001,ZONE_1\n")
    with pytest.raises(ValueError, match="missing required columns"):
        load_locations(bad_csv)


def test_duplicate_pk_raises(tmp_path):
    """Verify ValueError on duplicate primary keys."""
    content = (
        "location_id,zone,road_type,road_condition,population_density_per_km2,"
        "near_school,near_hospital,pedestrian_activity,latitude,longitude\n"
        "L0001,ZONE_1,Local,Good,1000,0,0,Low,16.5,80.5\n"
        "L0001,ZONE_1,Local,Good,1000,0,0,Low,16.5,80.5\n"
    )
    bad_csv = tmp_path / "dup_locations.csv"
    bad_csv.write_text(content)
    with pytest.raises(ValueError, match="Duplicate location_id"):
        load_locations(bad_csv)


def test_orphan_fk_raises(tmp_path):
    """Verify ValueError when foreign key points to non-existent location."""
    content = (
        "incident_id,location_id,timestamp,incident_type,severity,injuries,"
        "reported_by,resolved,resolution_hours\n"
        "I001,UNKNOWN_LOC,2025-01-01 10:00:00,Pothole,Low,0,Citizen,1,10.0\n"
    )
    bad_csv = tmp_path / "orphan_incidents.csv"
    bad_csv.write_text(content)
    with pytest.raises(ValueError, match="orphan location_ids"):
        load_incidents(bad_csv, valid_location_ids={"L0001"})
