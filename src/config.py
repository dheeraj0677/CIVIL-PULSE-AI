"""Configuration and constants for CivicPulse AI.

Provides centralized paths, schemas, weight defaults, and styling tokens.
"""

from pathlib import Path
from typing import Dict, List, Set

# Base directory paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "03_smart_city_where_fix_first"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
REPORTS_DIR = PROJECT_ROOT / "reports"

# Ensure runtime directories exist
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Dataset file paths
LOCATIONS_PATH = DATA_DIR / "locations.csv"
INCIDENTS_PATH = DATA_DIR / "incidents.csv"
COMPLAINTS_PATH = DATA_DIR / "public_complaints.csv"
README_PATH = DATA_DIR / "README.txt"

# Model artifact file paths
MODEL_PIPELINE_PATH = ARTIFACTS_DIR / "model_pipeline.pkl"
MODEL_METADATA_PATH = ARTIFACTS_DIR / "model_metadata.json"
FEATURE_IMPORTANCE_PATH = ARTIFACTS_DIR / "feature_importance.csv"

# Global reproducibility seed
RANDOM_SEED = 42

# Expected column schemas
LOCATIONS_COLUMNS: List[str] = [
    "location_id",
    "zone",
    "road_type",
    "road_condition",
    "population_density_per_km2",
    "near_school",
    "near_hospital",
    "pedestrian_activity",
    "latitude",
    "longitude",
]

INCIDENTS_COLUMNS: List[str] = [
    "incident_id",
    "location_id",
    "timestamp",
    "incident_type",
    "severity",
    "injuries",
    "reported_by",
    "resolved",
    "resolution_hours",
]

COMPLAINTS_COLUMNS: List[str] = [
    "complaint_id",
    "location_id",
    "created_at",
    "category",
    "priority_reported",
    "status",
    "days_to_resolution",
]

# Categorical domain definitions
VALID_SEVERITIES: List[str] = ["Low", "Medium", "High", "Critical"]
VALID_INCIDENT_TYPES: List[str] = [
    "Blocked drain",
    "Collision",
    "Flooding",
    "Pothole",
    "Signal failure",
    "Streetlight outage",
]
VALID_REPORTED_BY: List[str] = ["Authority", "Citizen", "Police", "Sensor"]
VALID_ROAD_TYPES: List[str] = ["Arterial", "Collector", "Highway", "Local", "Residential"]
VALID_ROAD_CONDITIONS: List[str] = ["Critical", "Poor", "Fair", "Good"]
VALID_PEDESTRIAN_ACTIVITY: List[str] = ["Low", "Medium", "High"]

ACTIVE_COMPLAINT_STATUSES: Set[str] = {"Open", "Assigned", "In progress"}
RESOLVED_COMPLAINT_STATUSES: Set[str] = {"Resolved", "Closed"}

# Scoring weights & ordinal mappings
SEVERITY_WEIGHTS: Dict[str, int] = {
    "Critical": 4,
    "High": 3,
    "Medium": 2,
    "Low": 1,
}

ROAD_CONDITION_VULNERABILITY: Dict[str, int] = {
    "Critical": 4,
    "Poor": 3,
    "Fair": 2,
    "Good": 1,
}

PEDESTRIAN_ACTIVITY_WEIGHT: Dict[str, int] = {
    "High": 3,
    "Medium": 2,
    "Low": 1,
}

# MCDA Default Weights (must sum to 1.0)
DEFAULT_PRIORITY_WEIGHTS: Dict[str, float] = {
    "severity_injury": 0.30,
    "unresolved_workload": 0.25,
    "complaint_urgency": 0.20,
    "recurrence_volume": 0.15,
    "location_vulnerability": 0.10,
}

# Design system colors
PALETTE = {
    "primary": "#06B6D4",      # Cyan accent
    "primary_dark": "#0891B2", # Deep cyan
    "background": "#FFFFFF",
    "card_bg": "#F8FAFC",
    "border": "#E2E8F0",
    "text": "#1E293B",         # Charcoal dark text
    "text_muted": "#64748B",
    "critical": "#EF4444",     # Red
    "high": "#F97316",         # Orange
    "medium": "#F59E0B",       # Amber
    "low": "#10B981",          # Emerald green
}
