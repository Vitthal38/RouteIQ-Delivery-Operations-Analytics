"""Cross-layer reconciliation: independent CSV recompute vs pandas outputs vs SQL vs Power BI (v1).

Each metric gets a value from every layer that can supply one. A metric PASSES when every available
layer agrees with the independent value within a tolerance (Power BI values are compared after
rounding to the decimals the report displays). Result: outputs/tables/reconciliation.csv.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd

from routeiq.config import CLEANED_DELIVERY_CSV, PROJECT_ROOT, RESULTS_JSON, SQL_RESULTS_DIR, TABLES_DIR
from routeiq.validation.independent import compute

PBI_OBSERVED = PROJECT_ROOT / "powerbi" / "v1_observed_values.csv"


def _load_pandas_layer() -> dict[str, float]:
    """Values taken from the delivered analysis outputs (not recomputed here)."""
    R = json.loads(RESULTS_JSON.read_text(encoding="utf-8"))
    t = lambda n: pd.read_csv(TABLES_DIR / f"{n}.csv")
    v: dict[str, float] = {}
    k = R["kpis"]
    v.update({"total_deliveries": k["total_deliveries"], "breached_deliveries": k["breached_deliveries"],
              "breach_rate_pct": k["breach_rate_pct"], "on_time_rate_pct": k["on_time_rate_pct"],
              "avg_delivery_minutes": k["average_delivery_minutes"], "p90_delivery_minutes": k["p90_delivery_minutes"]})
    seg = t("segment_breach_rates")
    for var, prefix in (("area", "area"), ("traffic", "traffic"), ("weather", "weather")):
        for r in seg[seg["variable"] == var].itertuples():
            v[f"breach_rate_pct_{prefix}_{r.level}"] = 100 * r.breach_rate
            v[f"n_{prefix}_{r.level}"] = r.n
    for r in t("hour_profile").itertuples():
        v[f"breach_rate_pct_hour_{int(r.order_hour)}"] = 100 * r.breach_rate
        v[f"n_hour_{int(r.order_hour)}"] = r.n
    ov = t("sla_sensitivity_overall")
    for r in ov.itertuples():
        v[f"breach_rate_pct_p{int(round(100 * r.percentile))}"] = r.breach_rate_pct
        v[f"breached_p{int(round(100 * r.percentile))}"] = r.breached_deliveries
    par = t("pareto_area_traffic")
    for r in par.itertuples():
        v[f"pareto_breaches_rank_{int(r.rank)}"] = r.breaches
        v[f"pareto_cumulative_pct_rank_{int(r.rank)}"] = 100 * r.cumulative_share
    v["rating_best_cut"] = R["rating"]["best_cut"]
    v["age_best_cut"] = R["age"]["best_cut"]
    info = R["driver_model"]["info"]
    v["model_population_rows"], v["model_population_events"] = info["n_model"], info["n_events"]
    reg = t("statistical_test_register").set_index("id")
    v["weekend_p_value"] = float(reg.loc["T12", "p_value"])
    return v


def _load_sql_layer() -> dict[str, float]:
    """Values read from the SQL result snapshots written by scripts/run_sql.py."""
    v: dict[str, float] = {}
    if not (SQL_RESULTS_DIR / "Q30_cross_validation_reconciliation.csv").exists():
        return v
    q = lambda name: pd.read_csv(next(SQL_RESULTS_DIR.glob(f"{name}_*.csv")))
    q30 = q("Q30")
    v["total_deliveries"] = float(q30.loc[q30["id"] == 1, "actual"].iloc[0])
    v["breached_deliveries"] = float(q30.loc[q30["id"] == 4, "actual"].iloc[0])
    v["q30_checks_passed"] = float((q30["status"] == "PASS").sum())
    for r in q("Q23").itertuples():
        v[f"breach_rate_pct_hour_{int(r.order_hour)}"] = r.breach_rate_pct
        v[f"n_hour_{int(r.order_hour)}"] = r.n
    q25, q26 = q("Q25"), q("Q26")
    v["rating_best_cut"] = float(q25.loc[q25["step_rank"] == 1, "cut"].iloc[0])
    v["age_best_cut"] = float(q26.loc[q26["step_rank"] == 1, "cut"].iloc[0])
    q27 = q("Q27")
    for r in q27.itertuples():
        p = int(round(100 * r.percentile))
        if r.cut == "overall":
            v[f"breach_rate_pct_p{p}"] = r.breach_rate_pct
            v[f"breached_p{p}"] = r.breaches
        elif r.cut in ("traffic", "area") and p == 75:
            v[f"breach_rate_pct_{r.cut}_{r.level}"] = r.breach_rate_pct
            v[f"n_{r.cut}_{r.level}"] = r.n
    v["model_population_rows"] = float(q("Q29")["rows"].iloc[0])
    v["model_population_events"] = float(q("Q29")["events"].iloc[0])
    return v


def _independent_layer(ind: dict) -> dict[str, float]:
    v: dict[str, float] = {k: ind[k] for k in ("total_deliveries", "breached_deliveries", "breach_rate_pct",
                                                "on_time_rate_pct", "avg_delivery_minutes", "p90_delivery_minutes",
                                                "adverse_vs_clear_delta_minutes")}
    for p in (70, 75, 80, 90):
        v[f"breach_rate_pct_p{p}"] = ind[f"breach_rate_pct_p{p}"]
        v[f"breached_p{p}"] = ind[f"breached_p{p}"]
    for prefix, key in (("area", "by_area"), ("traffic", "by_traffic"), ("weather", "by_weather")):
        for lvl, d in ind[key].items():
            v[f"breach_rate_pct_{prefix}_{lvl}"] = d["rate_pct"]
            v[f"n_{prefix}_{lvl}"] = d["n"]
    for h, d in ind["by_hour"].items():
        v[f"breach_rate_pct_hour_{h}"] = d["rate_pct"]
        v[f"n_hour_{h}"] = d["n"]
    ranked = sorted(ind["by_area_traffic"].items(), key=lambda kv: (-kv[1]["breaches"], " / ".join(kv[0])))
    running = 0
    total = sum(d["breaches"] for _, d in ranked)
    for i, (_, d) in enumerate(ranked, 1):
        running += d["breaches"]
        v[f"pareto_breaches_rank_{i}"] = d["breaches"]
        v[f"pareto_cumulative_pct_rank_{i}"] = 100 * running / total
    v["rating_best_cut"] = ind["rating_best_cut"][0]
    v["age_best_cut"] = ind["age_best_cut"][0]
    v["model_population_rows"] = ind["model_population_rows"]
    v["model_population_events"] = ind["model_population_events"]
    v["weekend_p_value"] = float("nan")  # needs a hypothesis test; not recomputed independently
    for band, val in ind["avg_delivery_by_rating_band"].items():
        v[f"avg_delivery_by_rating_{band:.1f}"] = val
    for band, val in ind["avg_delivery_by_age_band"].items():
        v[f"avg_delivery_by_age_{band}"] = val
    return v


def run_reconciliation(write: bool = True) -> pd.DataFrame:
    ind = compute(CLEANED_DELIVERY_CSV)
    layers = {"independent_csv": _independent_layer(ind), "pandas_outputs": _load_pandas_layer(),
              "sql": _load_sql_layer()}
    pbi = pd.read_csv(PBI_OBSERVED)
    pbi_vals = dict(zip(pbi["metric"], pbi["observed_value"]))
    pbi_dec = dict(zip(pbi["metric"], pbi["display_decimals"]))
    ind_v = layers["independent_csv"]

    metrics = sorted(set(ind_v) | set(pbi_vals))
    rows = []
    for m in metrics:
        base = ind_v.get(m)
        row = {"metric": m, "independent_csv": base, "pandas_outputs": layers["pandas_outputs"].get(m),
               "sql": layers["sql"].get(m), "powerbi_v1_displayed": pbi_vals.get(m)}
        if base is None or (isinstance(base, float) and math.isnan(base)):
            base = layers["pandas_outputs"].get(m)
            row["independent_csv"] = None
        status, notes = "PASS", []
        for layer in ("pandas_outputs", "sql"):
            val = row[layer]
            if val is None or base is None:
                continue
            tol = 1e-6 + 1e-9 * abs(base)
            if m == "weekend_p_value":
                tol = 5e-4
            if not math.isclose(float(val), float(base), rel_tol=1e-9, abs_tol=max(tol, 5e-5)):
                status = "FAIL"
                notes.append(f"{layer} differs")
        if m in pbi_vals and base is not None:
            dec = int(pbi_dec[m])
            shown = pbi_vals[m]
            if m == "weekend_p_value":
                ok = abs(shown - base) < 5e-4
            else:
                ok = abs(round(base, dec) - shown) < 10 ** (-dec) * 0.5 + 1e-9
            if not ok:
                status = "PBI_v1_DIFFERS"
                notes.append("v1 Power BI display differs from the reconciled value")
        row["status"], row["notes"] = status, "; ".join(notes)
        rows.append(row)
    out = pd.DataFrame(rows)
    if "q30_checks_passed" in layers["sql"]:
        out = pd.concat([out, pd.DataFrame([{"metric": "sql_q30_checks_passed_of_14", "sql": layers["sql"]["q30_checks_passed"],
                                             "independent_csv": 14.0,
                                             "status": "PASS" if layers["sql"]["q30_checks_passed"] == 14 else "FAIL",
                                             "notes": ""}])], ignore_index=True)
    if write:
        TABLES_DIR.mkdir(parents=True, exist_ok=True)
        out.to_csv(TABLES_DIR / "reconciliation.csv", index=False)
    return out
