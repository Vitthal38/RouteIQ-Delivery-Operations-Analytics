"""Data profiling checks, mirroring DATA_PROFILING_PLAN.md exactly.

Every function here is read-only: none of them mutate the DataFrame
passed in. This module is used twice by the pipeline — once against
the raw dataset (STEP 2, producing `profiling_report.md`) and once
against the cleaned dataset (STEP 7, to confirm every flagged issue
was resolved or intentionally retained-with-flag, per
PYTHON_ANALYSIS_PLAN.md Phase 1 step 4).
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from routeiq.cleaning.constants import (
    AGENT_AGE_MAX_PLAUSIBLE,
    AGENT_AGE_MIN_PLAUSIBLE,
    AGENT_RATING_MAX_VALID,
    AGENT_RATING_MIN_VALID,
    ALL_TRIM_COLUMNS,
    INDIA_LAT_MAX,
    INDIA_LAT_MIN,
    INDIA_LON_MAX,
    INDIA_LON_MIN,
    TRAFFIC_MASKED_NULL_LITERAL,
)

logger = logging.getLogger("routeiq_phase1")

_CATEGORICAL_COLUMNS: list[str] = ["Weather", "Traffic", "Area", "Vehicle", "Category"]


def profile_missing_values(df: pd.DataFrame) -> dict[str, Any]:
    """Count true (pandas-recognized) nulls per column.

    Note: this does NOT catch the masked-missing `"NaN "` literal in
    `Traffic` — that is a separate, deliberate check
    (`profile_masked_missing_traffic`), matching the distinction drawn
    in DATA_PROFILING_PLAN.md's Missing Values Profiling section.
    """
    counts = df.isna().sum()
    pct = (counts / len(df) * 100).round(2)
    return {
        col: {"missing_count": int(counts[col]), "missing_pct": float(pct[col])}
        for col in df.columns
        if counts[col] > 0
    }


def profile_masked_missing_traffic(df: pd.DataFrame) -> dict[str, Any]:
    """Count rows where `Traffic` holds the literal string `"NaN"` (post-trim)."""
    stripped = df["Traffic"].astype(str).str.strip()
    mask = stripped == TRAFFIC_MASKED_NULL_LITERAL
    return {"masked_missing_count": int(mask.sum())}


def profile_duplicates(df: pd.DataFrame) -> dict[str, Any]:
    """Full-row and `Order_ID` duplicate counts."""
    return {
        "full_row_duplicates": int(df.duplicated().sum()),
        "order_id_duplicates": int(df["Order_ID"].duplicated().sum()),
    }


def profile_outliers(df: pd.DataFrame) -> dict[str, Any]:
    """Range/plausibility checks for Delivery_Time, Agent_Rating, Agent_Age."""
    return {
        "delivery_time": {
            "min": float(df["Delivery_Time"].min()),
            "max": float(df["Delivery_Time"].max()),
            "mean": round(float(df["Delivery_Time"].mean()), 2),
            "median": float(df["Delivery_Time"].median()),
            "std": round(float(df["Delivery_Time"].std()), 2),
            "zero_or_negative_count": int((df["Delivery_Time"] <= 0).sum()),
        },
        "agent_rating": {
            "above_valid_ceiling_count": int((df["Agent_Rating"] > AGENT_RATING_MAX_VALID).sum()),
            "below_valid_floor_count": int(
                (df["Agent_Rating"] < AGENT_RATING_MIN_VALID).sum()
            ),
        },
        "agent_age": {
            "min": int(df["Agent_Age"].min()),
            "max": int(df["Agent_Age"].max()),
            "below_plausible_count": int((df["Agent_Age"] < AGENT_AGE_MIN_PLAUSIBLE).sum()),
            "above_plausible_count": int((df["Agent_Age"] > AGENT_AGE_MAX_PLAUSIBLE).sum()),
        },
    }


def profile_data_types(df: pd.DataFrame) -> dict[str, str]:
    """Observed dtype per column."""
    return {col: str(dtype) for col, dtype in df.dtypes.items()}


def profile_categorical(df: pd.DataFrame) -> dict[str, Any]:
    """Distinct raw value counts for every categorical column, plus a
    whitespace check (rows whose value differs from its trimmed form)."""
    result: dict[str, Any] = {}
    for col in _CATEGORICAL_COLUMNS:
        series = df[col].astype("string")
        non_null = series.dropna()
        whitespace_rows = int((non_null != non_null.str.strip()).sum())
        result[col] = {
            "distinct_count": int(non_null.nunique()),
            "value_counts": non_null.value_counts(dropna=False).to_dict(),
            "rows_with_whitespace": whitespace_rows,
        }
    return result


def profile_numerical(df: pd.DataFrame) -> dict[str, Any]:
    """Descriptive statistics for the core numeric fields."""
    result: dict[str, Any] = {}
    for col in ["Agent_Age", "Agent_Rating", "Delivery_Time"]:
        desc = df[col].describe()
        result[col] = {
            "count": int(desc["count"]),
            "min": round(float(desc["min"]), 2),
            "max": round(float(desc["max"]), 2),
            "mean": round(float(desc["mean"]), 2),
            "median": round(float(df[col].median()), 2),
            "std": round(float(desc["std"]), 2),
        }
    return result


def profile_coordinates(df: pd.DataFrame) -> dict[str, Any]:
    """India bounding-box validity check for store/drop coordinates."""
    store_invalid = ~df["Store_Latitude"].between(INDIA_LAT_MIN, INDIA_LAT_MAX) | ~df[
        "Store_Longitude"
    ].between(INDIA_LON_MIN, INDIA_LON_MAX)
    drop_invalid = ~df["Drop_Latitude"].between(INDIA_LAT_MIN, INDIA_LAT_MAX) | ~df[
        "Drop_Longitude"
    ].between(INDIA_LON_MIN, INDIA_LON_MAX)
    combined_invalid = store_invalid | drop_invalid

    store_zero = (df["Store_Latitude"] == 0) & (df["Store_Longitude"] == 0)
    drop_zero = (df["Drop_Latitude"] == 0) & (df["Drop_Longitude"] == 0)

    n = len(df)
    return {
        "store_outside_bounding_box": int(store_invalid.sum()),
        "store_outside_bounding_box_pct": round(float(store_invalid.sum() / n * 100), 2),
        "drop_outside_bounding_box": int(drop_invalid.sum()),
        "drop_outside_bounding_box_pct": round(float(drop_invalid.sum() / n * 100), 2),
        "combined_outside_bounding_box": int(combined_invalid.sum()),
        "combined_outside_bounding_box_pct": round(float(combined_invalid.sum() / n * 100), 2),
        "store_exact_zero_zero": int(store_zero.sum()),
        "drop_exact_zero_zero": int(drop_zero.sum()),
    }


def profile_datetime(df: pd.DataFrame) -> dict[str, Any]:
    """Parse-failure counts for Order_Date, Order_Time, Pickup_Time, and the
    confirmed row-level overlap between the masked-missing cluster and the
    Order_Time parse failures (DATA_PROFILING_PLAN.md > Datetime Validation)."""
    order_date_parsed = pd.to_datetime(df["Order_Date"], errors="coerce")
    order_time_parsed = pd.to_datetime(df["Order_Time"], format="%H:%M:%S", errors="coerce")
    pickup_time_parsed = pd.to_datetime(df["Pickup_Time"], format="%H:%M:%S", errors="coerce")

    weather_null_idx = set(df.index[df["Weather"].isna()])
    traffic_stripped = df["Traffic"].astype(str).str.strip()
    traffic_masked_idx = set(df.index[traffic_stripped == TRAFFIC_MASKED_NULL_LITERAL])
    order_time_fail_idx = set(df.index[order_time_parsed.isna()])

    return {
        "order_date_parse_failures": int(order_date_parsed.isna().sum()),
        "order_date_min": str(order_date_parsed.min().date()) if order_date_parsed.notna().any() else None,
        "order_date_max": str(order_date_parsed.max().date()) if order_date_parsed.notna().any() else None,
        "order_date_unique_days": int(order_date_parsed.dt.date.nunique()),
        "order_time_parse_failures": int(order_time_parsed.isna().sum()),
        "pickup_time_parse_failures": int(pickup_time_parsed.isna().sum()),
        "weather_null_equals_traffic_masked": weather_null_idx == traffic_masked_idx,
        "weather_null_equals_order_time_fail": weather_null_idx == order_time_fail_idx,
        "cluster_row_count": len(weather_null_idx | traffic_masked_idx | order_time_fail_idx),
    }


def profile_memory(df: pd.DataFrame) -> dict[str, Any]:
    """Total in-memory footprint (DATA_PROFILING_PLAN.md > Memory Usage Checks)."""
    total_bytes = int(df.memory_usage(deep=True).sum())
    return {
        "rows": int(len(df)),
        "columns": int(df.shape[1]),
        "total_memory_mb": round(total_bytes / (1024 * 1024), 3),
    }


def run_full_profile(df: pd.DataFrame) -> dict[str, Any]:
    """Run every profiling check documented in DATA_PROFILING_PLAN.md.

    Args:
        df: The dataset to profile — raw or cleaned. Never mutated.

    Returns:
        A nested dict with one key per profiling dimension, suitable
        both for rendering to Markdown and for before/after diffing.
    """
    logger.info("Running full profiling checklist on a %d-row dataset", len(df))
    return {
        "shape": {"rows": int(df.shape[0]), "columns": int(df.shape[1])},
        "missing_values": profile_missing_values(df),
        "masked_missing_traffic": profile_masked_missing_traffic(df)
        if "Traffic" in df.columns
        else {"masked_missing_count": None},
        "duplicates": profile_duplicates(df),
        "outliers": profile_outliers(df),
        "data_types": profile_data_types(df),
        "categorical": profile_categorical(df),
        "numerical": profile_numerical(df),
        "coordinates": profile_coordinates(df),
        "datetime": profile_datetime(df),
        "memory": profile_memory(df),
    }
