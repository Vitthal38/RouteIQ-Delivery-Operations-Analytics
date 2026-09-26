"""Fixed values referenced by the Phase 1 pipeline.

Every constant here is traceable to a specific figure or rule already
documented in the project's planning Markdown files (cited in each
comment). No value here introduces a new, undocumented business rule.
"""

from __future__ import annotations

# --- Expected raw-dataset shape (DATASET_OVERVIEW.md > Structure) ---
EXPECTED_RAW_ROW_COUNT: int = 43_739
EXPECTED_RAW_COLUMN_COUNT: int = 16

# --- Raw column names, in source order (KPI_DEFINITIONS.md grounding note) ---
RAW_COLUMNS: list[str] = [
    "Order_ID",
    "Agent_Age",
    "Agent_Rating",
    "Store_Latitude",
    "Store_Longitude",
    "Drop_Latitude",
    "Drop_Longitude",
    "Order_Date",
    "Order_Time",
    "Pickup_Time",
    "Weather",
    "Traffic",
    "Vehicle",
    "Area",
    "Delivery_Time",
    "Category",
]

# --- Categorical columns requiring whitespace trimming ---
# Primary (DATA_CLEANING_PLAN.md Step 1): Traffic, Vehicle, Area.
# Defensive (same step, "and defensively"): Weather, Category.
PRIMARY_TRIM_COLUMNS: list[str] = ["Traffic", "Vehicle", "Area"]
DEFENSIVE_TRIM_COLUMNS: list[str] = ["Weather", "Category"]
ALL_TRIM_COLUMNS: list[str] = PRIMARY_TRIM_COLUMNS + DEFENSIVE_TRIM_COLUMNS

# --- Masked-missing marker (DATA_CLEANING_PLAN.md Step 2) ---
TRAFFIC_MASKED_NULL_LITERAL: str = "NaN"

# --- Agent_Rating bounds (DATA_CLEANING_PLAN.md Steps 4-5; SLA/KPI #6 dependency) ---
AGENT_RATING_MIN_VALID: float = 1.0
AGENT_RATING_MAX_VALID: float = 5.0

# --- Agent_Age plausibility bound (DATA_CLEANING_PLAN.md Step 6: "e.g., 18-65") ---
AGENT_AGE_MIN_PLAUSIBLE: int = 18
AGENT_AGE_MAX_PLAUSIBLE: int = 65

# --- Coordinate plausibility bounding box (DATA_PROFILING_PLAN.md > Coordinate
# Validation: approximate India bounding box) ---
INDIA_LAT_MIN: float = 6.0
INDIA_LAT_MAX: float = 38.0
INDIA_LON_MIN: float = 68.0
INDIA_LON_MAX: float = 98.0

# --- Area category requiring exclusion from tier comparisons (DATA_CLEANING_PLAN.md
# Step 8) ---
AREA_UNDEFINED_VALUE: str = "Other"

# --- Haversine formula constant (FEATURE_ENGINEERING.md #1) ---
EARTH_RADIUS_KM: float = 6371.0

# --- SLA methodology (SLA_METHODOLOGY.md > Frozen SLA Definition — FROZEN, do not
# change without following the document's Change Control process) ---
SLA_PERCENTILE: float = 0.75

# --- delivery_bucket bin edges (FEATURE_ENGINEERING.md #4 — the document's own
# "illustrative scheme", the only concrete scheme it provides; final EDA-based
# confirmation is explicitly deferred to Phase 2, which is out of scope here.
# Right-closed bins so a boundary value (e.g., exactly 60) falls into the lower
# bucket, consistent with the doc's boundary-consistency requirement) ---
DELIVERY_BUCKET_EDGES: list[float] = [0, 60, 120, 180, float("inf")]
DELIVERY_BUCKET_LABELS: list[str] = [
    "0-60 minutes",
    "61-120 minutes",
    "121-180 minutes",
    "181+ minutes",
]

# --- Weekend day names (FEATURE_ENGINEERING.md #5) ---
WEEKEND_DAY_NAMES: set[str] = {"Saturday", "Sunday"}

# --- Minutes-per-day for midnight-crossover correction (FEATURE_ENGINEERING.md #8) ---
MINUTES_PER_DAY: int = 24 * 60

# --- Expected count of distinct Category values (SLA reference table size gate,
# PYTHON_ANALYSIS_PLAN.md Phase 1 validation gate) ---
EXPECTED_CATEGORY_COUNT: int = 16
