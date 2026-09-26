"""Illustrative what-if scenarios.

Every scenario here is ILLUSTRATIVE, NOT A CAUSAL FORECAST. It answers only: "if this
group's breach rate matched a comparison group's, holding today's delivery mix fixed,
how many fewer breaches would that be?" No cost, revenue or capacity data exists, so
no financial impact is estimated.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from routeiq.modeling.driver_model import SPECS, build_X, fit_spec, prepare_model_frame

LABEL = "Illustrative scenario - not a causal forecast"


def _model_scenario(frame: pd.DataFrame, res, spec: dict, mutate) -> tuple[float, float]:
    """(baseline predicted breaches, counterfactual predicted breaches) over the modelling frame."""
    X0 = build_X(frame, spec)[0].reindex(columns=res.names, fill_value=0.0)
    mod = mutate(frame.copy())
    X1 = build_X(mod, spec)[0].reindex(columns=res.names, fill_value=0.0)
    return float(res.predict(X0).sum()), float(res.predict(X1).sum())


def scenarios(df: pd.DataFrame) -> pd.DataFrame:
    total_breaches = int(df["breach_flag"].sum())
    n_total = len(df)
    frame, _ = prepare_model_frame(df)
    resC, _, _ = fit_spec(frame, SPECS["C"], cluster=False)
    rows = []

    def add(name, group, comparison, n_group, rate_group, rate_cmp, mut, assumption, limitation):
        raw = n_group * (rate_group - rate_cmp)
        base, cf = _model_scenario(frame, resC, SPECS["C"], mut)
        model_red = base - cf
        rows.append({
            "scenario": name, "label": LABEL, "group": group, "comparison_group": comparison,
            "n_group": int(n_group), "baseline_group_breach_rate": rate_group,
            "comparison_breach_rate": rate_cmp,
            "assumption": assumption,
            "raw_reduction_breaches": raw,
            "raw_reduction_pct_of_all_breaches": 100 * raw / total_breaches,
            "raw_overall_breach_rate_after_pct": 100 * (total_breaches - raw) / n_total,
            "model_adjusted_reduction_breaches": model_red,
            "model_adjusted_pct_of_all_breaches": 100 * model_red / total_breaches,
            "limitation": limitation,
        })

    jam, med = df[df["traffic"] == "Jam"], df[df["traffic"] == "Medium"]
    add("Jam-traffic breach rate matches Medium-traffic rate", "traffic = Jam", "traffic = Medium",
        len(jam), jam["breach_flag"].mean(), med["breach_flag"].mean(),
        lambda f: f.assign(traffic=np.where(f["traffic"] == "Jam", "Medium", f["traffic"])),
        "Jam rows would behave like Medium rows, keeping today's mix of weather, area, agents.",
        "Jam occurs only 19:00-22:00 here, so 'traffic' cannot be separated from time of day. "
        "It is unknown what operational lever could move Jam-hour performance to Medium level.")

    lo, hi = df[df["rating_lt_4_5"] == 1], df[df["rating_lt_4_5"] == 0]
    add("Rating < 4.5 breach rate matches rating >= 4.5 rate", "rating < 4.5", "rating >= 4.5",
        len(lo), lo["breach_flag"].mean(), hi["breach_flag"].mean(),
        lambda f: f.assign(rating_lt_4_5=0.0),
        "Low-rating rows would behave like high-rating rows.",
        "Rating may be an OUTCOME of delivery performance (reverse causation) or a marker of "
        "route/shift assignment. Coaching or reassigning agents is not shown to change breaches.")

    cf = df[(df["traffic"] == "Jam") & df["weather"].isin(["Cloudy", "Fog"])]
    cmp_ = df[(df["traffic"] == "Jam") & (df["weather"].isin(["Sandstorms", "Stormy", "Windy"]))]
    add("Jam + Cloudy/Fog breach rate matches Jam + other adverse weather", "Jam & (Cloudy|Fog)",
        "Jam & (Sandstorms|Stormy|Windy)", len(cf), cf["breach_flag"].mean(), cmp_["breach_flag"].mean(),
        lambda f: f.assign(weather=np.where((f["traffic"] == "Jam") & f["weather"].isin(["Cloudy", "Fog"]),
                                            "Windy", f["weather"])),
        "The highest-risk traffic-weather cell would behave like the next-highest adverse cell.",
        "Weather is not controllable; this sizes the concentration of risk, not an action.")
    return pd.DataFrame(rows)
