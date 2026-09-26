"""Phase 4, Module 3 — Correlation analysis and Pareto root-cause ranking.

Implements STATISTICAL_ANALYSIS.md's correlation inputs (Tests 3-4 use
these, but the formal hypothesis test is Module 4's job — this module
reports descriptive correlation coefficients only) and
PYTHON_ANALYSIS_PLAN.md's Pareto ranking, cross-validated against
sql/analysis/Q14 and Q20.

CORRELATION != CAUSATION: every result below is reported as an observed
relationship. No causal language is used anywhere in this module.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from _common import classify_correlation_r, load_cleaned_data, logger, save_json
from config import EDA_SUMMARY_JSON, PARETO_RANKING_CSV


def _correlation_pair(x: pd.Series, y: pd.Series, label: str) -> dict[str, Any]:
    """Pearson + Spearman for one variable pair, with a linearity diagnostic:
    if Spearman and Pearson are close, the relationship is well-approximated
    as linear; if Spearman notably exceeds Pearson in magnitude, the
    relationship is more monotonic-than-linear. This is a quantitative proxy
    for the "scatterplot review" STATISTICAL_ANALYSIS.md specifies — the
    actual scatterplot is also rendered in Module visualization output for
    direct visual review."""
    pearson_r, pearson_p = stats.pearsonr(x, y)
    spearman_r, spearman_p = stats.spearmanr(x, y)
    linearity_gap = abs(spearman_r) - abs(pearson_r)
    return {
        "label": label,
        "n": int(len(x)),
        "pearson_r": round(float(pearson_r), 4),
        "pearson_r_squared": round(float(pearson_r) ** 2, 4),
        "pearson_p_value": float(pearson_p),
        "pearson_strength": classify_correlation_r(pearson_r),
        "spearman_r": round(float(spearman_r), 4),
        "spearman_p_value": float(spearman_p),
        "linearity_gap_spearman_minus_pearson_abs": round(float(linearity_gap), 4),
        "relationship_shape_note": (
            "Spearman and Pearson are close in magnitude — a linear "
            "approximation is reasonable."
            if abs(linearity_gap) < 0.03
            else "Spearman exceeds Pearson notably — relationship is more "
            "monotonic than strictly linear; consider Spearman as primary."
        ),
    }


def distance_correlation(df: pd.DataFrame) -> dict[str, Any]:
    """distance_km vs delivery_time_minutes, coordinates_valid_flag rows only."""
    valid = df.loc[df["coordinates_valid_flag"]]
    return _correlation_pair(
        valid["distance_km"], valid["Delivery_Time"], "distance_km vs delivery_time_minutes"
    )


def agent_rating_correlation(df: pd.DataFrame) -> dict[str, Any]:
    """agent_rating vs delivery_time_minutes, agent_rating_valid_flag rows only."""
    valid = df.loc[df["agent_rating_valid_flag"]]
    return _correlation_pair(
        valid["Agent_Rating"], valid["Delivery_Time"], "agent_rating vs delivery_time_minutes"
    )


def agent_age_correlations(df: pd.DataFrame) -> dict[str, Any]:
    """agent_age vs delivery_time_minutes AND vs agent_rating, rows passing
    BOTH validity flags, per STATISTICAL_ANALYSIS.md / SQL_ANALYSIS_PLAN.md
    Q15's explicit requirement."""
    valid = df.loc[df["agent_age_valid_flag"] & df["agent_rating_valid_flag"]]
    return {
        "age_vs_delivery_time": _correlation_pair(
            valid["Agent_Age"], valid["Delivery_Time"], "agent_age vs delivery_time_minutes"
        ),
        "age_vs_rating": _correlation_pair(
            valid["Agent_Age"], valid["Agent_Rating"], "agent_age vs agent_rating"
        ),
    }


def pareto_ranking(df: pd.DataFrame) -> pd.DataFrame:
    """Breach-volume Pareto ranking by Area, Category, and Weather+Traffic
    combination — cross-validates against sql/analysis/Q14 and Q20. Reads
    the frozen sla_breach_flag as-is."""
    rows = []
    for dim_name, group_cols in [
        ("area", ["Area"]),
        ("category", ["Category"]),
        ("weather_traffic", ["Weather", "Traffic"]),
    ]:
        g = df.groupby(group_cols)["sla_breach_flag"].agg(breach_count="sum", n="count").reset_index()
        g = g.sort_values("breach_count", ascending=False).reset_index(drop=True)
        g["breach_rank"] = g.index + 1
        g["cumulative_breach_count"] = g["breach_count"].cumsum()
        g["cumulative_breach_share_pct"] = (
            100 * g["cumulative_breach_count"] / g["breach_count"].sum()
        ).round(4)
        g["dimension"] = dim_name
        g["segment"] = g[group_cols].astype(str).agg(" / ".join, axis=1)
        rows.append(
            g[["dimension", "segment", "n", "breach_count", "breach_rank", "cumulative_breach_share_pct"]]
        )

    pareto_df = pd.concat(rows, ignore_index=True)
    return pareto_df


def main() -> None:
    df = load_cleaned_data()

    results: dict[str, Any] = {
        "distance_vs_delivery_time": distance_correlation(df),
        "agent_rating_vs_delivery_time": agent_rating_correlation(df),
        "agent_age_correlations": agent_age_correlations(df),
    }
    save_json({"03_correlation_analysis": results}, EDA_SUMMARY_JSON)

    pareto_df = pareto_ranking(df)
    PARETO_RANKING_CSV.parent.mkdir(parents=True, exist_ok=True)
    pareto_df.to_csv(PARETO_RANKING_CSV, index=False)
    logger.info("Wrote %s (%d rows)", PARETO_RANKING_CSV, len(pareto_df))

    logger.info("Module 3 (correlation + Pareto) complete")


if __name__ == "__main__":
    main()
