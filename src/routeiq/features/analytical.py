"""Build the controlled analytical dataset.

Every analysis, statistical test, model and reconciliation in this project reads
this one table, so no script can silently use a different population. Every
derived feature is defined here and mirrored in SQL by
``sql/schema/09_create_analytical_view.sql`` (a test reconciles the two).

Input : ``data/processed/cleaned_delivery.csv`` (frozen Phase 1 output).
Output: ``data/processed/analytical_deliveries.csv``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from routeiq.config import (
    AGE_THRESHOLD,
    ANALYTICAL_DATASET_CSV,
    CLEANED_DELIVERY_CSV,
    RATING_THRESHOLD,
)

# Exploratory hour bands. They were chosen AFTER inspecting the hourly volume and
# traffic profile (see docs/analytical_findings.md), so treat them as descriptive
# bins, not pre-registered hypotheses. Hours with no orders (1-7) are not observed.
HOUR_BAND_EDGES: list[tuple[int, int, str]] = [
    (0, 7, "1_00-07 overnight"),
    (8, 10, "2_08-10 morning"),
    (11, 14, "3_11-14 midday"),
    (15, 16, "4_15-16 afternoon"),
    (17, 18, "5_17-18 early evening"),
    (19, 21, "6_19-21 evening peak"),
    (22, 23, "7_22-23 late evening"),
]

# Peak = hours whose order volume is at least 2x the median hourly volume.
# On this dataset that rule selects 17:00-23:59; ``derive_peak_hours`` recomputes it
# from the data and a test asserts it matches PEAK_HOURS.
PEAK_HOURS: tuple[int, ...] = tuple(range(17, 24))

ANALYTICAL_COLUMNS: list[str] = [
    "order_id", "order_date", "week_number", "is_weekend",
    "order_hour", "hour_band", "is_peak_hour",
    "prep_time_minutes",
    "delivery_time_minutes", "sla_threshold_minutes", "breach_flag", "minutes_over_sla",
    "category", "traffic", "weather", "area", "vehicle",
    "agent_rating", "rating_lt_4_5", "agent_age", "age_ge_30",
    "distance_km",
]


def hour_band(hour: int) -> str:
    for lo, hi, label in HOUR_BAND_EDGES:
        if lo <= hour <= hi:
            return label
    raise ValueError(f"hour out of range: {hour}")


def derive_peak_hours(order_hour: pd.Series) -> tuple[int, ...]:
    """Peak rule: hourly volume >= 2x the median hourly volume (observed hours only)."""
    volume = order_hour.value_counts()
    return tuple(sorted(int(h) for h in volume[volume >= 2 * volume.median()].index))


def build_analytical_dataset(cleaned: pd.DataFrame | None = None) -> pd.DataFrame:
    """Return the analytical table (one row per delivery, 43,648 rows)."""
    df = pd.read_csv(CLEANED_DELIVERY_CSV) if cleaned is None else cleaned.copy()

    rating = df["Agent_Rating"].where(df["agent_rating_valid_flag"])
    distance = df["distance_km"].where(df["coordinates_valid_flag"])
    delivery = df["Delivery_Time"].astype(int)
    threshold = df["sla_threshold_minutes"].astype(float)

    out = pd.DataFrame({
        "order_id": df["Order_ID"],
        "order_date": pd.to_datetime(df["Order_Date"]).dt.date,
        "week_number": df["week_number"].astype(int),
        "is_weekend": df["is_weekend"].astype(int),
        "order_hour": df["order_hour"].astype(int),
        "prep_time_minutes": df["prep_time_minutes"].astype(int),
        "delivery_time_minutes": delivery,
        "sla_threshold_minutes": threshold,
        # Frozen rule: breach = delivery time strictly greater than the category threshold.
        "breach_flag": (delivery > threshold).astype(int),
        "minutes_over_sla": (delivery - threshold).clip(lower=0),
        "category": df["Category"],
        "traffic": df["Traffic"],
        "weather": df["Weather"],
        "area": df["Area"],
        "vehicle": df["Vehicle"],
        "agent_rating": rating,
        "agent_age": df["Agent_Age"].astype(int),
        "distance_km": distance,
    })
    out["hour_band"] = out["order_hour"].map(hour_band)
    out["is_peak_hour"] = out["order_hour"].isin(PEAK_HOURS).astype(int)
    # Data-driven step points (docs/analytical_findings.md). Missing rating stays missing.
    out["rating_lt_4_5"] = np.where(out["agent_rating"].isna(), np.nan,
                                    (out["agent_rating"] < RATING_THRESHOLD).astype(float))
    out["age_ge_30"] = (out["agent_age"] >= AGE_THRESHOLD).astype(int)

    # The stored flag and the recomputed flag must agree exactly (frozen SLA rule).
    if not (out["breach_flag"] == df["sla_breach_flag"].astype(int)).all():
        raise ValueError("Recomputed breach_flag disagrees with stored sla_breach_flag")
    return out[ANALYTICAL_COLUMNS]


def load_analytical_dataset() -> pd.DataFrame:
    """Read the saved analytical dataset, building it first if it does not exist."""
    if not ANALYTICAL_DATASET_CSV.exists():
        save_analytical_dataset()
    df = pd.read_csv(ANALYTICAL_DATASET_CSV, parse_dates=["order_date"])
    df["order_date"] = df["order_date"].dt.date
    return df


def save_analytical_dataset() -> pd.DataFrame:
    df = build_analytical_dataset()
    ANALYTICAL_DATASET_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ANALYTICAL_DATASET_CSV, index=False)
    return df


# Human-readable feature definitions; docs/data_dictionary.md is generated from this.
FEATURE_DEFINITIONS: dict[str, str] = {
    "order_id": "Unique delivery identifier (natural key, traceability only).",
    "order_date": "Date the order was placed (11 Feb - 6 Apr 2022, 44 observed dates).",
    "week_number": "ISO week number of order_date.",
    "is_weekend": "1 if order_date is Saturday or Sunday.",
    "order_hour": "Hour of day (0-23) the order was placed, from Order_Time.",
    "hour_band": "Exploratory hour bands (see HOUR_BAND_EDGES); chosen after inspecting the hourly profile.",
    "is_peak_hour": "1 if hourly order volume >= 2x the median hourly volume (17:00-23:59 here).",
    "prep_time_minutes": "Pickup time minus order time, midnight-crossover corrected (values 5, 10, 15 only).",
    "delivery_time_minutes": "Outcome measure: delivery time in minutes.",
    "sla_threshold_minutes": "Frozen category-level P75 of delivery time (analyst-defined benchmark).",
    "breach_flag": "1 if delivery_time_minutes > sla_threshold_minutes (strict); recomputed and checked against the stored flag.",
    "minutes_over_sla": "max(0, delivery_time_minutes - sla_threshold_minutes): how late a breach is.",
    "category": "Product category (16 values).",
    "traffic": "Traffic level at order time: Low, Medium, High, Jam.",
    "weather": "Weather condition (6 values).",
    "area": "Area type: Metropolitian (spelling as in source), Urban, Semi-Urban, Other (not a formal tier).",
    "vehicle": "Vehicle type: motorcycle, scooter, van (no bicycle rows exist after cleaning).",
    "agent_rating": "Agent rating 2.5-5.0; missing for the 54 rows with no rating. Attribute of the delivery record, not an agent identity.",
    "rating_lt_4_5": "1 if agent_rating < 4.5, 0 if >= 4.5, missing if no rating. Data-driven step point.",
    "agent_age": "Agent age in years (20-39 observed). Attribute only; no agent identifier exists.",
    "age_ge_30": "1 if agent_age >= 30. Data-driven step point.",
    "distance_km": "Haversine store-to-drop distance; missing for the 3,651 rows with invalid coordinates.",
}
