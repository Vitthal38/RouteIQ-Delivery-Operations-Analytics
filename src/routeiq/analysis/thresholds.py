"""Agent rating and age: is the relationship a gradual slope, or a step?

Correlation coefficients (r, r-squared) describe a *linear* relationship. For an
ordinal attribute that behaves like a step (low below a cut, high above it) they
understate the effect badly. This module looks at the shape directly, using only
descriptive comparisons (breach rate by exact value, a scan over candidate cut
points scored by percentage-point gap, and stratified rate comparisons) -
no statistical model is fitted.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from routeiq.statistics.effects import (
    mantel_haenszel_or, mantel_haenszel_rr, risk_difference, risk_ratio, wilson_ci,
)


def exact_value_table(df: pd.DataFrame, col: str) -> pd.DataFrame:
    sub = df.dropna(subset=[col])
    g = sub.groupby(col)["breach_flag"].agg(n="size", breaches="sum").reset_index().rename(columns={col: "value"})
    g["breach_rate"] = g["breaches"] / g["n"]
    ci = [wilson_ci(r.breaches, r.n) for r in g.itertuples()]
    g["ci_low"], g["ci_high"] = [c[0] for c in ci], [c[1] for c in ci]
    g["small_sample_flag"] = g["n"] < 200
    return g


def scan_cutpoints(df: pd.DataFrame, col: str, candidates: list[float]) -> pd.DataFrame:
    """For each candidate cut c: breach rate below (< c) vs at/above (>= c).

    This is a SENSITIVITY table, not a way to locate the step: many nearby cuts across a wide,
    noisy-but-uniformly-high plateau can all show a similarly large two-group gap. The actual step
    location is found separately, from the single largest jump between adjacent exact values
    (see ``largest_single_step``). Cuts with fewer than 100 deliveries on either side are skipped.
    """
    sub = df.dropna(subset=[col])
    rows = []
    for c in candidates:
        below, above = sub[sub[col] < c], sub[sub[col] >= c]
        if len(below) < 100 or len(above) < 100:
            continue
        kb, nb, ka, na = below["breach_flag"].sum(), len(below), above["breach_flag"].sum(), len(above)
        rd, rd_lo, rd_hi = risk_difference(kb, nb, ka, na)
        rr, rr_lo, rr_hi = risk_ratio(kb, nb, ka, na)
        rows.append({"cut": c, "n_below": nb, "n_at_or_above": na,
                     "rate_below": kb / nb, "rate_at_or_above": ka / na,
                     "risk_diff_pts": 100 * rd, "rd_ci_low_pts": 100 * rd_lo, "rd_ci_high_pts": 100 * rd_hi,
                     "risk_ratio": rr, "rr_ci_low": rr_lo, "rr_ci_high": rr_hi})
    return pd.DataFrame(rows)


def largest_single_step(df: pd.DataFrame, col: str, min_n: int = 100) -> dict:
    """Where is the sharpest single jump in breach rate between two adjacent exact values?

    Values with fewer than ``min_n`` deliveries are dropped first (their jumps are noise, not
    signal), then the biggest jump between two values that remain NEXT TO EACH OTHER in the
    original sorted order is reported. This directly answers "where is the step", which a
    two-group cutpoint scan cannot: many splits across a flat-but-noisy plateau can all look
    similarly good, only the single adjacent-value jump pinpoints where the rate actually moves.
    """
    t = exact_value_table(df, col).sort_values("value").reset_index(drop=True)
    reliable = t[t["n"] >= min_n].reset_index(drop=True)
    gaps = reliable["breach_rate"].diff()
    idx = gaps.abs().idxmax()
    return {
        "column": col, "cut": float(reliable.loc[idx, "value"]),
        "value_below": float(reliable.loc[idx - 1, "value"]), "value_at_cut": float(reliable.loc[idx, "value"]),
        "rate_below": float(reliable.loc[idx - 1, "breach_rate"]), "rate_at_cut": float(reliable.loc[idx, "breach_rate"]),
        "n_below": int(reliable.loc[idx - 1, "n"]), "n_at_cut": int(reliable.loc[idx, "n"]),
        "step_size_pts": 100 * float(gaps.loc[idx]),
        "typical_other_step_pts": 100 * float(gaps.drop(index=idx).abs().median()),
        "n_reliable_values": len(reliable), "n_values_dropped_for_small_n": len(t) - len(reliable),
    }




def stratified_effect(df: pd.DataFrame, flag_col: str, strata: list[str]) -> dict[str, float]:
    """Mantel-Haenszel common risk/odds ratio for a 0/1 exposure, controlling for ``strata``.

    Semi-Urban (all breach) is excluded from the strata: a 100% cell carries no information
    about the contrast and only causes separation.
    """
    sub = df[(df["area"] != "Semi-Urban")].dropna(subset=[flag_col])
    tables, rr_strata = [], []
    for _, s in sub.groupby(strata):
        e, u = s[s[flag_col] == 1], s[s[flag_col] == 0]
        if len(e) == 0 or len(u) == 0:
            continue
        a, c = e["breach_flag"].sum(), u["breach_flag"].sum()
        tables.append([[a, len(e) - a], [c, len(u) - c]])
        rr_strata.append((a, len(e), c, len(u)))
    orr, olo, ohi = mantel_haenszel_or(tables)
    rr, rlo, rhi = mantel_haenszel_rr(rr_strata)
    # crude ratio for comparison
    e, u = sub[sub[flag_col] == 1], sub[sub[flag_col] == 0]
    crude, clo, chi = risk_ratio(e["breach_flag"].sum(), len(e), u["breach_flag"].sum(), len(u))
    return {"exposure": flag_col, "strata": " x ".join(strata), "n_strata": len(tables),
            "crude_risk_ratio": crude, "crude_rr_ci_low": clo, "crude_rr_ci_high": chi,
            "mh_risk_ratio": rr, "mh_rr_ci_low": rlo, "mh_rr_ci_high": rhi,
            "mh_odds_ratio": orr, "mh_or_ci_low": olo, "mh_or_ci_high": ohi}


def effect_by_traffic(df: pd.DataFrame, flag_col: str) -> pd.DataFrame:
    """The 0/1 exposure's breach rates inside each traffic level (does the effect persist?)."""
    sub = df[(df["area"] != "Semi-Urban")].dropna(subset=[flag_col])
    rows = []
    for traffic, s in sub.groupby("traffic"):
        e, u = s[s[flag_col] == 1], s[s[flag_col] == 0]
        rr, lo, hi = risk_ratio(e["breach_flag"].sum(), len(e), u["breach_flag"].sum(), len(u))
        rows.append({"traffic": traffic, "n_exposed": len(e), "rate_exposed": e["breach_flag"].mean(),
                     "n_unexposed": len(u), "rate_unexposed": u["breach_flag"].mean(),
                     "risk_ratio": rr, "rr_ci_low": lo, "rr_ci_high": hi})
    return pd.DataFrame(rows)


def rating_age_grid(df: pd.DataFrame) -> pd.DataFrame:
    sub = df.dropna(subset=["rating_lt_4_5"])
    g = sub.groupby(["rating_lt_4_5", "age_ge_30"])["breach_flag"].agg(n="size", breaches="sum").reset_index()
    g["breach_rate"] = g["breaches"] / g["n"]
    g["share_of_breaches"] = g["breaches"] / df["breach_flag"].sum()
    g["group"] = np.where(g["rating_lt_4_5"] == 1, "rating < 4.5", "rating >= 4.5") + ", " + np.where(
        g["age_ge_30"] == 1, "age >= 30", "age < 30")
    return g
