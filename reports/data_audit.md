# CivicPulse AI — Data Audit Report
## Datathon 2026 · Track 3: Smart City ("Where Should We Fix First?")

**Date of Audit:** October 2026  
**Audit Environment:** Python 3.12.10, pandas 3.0.5  
**Data Directory:** `03_smart_city_where_fix_first/`

---

## 1. Executive Summary

A comprehensive automated audit of all three source CSV files (`locations.csv`, `incidents.csv`, and `public_complaints.csv`) was conducted to evaluate data integrity, schema consistency, relational constraints, and feature distributions before any feature engineering or modeling.

### Key Audit Findings:
- **Overall Quality:** High structural integrity. Zero null values, zero duplicate primary keys, and zero orphan foreign key references.
- **Relational Integrity:** All 10,000 incidents and all 8,000 complaints reference valid `location_id` keys in the 1,000-location inventory.
- **Coverage:** Every one of the 1,000 locations has at least one recorded incident and complaint (dense urban synthetic grid).
- **Domain Discrepancies vs. README:**
  - `incident_type` contains **6 categories** (README listed 5): `"Blocked drain"` is present in addition to Collision, Flooding, Pothole, Signal failure, and Streetlight outage.
  - `reported_by` contains **4 channels** (README listed 3): `"Authority"` is present in addition to Citizen, Police, and Sensor.
- **Target Variable Quality (`resolution_hours`):**
  - Populated across all 10,000 incident rows, including 2,874 records marked as `resolved == 0`.
  - The mean and distribution of `resolution_hours` for unresolved incidents is virtually identical to resolved incidents (32.25h vs. 32.24h), indicating a synthetic data artifact.
  - **Mitigation Decision:** Downstream machine learning training will strictly filter to `resolved == 1` (7,126 records) to maintain sound engineering semantics.

---

## 2. Table-by-Table Schema & Distribution Audit

### 2.1 Locations Table (`locations.csv`)
- **Total Records:** 1,000 rows
- **Columns (10):** `location_id`, `zone`, `road_type`, `road_condition`, `population_density_per_km2`, `near_school`, `near_hospital`, `pedestrian_activity`, `latitude`, `longitude`
- **Primary Key:** `location_id` (Unique: 1,000 / Duplicates: 0)
- **Null Values:** 0 across all columns
- **Spatial Coverage:**
  - Latitude: [16.1860, 16.7065]
  - Longitude: [80.2481, 80.8186]
  - Zones: 20 distinct zones (`ZONE_01` to `ZONE_20`, 50 locations per zone)
- **Contextual Categoricals:**
  - `road_type`: Local (263), Collector (242), Residential (228), Arterial (215), Highway (52)
  - `road_condition`: Fair (383), Poor (309), Good (230), Critical (78)
  - `pedestrian_activity`: Medium (431), Low (316), High (253)
  - `near_school`: 286 locations near schools (28.6%)
  - `near_hospital`: 155 locations near hospitals (15.5%)
  - `population_density_per_km2`: Min 507, Max 24,983, Mean 12,719.8 people/km²

### 2.2 Incidents Table (`incidents.csv`)
- **Total Records:** 10,000 rows
- **Columns (9):** `incident_id`, `location_id`, `timestamp`, `incident_type`, `severity`, `injuries`, `reported_by`, `resolved`, `resolution_hours`
- **Primary Key:** `incident_id` (Unique: 10,000 / Duplicates: 0)
- **Foreign Key:** `location_id` (Valid: 10,000 / Orphans: 0)
- **Temporal Range:** 2025-01-01 00:32:00 to 2025-12-31 23:44:00 (1 full year)
- **Distributions:**
  - `incident_type`: Streetlight outage (1,726), Signal failure (1,699), Pothole (1,685), Blocked drain (1,651), Collision (1,641), Flooding (1,598)
  - `severity`: Low (3,819), Medium (3,726), High (1,985), Critical (470)
  - `reported_by`: Citizen (5,071), Authority (1,913), Police (1,533), Sensor (1,483)
  - `injuries`: 0 injuries (7,821), 1 injury (1,905), 2 injuries (252), 3 injuries (22) — Total injuries: 2,475
  - `resolved`: 7,126 resolved (71.3%), 2,874 unresolved (28.7%)
  - `resolution_hours`: Min 1.0h, Max 191.9h, Mean 32.24h, Std 22.53h

### 2.3 Public Complaints Table (`public_complaints.csv`)
- **Total Records:** 8,000 rows
- **Columns (7):** `complaint_id`, `location_id`, `created_at`, `category`, `priority_reported`, `status`, `days_to_resolution`
- **Primary Key:** `complaint_id` (Unique: 8,000 / Duplicates: 0)
- **Foreign Key:** `location_id` (Valid: 8,000 / Orphans: 0)
- **Temporal Range:** 2025-01-01 to 2025-12-31
- **Distributions:**
  - `category`: Road damage (1,361), Traffic (1,357), Lighting (1,343), Waste (1,330), Pedestrian safety (1,319), Drainage (1,290)
  - `priority_reported`: Normal (4,469), Low (1,943), High (1,588)
  - `status`: Resolved (3,258), In progress (1,440), Closed (1,304), Assigned (1,062), Open (936)
  - `active_complaints` (Open, Assigned, In progress): 3,438 (43.0%)
  - `resolved_complaints` (Resolved, Closed): 4,562 (57.0%)
  - `days_to_resolution`: Min 0.1d, Max 31.3d, Mean 6.04d

---

## 3. Data Integrity & Quality Checks

| Test Case | Method | Result | Notes |
|---|---|---|---|
| Null value audit | `df.isnull().sum()` across all tables | 0 nulls | Data is complete; no imputation required |
| Primary key uniqueness | `df[pk].duplicated().sum()` | 0 duplicates | Clean IDs (`L0001-L1000`, `I000001-I010000`, `C000001-C008000`) |
| Foreign key validity | `set(child['location_id']) - set(locations['location_id'])` | Empty set | Zero orphan records |
| Coordinate bounds | Range test on `latitude`, `longitude` | Valid | Coherent metropolitan cluster |
| Temporal continuity | Monotonic inspection & format check | Valid | All ISO timestamps parseable |

---

## 4. Modeling Guidelines Derived from Audit

1. **Target Filtering:** Train the resolution-time predictor strictly on `resolved == 1` records.
2. **Feature Leakage Prevention:** Do not pass `resolution_hours`, `resolved`, or identifier columns to the feature matrix.
3. **Data Aggregation:** Aggregation of incidents and complaints to `location_id` must use a left join on `locations` to preserve exactly 1,000 rows, with explicit zero-filling for locations that may lack specific event categories.
4. **Primary Product Emphasis:** The multi-criteria priority engine (`priority_engine.py`) provides the core prescriptive output, operating deterministically on verified tabular aggregations.
