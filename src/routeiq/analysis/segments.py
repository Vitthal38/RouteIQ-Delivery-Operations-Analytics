"""Segment breach rates with confidence intervals, KPIs and a deterministic Pareto."""

from __future__ import annotations

import numpy as np
import pandas as pd

from routeiq.statistics.effects import (
    classify_cramers_v, cramers_v, odds_ratio, risk_ratio, wilson_ci,
)


def kpis(df: pd.DataFrame) -> dict[str, float]:
    """Headline KPIs. The SLA threshold is the frozen category-level P75."""
    n = len(df)
    breaches = int(df["breach_flag"].sum())
    return {
        "total_deliveries": n,
        "breached_deliveries": breaches,
        "breach_rate_pct": 100 * breaches / n,
        "on_time_rate_pct": 100 * (n - breaches) / n,
        "average_delivery_minutes": float(df["delivery_time_minutes"].mean()),
        "median_delivery_minutes": float(df["delivery_time_minutes"].median()),
        "p90_delivery_minutes": float(np.percentile(df["delivery_time_minutes"], 90)),
        "p75_delivery_minutes": float(np.percentile(df["delivery_time_minutes"], 75)),
        "average_minutes_over_sla_when_breached": float(df.loc[df["breach_flag"] == 1, "minutes_over_sla"].mean()),
    }


def segment_table(df: pd.DataFrame, col: str, reference: str | None = None,
                  order: list | None = None) -> pd.DataFrame:
    """Breach rate per level of ``col`` with Wilson CI, volume/breach shares and ratios.

    ``lift`` = share of breaches / share of deliveries (1.0 = proportional).
    Risk ratio and odds ratio are versus ``reference`` (default: the lowest-rate level).
    """
    g = (df.groupby(col, dropna=False)["breach_flag"].agg(n="size", breaches="sum").reset_index()
         .rename(columns={col: "level"}))
    g["breach_rate"] = g["breaches"] / g["n"]
    ci = g.apply(lambda r: wilson_ci(r["breaches"], r["n"]), axis=1)
    g["ci_low"] = [c[0] for c in ci]
    g["ci_high"] = [c[1] for c in ci]
    g["share_of_deliveries"] = g["n"] / g["n"].sum()
    g["share_of_breaches"] = g["breaches"] / g["breaches"].sum()
    g["lift"] = g["share_of_breaches"] / g["share_of_deliveries"]
    ref_level = reference if reference is not None else g.loc[g["breach_rate"].idxmin(), "level"]
    ref = g.loc[g["level"] == ref_level].iloc[0]
    rr = [risk_ratio(r.breaches, r.n, ref.breaches, ref.n) for r in g.itertuples()]
    orr = [odds_ratio(r.breaches, r.n, ref.breaches, ref.n) for r in g.itertuples()]
    g["reference"] = ref_level
    g["risk_ratio"] = [x[0] for x in rr]
    g["rr_ci_low"] = [x[1] for x in rr]
    g["rr_ci_high"] = [x[2] for x in rr]
    g["odds_ratio"] = [x[0] for x in orr]
    g["or_ci_low"] = [x[1] for x in orr]
    g["or_ci_high"] = [x[2] for x in orr]
    g["small_sample_flag"] = g["n"] < 200
    g.insert(0, "variable", col)
    if order is not None:
        g["_o"] = g["level"].map({v: i for i, v in enumerate(order)})
        g = g.sort_values("_o").drop(columns="_o")
    else:
        g = g.sort_values("breach_rate", ascending=False)
    return g.reset_index(drop=True)


def association(df: pd.DataFrame, col: str, outcome: str = "breach_flag") -> dict:
    """Chi-square / Cramer's V for breach vs a categorical variable (effect size first)."""
    tab = pd.crosstab(df[col], df[outcome])
    res = cramers_v(tab.to_numpy())
    res["variable"] = col
    res["effect_band"] = classify_cramers_v(res["cramers_v"], min(tab.shape) - 1)
    return res


def pareto(df: pd.DataFrame, cols: tuple[str, ...] = ("area", "traffic")) -> pd.DataFrame:
    """Breach Pareto with a DETERMINISTIC order: breaches descending, then segment name.

    Ties therefore always rank the same way in Python, SQL (Q14/Q28) and DAX, and the
    cumulative share increases strictly one segment at a time (no duplicated labels).
    """
    g = (df.groupby(list(cols))["breach_flag"].agg(breaches="sum", n="size").reset_index())
    g["segment"] = g[list(cols)].astype(str).agg(" / ".join, axis=1)
    g = g.sort_values(["breaches", "segment"], ascending=[False, True]).reset_index(drop=True)
    g["rank"] = np.arange(1, len(g) + 1)
    g["breach_rate"] = g["breaches"] / g["n"]
    g["share_of_breaches"] = g["breaches"] / g["breaches"].sum()
    g["cumulative_share"] = g["share_of_breaches"].cumsum()
    g["share_of_deliveries"] = g["n"] / g["n"].sum()
    return g
