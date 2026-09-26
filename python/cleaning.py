"""Cleaning transformations, implementing DATA_CLEANING_PLAN.md Steps 1-9
in their documented execution order. No step here introduces logic beyond
what that document specifies — see the module-level docstring of each
function for its exact source reference.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from constants import (
    AGENT_AGE_MAX_PLAUSIBLE,
    AGENT_AGE_MIN_PLAUSIBLE,
    AGENT_RATING_MAX_VALID,
    AGENT_RATING_MIN_VALID,
    ALL_TRIM_COLUMNS,
    AREA_UNDEFINED_VALUE,
    INDIA_LAT_MAX,
    INDIA_LAT_MIN,
    INDIA_LON_MAX,
    INDIA_LON_MIN,
    TRAFFIC_MASKED_NULL_LITERAL,
)

logger = logging.getLogger("routeiq_phase1")


def _step1_trim_whitespace(df: pd.DataFrame) -> pd.DataFrame:
    """Step 1 — trim whitespace on Traffic/Vehicle/Area (+ defensively
    Weather/Category). See DATA_CLEANING_PLAN.md Step 1."""
    df = df.copy()
    for col in ALL_TRIM_COLUMNS:
        df[col] = df[col].astype("string").str.strip()
    return df


def _step2_recode_masked_traffic(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Step 2 — recode the literal string "NaN" in Traffic to a true null.
    See DATA_CLEANING_PLAN.md Step 2. Must run after Step 1's trim."""
    df = df.copy()
    mask = df["Traffic"] == TRAFFIC_MASKED_NULL_LITERAL
    recoded_count = int(mask.sum())
    df.loc[mask, "Traffic"] = pd.NA
    return df, recoded_count


def _step3_exclude_missing_cluster(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, bool]:
    """Step 3 — exclude the confirmed 91-row Weather/Traffic missing-data
    cluster from the analysis dataset. See DATA_CLEANING_PLAN.md Step 3.

    Returns:
        (retained_df, excluded_df, confirmed_full_overlap) where
        `confirmed_full_overlap` states whether the Order_Time parse
        failures are exactly the same rows as the Weather/Traffic
        cluster (row-index intersection, not just matching counts).
    """
    order_time_parsed = pd.to_datetime(df["Order_Time"], format="%H:%M:%S", errors="coerce")
    weather_missing = df["Weather"].isna()
    traffic_missing = df["Traffic"].isna()
    order_time_fail = order_time_parsed.isna()

    cluster_mask = weather_missing | traffic_missing
    confirmed_full_overlap = bool(
        set(df.index[cluster_mask]) == set(df.index[order_time_fail])
    )

    excluded_df = df.loc[cluster_mask].copy()
    excluded_df["exclusion_reason"] = "missing Weather / masked-missing Traffic (Step 3 cluster)"
    retained_df = df.loc[~cluster_mask].copy()
    return retained_df, excluded_df, confirmed_full_overlap


def _step4_5_agent_rating_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Steps 4-5 — flag Agent_Rating bound violations (>5, a data-entry
    error) and true nulls, both excluded from the agent-rating KPI only.
    See DATA_CLEANING_PLAN.md Steps 4-5 and STAR_SCHEMA.md DimAgent.

    Two distinct flags are added, per STAR_SCHEMA.md's design:
      - `agent_rating_available_flag`: True if the rating is not null.
      - `agent_rating_valid_flag`: True only if available AND within
        the plausible 1-5 scale (used to exclude the rating KPI).
    """
    df = df.copy()
    df["agent_rating_available_flag"] = df["Agent_Rating"].notna()
    df["agent_rating_valid_flag"] = df["agent_rating_available_flag"] & df[
        "Agent_Rating"
    ].between(AGENT_RATING_MIN_VALID, AGENT_RATING_MAX_VALID)
    return df


def _step6_agent_age_flag(df: pd.DataFrame) -> pd.DataFrame:
    """Step 6 — flag Agent_Age outside the plausible 18-65 working-age bound.
    See DATA_CLEANING_PLAN.md Step 6."""
    df = df.copy()
    df["agent_age_valid_flag"] = df["Agent_Age"].between(
        AGENT_AGE_MIN_PLAUSIBLE, AGENT_AGE_MAX_PLAUSIBLE
    )
    return df


def _step7_coordinates_flag(df: pd.DataFrame) -> pd.DataFrame:
    """Step 7 — flag rows with store or drop coordinates outside the
    plausible India bounding box (includes exact (0,0) placeholders as a
    subset). See DATA_CLEANING_PLAN.md Step 7."""
    df = df.copy()
    store_valid = df["Store_Latitude"].between(INDIA_LAT_MIN, INDIA_LAT_MAX) & df[
        "Store_Longitude"
    ].between(INDIA_LON_MIN, INDIA_LON_MAX)
    drop_valid = df["Drop_Latitude"].between(INDIA_LAT_MIN, INDIA_LAT_MAX) & df[
        "Drop_Longitude"
    ].between(INDIA_LON_MIN, INDIA_LON_MAX)
    df["coordinates_valid_flag"] = store_valid & drop_valid
    return df


def _step8_area_other_flag(df: pd.DataFrame) -> pd.DataFrame:
    """Step 8 — flag `Area == "Other"` rows as excluded from area-tier
    comparisons only; rows are retained in the full dataset.
    See DATA_CLEANING_PLAN.md Step 8."""
    df = df.copy()
    df["area_tier_valid_flag"] = df["Area"] != AREA_UNDEFINED_VALUE
    return df


def _step9_note_spelling_preserved() -> str:
    """Step 9 — the "Metropolitian" spelling is preserved as-is in stored
    data; no transformation applied. See DATA_CLEANING_PLAN.md Step 9."""
    return (
        "Preserved source spelling 'Metropolitian' in the Area column "
        "(no data mutation). Display-label mapping to 'Metropolitan' is "
        "deferred to the dashboard/documentation layer, per DATA_CLEANING_PLAN.md Step 9."
    )


def apply_cleaning_steps(df_raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Apply DATA_CLEANING_PLAN.md Steps 1-9, in order, to the raw dataset.

    Args:
        df_raw: The unmodified raw dataset as loaded by `data_loader`.

    Returns:
        (cleaned_df, summary) where `cleaned_df` is the dataset used for
        all downstream feature engineering (with the Step 3 cluster
        excluded and Steps 4-8 validity flags attached), and `summary`
        is a dict following the DATA_CLEANING_PLAN.md Cleaning Log
        Template exactly, for rendering into `cleaning_log.md`.
    """
    input_rows = len(df_raw)
    logger.info("Starting cleaning pipeline on %d raw rows", input_rows)

    df = _step1_trim_whitespace(df_raw)
    logger.info("Step 1 (whitespace trim) applied to %s", ALL_TRIM_COLUMNS)

    df, recoded_count = _step2_recode_masked_traffic(df)
    logger.info("Step 2 (Traffic 'NaN' recode): %d values recoded", recoded_count)

    df, excluded_df, confirmed_overlap = _step3_exclude_missing_cluster(df)
    logger.info(
        "Step 3 (91-row cluster exclusion): %d rows removed; confirmed full "
        "row-level overlap with Order_Time parse failures = %s",
        len(excluded_df),
        confirmed_overlap,
    )

    df = _step4_5_agent_rating_flags(df)
    rating_out_of_range = int(
        (~df["agent_rating_valid_flag"] & df["agent_rating_available_flag"]).sum()
    )
    rating_null = int((~df["agent_rating_available_flag"]).sum())
    logger.info(
        "Step 4 (Agent_Rating >5 flag): %d rows flagged, excluded from agent-rating "
        "KPI only",
        rating_out_of_range,
    )
    logger.info(
        "Step 5 (Agent_Rating null flag): %d rows flagged, excluded from agent-rating "
        "KPI only",
        rating_null,
    )

    df = _step6_agent_age_flag(df)
    age_flagged = int((~df["agent_age_valid_flag"]).sum())
    logger.info(
        "Step 6 (Agent_Age implausible flag): %d rows flagged, excluded from "
        "age-specific analysis only",
        age_flagged,
    )

    df = _step7_coordinates_flag(df)
    coords_flagged = int((~df["coordinates_valid_flag"]).sum())
    logger.info(
        "Step 7 (coordinate bounding-box flag): %d rows flagged, excluded from "
        "distance analysis only",
        coords_flagged,
    )

    df = _step8_area_other_flag(df)
    area_other_count = int((~df["area_tier_valid_flag"]).sum())
    logger.info(
        "Step 8 (Area='Other' handling): %d rows retained, excluded from "
        "area-tier comparison only",
        area_other_count,
    )

    step9_note = _step9_note_spelling_preserved()
    logger.info("Step 9 (Metropolitian spelling): %s", step9_note)

    output_rows_full_exclusion = len(df)
    output_rows_distance_eligible = int(df["coordinates_valid_flag"].sum())
    output_rows_rating_eligible = int(df["agent_rating_valid_flag"].sum())

    summary: dict[str, Any] = {
        "input_rows": input_rows,
        "step1_whitespace_trim": {
            "columns": ALL_TRIM_COLUMNS,
            "rows_removed": 0,
        },
        "step2_traffic_nan_recode": {"values_recoded": recoded_count},
        "step3_cluster_exclusion": {
            "rows_removed": len(excluded_df),
            "reason": "missing Weather / masked-missing Traffic (confirmed row-level "
            "overlap with Order_Time parse failures)",
            "confirmed_full_overlap_with_order_time_failures": confirmed_overlap,
        },
        "step4_agent_rating_out_of_range": {
            "rows_flagged": rating_out_of_range,
            "excluded_from": "agent-rating KPI (KPI_DEFINITIONS.md #6) only",
        },
        "step5_agent_rating_null": {
            "rows_flagged": rating_null,
            "excluded_from": "agent-rating KPI (KPI_DEFINITIONS.md #6) only",
        },
        "step6_agent_age_implausible": {
            "rows_flagged": age_flagged,
            "bound": f"{AGENT_AGE_MIN_PLAUSIBLE}-{AGENT_AGE_MAX_PLAUSIBLE}",
            "excluded_from": "age-specific analysis (Business Question 15) only",
        },
        "step7_coordinate_bounding_box": {
            "rows_flagged": coords_flagged,
            "excluded_from": "distance_km calculation and distance-dependent analysis only",
        },
        "step8_area_other": {
            "rows_retained": area_other_count,
            "excluded_from": "area-tier (Urban/Metropolitan/Semi-Urban) comparisons only",
        },
        "step9_metropolitian_spelling": {"note": step9_note},
        "output_rows_full_exclusion_applied": output_rows_full_exclusion,
        "output_rows_available_for_distance_analysis": output_rows_distance_eligible,
        "output_rows_available_for_agent_rating_analysis": output_rows_rating_eligible,
    }

    logger.info(
        "Cleaning complete: input=%d, output=%d (after Step 3 exclusion only)",
        input_rows,
        output_rows_full_exclusion,
    )
    return df, summary
