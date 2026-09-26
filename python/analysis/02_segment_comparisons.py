"""Phase 4, Module 2 — Segment comparisons: weekend/weekday, temporal
pattern, and agent-attribute-level comparisons.

Implements the remaining PYTHON_ANALYSIS_PLAN.md Phase 2 EDA items not
covered by Module 1 (which handled Area/Category/Weather/Traffic/Vehicle
by Delivery_Time). Reads data/cleaned/cleaned_delivery.csv read-only.

AGENT LIMITATION (Step 12): the source dataset has no true Agent_ID.
Every agent comparison below is at the attribute level (rating band, age
band) — never an individual-agent claim.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from _common import load_cleaned_data, logger, save_json
from config import EDA_SUMMARY_JSON


def weekend_vs_weekday(df: pd.DataFrame) -> dict[str, Any]:
    grouped = df.groupby("is_weekend")["Delivery_Time"]
    result = {}
    for is_weekend, series in grouped:
        label = "weekend" if is_weekend else "weekday"
        result[label] = {
            "n": int(len(series)),
            "mean": round(float(series.mean()), 4),
            "median": float(series.median()),
            "std": round(float(series.std()), 2),
            "p90": round(float(np.percentile(series, 90)), 2),
        }
    return result


def weekly_temporal_pattern(df: pd.DataFrame) -> dict[str, Any]:
    """Weekly avg/P90 trend, mirroring sql/analysis/Q11 for cross-validation.
    Partial weeks (fewer than 7 distinct calendar days observed) are flagged,
    not silently treated as full weeks."""
    weekly = df.groupby("week_number").agg(
        n=("Delivery_Time", "count"),
        avg_delivery_time=("Delivery_Time", "mean"),
        p90_delivery_time=("Delivery_Time", lambda s: np.percentile(s, 90)),
        distinct_days_observed=("day_of_week", "count"),  # placeholder, corrected below
    )
    # distinct_days_observed needs actual distinct Order_Date count per week,
    # not a row count — recompute properly.
    order_date = pd.to_datetime(df["Order_Date"])
    distinct_days = (
        df.assign(_date=order_date)
        .groupby("week_number")["_date"]
        .nunique()
    )
    weekly["distinct_days_observed"] = distinct_days
    weekly["partial_week_flag"] = weekly["distinct_days_observed"] < 7
    weekly["week_avg_delta_vs_prior"] = weekly["avg_delivery_time"].diff()

    result: dict[str, Any] = {}
    for week_number, row in weekly.iterrows():
        result[str(week_number)] = {
            "n": int(row["n"]),
            "avg_delivery_time": round(float(row["avg_delivery_time"]), 2),
            "p90_delivery_time": round(float(row["p90_delivery_time"]), 2),
            "distinct_days_observed": int(row["distinct_days_observed"]),
            "partial_week_flag": bool(row["partial_week_flag"]),
            "avg_delta_vs_prior_week": (
                round(float(row["week_avg_delta_vs_prior"]), 2)
                if pd.notna(row["week_avg_delta_vs_prior"]) else None
            ),
        }
    return result


def agent_rating_band_comparison(df: pd.DataFrame) -> dict[str, Any]:
    """ATTRIBUTE-LEVEL only — rating band, not individual agent (Step 12)."""
    valid = df.loc[df["agent_rating_valid_flag"]].copy()
    valid["rating_band"] = (np.floor(valid["Agent_Rating"] / 0.5) * 0.5).astype(float)
    grouped = valid.groupby("rating_band")["Delivery_Time"]
    result = {}
    for band, series in grouped:
        result[str(band)] = {
            "n": int(len(series)),
            "mean": round(float(series.mean()), 2),
            "std": round(float(series.std()), 2),
        }
    return {"n_valid_rating_rows": int(len(valid)), "by_rating_band": result}


def agent_age_band_comparison(df: pd.DataFrame) -> dict[str, Any]:
    """ATTRIBUTE-LEVEL only — age band, not individual agent (Step 12)."""
    valid = df.loc[df["agent_age_valid_flag"]].copy()
    bins = [17, 25, 35, 45, 65]
    labels = ["18-25", "26-35", "36-45", "46-65"]
    valid["age_band"] = pd.cut(valid["Agent_Age"], bins=bins, labels=labels)
    grouped = valid.groupby("age_band", observed=True)["Delivery_Time"]
    result = {}
    for band, series in grouped:
        result[str(band)] = {
            "n": int(len(series)),
            "mean": round(float(series.mean()), 2),
            "std": round(float(series.std()), 2),
        }
    return {"n_valid_age_rows": int(len(valid)), "by_age_band": result}


def main() -> None:
    df = load_cleaned_data()

    results: dict[str, Any] = {
        "weekend_vs_weekday": weekend_vs_weekday(df),
        "weekly_temporal_pattern": weekly_temporal_pattern(df),
        "agent_rating_band_comparison_attribute_level_only": agent_rating_band_comparison(df),
        "agent_age_band_comparison_attribute_level_only": agent_age_band_comparison(df),
    }

    save_json({"02_segment_comparisons": results}, EDA_SUMMARY_JSON)
    logger.info("Module 2 (segment comparisons) complete")


if __name__ == "__main__":
    main()
