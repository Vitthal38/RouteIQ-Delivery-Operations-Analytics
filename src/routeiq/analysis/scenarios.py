"""Illustrative what-if scenarios (descriptive arithmetic only, no model).

Every scenario here is ILLUSTRATIVE, NOT A CAUSAL FORECAST. It answers only: "if this
group's breach rate matched a comparison group's, holding today's delivery mix fixed,
how many fewer breaches would that be?" No cost, revenue or capacity data exists, so
no financial impact is estimated.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

LABEL = "Illustrative scenario - not a causal forecast"


def scenarios(df: pd.DataFrame) -> pd.DataFrame:
    total_breaches = int(df["breach_flag"].sum())
    n_total = len(df)
    rows = []

    def add(name, group, comparison, n_group, rate_group, rate_cmp, assumption, limitation):
        reduction = n_group * (rate_group - rate_cmp)
        rows.append({
            "scenario": name, "label": LABEL, "group": group, "comparison_group": comparison,
            "n_group": int(n_group), "baseline_group_breach_rate": rate_group,
            "comparison_breach_rate": rate_cmp,
            "assumption": assumption,
            "reduction_breaches": reduction,
            "reduction_pct_of_all_breaches": 100 * reduction / total_breaches,
            "overall_breach_rate_after_pct": 100 * (total_breaches - reduction) / n_total,
            "limitation": limitation,
        })

    jam, med = df[df["traffic"] == "Jam"], df[df["traffic"] == "Medium"]
    add("Jam-traffic breach rate matches Medium-traffic rate", "traffic = Jam", "traffic = Medium",
        len(jam), jam["breach_flag"].mean(), med["breach_flag"].mean(),
        "Every Jam-traffic delivery would breach at the rate today's Medium-traffic deliveries do, "
        "keeping the same volume and mix of everything else.",
        "Jam occurs only 19:00-22:00 in this data, so 'traffic' cannot be separated from time of day. "
        "It is unknown what operational lever could move Jam-hour performance to Medium level.")

    lo, hi = df[df["rating_lt_4_5"] == 1], df[df["rating_lt_4_5"] == 0]
    add("Rating < 4.5 breach rate matches rating >= 4.5 rate", "rating < 4.5", "rating >= 4.5",
        len(lo), lo["breach_flag"].mean(), hi["breach_flag"].mean(),
        "Every low-rating delivery would breach at the rate today's higher-rating deliveries do.",
        "Rating may be an OUTCOME of delivery performance (reverse causation) or a marker of "
        "route/shift assignment. This does not show that coaching or reassigning agents would change breaches.")

    cf = df[(df["traffic"] == "Jam") & df["weather"].isin(["Cloudy", "Fog"])]
    cmp_ = df[(df["traffic"] == "Jam") & (df["weather"].isin(["Sandstorms", "Stormy", "Windy"]))]
    add("Jam + Cloudy/Fog breach rate matches Jam + other adverse weather", "Jam & (Cloudy|Fog)",
        "Jam & (Sandstorms|Stormy|Windy)", len(cf), cf["breach_flag"].mean(), cmp_["breach_flag"].mean(),
        "The highest-risk traffic-weather combination would breach at the rate of the next-highest adverse combination.",
        "Weather is not controllable; this sizes the concentration of risk, not an action.")
    return pd.DataFrame(rows)
