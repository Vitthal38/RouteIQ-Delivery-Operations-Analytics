"""How much do the conclusions depend on the SLA definition?

The SLA is an analyst-defined benchmark: each category's P75 of delivery time,
computed in-sample. So ~25% of deliveries breach BY CONSTRUCTION, and 76% on-time
is not evidence of good or bad performance. No external business promise exists in
the data, and none is invented here. Instead this module re-runs the analysis at
P70 / P75 / P80 / P90 and asks which findings survive.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from routeiq.analysis.segments import segment_table
from routeiq.config import SLA_SENSITIVITY_PERCENTILES
from routeiq.statistics.effects import risk_ratio


def category_thresholds(df: pd.DataFrame, p: float) -> pd.Series:
    """Per-category percentile of delivery time (linear interpolation = SQL PERCENTILE_CONT = DAX PERCENTILE.INC)."""
    return df.groupby("category")["delivery_time_minutes"].apply(lambda s: float(np.percentile(s, 100 * p)))


def breach_at(df: pd.DataFrame, p: float) -> pd.Series:
    thr = df["category"].map(category_thresholds(df, p))
    return (df["delivery_time_minutes"] > thr).astype(int)


def threshold_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for p in SLA_SENSITIVITY_PERCENTILES:
        for cat, thr in category_thresholds(df, p).items():
            rows.append({"percentile": p, "category": cat, "threshold_minutes": thr})
    return pd.DataFrame(rows)


def overall_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for p in SLA_SENSITIVITY_PERCENTILES:
        b = breach_at(df, p)
        rows.append({"percentile": p, "breached_deliveries": int(b.sum()), "breach_rate_pct": 100 * b.mean(),
                     "on_time_rate_pct": 100 * (1 - b.mean()),
                     "expected_breach_rate_if_no_ties_pct": 100 * (1 - p)})
    return pd.DataFrame(rows)


SEGMENT_VARIABLES = ["traffic", "weather", "area", "vehicle", "rating_group", "age_group", "hour_band"]


def _with_groups(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["rating_group"] = np.where(out["rating_lt_4_5"].isna(), "no rating",
                                   np.where(out["rating_lt_4_5"] == 1, "rating < 4.5", "rating >= 4.5"))
    out["age_group"] = np.where(out["age_ge_30"] == 1, "age >= 30", "age < 30")
    return out


def segment_rates_by_percentile(df: pd.DataFrame) -> pd.DataFrame:
    d = _with_groups(df)
    rows = []
    for p in SLA_SENSITIVITY_PERCENTILES:
        dd = d.assign(breach_flag=breach_at(d, p))
        for var in SEGMENT_VARIABLES:
            t = segment_table(dd, var)
            t["percentile"] = p
            rows.append(t[["percentile", "variable", "level", "n", "breaches", "breach_rate"]])
    return pd.concat(rows, ignore_index=True)


def ranking_stability(seg: pd.DataFrame, min_n: int = 200) -> pd.DataFrame:
    """Does the ordering of segments survive a different SLA percentile?

    Levels with fewer than ``min_n`` deliveries at P75 (e.g. the 54 unrated rows) are left out:
    they would create instability that is just sampling noise. Kendall tau needs >= 3 levels;
    for two-level variables the useful question is whether the riskier level stays the same.
    """
    rows = []
    for var, sub in seg.groupby("variable"):
        base_n = sub[sub["percentile"] == 0.75].set_index("level")["n"]
        sub = sub[sub["level"].isin(base_n[base_n >= min_n].index)]
        wide = sub.pivot(index="level", columns="percentile", values="breach_rate")
        base = wide[0.75]
        for p in SLA_SENSITIVITY_PERCENTILES:
            tau = stats.kendalltau(base, wide[p])[0] if len(wide) >= 3 else np.nan
            rows.append({"variable": var, "percentile": p, "n_levels": len(wide),
                         "kendall_tau_vs_p75": tau,
                         "same_highest_level_as_p75": bool(wide[p].idxmax() == base.idxmax()),
                         "same_lowest_level_as_p75": bool(wide[p].idxmin() == base.idxmin()),
                         "highest_breach_level": wide[p].idxmax(), "highest_breach_rate": float(wide[p].max()),
                         "lowest_breach_level": wide[p].idxmin(), "lowest_breach_rate": float(wide[p].min())})
    return pd.DataFrame(rows)


def driver_stability(df: pd.DataFrame) -> pd.DataFrame:
    """Risk ratios and Model-A odds ratios for the main drivers at each SLA percentile."""
    d = _with_groups(df)
    rows = []
    contrasts = [
        ("Jam vs Low traffic", lambda x: (x["traffic"] == "Jam", x["traffic"] == "Low")),
        ("Cloudy/Fog vs Sunny weather", lambda x: (x["weather"].isin(["Cloudy", "Fog"]), x["weather"] == "Sunny")),
        ("rating < 4.5 vs >= 4.5", lambda x: (x["rating_lt_4_5"] == 1, x["rating_lt_4_5"] == 0)),
        ("age >= 30 vs < 30", lambda x: (x["age_ge_30"] == 1, x["age_ge_30"] == 0)),
        ("peak (17-23h) vs off-peak", lambda x: (x["is_peak_hour"] == 1, x["is_peak_hour"] == 0)),
        ("motorcycle vs scooter/van", lambda x: (x["vehicle"] == "motorcycle", x["vehicle"] != "motorcycle")),
        ("prep 15 vs 5 min", lambda x: (x["prep_time_minutes"] == 15, x["prep_time_minutes"] == 5)),
    ]
    for p in SLA_SENSITIVITY_PERCENTILES:
        dd = d.assign(breach_flag=breach_at(d, p))
        for label, fn in contrasts:
            exp, ref = fn(dd)
            a, b = dd[exp], dd[ref]
            rr, lo, hi = risk_ratio(a["breach_flag"].sum(), len(a), b["breach_flag"].sum(), len(b))
            rows.append({"percentile": p, "contrast": label, "rate_exposed": a["breach_flag"].mean(),
                         "rate_reference": b["breach_flag"].mean(), "risk_ratio": rr, "rr_ci_low": lo, "rr_ci_high": hi})
    return pd.DataFrame(rows)


def semi_urban_by_percentile(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for p in SLA_SENSITIVITY_PERCENTILES:
        b = breach_at(df, p)
        su = df["area"] == "Semi-Urban"
        rows.append({"percentile": p, "semi_urban_n": int(su.sum()), "semi_urban_breach_rate": float(b[su].mean())})
    return pd.DataFrame(rows)
