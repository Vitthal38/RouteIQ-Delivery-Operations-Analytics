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
    def best_cut(value_fn, cuts):
        pts = [(value_fn(r), b) for r, b in zip(rows, b75) if value_fn(r) is not None]
        best = None
        for c in cuts:
            kb = sum(b for v, b in pts if v < c); nb = sum(1 for v, _ in pts if v < c)
            ka = sum(b for v, b in pts if v >= c); na = sum(1 for v, _ in pts if v >= c)
            if nb < 100 or na < 100:
                continue
            ll = sum((k * math.log(k / m) + (m - k) * math.log(1 - k / m)) if 0 < k < m else 0.0
                     for k, m in ((kb, nb), (ka, na)))
            if best is None or ll > best[1]:
                best = (c, ll, 100 * kb / nb, 100 * ka / na)
        return best

    rating = lambda r: float(r["Agent_Rating"]) if _flag(r["agent_rating_valid_flag"]) else None
    out["rating_best_cut"] = best_cut(rating, [round(x / 10, 1) for x in range(30, 51)])
    out["age_best_cut"] = best_cut(lambda r: int(r["Agent_Age"]), list(range(21, 40)))

    # model population: exclude Semi-Urban and unrated rows
    pop = [(r, b) for r, b in zip(rows, b75) if r["Area"] != "Semi-Urban" and _flag(r["agent_rating_valid_flag"])]
    out["model_population_rows"] = len(pop)
    out["model_population_events"] = sum(b for _, b in pop)

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
