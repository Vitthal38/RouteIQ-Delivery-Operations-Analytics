"""The statistical test register.

Each row answers one business question with the simplest defensible method, states
the assumptions that matter, and reports an EFFECT SIZE with a confidence interval as
the headline. p-values are recorded but not used to judge importance: at n ~ 43,000
almost every difference is "significant".
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from routeiq.analysis.segments import association
from routeiq.statistics.effects import (
    probability_of_superiority, cohens_d, kruskal_epsilon_squared, odds_ratio,
    risk_difference, risk_ratio,
)


def _binary_contrast(a: pd.DataFrame, b: pd.DataFrame) -> dict:
    k1, n1, k0, n0 = a["breach_flag"].sum(), len(a), b["breach_flag"].sum(), len(b)
    rr, rlo, rhi = risk_ratio(k1, n1, k0, n0)
    orr, olo, ohi = odds_ratio(k1, n1, k0, n0)
    rd, dlo, dhi = risk_difference(k1, n1, k0, n0)
    return {"rate_group": k1 / n1, "rate_reference": k0 / n0, "risk_diff_pts": 100 * rd,
            "rd_ci_low_pts": 100 * dlo, "rd_ci_high_pts": 100 * dhi, "risk_ratio": rr, "rr_ci_low": rlo,
            "rr_ci_high": rhi, "odds_ratio": orr, "or_ci_low": olo, "or_ci_high": ohi}


def test_register(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    d = df.copy()

    def cat_row(tid, question, col, contrast_a, contrast_b, label, meaning, limitation, frame=None):
        f = d if frame is None else frame
        assoc = association(f, col)
        c = _binary_contrast(f[contrast_a(f)], f[contrast_b(f)])
        rows.append({
            "id": tid, "business_question": question, "method": "Chi-square test of independence (breach x level); "
            "effect size = Cramer's V; headline contrast reported as risk ratio and risk difference with 95% CI",
            "why_this_test": "Breach is binary and the factor is categorical; V is comparable across factors of different size.",
            "key_assumptions": "Independent observations; expected cell counts >= 5 (true here except where flagged).",
            "effect_size_name": "Cramer's V", "effect_size": assoc["cramers_v"], "effect_band": assoc["effect_band"],
            "headline_contrast": label, "rate_group": c["rate_group"], "rate_reference": c["rate_reference"],
            "risk_diff_pts": c["risk_diff_pts"], "risk_ratio": c["risk_ratio"], "ci_low": c["rr_ci_low"],
            "ci_high": c["rr_ci_high"], "p_value": assoc["p_value"], "n": assoc["n"],
            "practical_meaning": meaning, "limitations": limitation})

    cat_row("T1", "Is breach rate related to traffic level?", "traffic",
            lambda f: f["traffic"] == "Jam", lambda f: f["traffic"] == "Low", "Jam vs Low (risk ratio)",
            "Breach rate is several times higher in Jam than Low traffic.",
            "Traffic is almost a function of order hour (Jam only 19-22h); effects of traffic and time of day overlap.")
    cat_row("T2", "Is breach rate related to weather?", "weather",
            lambda f: f["weather"].isin(["Cloudy", "Fog"]), lambda f: f["weather"] == "Sunny",
            "Cloudy/Fog vs Sunny", "Cloudy and Fog carry clearly higher breach rates than Sunny.",
            "The traffic effect depends on weather (interaction), so this main effect is an average.")
    cat_row("T3", "Is breach rate related to area type?", "area",
            lambda f: f["area"] == "Metropolitian", lambda f: f["area"] == "Urban", "Metropolitian vs Urban",
            "Metropolitian breaches more often than Urban.",
            "Semi-Urban (n=152, 100% breach) is included in V but excluded from the contrast; area is confounded with traffic and agent mix.")
    cat_row("T4", "Is breach rate related to vehicle type?", "vehicle",
            lambda f: f["vehicle"] == "motorcycle", lambda f: f["vehicle"].isin(["scooter", "van"]),
            "Motorcycle vs scooter/van", "Motorcycle deliveries breach noticeably more often.",
            "Vehicle assignment is not randomised; other differences may travel with vehicle type.")
    cat_row("T5", "Is breach rate related to time of day?", "hour_band",
            lambda f: f["is_peak_hour"] == 1, lambda f: f["is_peak_hour"] == 0, "Peak (17-23h) vs off-peak",
            "Breaches concentrate in the evening peak, especially 19-21h.",
            "Hour bands were chosen after inspecting the data; peak rule (>=2x median hourly volume) is descriptive.")
    cat_row("T6", "Is breach rate related to agent rating?", "rating_lt_4_5",
            lambda f: f["rating_lt_4_5"] == 1, lambda f: f["rating_lt_4_5"] == 0, "rating < 4.5 vs >= 4.5",
            "Deliveries with ratings below 4.5 breach several times more often, a large practical effect.",
            "Rating may be an outcome of delivery performance (reverse causation); attribute-level only, no agent ID.",
            frame=d.dropna(subset=["rating_lt_4_5"]))
    cat_row("T7", "Is breach rate related to agent age?", "age_ge_30",
            lambda f: f["age_ge_30"] == 1, lambda f: f["age_ge_30"] == 0, "age >= 30 vs < 30",
            "Deliveries by agents aged 30+ breach more often; the change is a step at 30, not gradual.",
            "Age and rating are related to area; the step at exactly 30 is unusual for real data.")
    cat_row("T8", "Is breach rate related to weekend vs weekday?", "is_weekend",
            lambda f: f["is_weekend"] == 1, lambda f: f["is_weekend"] == 0, "Weekend vs weekday",
            "No meaningful difference.", "About 8 weeks of data.")
    cat_row("T9", "Is breach rate related to preparation time?", "prep_time_minutes",
            lambda f: f["prep_time_minutes"] == 15, lambda f: f["prep_time_minutes"] == 5, "15 vs 5 minutes",
            "No association: prep time is not a lever in this dataset.",
            "Prep time takes only three values (5/10/15) and looks uniformly assigned.")

    # --- continuous outcome: delivery time
    for tid, col, label in (("T10", "traffic", "traffic"), ("T11", "weather", "weather")):
        groups = [g["delivery_time_minutes"].to_numpy() for _, g in d.groupby(col)]
        h, p, eps2 = kruskal_epsilon_squared(groups)
        rows.append({
            "id": tid, "business_question": f"Does delivery time differ across {label} levels?",
            "method": "Kruskal-Wallis H test; effect size = epsilon-squared",
            "why_this_test": "Delivery time is skewed and group variances differ (Levene), so a rank-based test is safer than ANOVA.",
            "key_assumptions": "Independent observations; similar distribution shapes for a pure location comparison.",
            "effect_size_name": "epsilon-squared", "effect_size": eps2,
            "effect_band": "large" if eps2 >= 0.14 else "medium" if eps2 >= 0.06 else "small" if eps2 >= 0.01 else "negligible",
            "headline_contrast": f"medians by {label}", "rate_group": np.nan, "rate_reference": np.nan,
            "risk_diff_pts": np.nan, "risk_ratio": np.nan, "ci_low": np.nan, "ci_high": np.nan,
            "p_value": p, "n": len(d),
            "practical_meaning": f"Share of rank variance in delivery time associated with {label}.",
            "limitations": "Omnibus test only; no post-hoc method was pre-specified. Not comparable to r-squared."})

    def two_group(tid, question, a, b, label, meaning, limitation):
        x, y = a["delivery_time_minutes"].to_numpy(float), b["delivery_time_minutes"].to_numpy(float)
        dcoh, dlo, dhi = cohens_d(x, y)
        pos = probability_of_superiority(x, y)
        u_p = stats.mannwhitneyu(x, y, alternative="two-sided")[1]
        # Welch CI for the mean difference. (A bootstrap CI for the median difference collapses to a
        # single value here because delivery times are multiples of 5, so it is not informative.)
        diff = x.mean() - y.mean()
        se = np.sqrt(x.var(ddof=1) / len(x) + y.var(ddof=1) / len(y))
        lo, hi = diff - 1.959964 * se, diff + 1.959964 * se
        med = float(np.median(x) - np.median(y))
        rows.append({
            "id": tid, "business_question": question,
            "method": "Mann-Whitney U; effects: mean difference (Welch 95% CI), median difference, Cohen's d (95% CI), probability of superiority",
            "why_this_test": "Rank-based test for skewed times; effect sizes tell the practical story.",
            "key_assumptions": "Independent observations; groups defined before looking at outcomes (except data-driven cuts, flagged).",
            "effect_size_name": "Cohen's d", "effect_size": dcoh,
            "effect_band": "negligible" if abs(dcoh) < 0.2 else "small" if abs(dcoh) < 0.5 else "medium" if abs(dcoh) < 0.8 else "large",
            "headline_contrast": f"{label}: mean difference {diff:+.1f} min (95% CI {lo:+.1f} to {hi:+.1f}); median difference {med:+.0f} min; probability of superiority {pos:.2f}",
            "rate_group": np.nan, "rate_reference": np.nan, "risk_diff_pts": np.nan, "risk_ratio": np.nan,
            "ci_low": dlo, "ci_high": dhi, "p_value": u_p, "n": len(x) + len(y),
            "practical_meaning": meaning, "limitations": limitation})

    two_group("T12", "Is delivery time different on weekends?", d[d["is_weekend"] == 1], d[d["is_weekend"] == 0],
              "weekend - weekday", "Practically identical; a clean null result.", "About 8 weeks of data.")
    valid = d.dropna(subset=["rating_lt_4_5"])
    two_group("T13", "Do low-rated deliveries take longer?", valid[valid["rating_lt_4_5"] == 1],
              valid[valid["rating_lt_4_5"] == 0], "rating < 4.5 - rating >= 4.5",
              "Low-rated deliveries take about 50 minutes longer on average, a large effect.",
              "Reverse causation is plausible (slow deliveries may earn low ratings).")
    two_group("T14", "Do deliveries by agents aged 30+ take longer?", d[d["age_ge_30"] == 1], d[d["age_ge_30"] == 0],
              "age >= 30 - age < 30", "A sizeable step at age 30.", "Data-driven cut; area and rating mix differ by age group.")
    out = pd.DataFrame(rows)
    out["p_value_note"] = "not used to judge importance (n ~ 43,000)"
    return out
