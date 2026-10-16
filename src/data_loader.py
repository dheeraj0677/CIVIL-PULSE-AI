"""Data loading and schema validation module for CivicPulse AI.

Ensures strict column validation, integrity checks, type casting,
and foreign-key verification without altering the underlying source files.
"""

from pathlib import Path
from typing import Optional, Tuple
import pandas as pd

from src.config import (
    COMPLAINTS_COLUMNS,
    COMPLAINTS_PATH,
    INCIDENTS_COLUMNS,
    INCIDENTS_PATH,
    LOCATIONS_COLUMNS,
    LOCATIONS_PATH,
    VALID_INCIDENT_TYPES,
    VALID_REPORTED_BY,
    VALID_SEVERITIES,
)


def load_locations(path: Path = LOCATIONS_PATH) -> pd.DataFrame:
    """Load and validate the locations dataset.

    Args:
        path: Path to locations.csv

    Returns:
        Validated DataFrame of locations.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If columns are missing, primary keys are duplicated,
                    or values are out of bounds.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Locations file not found at: {path}")

    df = pd.read_csv(path)

    # Validate column presence
    missing_cols = set(LOCATIONS_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Locations file is missing required columns: {missing_cols}")

    # Reorder to canonical schema
    df = df[LOCATIONS_COLUMNS].copy()

    # Null checks
    null_counts = df.isnull().sum()
    if null_counts.any():
        cols_with_nulls = null_counts[null_counts > 0].to_dict()
        raise ValueError(f"Null values detected in locations: {cols_with_nulls}")

    # Primary key uniqueness
    if df["location_id"].duplicated().any():
        dups = df["location_id"][df["location_id"].duplicated()].tolist()
        raise ValueError(f"Duplicate location_id values found: {dups[:5]}")

    # Boundary & type validations
    if not ((-90 <= df["latitude"]) & (df["latitude"] <= 90)).all():
        raise ValueError("Latitude out of range [-90, 90]")
    if not ((-180 <= df["longitude"]) & (df["longitude"] <= 180)).all():
        raise ValueError("Longitude out of range [-180, 180]")
    if (df["population_density_per_km2"] < 0).any():
        raise ValueError("Population density cannot be negative")
    if not set(df["near_school"].unique()).issubset({0, 1}):
        raise ValueError("near_school must be binary 0 or 1")
    if not set(df["near_hospital"].unique()).issubset({0, 1}):
        raise ValueError("near_hospital must be binary 0 or 1")

    return df


def load_incidents(
    path: Path = INCIDENTS_PATH,
    valid_location_ids: Optional[set] = None,
) -> pd.DataFrame:
    """Load and validate the incidents dataset.

    Args:
        path: Path to incidents.csv
        valid_location_ids: Optional set of known location_id values for FK checks.

    Returns:
        Validated DataFrame of incidents with parsed timestamps.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If schema or relational constraints are violated.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Incidents file not found at: {path}")

    df = pd.read_csv(path)

    missing_cols = set(INCIDENTS_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Incidents file is missing required columns: {missing_cols}")

    df = df[INCIDENTS_COLUMNS].copy()

    null_counts = df.isnull().sum()
    if null_counts.any():
        cols_with_nulls = null_counts[null_counts > 0].to_dict()
        raise ValueError(f"Null values detected in incidents: {cols_with_nulls}")

    if df["incident_id"].duplicated().any():
        dups = df["incident_id"][df["incident_id"].duplicated()].tolist()
        raise ValueError(f"Duplicate incident_id values found: {dups[:5]}")

    # FK validation
    if valid_location_ids is not None:
        orphans = set(df["location_id"]) - valid_location_ids
        if orphans:
            raise ValueError(f"Found orphan location_ids in incidents: {list(orphans)[:5]}")

    # Domain validations
    invalid_types = set(df["incident_type"].unique()) - set(VALID_INCIDENT_TYPES)
    if invalid_types:
        raise ValueError(f"Unexpected incident_type values: {invalid_types}")

    invalid_severities = set(df["severity"].unique()) - set(VALID_SEVERITIES)
    if invalid_severities:
        raise ValueError(f"Unexpected severity values: {invalid_severities}")

    invalid_reporters = set(df["reported_by"].unique()) - set(VALID_REPORTED_BY)
    if invalid_reporters:
        raise ValueError(f"Unexpected reported_by values: {invalid_reporters}")

    if not set(df["resolved"].unique()).issubset({0, 1}):
        raise ValueError("resolved must be binary 0 or 1")
    if (df["injuries"] < 0).any():
        raise ValueError("Injuries count cannot be negative")
    if (df["resolution_hours"] <= 0).any():
        raise ValueError("resolution_hours must be strictly positive")

    # Parse timestamps
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    return df


def load_complaints(
    path: Path = COMPLAINTS_PATH,
    valid_location_ids: Optional[set] = None,
) -> pd.DataFrame:
    """Load and validate the public complaints dataset.

    Args:
        path: Path to public_complaints.csv
        valid_location_ids: Optional set of known location_id values for FK checks.

    Returns:
        Validated DataFrame of complaints with parsed created_at.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If schema or relational constraints are violated.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Complaints file not found at: {path}")

    df = pd.read_csv(path)

    missing_cols = set(COMPLAINTS_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Complaints file is missing required columns: {missing_cols}")

    df = df[COMPLAINTS_COLUMNS].copy()

    null_counts = df.isnull().sum()
    if null_counts.any():
        cols_with_nulls = null_counts[null_counts > 0].to_dict()
        raise ValueError(f"Null values detected in complaints: {cols_with_nulls}")

    if df["complaint_id"].duplicated().any():
        dups = df["complaint_id"][df["complaint_id"].duplicated()].tolist()
        raise ValueError(f"Duplicate complaint_id values found: {dups[:5]}")

    if valid_location_ids is not None:
        orphans = set(df["location_id"]) - valid_location_ids
        if orphans:
            raise ValueError(f"Found orphan location_ids in complaints: {list(orphans)[:5]}")

    if (df["days_to_resolution"] < 0).any():
        raise ValueError("days_to_resolution cannot be negative")

    df["created_at"] = pd.to_datetime(df["created_at"])

    return df


def load_all_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Convenience function to load and cross-validate all three datasets.

    Returns:
        Tuple of (locations_df, incidents_df, complaints_df).
    """
    locations = load_locations()
    valid_loc_ids = set(locations["location_id"])
    incidents = load_incidents(valid_location_ids=valid_loc_ids)
    complaints = load_complaints(valid_location_ids=valid_loc_ids)
    return locations, incidents, complaints
