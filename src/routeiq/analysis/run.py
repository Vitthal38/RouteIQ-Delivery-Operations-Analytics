"""Run the full analysis: analytical dataset -> tables -> figures -> outputs/results.json."""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from routeiq.analysis import (
    data_realism, figures, prep_time, scenarios, segments, sla_sensitivity, thresholds, time_of_day,
)
from routeiq.config import (
    AGE_THRESHOLD, FIGURES_DIR, RATING_THRESHOLD, RAW_DATA_CSV, RESULTS_JSON, TABLES_DIR,
    ensure_directory_structure,
)
from routeiq.features.analytical import save_analytical_dataset
from routeiq.statistics.tests import test_register


def _clean(o):
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if (isinstance(o, float) and np.isnan(o)) else float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, pd.DataFrame):
        return _clean(o.to_dict(orient="records"))
    return o


def _save(df: pd.DataFrame, name: str, tables: dict) -> None:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(TABLES_DIR / f"{name}.csv", index=False)
    tables[name] = df


def run_all(verbose: bool = True) -> dict:
    t0 = time.time()
    ensure_directory_structure()
    df = save_analytical_dataset()
    tables: dict[str, pd.DataFrame] = {}
    R: dict = {}
    log = (lambda m: print(f"[{time.time() - t0:5.1f}s] {m}")) if verbose else (lambda m: None)

    # ---- KPIs and segments -------------------------------------------------
    R["kpis"] = segments.kpis(df)
    orders = {"traffic": ["Low", "Medium", "High", "Jam"], "weather": None, "area": None, "vehicle": None,
              "category": None, "is_weekend": [0, 1]}
    refs = {"traffic": "Low", "weather": "Sunny", "area": "Metropolitian", "vehicle": "motorcycle",
            "category": None, "is_weekend": 0}
    seg_parts = []
    for col, order in orders.items():
        t = segments.segment_table(df, col, reference=refs[col], order=order)
        seg_parts.append(t)
    d2 = df.assign(rating_group=np.where(df["rating_lt_4_5"].isna(), "no rating",
                                         np.where(df["rating_lt_4_5"] == 1, "rating < 4.5", "rating >= 4.5")),
                   age_group=np.where(df["age_ge_30"] == 1, "age >= 30", "age < 30"))
    seg_parts.append(segments.segment_table(d2, "rating_group", reference="rating >= 4.5"))
    seg_parts.append(segments.segment_table(d2, "age_group", reference="age < 30"))
    _save(pd.concat(seg_parts, ignore_index=True), "segment_breach_rates", tables)
    R["associations"] = [segments.association(df, c) for c in
                         ("traffic", "weather", "area", "vehicle", "hour_band", "is_weekend", "prep_time_minutes")]
    pareto = segments.pareto(df, ("area", "traffic"))
    _save(pareto, "pareto_area_traffic", tables)
    _save(segments.pareto(df, ("area",)), "pareto_area", tables)
    log("KPIs, segments, Pareto done")

    # ---- Time of day -------------------------------------------------------
    hp = time_of_day.hour_profile(df)
    _save(hp, "hour_profile", tables)
    for name, t in time_of_day.band_tables(df).items():
        _save(t, name, tables)
    for name, t in time_of_day.cross_tables(df).items():
        _save(t, name, tables)
    _save(time_of_day.within_hour_traffic_contrasts(df), "within_hour_traffic_contrasts", tables)
    _save(time_of_day.within_traffic_hour_contrasts(df), "within_traffic_hour_contrasts", tables)
    R["traffic_hour_identifiability"] = time_of_day.traffic_hour_identifiability(df)
    peak = tables["peak_vs_offpeak"].set_index("level")
    R["peak"] = {"peak_share_of_deliveries": float(peak.loc["peak (17-23h)", "share_of_deliveries"]),
                 "peak_share_of_breaches": float(peak.loc["peak (17-23h)", "share_of_breaches"]),
                 "peak_breach_rate": float(peak.loc["peak (17-23h)", "breach_rate"]),
                 "offpeak_breach_rate": float(peak.loc["off-peak", "breach_rate"])}
    ev = df[df["order_hour"].between(19, 21)]
    R["evening_peak_19_21"] = {"share_of_deliveries": len(ev) / len(df),
                               "share_of_breaches": float(ev["breach_flag"].sum() / df["breach_flag"].sum()),
                               "breach_rate": float(ev["breach_flag"].mean())}
    log("Time-of-day done")

    # ---- Prep time ---------------------------------------------------------
    _save(prep_time.prep_profile(df), "prep_profile", tables)
    R["prep_tests"] = prep_time.prep_tests(df)
    for name, t in prep_time.prep_cross(df).items():
        _save(t, name, tables)
    log("Prep time done")

    # ---- Rating and age: shape, thresholds, stratification -------------------
    _save(thresholds.exact_value_table(df, "agent_rating"), "rating_by_value", tables)
    _save(thresholds.exact_value_table(df, "agent_age"), "age_by_value", tables)
    rs = thresholds.scan_cutpoints(df, "agent_rating", [round(x, 1) for x in np.arange(3.0, 5.01, 0.1)])
    as_ = thresholds.scan_cutpoints(df, "agent_age", list(range(21, 40)))
    _save(rs, "rating_cut_scan", tables)
    _save(as_, "age_cut_scan", tables)
    rating_step = thresholds.largest_single_step(df, "agent_rating")
    age_step = thresholds.largest_single_step(df, "agent_age")
    R["rating_shape"] = rating_step
    R["age_shape"] = age_step
    _save(thresholds.rating_age_grid(df), "rating_age_grid", tables)
    _save(thresholds.effect_by_traffic(df, "rating_lt_4_5"), "rating_effect_by_traffic", tables)
    _save(thresholds.effect_by_traffic(df, "age_ge_30"), "age_effect_by_traffic", tables)
    R["rating"] = {"best_cut": rating_step["cut"],
                   "stratified_by_traffic_x_area": thresholds.stratified_effect(df, "rating_lt_4_5", ["traffic", "area"]),
                   "stratified_by_traffic_x_weather": thresholds.stratified_effect(df, "rating_lt_4_5", ["traffic", "weather"])}
    R["age"] = {"best_cut": age_step["cut"],
                "stratified_by_traffic_x_area": thresholds.stratified_effect(df, "age_ge_30", ["traffic", "area"]),
                "stratified_by_traffic_x_weather": thresholds.stratified_effect(df, "age_ge_30", ["traffic", "weather"])}
    lo = df[df["rating_lt_4_5"] == 1]
    R["rating"].update({"n_low": len(lo), "share_of_deliveries_low": len(lo) / df["rating_lt_4_5"].notna().sum(),
                        "share_of_breaches_low": float(lo["breach_flag"].sum() / df["breach_flag"].sum()),
                        "breach_rate_low": float(lo["breach_flag"].mean()),
                        "breach_rate_high": float(df[df["rating_lt_4_5"] == 0]["breach_flag"].mean())})
    log("Rating/age thresholds done")

    # ---- Statistical test register -------------------------------------------
    reg = test_register(df)
    _save(reg, "statistical_test_register", tables)
    log("Test register done")

    # ---- Rating/age analysis population (descriptive; excludes Semi-Urban and unrated rows) ----
    pop = df[(df["area"] != "Semi-Urban") & df["rating_lt_4_5"].notna()]
    R["rating_age_analysis_population"] = {
        "n_total": len(df), "excluded_semi_urban": int((df["area"] == "Semi-Urban").sum()),
        "excluded_missing_rating": int(df["rating_lt_4_5"].isna().sum()), "n_analysis": len(pop),
        "n_events": int(pop["breach_flag"].sum()),
        "note": "Excluded so a 100%-breach group (Semi-Urban) and missing ratings do not distort rate comparisons.",
    }
    log("Analysis population done")

    # ---- SLA sensitivity -----------------------------------------------------
    ov = sla_sensitivity.overall_table(df)
    _save(ov, "sla_sensitivity_overall", tables)
    _save(sla_sensitivity.threshold_table(df), "sla_sensitivity_thresholds", tables)
    seg = sla_sensitivity.segment_rates_by_percentile(df)
    _save(seg, "sla_sensitivity_segments", tables)
    _save(sla_sensitivity.ranking_stability(seg), "sla_sensitivity_ranking_stability", tables)
    drv = sla_sensitivity.driver_stability(df)
    _save(drv, "sla_sensitivity_driver_risk_ratios", tables)
    _save(sla_sensitivity.semi_urban_by_percentile(df), "sla_sensitivity_semi_urban", tables)
    R["sla_sensitivity"] = {"overall": ov}
    log("SLA sensitivity done")

    # ---- Scenarios + data realism ------------------------------------------------
    sc = scenarios.scenarios(df)
    _save(sc, "scenarios", tables)
    raw = None
    if RAW_DATA_CSV.exists():
        raw = pd.read_csv(RAW_DATA_CSV)
    realism = data_realism.realism_checks(df, raw)
    _save(realism, "data_realism_checks", tables)
    R["data_realism"] = data_realism.weather_tier_check(df)
    log("Scenarios and realism done")

    # ---- Figures -------------------------------------------------------------
    F = FIGURES_DIR
    figures.step_plot(tables["rating_by_value"], "Agent rating", RATING_THRESHOLD,
                      "Breach rate by exact agent rating: a step at 4.5, not a slope", F / "rating_step.png",
                      "Points = breach rate with 95% Wilson CI. Small n below 3.5 (see rating_by_value.csv).")
    figures.step_plot(tables["age_by_value"], "Agent age (years)", AGE_THRESHOLD,
                      "Breach rate by agent age: a step at 30", F / "age_step.png")
    figures.hour_profile_plot(hp, F / "hour_profile.png")
    figures.traffic_hour_heatmap(df, F / "traffic_hour_heatmap.png")
    figures.traffic_weather_heatmap(df, F / "traffic_weather_heatmap.png")
    rr75 = drv[drv["percentile"] == 0.75].rename(columns={"contrast": "label"})
    figures.risk_ratio_plot(rr75, F / "risk_ratios_by_factor.png")
    figures.sensitivity_plot(ov, drv, F / "sla_sensitivity.png")
    figures.pareto_plot(pareto, F / "pareto_area_traffic.png")
    figures.scenario_plot(sc, F / "scenarios.png")
    log("Figures done")

    RESULTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump(_clean(R), f, indent=2)
    log(f"Wrote {RESULTS_JSON}")
    return {"results": R, "tables": tables, "df": df}


if __name__ == "__main__":
    run_all()
