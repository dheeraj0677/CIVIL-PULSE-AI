"""Priority scoring and multi-criteria decision analysis (MCDA) engine.

Computes explainable, deterministic 0-100 priority scores and ranking
for city locations based on severity burden, backlogs, public urgency,
recurrence volume, and contextual vulnerability.
"""

from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from src.config import (
    DEFAULT_PRIORITY_WEIGHTS,
    PEDESTRIAN_ACTIVITY_WEIGHT,
    ROAD_CONDITION_VULNERABILITY,
)


def normalize_weights(custom_weights: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    """Validate and normalize MCDA component weights so they sum strictly to 1.0.

    Args:
        custom_weights: Optional dictionary of weights.

    Returns:
        Dictionary of normalized weights.

    Raises:
        ValueError: If weights are missing, negative, or sum to zero.
    """
    weights = (custom_weights or DEFAULT_PRIORITY_WEIGHTS).copy()
    expected_keys = set(DEFAULT_PRIORITY_WEIGHTS.keys())
    missing = expected_keys - set(weights.keys())
    if missing:
        raise ValueError(f"Missing required priority weight keys: {missing}")

    for k, v in weights.items():
        if v < 0:
            raise ValueError(f"Weight '{k}' must be non-negative, got {v}")

    total = sum(weights.values())
    if total <= 0:
        raise ValueError("Sum of weights must be strictly positive")

    return {k: v / total for k, v in weights.items()}


def compute_component_scores(location_features: pd.DataFrame) -> pd.DataFrame:
    """Compute individual 0-100 sub-scores for each evaluation dimension.

    Dimensions:
    1. severity_injury: Severity burden and casualties
    2. unresolved_workload: Unresolved incidents and active citizen complaints
    3. complaint_urgency: Total public complaints and high-priority complaints
    4. recurrence_volume: Total historical incidents and repeat issue volume
    5. location_vulnerability: Road condition, pedestrian density, schools, hospitals

    Args:
        location_features: Unified DataFrame from build_location_features().

    Returns:
        DataFrame with 5 component score columns (0.0 to 100.0).
    """
    df = location_features.copy()
    n = len(df)

    def to_percentile(s: pd.Series) -> pd.Series:
        if n <= 1:
            return pd.Series([50.0] * n, index=s.index)
        if s.max() == s.min():
            return pd.Series([50.0] * n, index=s.index)
        # Percentile rank (1/N to 1.0) scaled to 0-100
        return (s.rank(pct=True, method="average") * 100.0).round(2)

    # 1. Severity & Injury Burden
    sev_burden = df.get("weighted_severity_burden", pd.Series(0, index=df.index))
    injuries = df.get("total_injuries", pd.Series(0, index=df.index))
    raw_sev = sev_burden * 1.0 + injuries * 2.0
    c_severity = to_percentile(raw_sev)

    # 2. Unresolved Workload
    unres_inc = df.get("unresolved_incidents", pd.Series(0, index=df.index))
    active_comp = df.get("active_complaints", pd.Series(0, index=df.index))
    raw_unres = unres_inc * 2.0 + active_comp * 1.5
    c_unresolved = to_percentile(raw_unres)

    # 3. Citizen Complaint Urgency
    tot_comp = df.get("total_complaints", pd.Series(0, index=df.index))
    high_comp = df.get("high_priority_complaints", pd.Series(0, index=df.index))
    raw_comp = tot_comp * 1.0 + high_comp * 2.0
    c_complaints = to_percentile(raw_comp)

    # 4. Recurrence Volume
    tot_inc = df.get("total_incidents", pd.Series(0, index=df.index))
    c_recurrence = to_percentile(tot_inc * 1.0)

    # 5. Location Vulnerability
    rc_ord = df.get("road_condition", pd.Series("Good", index=df.index)).map(
        ROAD_CONDITION_VULNERABILITY
    ).fillna(1)
    ped_ord = df.get("pedestrian_activity", pd.Series("Low", index=df.index)).map(
        PEDESTRIAN_ACTIVITY_WEIGHT
    ).fillna(1)
    pop_den = df.get("population_density_per_km2", pd.Series(1000, index=df.index))
    pop_den_min = pop_den.min()
    pop_den_range = pop_den.max() - pop_den_min
    pop_norm = (pop_den - pop_den_min) / pop_den_range if pop_den_range > 0 else 0

    school = df.get("near_school", pd.Series(0, index=df.index))
    hosp = df.get("near_hospital", pd.Series(0, index=df.index))

    raw_ctx = (
        rc_ord * 2.0
        + ped_ord * 1.5
        + school * 2.0
        + hosp * 2.0
        + pop_norm * 3.0
    )
    c_context = to_percentile(raw_ctx)

    scores_df = pd.DataFrame(
        {
            "component_severity": c_severity,
            "component_unresolved": c_unresolved,
            "component_complaints": c_complaints,
            "component_recurrence": c_recurrence,
            "component_context": c_context,
        },
        index=df.index,
    )
    return scores_df


def generate_evidence_summary(row: pd.Series) -> str:
    """Generate interpretable narrative reasoning for a location's priority.

    Args:
        row: Series containing location features and component scores.

    Returns:
        Clear human-readable justification string.
    """
    comp_map = {
        "Severity Burden": (row["component_severity"], f"weighted burden {int(row.get('weighted_severity_burden', 0))} pts, {int(row.get('total_injuries', 0))} casualties"),
        "Unresolved Backlog": (row["component_unresolved"], f"{int(row.get('unresolved_incidents', 0))} open incidents, {int(row.get('active_complaints', 0))} active complaints"),
        "Public Urgency": (row["component_complaints"], f"{int(row.get('total_complaints', 0))} citizen complaints ({int(row.get('high_priority_complaints', 0))} high-priority)"),
        "Recurrence Volume": (row["component_recurrence"], f"{int(row.get('total_incidents', 0))} total incidents"),
        "Context Vulnerability": (row["component_context"], f"{row.get('road_condition', 'Fair')} road, {row.get('pedestrian_activity', 'Med')} pedestrian density"),
    }

    # Sort components by score descending
    sorted_comps = sorted(comp_map.items(), key=lambda item: item[1][0], reverse=True)
    top1_name, (top1_val, top1_desc) = sorted_comps[0]
    top2_name, (top2_val, top2_desc) = sorted_comps[1]

    notes = []
    if row.get("near_school", 0) == 1:
        notes.append("adjacent to school")
    if row.get("near_hospital", 0) == 1:
        notes.append("adjacent to hospital")
    infra_note = f" Sensitive zone: {', '.join(notes)}." if notes else ""

    summary = (
        f"Primary driver: {top1_name} ({top1_desc}, score {top1_val:.1f}). "
        f"Secondary driver: {top2_name} ({top2_desc}, score {top2_val:.1f})."
        f"{infra_note}"
    )
    return summary


def rank_locations(
    location_features: pd.DataFrame,
    weights: Optional[Dict[str, float]] = None,
) -> pd.DataFrame:
    """Compute composite priority scores and deterministic ranking for all locations.

    Args:
        location_features: Unified DataFrame from build_location_features().
        weights: Optional custom weights mapping.

    Returns:
        DataFrame sorted by priority_rank, containing priority_score,
        component scores, rank, and evidence summary.
    """
    w = normalize_weights(weights)
    components = compute_component_scores(location_features)

    composite = (
        w["severity_injury"] * components["component_severity"]
        + w["unresolved_workload"] * components["component_unresolved"]
        + w["complaint_urgency"] * components["component_complaints"]
        + w["recurrence_volume"] * components["component_recurrence"]
        + w["location_vulnerability"] * components["component_context"]
    ).round(2)

    df_out = location_features.copy()
    for col in components.columns:
        df_out[col] = components[col]
    df_out["priority_score"] = composite

    # Evidence narratives
    df_out["evidence_summary"] = df_out.apply(generate_evidence_summary, axis=1)

    # Deterministic sort: priority_score DESC, location_id ASC (tie-breaker)
    df_out = df_out.sort_values(
        by=["priority_score", "location_id"],
        ascending=[False, True],
    ).reset_index(drop=True)

    df_out["priority_rank"] = np.arange(1, len(df_out) + 1)

    return df_out
