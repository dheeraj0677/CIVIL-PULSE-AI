"""Feature engineering module for CivicPulse AI.

Aggregates fine-grained incidents and public complaints up to the location level,
reconciling counts and producing a single structured location feature table.
"""

from typing import Optional
import numpy as np
import pandas as pd

from src.config import (
    ACTIVE_COMPLAINT_STATUSES,
    RESOLVED_COMPLAINT_STATUSES,
    SEVERITY_WEIGHTS,
    VALID_INCIDENT_TYPES,
)


def aggregate_incidents(incidents_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate incident events by location_id.

    Calculates incident volumes, resolution status, severity burdens,
    injuries, average resolution durations, and incident type breakdowns.

    Args:
        incidents_df: Validated incidents DataFrame.

    Returns:
        DataFrame indexed by location_id with incident aggregate metrics.
    """
    if incidents_df.empty:
        cols = [
            "total_incidents", "resolved_incidents", "unresolved_incidents",
            "resolution_rate", "severity_critical_count", "severity_high_count",
            "severity_medium_count", "severity_low_count", "weighted_severity_burden",
            "total_injuries", "avg_resolution_hours",
        ]
        return pd.DataFrame(columns=cols).rename_axis("location_id")

    # Map numerical severity weight
    inc_copy = incidents_df.copy()
    inc_copy["severity_weight"] = inc_copy["severity"].map(SEVERITY_WEIGHTS).fillna(1)

    # Base counts and sums
    grouped = inc_copy.groupby("location_id")
    agg_dict = {
        "incident_id": "count",
        "resolved": ["sum", lambda s: (s == 0).sum()],
        "injuries": "sum",
        "severity_weight": "sum",
    }
    base_agg = grouped.agg(agg_dict)
    base_agg.columns = [
        "total_incidents",
        "resolved_incidents",
        "unresolved_incidents",
        "total_injuries",
        "weighted_severity_burden",
    ]

    base_agg["resolution_rate"] = np.where(
        base_agg["total_incidents"] > 0,
        base_agg["resolved_incidents"] / base_agg["total_incidents"],
        0.0,
    )

    # Average resolution hours for resolved incidents only
    resolved_only = inc_copy[inc_copy["resolved"] == 1]
    avg_res = (
        resolved_only.groupby("location_id")["resolution_hours"]
        .mean()
        .rename("avg_resolution_hours")
    )
    base_agg = base_agg.join(avg_res, how="left")
    base_agg["avg_resolution_hours"] = base_agg["avg_resolution_hours"].fillna(0.0)

    # Severity level counts
    sev_piv = (
        pd.crosstab(inc_copy["location_id"], inc_copy["severity"])
        .rename(columns=lambda c: f"severity_{c.lower()}_count")
    )
    for s in ["critical", "high", "medium", "low"]:
        col = f"severity_{s}_count"
        if col not in sev_piv.columns:
            sev_piv[col] = 0
    base_agg = base_agg.join(sev_piv, how="left")

    # Incident type counts
    type_piv = (
        pd.crosstab(inc_copy["location_id"], inc_copy["incident_type"])
        .rename(columns=lambda c: f"incident_{c.lower().replace(' ', '_')}")
    )
    for it in VALID_INCIDENT_TYPES:
        cname = f"incident_{it.lower().replace(' ', '_')}"
        if cname not in type_piv.columns:
            type_piv[cname] = 0
    base_agg = base_agg.join(type_piv, how="left")

    return base_agg.fillna(0)


def aggregate_complaints(complaints_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate public citizen complaints by location_id.

    Calculates complaint volumes, active vs resolved backlogs,
    priority distributions, and turnaround times.

    Args:
        complaints_df: Validated complaints DataFrame.

    Returns:
        DataFrame indexed by location_id with complaint aggregate metrics.
    """
    if complaints_df.empty:
        cols = [
            "total_complaints", "active_complaints", "resolved_complaints",
            "high_priority_complaints", "normal_priority_complaints",
            "low_priority_complaints", "avg_complaint_resolution_days",
        ]
        return pd.DataFrame(columns=cols).rename_axis("location_id")

    comp = complaints_df.copy()
    grouped = comp.groupby("location_id")

    # Total complaints
    total = grouped["complaint_id"].count().rename("total_complaints")

    # Active vs resolved complaints
    active = (
        comp[comp["status"].isin(ACTIVE_COMPLAINT_STATUSES)]
        .groupby("location_id")["complaint_id"]
        .count()
        .rename("active_complaints")
    )
    resolved = (
        comp[comp["status"].isin(RESOLVED_COMPLAINT_STATUSES)]
        .groupby("location_id")["complaint_id"]
        .count()
        .rename("resolved_complaints")
    )

    # Priority counts
    prio_piv = (
        pd.crosstab(comp["location_id"], comp["priority_reported"])
        .rename(columns=lambda c: f"{c.lower()}_priority_complaints")
    )
    for p in ["high", "normal", "low"]:
        col = f"{p}_priority_complaints"
        if col not in prio_piv.columns:
            prio_piv[col] = 0

    # Mean days to resolution
    avg_days = (
        grouped["days_to_resolution"]
        .mean()
        .rename("avg_complaint_resolution_days")
    )

    # Category counts
    cat_piv = (
        pd.crosstab(comp["location_id"], comp["category"])
        .rename(columns=lambda c: f"complaint_{c.lower().replace(' ', '_')}")
    )

    agg = pd.concat([total, active, resolved, avg_days], axis=1)
    agg = agg.join(prio_piv, how="left").join(cat_piv, how="left")
    return agg.fillna(0)


def build_location_features(
    locations_df: pd.DataFrame,
    incidents_df: pd.DataFrame,
    complaints_df: pd.DataFrame,
) -> pd.DataFrame:
    """Build unified location-level feature dataset.

    Performs left-joins from the master location table to aggregate metrics,
    guaranteeing no row multiplication or dropped locations.

    Args:
        locations_df: Master locations DataFrame.
        incidents_df: Master incidents DataFrame.
        complaints_df: Master complaints DataFrame.

    Returns:
        Complete location feature DataFrame with 1 row per location_id.

    Raises:
        ValueError: If row counts or reconciled totals do not match.
    """
    loc_count = len(locations_df)
    inc_agg = aggregate_incidents(incidents_df)
    comp_agg = aggregate_complaints(complaints_df)

    merged = locations_df.copy()
    merged = merged.merge(inc_agg, on="location_id", how="left")
    merged = merged.merge(comp_agg, on="location_id", how="left")

    if len(merged) != loc_count:
        raise ValueError(
            f"Row count mismatch after join: expected {loc_count}, got {len(merged)}"
        )

    # Fill NA values for any locations that had zero events
    numeric_cols = merged.select_dtypes(include=[np.number]).columns
    merged[numeric_cols] = merged[numeric_cols].fillna(0)

    # Verify reconciliation with input data
    if not incidents_df.empty:
        sum_inc = int(merged["total_incidents"].sum())
        expected_inc = len(incidents_df)
        if sum_inc != expected_inc:
            raise ValueError(
                f"Incident count mismatch: aggregated {sum_inc} vs expected {expected_inc}"
            )

        sum_inj = int(merged["total_injuries"].sum())
        expected_inj = int(incidents_df["injuries"].sum())
        if sum_inj != expected_inj:
            raise ValueError(
                f"Injury count mismatch: aggregated {sum_inj} vs expected {expected_inj}"
            )

    if not complaints_df.empty:
        sum_comp = int(merged["total_complaints"].sum())
        expected_comp = len(complaints_df)
        if sum_comp != expected_comp:
            raise ValueError(
                f"Complaint count mismatch: aggregated {sum_comp} vs expected {expected_comp}"
            )

    return merged
