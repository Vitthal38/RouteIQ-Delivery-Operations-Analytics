"""Is this real operational data, or a rule-built simulation?

Several patterns in the data are hard to explain as organic delivery operations. This
module quantifies them so the README can describe the data honestly. It does NOT prove
how the data was made (provenance cannot be verified from the repository); it measures
how far the data departs from what real operational logs typically look like.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from routeiq.analysis.time_of_day import traffic_hour_identifiability


def _ols(y: np.ndarray, X: pd.DataFrame) -> tuple[np.ndarray, float, float]:
    Xv = X.to_numpy(float)
    beta = np.linalg.lstsq(Xv, y, rcond=None)[0]
    resid = y - Xv @ beta
    r2 = 1 - (resid ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return beta, float(r2), float(resid.std())


def weather_tier_check(df: pd.DataFrame) -> dict:
    """OLS of delivery time on conditions; do weather effects collapse into a few identical tiers?"""
    d = df.dropna(subset=["rating_lt_4_5"]).copy()
    X = pd.get_dummies(d[["traffic", "weather", "area", "vehicle"]], drop_first=False).astype(float)
    X = X.drop(columns=["traffic_High", "weather_Cloudy", "area_Metropolitian", "vehicle_motorcycle"])
    X["low_rating"] = d["rating_lt_4_5"].astype(float)
    X["age_ge_30"] = d["age_ge_30"].astype(float)
    X["grocery"] = (d["category"] == "Grocery").astype(float)
    X.insert(0, "const", 1.0)
    beta, r2, sd = _ols(d["delivery_time_minutes"].to_numpy(float), X)
    coef = dict(zip(X.columns, beta))
    tier_mid = [coef["weather_Sandstorms"], coef["weather_Stormy"], coef["weather_Windy"]]
    return {"ols_r2_additive_rules": r2, "ols_resid_sd_minutes": sd,
            "weather_coef_fog_vs_cloudy": coef["weather_Fog"],
            "weather_coefs_sandstorms_stormy_windy": tier_mid,
            "weather_mid_tier_spread_minutes": float(max(tier_mid) - min(tier_mid)),
            "weather_gap_between_tiers_minutes": float(abs(np.mean(tier_mid) - coef["weather_Sunny"])),
            "coef_semi_urban_minutes": coef.get("area_Semi-Urban"), "coef_grocery_minutes": coef["grocery"],
            "coef_low_rating_minutes": coef["low_rating"], "coef_age_ge_30_minutes": coef["age_ge_30"]}


def realism_checks(df: pd.DataFrame, raw: pd.DataFrame | None = None) -> pd.DataFrame:
    rows = []

    def add(check, observed, expectation, strength, note=""):
        rows.append({"check": check, "observed": observed, "expected_if_real_operational_data": expectation,
                     "evidence_of_rule_based_construction": strength, "note": note})

    dt = df["delivery_time_minutes"]
    m5 = float((dt % 5 == 0).mean())
    add("Delivery times that are multiples of 5 minutes", f"{100 * m5:.1f}% ({dt.nunique()} distinct values)",
        "about 20% (timestamps measured to the minute)", "strong",
        "Present in the RAW file too, so it is not an artefact of cleaning.")

    prep = df["prep_time_minutes"].value_counts().sort_index()
    _, p_u = stats.chisquare(prep.to_numpy())
    add("Preparation time values", f"only {list(prep.index)}; shares "
        f"{', '.join(f'{100 * v / prep.sum():.1f}%' for v in prep)} (uniform-fit p={p_u:.2f})",
        "a continuous, right-skewed distribution", "strong", "Prep time has no association with breach or delivery time (see docs).")

    ident = traffic_hour_identifiability(df)
    add("Traffic level determined by order hour",
        f"{100 * ident['share_of_deliveries_matching_hours_modal_traffic']:.1f}% of deliveries match their hour's most common traffic level; "
        f"Jam only in hours {ident['jam_first_hour']}-{ident['jam_last_hour']}; "
        f"{ident['hours_with_more_than_one_traffic_level']} of {ident['hours_observed']} hours have >1 level",
        "traffic varies within an hour (incidents, routes, weekdays)", "strong",
        "Traffic and time of day are nearly the same variable here, so they cannot be cleanly separated.")

    vol = df["order_hour"].value_counts()
    ev = vol[vol.index >= 17]
    add("Hourly order volume", f"no orders 01-07h; evening plateau 17-23h CV={ev.std() / ev.mean():.2f} "
        f"(min {ev.min()}, max {ev.max()})", "smooth demand curve with peaks", "moderate")

    ages = df.groupby("age_ge_30")["breach_flag"].mean()
    by_age = df.groupby("agent_age")["breach_flag"].mean()
    jump = float(by_age.loc[30] - by_age.loc[29])
    within = float(by_age.loc[20:29].std())
    add("Breach rate step at agent age 30", f"{100 * ages.loc[0]:.1f}% (age<30) vs {100 * ages.loc[1]:.1f}% (age>=30); "
        f"29->30 jump {100 * jump:.1f} pts vs year-to-year SD {100 * within:.1f} pts",
        "gradual change with age, not a cliff at a round number", "strong")

    by_rating = df.dropna(subset=["agent_rating"]).groupby("agent_rating")["breach_flag"].mean()
    rjump = float(by_rating.loc[4.4] - by_rating.loc[4.5])
    add("Breach rate step at agent rating 4.5", f"4.4 -> {100 * by_rating.loc[4.4]:.1f}%, 4.5 -> {100 * by_rating.loc[4.5]:.1f}% "
        f"(drop {100 * rjump:.1f} pts)", "gradual change with rating", "strong",
        "Below 4.5 the breach rate is flat around 60-90%: a step, not a slope.")

    tiers = weather_tier_check(df)
    add("Weather effects collapse into three tiers",
        f"Sandstorms/Stormy/Windy coefficients differ by only {tiers['weather_mid_tier_spread_minutes']:.1f} min; "
        f"Fog vs Cloudy {tiers['weather_coef_fog_vs_cloudy']:+.1f} min; Sunny vs the mid tier "
        f"{tiers['weather_gap_between_tiers_minutes']:.1f} min",
        "each weather type has its own effect", "strong")
    add("A handful of additive rules explain delivery time",
        f"OLS R2 = {tiers['ols_r2_additive_rules']:.2f} using traffic, weather, area, vehicle, rating<4.5, age>=30, grocery",
        "much lower explanatory power from coarse categories alone", "moderate")

    su = df[df["area"] == "Semi-Urban"]
    add("Semi-Urban area", f"n={len(su)}, {100 * su['breach_flag'].mean():.0f}% breach, "
        f"{100 * (su['traffic'] == 'Jam').mean():.0f}% in Jam traffic, delivery time {su['delivery_time_minutes'].median():.0f} min median",
        "some variation; a perfect 100% is rare", "strong")

    if raw is not None:
        rating_6 = int((raw["Agent_Rating"] == 6.0).sum())
        coord_zero = int(((raw["Store_Latitude"] == 0) | (raw["Store_Longitude"] == 0)).sum())
        pad = float(np.mean([(raw[c].astype(str) != raw[c].astype(str).str.strip()).mean() for c in ("Traffic", "Vehicle", "Area")]))
        add("Raw file formatting and range defects", f"{rating_6} ratings of 6.0 (scale is 1-5); {coord_zero} zero coordinates; "
            f"{100 * pad:.0f}% of Traffic/Vehicle/Area values padded with trailing spaces",
            "some defects, but rarely this systematic", "weak",
            "Zero coordinates and stray spaces also occur in real exports; only weak evidence on its own.")
    return pd.DataFrame(rows)
