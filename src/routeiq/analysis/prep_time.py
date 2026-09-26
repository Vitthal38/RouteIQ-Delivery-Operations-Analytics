"""Is preparation time associated with delivery time or SLA breach?"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from routeiq.analysis.segments import association, segment_table
from routeiq.statistics.effects import (
    cohens_d, kruskal_epsilon_squared, mantel_haenszel_rr,
)


def prep_profile(df: pd.DataFrame) -> pd.DataFrame:
    seg = segment_table(df, "prep_time_minutes", reference=5, order=[5, 10, 15])
    extra = (df.groupby("prep_time_minutes")["delivery_time_minutes"].agg(mean_delivery_minutes="mean",
                                                                          median_delivery_minutes="median")
             .reset_index().rename(columns={"prep_time_minutes": "level"}))
    return seg.merge(extra, on="level")


def prep_tests(df: pd.DataFrame) -> dict[str, float]:
    """Effect sizes first: V for breach vs prep, epsilon-squared and d for delivery time."""
    assoc = association(df, "prep_time_minutes")
    groups = [g["delivery_time_minutes"].to_numpy() for _, g in df.groupby("prep_time_minutes")]
    h, p, eps2 = kruskal_epsilon_squared(groups)
    d, d_lo, d_hi = cohens_d(groups[2], groups[0])  # 15 min vs 5 min
    rho, rho_p = stats.spearmanr(df["prep_time_minutes"], df["delivery_time_minutes"])
    counts = df["prep_time_minutes"].value_counts().sort_index()
    gof_chi2, gof_p = stats.chisquare(counts.to_numpy())
    return {
        "cramers_v_breach_vs_prep": assoc["cramers_v"],
        "chi2_p_value": assoc["p_value"],
        "kruskal_H": h, "kruskal_p": p, "epsilon_squared_delivery_time": eps2,
        "cohens_d_15_vs_5min": d, "cohens_d_ci_low": d_lo, "cohens_d_ci_high": d_hi,
        "spearman_rho_prep_vs_delivery": float(rho), "spearman_p": float(rho_p),
        "prep_uniform_gof_chi2": float(gof_chi2), "prep_uniform_gof_p": float(gof_p),
        "prep_share_5": float(counts.iloc[0] / counts.sum()),
        "prep_share_10": float(counts.iloc[1] / counts.sum()),
        "prep_share_15": float(counts.iloc[2] / counts.sum()),
    }


def prep_cross(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    out = {}
    for other in ("traffic", "area"):
        g = (df.groupby(["prep_time_minutes", other]).agg(n=("breach_flag", "size"), breaches=("breach_flag", "sum"))
             .reset_index())
        g["breach_rate"] = g["breaches"] / g["n"]
        out[f"prep_x_{other}"] = g
    # Stratified (traffic x area) risk ratio for 15 vs 5 minutes prep.
    strata = []
    for _, sub in df[df["area"] != "Semi-Urban"].groupby(["traffic", "area"]):
        a, b = sub[sub["prep_time_minutes"] == 15], sub[sub["prep_time_minutes"] == 5]
        strata.append((a["breach_flag"].sum(), len(a), b["breach_flag"].sum(), len(b)))
    rr, lo, hi = mantel_haenszel_rr(strata)
    out["prep_mh_rr"] = pd.DataFrame([{"contrast": "prep 15 min vs 5 min (stratified by traffic x area)",
                                       "mh_risk_ratio": rr, "ci_low": lo, "ci_high": hi}])
    return out
