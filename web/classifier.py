"""NLP Complaint Classifier and ML Dispatch Assessment Engine for CivicPulse AI.

Analyzes citizen grievance text to classify category and severity, merges physical
location attributes, computes MCDA priority scores, and estimates turnaround time.
"""

from datetime import datetime
import re
from typing import Any, Dict, List, Tuple
import pandas as pd

from src.config import ROAD_CONDITION_VULNERABILITY, VALID_INCIDENT_TYPES
from src.modeling import load_trained_model

# Category lexicons for keyword scoring
CATEGORY_LEXICONS = {
    "Road damage": [
        "pothole", "potholes", "crater", "sinkhole", "asphalt", "cracked", "pavement",
        "uneven", "manhole", "road broke", "road cave", "tar", "bumpy", "trench",
    ],
    "Drainage": [
        "drain", "drainage", "waterlogging", "flooding", "sewer", "overflow", "stagnant",
        "gutter", "blocked drain", "choked", "clogged", "sewage", "rainwater",
    ],
    "Traffic": [
        "signal", "traffic", "jam", "congestion", "gridlock", "red light", "traffic light",
        "signal failure", "collision", "accident", "intersection", "deadlock",
    ],
    "Lighting": [
        "light", "lighting", "streetlight", "lamp", "dark", "pitch black", "flickering",
        "bulb", "pole", "no light", "street light outage", "blackout",
    ],
    "Pedestrian safety": [
        "pedestrian", "walkway", "sidewalk", "zebra crossing", "footpath", "crosswalk",
        "jaywalking", "school crossing", "curb", "pedestrian safety", "crossing",
    ],
    "Waste": [
        "garbage", "waste", "trash", "dump", "litter", "rubbish", "debris",
        "overflowing bin", "smell", "rotting", "filth", "dumping",
    ],
}

# Severity trigger terms
CRITICAL_TERMS = [
    "critical", "fatal", "blood", "severe", "life threatening", "collapsed", "emergency",
    "deadly", "danger to life", "ambulance", "trapped", "casualty", "major accident",
]
HIGH_TERMS = [
    "urgent", "danger", "hazardous", "deep", "heavy damage", "injured", "hospital",
    "school children", "school kid", "massive", "risky", "immediate", "blocked road",
]
MEDIUM_TERMS = [
    "broken", "damaged", "moderate", "inconvenience", "delay", "slow", "disruption",
    "problem", "bad condition",
]


class ComplaintClassifier:
    """Classifies unstructured complaint text and assesses infrastructure impact."""

    def __init__(self):
        self.pipeline, self.metadata, self.importance = load_trained_model()

    def classify_text(self, text: str, user_category: str = None) -> Tuple[str, float]:
        """Classify complaint text into one of the 6 city categories.

        Args:
            text: Citizen complaint description.
            user_category: Optional user-provided category hint.

        Returns:
            Tuple of (predicted_category, confidence_score).
        """
        clean_text = text.lower()
        scores: Dict[str, float] = {cat: 0.0 for cat in CATEGORY_LEXICONS}

        for cat, keywords in CATEGORY_LEXICONS.items():
            for kw in keywords:
                if kw in clean_text:
                    # Exact word boundary or substring match
                    scores[cat] += 2.0 if re.search(r"\b" + re.escape(kw) + r"\b", clean_text) else 1.0

        if user_category and user_category in scores:
            scores[user_category] += 2.5

        top_cat = max(scores, key=scores.get)
        top_score = scores[top_cat]

        if top_score == 0:
            return user_category if user_category in CATEGORY_LEXICONS else "Road damage", 0.55

        total = sum(scores.values())
        confidence = min(0.96, round(top_score / total if total > 0 else 0.60, 2))
        return top_cat, max(0.60, confidence)

    def infer_severity(
        self,
        text: str,
        user_urgency: str = "Standard",
        location_meta: Dict[str, Any] = None,
    ) -> Tuple[str, List[str]]:
        """Infer severity tier from keywords, reported urgency, and physical context."""
        clean = text.lower()
        reasons = []

        is_critical = any(term in clean for term in CRITICAL_TERMS) or user_urgency == "Life Hazard"
        is_high = any(term in clean for term in HIGH_TERMS) or user_urgency == "Urgent"

        if location_meta:
            if location_meta.get("near_hospital") == 1:
                reasons.append("Adjacent to hospital emergency corridor")
                if not is_critical:
                    is_high = True
            if location_meta.get("near_school") == 1:
                reasons.append("Adjacent to school pedestrian zone")
                if not is_critical:
                    is_high = True
            if location_meta.get("road_condition") == "Critical":
                reasons.append("Underlying road condition is classified as Critical")
                is_high = True

        if is_critical:
            severity = "Critical"
            reasons.insert(0, "Detected high-hazard life-safety keywords")
        elif is_high:
            severity = "High"
            reasons.insert(0, "Identified elevated infrastructure risk indicators")
        elif any(term in clean for term in MEDIUM_TERMS):
            severity = "Medium"
            reasons.append("Standard municipal service degradation")
        else:
            severity = "Low"
            reasons.append("Routine maintenance grievance")

        return severity, reasons

    def assess_complaint(
        self,
        description: str,
        location_id: str,
        location_meta: Dict[str, Any],
        user_urgency: str = "Standard",
        user_category: str = None,
    ) -> Dict[str, Any]:
        """Perform full multi-dimensional assessment of a citizen complaint.

        Args:
            description: Citizen complaint narrative.
            location_id: Target location ID (e.g. 'L0001').
            location_meta: Metadata dictionary for the location.
            user_urgency: User selected urgency level.
            user_category: Optional user category.

        Returns:
            Dictionary containing category, severity, priority_score,
            estimated_resolution_hours, and explainable rationale.
        """
        category, cat_confidence = self.classify_text(description, user_category)
        severity, severity_reasons = self.infer_severity(description, user_urgency, location_meta)

        # Priority calculation (0-100 scale)
        sev_base = {"Critical": 92.0, "High": 76.0, "Medium": 54.0, "Low": 32.0}[severity]

        # Location context bonus
        bonus = 0.0
        if location_meta.get("near_hospital") == 1:
            bonus += 5.0
        if location_meta.get("near_school") == 1:
            bonus += 4.0
        if location_meta.get("pedestrian_activity") == "High":
            bonus += 3.0
        if location_meta.get("road_condition") in ["Poor", "Critical"]:
            bonus += 3.0

        priority_score = min(99.0, max(10.0, round(sev_base + bonus, 1)))

        # Turnaround estimation via trained ML pipeline if available
        est_hours = 24.0
        if self.pipeline is not None and location_meta:
            now = datetime.now()
            # Map category to matching incident_type
            type_mapping = {
                "Road damage": "Pothole",
                "Drainage": "Blocked drain",
                "Traffic": "Signal failure",
                "Lighting": "Streetlight outage",
                "Pedestrian safety": "Collision",
                "Waste": "Flooding",
            }
            inc_type = type_mapping.get(category, "Pothole")

            sample_df = pd.DataFrame([{
                "incident_type": inc_type,
                "severity": severity,
                "reported_by": "Citizen",
                "zone": location_meta.get("zone", "ZONE_01"),
                "road_type": location_meta.get("road_type", "Local"),
                "road_condition": location_meta.get("road_condition", "Fair"),
                "pedestrian_activity": location_meta.get("pedestrian_activity", "Medium"),
                "injuries": 1 if severity == "Critical" else 0,
                "near_school": int(location_meta.get("near_school", 0)),
                "near_hospital": int(location_meta.get("near_hospital", 0)),
                "population_density_per_km2": int(location_meta.get("population_density_per_km2", 10000)),
                "hour": now.hour,
                "day_of_week": now.weekday(),
                "month": now.month,
            }])
            try:
                raw_pred = float(self.pipeline.predict(sample_df)[0])
                est_hours = max(2.0, round(raw_pred, 1))
            except Exception:
                est_hours = 28.5

        # Format rationale
        primary_reason = severity_reasons[0] if severity_reasons else "Normal priority grievance"
        secondary_reason = severity_reasons[1] if len(severity_reasons) > 1 else f"Location {location_id} in {location_meta.get('zone', 'Zone')}"
        rationale = f"{primary_reason}. {secondary_reason}."

        return {
            "predicted_category": category,
            "category_confidence": cat_confidence,
            "inferred_severity": severity,
            "priority_score": priority_score,
            "priority_tier": "CRITICAL" if priority_score >= 85 else ("HIGH" if priority_score >= 70 else ("MEDIUM" if priority_score >= 45 else "ROUTINE")),
            "estimated_resolution_hours": est_hours,
            "rationale": rationale,
        }
