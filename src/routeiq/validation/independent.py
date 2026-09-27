"""Independent recomputation of the key figures from the cleaned CSV.

Deliberately uses only the standard library (csv, math): no pandas, no numpy, no code shared with
the analysis package, and its own percentile function. If the pandas analysis, the SQL layer and
this module agree, three separately written implementations reached the same numbers from the same
file. That is cross-layer reconciliation, NOT proof that the source data itself is correct.
"""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path


def percentile_linear(values: list[float], p: float) -> float:
    """Linear-interpolation percentile (numpy default / SQL PERCENTILE_CONT / DAX PERCENTILE.INC)."""
    xs = sorted(values)
    if not xs:
        raise ValueError("empty")
    k = (len(xs) - 1) * p
    lo, hi = math.floor(k), math.ceil(k)
    return xs[lo] if lo == hi else xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def _read(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _flag(v: str) -> bool:
    return v.strip().lower() in ("true", "1")


def compute(cleaned_csv: Path, percentiles: tuple[float, ...] = (0.70, 0.75, 0.80, 0.90)) -> dict:
    rows = _read(cleaned_csv)
    n = len(rows)
    times = [float(r["Delivery_Time"]) for r in rows]
    by_cat: dict[str, list[float]] = defaultdict(list)
    for r, t in zip(rows, times):
        by_cat[r["Category"]].append(t)

    out: dict = {"total_deliveries": n}
    thresholds = {p: {c: percentile_linear(v, p) for c, v in by_cat.items()} for p in percentiles}
    out["thresholds_p75"] = thresholds[0.75]

    def breach(r, t, p):
        return t > thresholds[p][r["Category"]]

    b75 = [breach(r, t, 0.75) for r, t in zip(rows, times)]
    out["breached_deliveries"] = sum(b75)
    out["breach_rate_pct"] = 100 * sum(b75) / n
    out["on_time_rate_pct"] = 100 - out["breach_rate_pct"]
    out["stored_flag_breaches"] = sum(_flag(r["sla_breach_flag"]) for r in rows)
    out["stored_flag_mismatches_vs_recomputed"] = sum(_flag(r["sla_breach_flag"]) != b for r, b in zip(rows, b75))
    out["avg_delivery_minutes"] = sum(times) / n
    out["p90_delivery_minutes"] = percentile_linear(times, 0.90)

    for p in percentiles:
        k = sum(breach(r, t, p) for r, t in zip(rows, times))
        out[f"breached_p{int(100 * p)}"] = k
        out[f"breach_rate_pct_p{int(100 * p)}"] = 100 * k / n

    def group_rate(key_fn, p=0.75):
        agg = defaultdict(lambda: [0, 0])
        for r, t in zip(rows, times):
            k = key_fn(r)
            if k is None:
                continue
            agg[k][0] += 1
            agg[k][1] += breach(r, t, p)
        return {k: {"n": v[0], "breaches": v[1], "rate_pct": 100 * v[1] / v[0]} for k, v in agg.items()}

    out["by_area"] = group_rate(lambda r: r["Area"])
    out["by_traffic"] = group_rate(lambda r: r["Traffic"])
    out["by_weather"] = group_rate(lambda r: r["Weather"])
    out["by_hour"] = group_rate(lambda r: int(r["order_hour"]))
    out["by_prep"] = group_rate(lambda r: int(r["prep_time_minutes"]))
    out["by_rating_group"] = group_rate(lambda r: ("lt" if float(r["Agent_Rating"]) < 4.5 else "ge") if _flag(r["agent_rating_valid_flag"]) else None)
    out["by_age_group"] = group_rate(lambda r: "ge30" if int(r["Agent_Age"]) >= 30 else "lt30")
    for p in (0.70, 0.90):
        out[f"by_traffic_p{int(100 * p)}"] = group_rate(lambda r: r["Traffic"], p)
        out[f"by_area_p{int(100 * p)}"] = group_rate(lambda r: r["Area"], p)
    out["by_area_traffic"] = group_rate(lambda r: (r["Area"], r["Traffic"]))

    # rating / age exact-value and cut scans (independent re-derivation of the "step")
    def largest_single_step(value_fn, min_n=100):
        """Where is the sharpest jump between two ADJACENT exact values? Values with fewer than
        ``min_n`` rows are dropped first (their jumps are noise), then the biggest jump between
        two still-adjacent remaining values is returned as (cut, jump_pts, rate_prev_pct, rate_at_pct)."""
        pts = [(value_fn(r), b) for r, b in zip(rows, b75) if value_fn(r) is not None]
        agg: dict[float, list[int]] = defaultdict(lambda: [0, 0])
        for v, b in pts:
            agg[v][0] += 1
            agg[v][1] += b
        values = sorted(v for v, (n, _) in agg.items() if n >= min_n)
        best = None
        for prev, cur in zip(values, values[1:]):
            n_prev, k_prev = agg[prev]
            n_cur, k_cur = agg[cur]
            rate_prev, rate_cur = k_prev / n_prev, k_cur / n_cur
            jump = 100 * (rate_cur - rate_prev)
            if best is None or abs(jump) > abs(best[1]):
                best = (cur, jump, 100 * rate_prev, 100 * rate_cur)
        return best

    rating = lambda r: float(r["Agent_Rating"]) if _flag(r["agent_rating_valid_flag"]) else None
    out["rating_best_cut"] = largest_single_step(rating)
    out["age_best_cut"] = largest_single_step(lambda r: int(r["Agent_Age"]))

    # rating/age analysis population: exclude Semi-Urban (100% breach) and unrated rows
    pop = [(r, b) for r, b in zip(rows, b75) if r["Area"] != "Semi-Urban" and _flag(r["agent_rating_valid_flag"])]
    out["analysis_population_rows"] = len(pop)
    out["analysis_population_events"] = sum(b for _, b in pop)

    sunny = [t for r, t in zip(rows, times) if r["Weather"] == "Sunny"]
    adverse = [t for r, t in zip(rows, times) if r["Weather"] != "Sunny"]
    out["adverse_vs_clear_delta_minutes"] = sum(adverse) / len(adverse) - sum(sunny) / len(sunny)

    rating_means = defaultdict(list)
    for r, t in zip(rows, times):
        if _flag(r["agent_rating_valid_flag"]):
            rating_means[math.floor(float(r["Agent_Rating"]) / 0.5 + 1e-9) * 0.5].append(t)
    out["avg_delivery_by_rating_band"] = {k: sum(v) / len(v) for k, v in rating_means.items()}
    age_means = defaultdict(list)
    for r, t in zip(rows, times):
        a = int(r["Agent_Age"])
        age_means["18-25" if a <= 25 else "26-35" if a <= 35 else "36-45" if a <= 45 else "46-65"].append(t)
    out["avg_delivery_by_age_band"] = {k: sum(v) / len(v) for k, v in age_means.items()}
    return out
