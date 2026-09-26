"""When do breaches happen? Hour-of-day analysis, and how far it can be separated from traffic."""

from __future__ import annotations

import numpy as np
import pandas as pd

from routeiq.analysis.segments import segment_table
from routeiq.statistics.effects import (
    mantel_haenszel_rr, risk_difference, risk_ratio, wilson_ci,
)


def hour_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Per-hour volume, breach rate (Wilson CI), share of breaches and modal traffic."""
    g = (df.groupby("order_hour").agg(n=("breach_flag", "size"), breaches=("breach_flag", "sum"),
                                      mean_delivery_minutes=("delivery_time_minutes", "mean"))
         .reset_index())
    g["breach_rate"] = g["breaches"] / g["n"]
    ci = [wilson_ci(r.breaches, r.n) for r in g.itertuples()]
    g["ci_low"], g["ci_high"] = [c[0] for c in ci], [c[1] for c in ci]
    g["share_of_deliveries"] = g["n"] / g["n"].sum()
    g["share_of_breaches"] = g["breaches"] / g["breaches"].sum()
    modal = df.groupby("order_hour")["traffic"].agg(lambda s: s.value_counts().index[0])
    modal_share = df.groupby("order_hour")["traffic"].agg(lambda s: s.value_counts(normalize=True).iloc[0])
    g["modal_traffic"] = g["order_hour"].map(modal)
    g["modal_traffic_share"] = g["order_hour"].map(modal_share)
    return g


def band_tables(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {
        "hour_band": segment_table(df, "hour_band", order=sorted(df["hour_band"].unique())),
        "peak_vs_offpeak": segment_table(df.assign(peak=np.where(df["is_peak_hour"] == 1, "peak (17-23h)", "off-peak")),
                                         "peak", reference="off-peak"),
    }


def cross_tables(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """hour_band x {traffic, area, weather}: n, breaches and breach rate per cell."""
    out = {}
    for other in ("traffic", "area", "weather"):
        g = (df.groupby(["hour_band", other]).agg(n=("breach_flag", "size"), breaches=("breach_flag", "sum"))
             .reset_index())
        g["breach_rate"] = g["breaches"] / g["n"]
        g["small_sample_flag"] = g["n"] < 200
        out[f"hour_band_x_{other}"] = g
    return out


def traffic_hour_identifiability(df: pd.DataFrame) -> dict[str, float]:
    """How much of 'traffic' is just time of day? (This limits what the data can separate.)"""
    by_hour = df.groupby(["order_hour", "traffic"]).size().unstack(fill_value=0)
    purity = by_hour.max(axis=1).sum() / by_hour.values.sum()
    mixed = (by_hour.gt(0).sum(axis=1) > 1)
    return {
        "share_of_deliveries_matching_hours_modal_traffic": float(purity),
        "hours_observed": int(len(by_hour)),
        "hours_with_more_than_one_traffic_level": int(mixed.sum()),
        "boundary_hours": [int(h) for h in by_hour.index[mixed]],
        "deliveries_in_boundary_hours": int(by_hour[mixed].values.sum()),
        "jam_first_hour": int(df.loc[df["traffic"] == "Jam", "order_hour"].min()),
        "jam_last_hour": int(df.loc[df["traffic"] == "Jam", "order_hour"].max()),
    }


def within_hour_traffic_contrasts(df: pd.DataFrame, min_n: int = 100) -> pd.DataFrame:
    """Compare traffic levels INSIDE the same hour, where the data allows it.

    Only boundary hours contain more than one traffic level, so these are the only
    contrasts that hold time of day fixed. Rows with n < min_n in either group are dropped.
    """
    rows = []
    for hour, sub in df.groupby("order_hour"):
        levels = sub["traffic"].unique()
        if len(levels) < 2:
            continue
        stats_ = sub.groupby("traffic")["breach_flag"].agg(["sum", "size"])
        for a in stats_.index:
            for b in stats_.index:
                if a >= b:
                    continue
                (ka, na), (kb, nb) = stats_.loc[a], stats_.loc[b]
                if na < min_n or nb < min_n:
                    continue
                hi, lo = (a, b) if ka / na > kb / nb else (b, a)
                (k1, n1), (k0, n0) = stats_.loc[hi], stats_.loc[lo]
                rd, rd_lo, rd_hi = risk_difference(k1, n1, k0, n0)
                rr, rr_lo, rr_hi = risk_ratio(k1, n1, k0, n0)
                rows.append({"order_hour": int(hour), "higher_risk_traffic": hi, "lower_risk_traffic": lo,
                             "n_higher": int(n1), "n_lower": int(n0), "rate_higher": k1 / n1, "rate_lower": k0 / n0,
                             "risk_diff_pts": 100 * rd, "rd_ci_low_pts": 100 * rd_lo, "rd_ci_high_pts": 100 * rd_hi,
                             "risk_ratio": rr, "rr_ci_low": rr_lo, "rr_ci_high": rr_hi})
    return pd.DataFrame(rows)


def within_traffic_hour_contrasts(df: pd.DataFrame) -> pd.DataFrame:
    """Holding traffic fixed, does time of day still matter? (Low: morning vs late; Medium: afternoon vs evening.)"""
    pairs = [("Low", [8, 9, 10], [22, 23], "Low traffic: 08-10h vs 22-23h"),
             ("Medium", [15, 16], [17, 18, 19], "Medium traffic: 15-16h vs 17-19h"),
             ("High", [11, 12, 13, 14], [15], "High traffic: 11-14h vs 15h")]
    rows = []
    for traffic, hours_a, hours_b, label in pairs:
        sub = df[df["traffic"] == traffic]
        a, b = sub[sub["order_hour"].isin(hours_a)], sub[sub["order_hour"].isin(hours_b)]
        if len(a) < 100 or len(b) < 100:
            continue
        rr, lo, hi = risk_ratio(b["breach_flag"].sum(), len(b), a["breach_flag"].sum(), len(a))
        rows.append({"contrast": label, "n_first": len(a), "rate_first": a["breach_flag"].mean(),
                     "n_second": len(b), "rate_second": b["breach_flag"].mean(),
                     "risk_ratio_second_vs_first": rr, "rr_ci_low": lo, "rr_ci_high": hi})
    return pd.DataFrame(rows)
