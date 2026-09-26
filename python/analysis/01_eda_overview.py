"""Phase 4, Module 1 — Descriptive EDA overview.

Implements PYTHON_ANALYSIS_PLAN.md Phase 2 > EDA: overall/segment
distributions of delivery_time_minutes, central tendency/spread, percentile
analysis (P50/P75/P90/P95), SLA breach distribution, and the Step 4 outlier
analysis (descriptive only — the cleaned dataset is an approved artifact
and is never modified here).

Reads data/cleaned/cleaned_delivery.csv read-only. Writes to
output/eda_summary.json (merged with other modules' keys).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from _common import classify_correlation_r, load_cleaned_data, logger, save_json
from config import EDA_SUMMARY_JSON

PERCENTILES = [0.50, 0.75, 0.90, 0.95]


def describe_delivery_time(df: pd.DataFrame) -> dict[str, Any]:
    """Overall delivery-time distribution: central tendency, spread, percentiles."""
    dt = df["Delivery_Time"]
    result = {
        "n": int(len(dt)),
        "min": float(dt.min()),
        "max": float(dt.max()),
        "mean": round(float(dt.mean()), 2),
        "median": float(dt.median()),
        "std": round(float(dt.std()), 2),
        "skewness": round(float(dt.skew()), 4),
        "percentiles": {
            f"p{int(p * 100)}": round(float(np.percentile(dt, p * 100)), 2) for p in PERCENTILES
        },
    }
    logger.info("Overall delivery time: mean=%.2f median=%.1f std=%.2f skew=%.4f",
                result["mean"], result["median"], result["std"], result["skewness"])
    return result


def describe_by_segment(df: pd.DataFrame, segment_col: str) -> dict[str, Any]:
    """Delivery-time distribution grouped by a categorical segment."""
    grouped = df.groupby(segment_col)["Delivery_Time"]
    result: dict[str, Any] = {}
    for name, series in grouped:
        result[str(name)] = {
            "n": int(len(series)),
            "mean": round(float(series.mean()), 2),
            "median": float(series.median()),
            "std": round(float(series.std()), 2),
            "p90": round(float(np.percentile(series, 90)), 2),
        }
    return result


def sla_breach_distribution(df: pd.DataFrame) -> dict[str, Any]:
    """SLA breach distribution overall and by delivery_bucket. Reads the
    frozen sla_breach_flag as-is — never recalculated."""
    overall_rate = round(float(df["sla_breach_flag"].mean() * 100), 4)
    by_bucket = (
        df.groupby("delivery_bucket", observed=True)["sla_breach_flag"]
        .agg(n="count", breach_rate=lambda s: round(float(s.mean() * 100), 2))
        .to_dict(orient="index")
    )
    logger.info("Overall SLA breach rate: %.4f%%", overall_rate)
    return {"overall_breach_rate_pct": overall_rate, "by_delivery_bucket": by_bucket}


def outlier_analysis(df: pd.DataFrame) -> dict[str, Any]:
    """Descriptive outlier analysis (Step 4) — Tukey 1.5xIQR rule applied
    PER CATEGORY (category-level, since categories have materially
    different delivery-time scales — Grocery vs. everything else — a
    global IQR would mislabel Grocery's entire distribution as low
    outliers). No row is removed; this only characterizes what exists in
    the already-approved, already-cleaned dataset.

    Distinguishes:
      - statistical outliers (Tukey rule, within the observed data)
      - whether those rows co-occur with a data-quality flag already
        raised in Phase 1 (invalid coordinates / rating / age) — if so,
        the outlier is likely explained by a known data-quality issue,
        not a genuine extreme delivery
      - the remainder are treated as valid extreme deliveries (long tail
        is the reason P90 is tracked at all, per DATA_PROFILING_PLAN.md's
        Outlier Strategy — they are not errors)
    """
    outlier_flags = pd.Series(False, index=df.index)
    per_category_counts: dict[str, Any] = {}

    for category, group in df.groupby("Category"):
        q1, q3 = np.percentile(group["Delivery_Time"], [25, 75])
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        cat_outliers = (group["Delivery_Time"] < lower) | (group["Delivery_Time"] > upper)
        outlier_flags.loc[group.index] = cat_outliers
        per_category_counts[category] = {
            "n": int(len(group)),
            "iqr_lower_bound": round(float(lower), 2),
            "iqr_upper_bound": round(float(upper), 2),
            "statistical_outliers": int(cat_outliers.sum()),
        }

    total_outliers = int(outlier_flags.sum())
    outlier_rows = df.loc[outlier_flags]

    co_occurs_with_dq_flag = int(
        (
            ~outlier_rows["coordinates_valid_flag"]
            | ~outlier_rows["agent_rating_valid_flag"]
            | ~outlier_rows["agent_age_valid_flag"]
        ).sum()
    )

    result = {
        "method": "Tukey 1.5xIQR rule, computed per Category (not globally) "
        "because category-level delivery-time scale varies materially "
        "(e.g. Grocery). No row is removed from the approved dataset.",
        "total_statistical_outliers": total_outliers,
        "total_outliers_pct_of_dataset": round(100 * total_outliers / len(df), 3),
        "outliers_co_occurring_with_a_known_data_quality_flag": co_occurs_with_dq_flag,
        "outliers_with_no_known_data_quality_flag_valid_extreme_deliveries":
            total_outliers - co_occurs_with_dq_flag,
        "per_category": per_category_counts,
    }
    logger.info(
        "Outlier analysis: %d statistical outliers (%.3f%% of dataset), "
        "%d co-occur with a known data-quality flag, %d are unflagged (valid extreme)",
        total_outliers, result["total_outliers_pct_of_dataset"],
        co_occurs_with_dq_flag, result["outliers_with_no_known_data_quality_flag_valid_extreme_deliveries"],
    )
    return result


def missingness_exclusion_summary(df: pd.DataFrame) -> dict[str, Any]:
    """Self-documenting restatement of Phase 1's exclusion flags, per
    PYTHON_ANALYSIS_PLAN.md Phase 2 EDA requirement (not a re-cleaning)."""
    return {
        "agent_rating_available_flag_false": int((~df["agent_rating_available_flag"]).sum()),
        "agent_rating_valid_flag_false": int((~df["agent_rating_valid_flag"]).sum()),
        "agent_age_valid_flag_false": int((~df["agent_age_valid_flag"]).sum()),
        "coordinates_valid_flag_false": int((~df["coordinates_valid_flag"]).sum()),
        "area_tier_valid_flag_false": int((~df["area_tier_valid_flag"]).sum()),
    }


def main() -> None:
    df = load_cleaned_data()

    results: dict[str, Any] = {
        "overall_delivery_time": describe_delivery_time(df),
        "delivery_time_by_area": describe_by_segment(df, "Area"),
        "delivery_time_by_category": describe_by_segment(df, "Category"),
        "delivery_time_by_weather": describe_by_segment(df, "Weather"),
        "delivery_time_by_traffic": describe_by_segment(df, "Traffic"),
        "delivery_time_by_vehicle": describe_by_segment(df, "Vehicle"),
        "sla_breach_distribution": sla_breach_distribution(df),
        "outlier_analysis": outlier_analysis(df),
        "missingness_exclusion_summary": missingness_exclusion_summary(df),
    }

    save_json({"01_eda_overview": results}, EDA_SUMMARY_JSON)
    logger.info("Module 1 (EDA overview) complete")


if __name__ == "__main__":
    main()
