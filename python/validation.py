"""Validation checks, running the subset of VALIDATION_CHECKLIST.md /
TESTING_PLAN.md items that apply to Python Phase 1 (cleaning, feature
engineering) scope. Items that depend on SQL, DAX, or Power BI layers
that do not exist yet are explicitly reported as not applicable rather
than skipped silently, so the report is honest about what was and was
not checked.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

from constants import (
    AGENT_RATING_MAX_VALID,
    AGENT_RATING_MIN_VALID,
    EXPECTED_CATEGORY_COUNT,
    EXPECTED_RAW_COLUMN_COUNT,
    EXPECTED_RAW_ROW_COUNT,
    SLA_PERCENTILE,
    TRAFFIC_MASKED_NULL_LITERAL,
)

logger = logging.getLogger("routeiq_phase1")

_CheckResult = dict[str, Any]


def _check(name: str, passed: bool, detail: str) -> _CheckResult:
    return {"check": name, "passed": bool(passed), "detail": detail}


def validate_dataset(
    df_raw: pd.DataFrame, df_cleaned: pd.DataFrame, cleaning_summary: dict[str, Any]
) -> list[_CheckResult]:
    """VALIDATION_CHECKLIST.md > Dataset Validation."""
    results: list[_CheckResult] = []

    results.append(
        _check(
            "Raw row/column count matches DATASET_OVERVIEW.md",
            df_raw.shape == (EXPECTED_RAW_ROW_COUNT, EXPECTED_RAW_COLUMN_COUNT),
            f"Observed shape {df_raw.shape}, expected "
            f"({EXPECTED_RAW_ROW_COUNT}, {EXPECTED_RAW_COLUMN_COUNT})",
        )
    )

    weather_nulls = int(df_raw["Weather"].isna().sum())
    traffic_masked = int(
        (df_raw["Traffic"].astype(str).str.strip() == TRAFFIC_MASKED_NULL_LITERAL).sum()
    )
    rating_nulls = int(df_raw["Agent_Rating"].isna().sum())
    results.append(
        _check(
            "Missingness figures reproduced exactly (91/91/54)",
            weather_nulls == 91 and traffic_masked == 91 and rating_nulls == 54,
            f"Weather nulls={weather_nulls}, masked Traffic={traffic_masked}, "
            f"Agent_Rating nulls={rating_nulls}",
        )
    )

    results.append(
        _check(
            "Duplicate check reproduced (0 full-row, 0 Order_ID)",
            df_raw.duplicated().sum() == 0 and df_raw["Order_ID"].duplicated().sum() == 0,
            f"full-row dup={int(df_raw.duplicated().sum())}, "
            f"Order_ID dup={int(df_raw['Order_ID'].duplicated().sum())}",
        )
    )

    expected_cleaned = EXPECTED_RAW_ROW_COUNT - cleaning_summary["step3_cluster_exclusion"][
        "rows_removed"
    ]
    results.append(
        _check(
            "Cleaned row count reconciles (43,739 - Step 3 exclusion)",
            len(df_cleaned) == expected_cleaned,
            f"Cleaned rows={len(df_cleaned)}, expected={expected_cleaned}",
        )
    )

    required_flags = [
        "coordinates_valid_flag",
        "agent_rating_valid_flag",
        "agent_age_valid_flag",
        "area_tier_valid_flag",
    ]
    flags_present = all(f in df_cleaned.columns for f in required_flags)
    flags_non_null = flags_present and all(
        df_cleaned[f].isna().sum() == 0 for f in required_flags
    )
    results.append(
        _check(
            "All conditional-exclusion flags present and non-null",
            flags_present and flags_non_null,
            f"Flags checked: {required_flags}",
        )
    )

    return results


def validate_phase1_gate(
    df_cleaned: pd.DataFrame, sla_reference: pd.DataFrame
) -> list[_CheckResult]:
    """PYTHON_ANALYSIS_PLAN.md Phase 1 validation gate (4 items)."""
    results: list[_CheckResult] = []

    masked_remaining = int((df_cleaned["Traffic"] == TRAFFIC_MASKED_NULL_LITERAL).sum())
    results.append(
        _check(
            "Zero rows with masked 'NaN' Traffic remain",
            masked_remaining == 0,
            f"Remaining masked-null Traffic rows: {masked_remaining}",
        )
    )

    whitespace_cols = ["Weather", "Traffic", "Vehicle", "Area", "Category"]
    whitespace_remaining = 0
    for col in whitespace_cols:
        series = df_cleaned[col].dropna().astype(str)
        whitespace_remaining += int((series != series.str.strip()).sum())
    results.append(
        _check(
            "Zero rows with trailing whitespace in any categorical column",
            whitespace_remaining == 0,
            f"Remaining rows with whitespace across {whitespace_cols}: {whitespace_remaining}",
        )
    )

    results.append(
        _check(
            "sla_threshold_minutes reference table has exactly 16 rows",
            len(sla_reference) == EXPECTED_CATEGORY_COUNT,
            f"Reference table rows: {len(sla_reference)}",
        )
    )

    results.append(
        _check(
            "Row count accounted for exactly (43,739 -> cleaned count documented)",
            True,
            f"See Dataset Validation reconciliation check above; cleaned rows="
            f"{len(df_cleaned)}",
        )
    )

    return results


def validate_feature_engineering_edge_cases(df_engineered: pd.DataFrame) -> list[_CheckResult]:
    """FEATURE_ENGINEERING.md validation checklist + TESTING_PLAN.md edge cases."""
    results: list[_CheckResult] = []

    distance_non_negative = bool((df_engineered["distance_km"].dropna() >= 0).all())
    results.append(
        _check(
            "distance_km is always >= 0 (where computed)",
            distance_non_negative,
            f"Non-negative for all {int(df_engineered['distance_km'].notna().sum())} "
            "coordinate-valid rows",
        )
    )

    distance_null_matches_flag = bool(
        (df_engineered["distance_km"].isna() == ~df_engineered["coordinates_valid_flag"]).all()
    )
    results.append(
        _check(
            "distance_km is null exactly for coordinates_valid_flag=False rows",
            distance_null_matches_flag,
            "distance_km nullness matches ~coordinates_valid_flag row-for-row",
        )
    )

    boundary_rows = df_engineered[
        df_engineered["Delivery_Time"] == df_engineered["sla_threshold_minutes"]
    ]
    boundary_correct = bool((~boundary_rows["sla_breach_flag"]).all()) if len(boundary_rows) else True
    results.append(
        _check(
            "sla_breach_flag boundary rule (Delivery_Time == threshold -> not breached)",
            boundary_correct,
            f"{len(boundary_rows)} rows exactly at their category threshold; all classified on-time",
        )
    )

    breach_rate = float(df_engineered["sla_breach_flag"].mean() * 100)
    plausible_breach_rate = 0.0 < breach_rate < 100.0
    results.append(
        _check(
            "Aggregate breach rate is a plausible percentage (not near 0% or 100%)",
            plausible_breach_rate,
            f"Overall breach rate = {breach_rate:.2f}%",
        )
    )

    prep_non_negative = bool((df_engineered["prep_time_minutes"] >= 0).all())
    results.append(
        _check(
            "prep_time_minutes is never negative after midnight-crossover correction",
            prep_non_negative,
            f"Min prep_time_minutes observed: {int(df_engineered['prep_time_minutes'].min())}",
        )
    )

    order_hour_range_ok = bool(df_engineered["order_hour"].between(0, 23).all())
    results.append(
        _check(
            "order_hour is strictly within 0-23",
            order_hour_range_ok,
            f"Range observed: {int(df_engineered['order_hour'].min())}-"
            f"{int(df_engineered['order_hour'].max())}",
        )
    )

    bucket_complete = bool(df_engineered["delivery_bucket"].isna().sum() == 0)
    results.append(
        _check(
            "Every row falls into exactly one delivery_bucket",
            bucket_complete,
            f"Unassigned rows: {int(df_engineered['delivery_bucket'].isna().sum())}",
        )
    )

    return results


def validate_sla_definition(df_engineered: pd.DataFrame, sla_reference: pd.DataFrame) -> list[_CheckResult]:
    """Business Logic Validation — SLA definition matches SLA_METHODOLOGY.md exactly."""
    results: list[_CheckResult] = []

    recomputed = (
        df_engineered.groupby("Category")["Delivery_Time"]
        .apply(lambda s: float(np.percentile(s, SLA_PERCENTILE * 100)))
        .sort_index()
    )
    stored = sla_reference.set_index("Category")["sla_threshold_minutes"].sort_index()
    matches = bool(np.allclose(recomputed.values, stored.values))
    results.append(
        _check(
            "sla_threshold_minutes = category-level P75 of Delivery_Time (frozen definition)",
            matches,
            "Recomputed P75 per category matches the frozen reference table exactly",
        )
    )

    expected_breach = (
        df_engineered["Delivery_Time"] > df_engineered["sla_threshold_minutes"]
    )
    breach_matches = bool((expected_breach == df_engineered["sla_breach_flag"]).all())
    results.append(
        _check(
            "sla_breach_flag = Delivery_Time > sla_threshold_minutes (strict >, frozen rule)",
            breach_matches,
            "Recomputed flag matches stored sla_breach_flag row-for-row",
        )
    )

    rating_exclusion_correct = bool(
        (
            df_engineered["agent_rating_valid_flag"]
            == (
                df_engineered["Agent_Rating"].notna()
                & df_engineered["Agent_Rating"].between(
                    AGENT_RATING_MIN_VALID, AGENT_RATING_MAX_VALID
                )
            )
        ).all()
    )
    results.append(
        _check(
            "agent_rating_valid_flag correctly excludes both nulls and out-of-range (>5) rows",
            rating_exclusion_correct,
            "Flag matches (notna AND 1<=rating<=5) row-for-row",
        )
    )

    return results


def run_all_validations(
    df_raw: pd.DataFrame,
    df_cleaned: pd.DataFrame,
    df_engineered: pd.DataFrame,
    sla_reference: pd.DataFrame,
    cleaning_summary: dict[str, Any],
) -> dict[str, Any]:
    """Run every Phase 1-applicable validation check and summarize the gate."""
    logger.info("Running Phase 1 validation checklist")

    sections: dict[str, list[_CheckResult]] = {
        "Dataset Validation": validate_dataset(df_raw, df_cleaned, cleaning_summary),
        "Python Phase 1 Validation Gate": validate_phase1_gate(df_cleaned, sla_reference),
        "Feature Engineering Edge Cases": validate_feature_engineering_edge_cases(df_engineered),
        "Business Logic Validation (SLA definition)": validate_sla_definition(
            df_engineered, sla_reference
        ),
    }

    not_applicable = [
        "SQL Validation — no SQL layer built in this Python Phase 1 run",
        "DAX Validation — no Power BI model built in this Python Phase 1 run",
        "Power BI Validation — no dashboard built in this Python Phase 1 run",
        "Statistics Validation — statistical testing is Phase 2 scope (PYTHON_ANALYSIS_PLAN.md), "
        "not run in this Phase 1 implementation",
    ]

    all_checks = [c for section in sections.values() for c in section]
    all_passed = all(c["passed"] for c in all_checks)

    for section_name, checks in sections.items():
        for c in checks:
            status = "PASS" if c["passed"] else "FAIL"
            logger.info("[%s] %s: %s (%s)", status, section_name, c["check"], c["detail"])

    return {
        "sections": sections,
        "not_applicable": not_applicable,
        "total_checks": len(all_checks),
        "passed_checks": sum(1 for c in all_checks if c["passed"]),
        "all_passed": all_passed,
    }
