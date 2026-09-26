"""Feature engineering, implementing FEATURE_ENGINEERING.md fields 1-8 in
their documented dependency order. `sla_threshold_minutes` is computed
once on the full cleaned dataset and frozen into a static reference
table before `sla_breach_flag` is derived, per SLA_METHODOLOGY.md's
change-control rule — it must never be recalculated after this point.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

from routeiq.cleaning.constants import (
    DELIVERY_BUCKET_EDGES,
    DELIVERY_BUCKET_LABELS,
    EARTH_RADIUS_KM,
    MINUTES_PER_DAY,
    SLA_PERCENTILE,
    WEEKEND_DAY_NAMES,
)

logger = logging.getLogger("routeiq_phase1")


def _haversine_km(
    lat1: pd.Series, lon1: pd.Series, lat2: pd.Series, lon2: pd.Series
) -> pd.Series:
    """Vectorized great-circle distance (FEATURE_ENGINEERING.md #1 formula)."""
    lat1_r, lon1_r, lat2_r, lon2_r = map(np.radians, (lat1, lon1, lat2, lon2))
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1_r) * np.cos(lat2_r) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return EARTH_RADIUS_KM * c


def add_distance_km(df: pd.DataFrame) -> pd.DataFrame:
    """Field 1 — `distance_km`, null for coordinate-invalid rows.

    See FEATURE_ENGINEERING.md #1. Requires `coordinates_valid_flag`
    from DATA_CLEANING_PLAN.md Step 7 to already be present.
    """
    df = df.copy()
    distance = _haversine_km(
        df["Store_Latitude"], df["Store_Longitude"], df["Drop_Latitude"], df["Drop_Longitude"]
    )
    df["distance_km"] = distance.where(df["coordinates_valid_flag"], other=np.nan)
    return df


def compute_sla_reference_table(df: pd.DataFrame) -> pd.DataFrame:
    """Field 2 — frozen `sla_threshold_minutes` per Category (P75).

    Computed once on the full cleaned dataset, per SLA_METHODOLOGY.md's
    Frozen SLA Definition: category-level 75th percentile of
    `Delivery_Time`. This table is the single source every downstream
    layer (Python, SQL, DAX) must read from — never recalculated.
    """
    grouped = df.groupby("Category")["Delivery_Time"]
    reference = grouped.agg(
        row_count="count",
        sla_threshold_minutes=lambda s: float(np.percentile(s, SLA_PERCENTILE * 100)),
    ).reset_index()
    reference = reference.sort_values("Category").reset_index(drop=True)
    logger.info(
        "Computed frozen sla_threshold_minutes reference table: %d categories",
        len(reference),
    )
    return reference


def add_sla_threshold(df: pd.DataFrame, sla_reference: pd.DataFrame) -> pd.DataFrame:
    """Join the frozen per-category `sla_threshold_minutes` onto every row."""
    df = df.merge(
        sla_reference[["Category", "sla_threshold_minutes"]], on="Category", how="left"
    )
    return df


def add_sla_breach_flag(df: pd.DataFrame) -> pd.DataFrame:
    """Field 3 — `sla_breach_flag`. Strictly-greater-than the frozen
    threshold; exactly-equal is on-time (FEATURE_ENGINEERING.md #3 edge case)."""
    df = df.copy()
    df["sla_breach_flag"] = df["Delivery_Time"] > df["sla_threshold_minutes"]
    return df


def add_delivery_bucket(df: pd.DataFrame) -> pd.DataFrame:
    """Field 4 — `delivery_bucket`, using FEATURE_ENGINEERING.md #4's
    illustrative bin scheme (the only concrete scheme the document
    provides; final EDA-based confirmation is explicitly deferred to
    Phase 2, out of scope for this Phase 1 run — see cleaning_log.md)."""
    df = df.copy()
    df["delivery_bucket"] = pd.cut(
        df["Delivery_Time"],
        bins=DELIVERY_BUCKET_EDGES,
        labels=DELIVERY_BUCKET_LABELS,
        right=True,
        include_lowest=True,
    )
    return df


def add_day_of_week(df: pd.DataFrame) -> pd.DataFrame:
    """Field 5 — `day_of_week` and `is_weekend`, from `Order_Date`."""
    df = df.copy()
    order_date = pd.to_datetime(df["Order_Date"])
    df["day_of_week"] = order_date.dt.day_name()
    df["is_weekend"] = df["day_of_week"].isin(WEEKEND_DAY_NAMES)
    return df


def add_order_hour(df: pd.DataFrame) -> pd.DataFrame:
    """Field 6 — `order_hour`, extracted from `Order_Time`.

    The 91 rows with unparseable `Order_Time` were already fully
    excluded in DATA_CLEANING_PLAN.md Step 3, so every remaining row
    parses cleanly here — no default/placeholder hour is ever produced.
    """
    df = df.copy()
    order_time = pd.to_datetime(df["Order_Time"], format="%H:%M:%S", errors="raise")
    df["order_hour"] = order_time.dt.hour
    return df


def add_week_number(df: pd.DataFrame) -> pd.DataFrame:
    """Field 7 — ISO `week_number`, from `Order_Date`."""
    df = df.copy()
    order_date = pd.to_datetime(df["Order_Date"])
    df["week_number"] = order_date.dt.isocalendar().week.astype(int)
    return df


def add_prep_time_minutes(df: pd.DataFrame) -> pd.DataFrame:
    """Field 8 — `prep_time_minutes` = Pickup_Time - Order_Time, with a
    midnight-crossover correction (+24h) so the result is never negative."""
    df = df.copy()
    order_time = pd.to_datetime(df["Order_Time"], format="%H:%M:%S", errors="raise")
    pickup_time = pd.to_datetime(df["Pickup_Time"], format="%H:%M:%S", errors="raise")

    delta_minutes = (pickup_time - order_time).dt.total_seconds() / 60.0
    crossed_midnight = delta_minutes < 0
    delta_minutes = delta_minutes.where(~crossed_midnight, delta_minutes + MINUTES_PER_DAY)

    df["prep_time_minutes"] = delta_minutes.astype(int)
    return df


def engineer_features(df_cleaned: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Apply FEATURE_ENGINEERING.md fields 1-8, in their documented order.

    Args:
        df_cleaned: Output of `cleaning.apply_cleaning_steps` — the Step 3
            cluster already excluded, Steps 4-8 validity flags present.

    Returns:
        (df_engineered, sla_reference_table, summary) — the fully
        engineered dataset, the frozen per-category SLA reference table
        (written separately to `sla_reference.csv`), and a summary dict
        for the cleaning log / validation report.
    """
    logger.info("Starting feature engineering on %d cleaned rows", len(df_cleaned))

    df = add_distance_km(df_cleaned)
    distance_eligible = int(df["distance_km"].notna().sum())
    logger.info(
        "Field 1 (distance_km): computed for %d rows (coordinates_valid_flag=True)",
        distance_eligible,
    )

    sla_reference = compute_sla_reference_table(df)
    df = add_sla_threshold(df, sla_reference)
    logger.info("Field 2 (sla_threshold_minutes): frozen, joined from reference table")

    df = add_sla_breach_flag(df)
    breach_rate = round(float(df["sla_breach_flag"].mean() * 100), 2)
    logger.info("Field 3 (sla_breach_flag): overall breach rate = %.2f%%", breach_rate)

    df = add_delivery_bucket(df)
    logger.info("Field 4 (delivery_bucket): illustrative bins applied")

    df = add_day_of_week(df)
    logger.info("Field 5 (day_of_week / is_weekend): derived from Order_Date")

    df = add_order_hour(df)
    logger.info("Field 6 (order_hour): derived from Order_Time")

    df = add_week_number(df)
    n_weeks = int(df["week_number"].nunique())
    logger.info("Field 7 (week_number): %d distinct ISO weeks observed", n_weeks)

    df = add_prep_time_minutes(df)
    negative_prep = int((df["prep_time_minutes"] < 0).sum())
    logger.info(
        "Field 8 (prep_time_minutes): computed for all rows, %d negative after "
        "midnight-crossover correction",
        negative_prep,
    )

    summary: dict[str, Any] = {
        "distance_km_eligible_rows": distance_eligible,
        "distance_km_null_rows": int(len(df) - distance_eligible),
        "sla_reference_category_count": int(len(sla_reference)),
        "overall_sla_breach_rate_pct": breach_rate,
        "distinct_iso_weeks": n_weeks,
        "prep_time_negative_count": negative_prep,
    }

    logger.info("Feature engineering complete: %d rows, %d columns", *df.shape)
    return df, sla_reference, summary
