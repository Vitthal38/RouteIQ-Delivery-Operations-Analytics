"""Phase 4, Module 4 — Formal statistical tests, per STATISTICAL_ANALYSIS.md.

Implements Tests 1-5 exactly as documented: research question, groups, DV,
assumption checks (normality, homogeneity of variance / linearity as
applicable), test selection via the documented decision tree, test
statistic, p-value, effect size, and a plain interpretation that never
claims causation.

MULTIPLE COMPARISONS (Step 8): STATISTICAL_ANALYSIS.md documents omnibus
tests only (ANOVA/Kruskal-Wallis "at least one group differs") and does
not specify a post-hoc pairwise comparison method or multiple-comparison
correction anywhere in the 5 tests or the general decision tree. Per this
project's rule ("if no alternative is documented, STOP and report rather
than invent a methodology"), NO pairwise post-hoc comparisons are
performed in this module — inventing a correction method (Tukey HSD,
Bonferroni, Dunn's test) would itself be an undocumented methodological
choice. This is noted explicitly in the results, not silently skipped.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from _common import (
    classify_correlation_r,
    classify_effect_size_d,
    classify_effect_size_eta_epsilon,
    cohens_d,
    eta_squared_from_anova,
    epsilon_squared_from_kruskal,
    load_cleaned_data,
    logger,
    save_json,
)
from config import STATISTICAL_TEST_RESULTS_JSON

ALPHA = 0.05
SHAPIRO_MAX_SAMPLE = 5000
RNG_SEED = 42


def _shapiro_on_sample(values: np.ndarray, rng: np.random.Generator) -> tuple[float, float, int]:
    """Shapiro-Wilk on a random sample (max SHAPIRO_MAX_SAMPLE), since scipy's
    implementation is both size-limited and, per STATISTICAL_ANALYSIS.md,
    "oversensitive" at this dataset's full group sizes (thousands of rows) —
    at large n, Shapiro-Wilk rejects normality for even trivial deviations.
    Sampling is deterministic (fixed seed) for reproducibility."""
    n = len(values)
    sample = rng.choice(values, size=min(n, SHAPIRO_MAX_SAMPLE), replace=False)
    stat, p = stats.shapiro(sample)
    return float(stat), float(p), len(sample)


def _assumption_checks_multi_group(
    groups: dict[str, np.ndarray], rng: np.random.Generator
) -> dict[str, Any]:
    normality = {}
    for name, values in groups.items():
        stat, p, n_sampled = _shapiro_on_sample(values, rng)
        normality[name] = {
            "shapiro_w": round(stat, 4),
            "shapiro_p": p,
            "n_sampled": n_sampled,
            "n_total": len(values),
            "skewness": round(float(stats.skew(values)), 4),
            "normal_at_alpha_0.05": p > ALPHA,
        }
    levene_stat, levene_p = stats.levene(*groups.values())
    all_normal = all(v["normal_at_alpha_0.05"] for v in normality.values())
    equal_variance = levene_p > ALPHA
    return {
        "normality_per_group_shapiro_on_sample": normality,
        "homogeneity_of_variance_levene": {
            "statistic": round(float(levene_stat), 4),
            "p_value": float(levene_p),
            "equal_variance_at_alpha_0.05": equal_variance,
        },
        "all_groups_normal": all_normal,
        "equal_variance": equal_variance,
    }


def _run_multi_group_test(
    business_question: str, df: pd.DataFrame, group_col: str, rng: np.random.Generator
) -> dict[str, Any]:
    """Full decision-tree implementation for a >2-group comparison
    (Traffic = Test 1, Weather = Test 2)."""
    groups = {name: g["Delivery_Time"].to_numpy() for name, g in df.groupby(group_col)}
    assumptions = _assumption_checks_multi_group(groups, rng)

    group_values = list(groups.values())
    n_total = sum(len(g) for g in group_values)
    k_groups = len(group_values)

    if assumptions["all_groups_normal"] and assumptions["equal_variance"]:
        test_used = "One-way ANOVA"
        stat, p = stats.f_oneway(*group_values)
        effect_size = eta_squared_from_anova(group_values)
        effect_size_name = "eta_squared"
        effect_band = classify_effect_size_eta_epsilon(effect_size)
    else:
        test_used = "Kruskal-Wallis H-test"
        stat, p = stats.kruskal(*group_values)
        effect_size = epsilon_squared_from_kruskal(float(stat), n_total, k_groups)
        effect_size_name = "epsilon_squared"
        effect_band = classify_effect_size_eta_epsilon(effect_size)

    return {
        "business_question": business_question,
        "h0": f"Mean/distribution of delivery_time_minutes is equal across all {group_col} groups.",
        "h1": f"At least one {group_col} group's delivery_time_minutes differs.",
        "groups": {name: len(g) for name, g in groups.items()},
        "n_total": n_total,
        "assumption_checks": assumptions,
        "test_selected": test_used,
        "test_selection_reason": (
            "Both normality (per-group Shapiro on sample) and homogeneity of "
            "variance (Levene's) held at alpha=0.05."
            if test_used == "One-way ANOVA"
            else "Normality and/or homogeneity of variance failed at alpha=0.05 "
            "-> non-parametric fallback used, per the documented decision tree."
        ),
        "test_statistic": round(float(stat), 4),
        "p_value": float(p),
        "significant_at_alpha_0.05": bool(p < ALPHA),
        "effect_size_name": effect_size_name,
        "effect_size_value": round(float(effect_size), 4),
        "effect_size_band": effect_band,
        "interpretation": (
            f"The {test_used} result is "
            f"{'statistically significant' if p < ALPHA else 'not statistically significant'} "
            f"(p={p:.6g}). Effect size ({effect_size_name}={effect_size:.4f}) is classified as "
            f"'{effect_band}' per Cohen's conventional bands. This describes an observed "
            f"association between {group_col} and delivery time — it does not establish "
            f"that {group_col} causes delivery delay."
        ),
        "limitation": (
            f"At n_total={n_total}, even a small effect can reach statistical significance; "
            "the effect-size band above, not the p-value alone, should drive any operational "
            "interpretation. No pairwise post-hoc comparison is performed — "
            "STATISTICAL_ANALYSIS.md does not document a post-hoc method or multiple-comparison "
            "correction for this test."
        ),
    }


def _run_two_group_test(
    business_question: str, a: np.ndarray, a_label: str, b: np.ndarray, b_label: str,
    rng: np.random.Generator,
) -> dict[str, Any]:
    """Full decision-tree implementation for a 2-group comparison (Weekend
    vs. Weekday = Test 5)."""
    stat_a, p_a, n_a = _shapiro_on_sample(a, rng)
    stat_b, p_b, n_b = _shapiro_on_sample(b, rng)
    levene_stat, levene_p = stats.levene(a, b)

    normal = (p_a > ALPHA) and (p_b > ALPHA)
    equal_var = levene_p > ALPHA

    if normal and equal_var:
        test_used = "Independent samples t-test (equal variance)"
        stat, p = stats.ttest_ind(a, b, equal_var=True)
    elif normal and not equal_var:
        test_used = "Welch's t-test (unequal variance)"
        stat, p = stats.ttest_ind(a, b, equal_var=False)
    else:
        test_used = "Mann-Whitney U test"
        stat, p = stats.mannwhitneyu(a, b, alternative="two-sided")

    d = cohens_d(a, b)

    return {
        "business_question": business_question,
        "h0": f"Mean delivery_time_minutes is equal between {a_label} and {b_label}.",
        "h1": f"Mean delivery_time_minutes differs between {a_label} and {b_label}.",
        "group_sizes": {a_label: len(a), b_label: len(b)},
        "assumption_checks": {
            "normality": {
                a_label: {"shapiro_w": round(stat_a, 4), "shapiro_p": p_a, "n_sampled": n_a, "normal": p_a > ALPHA},
                b_label: {"shapiro_w": round(stat_b, 4), "shapiro_p": p_b, "n_sampled": n_b, "normal": p_b > ALPHA},
            },
            "homogeneity_of_variance_levene": {
                "statistic": round(float(levene_stat), 4), "p_value": float(levene_p), "equal_variance": equal_var,
            },
        },
        "test_selected": test_used,
        "test_statistic": round(float(stat), 4),
        "p_value": float(p),
        "significant_at_alpha_0.05": bool(p < ALPHA),
        "effect_size_name": "cohens_d",
        "effect_size_value": round(float(d), 4),
        "effect_size_band": classify_effect_size_d(d),
        "interpretation": (
            f"The {test_used} result is "
            f"{'statistically significant' if p < ALPHA else 'not statistically significant'} "
            f"(p={p:.6g}). Cohen's d={d:.4f} is classified as '{classify_effect_size_d(d)}'. "
            f"This describes an observed difference between {a_label} and {b_label} — it does "
            "not establish that day type causes a delivery-time difference."
        ),
        "limitation": (
            f"At n={len(a) + len(b)}, statistical significance is easy to reach even for a "
            "practically negligible difference; the effect-size band should drive interpretation."
        ),
    }


def _run_correlation_test(
    business_question: str, x: np.ndarray, y: np.ndarray, x_label: str, y_label: str
) -> dict[str, Any]:
    """Pearson primary / Spearman fallback correlation test, per Tests 3-4's
    documented structure."""
    pearson_r, pearson_p = stats.pearsonr(x, y)
    spearman_r, spearman_p = stats.spearmanr(x, y)
    linearity_gap = abs(spearman_r) - abs(pearson_r)
    linear_enough = abs(linearity_gap) < 0.03

    primary = "Pearson" if linear_enough else "Spearman"
    primary_r = pearson_r if linear_enough else spearman_r
    primary_p = pearson_p if linear_enough else spearman_p

    return {
        "business_question": business_question,
        "h0": f"No linear relationship between {x_label} and {y_label} (population correlation rho=0).",
        "h1": "rho != 0.",
        "n": int(len(x)),
        "assumption_checks": {
            "linearity_diagnostic": {
                "pearson_r": round(float(pearson_r), 4),
                "spearman_r": round(float(spearman_r), 4),
                "gap": round(float(linearity_gap), 4),
                "linear_relationship_reasonable": linear_enough,
            },
        },
        "test_selected": f"{primary} correlation ({'primary' if linear_enough else 'fallback, linearity assumption did not hold'})",
        "correlation_coefficient": round(float(primary_r), 4),
        "r_squared": round(float(primary_r) ** 2, 4),
        "p_value": float(primary_p),
        "significant_at_alpha_0.05": bool(primary_p < ALPHA),
        "effect_size_name": "r (the coefficient itself)",
        "effect_size_band": classify_correlation_r(primary_r),
        "interpretation": (
            f"{primary} r={primary_r:.4f} (r^2={primary_r**2:.4f}), "
            f"{'statistically significant' if primary_p < ALPHA else 'not statistically significant'} "
            f"(p={primary_p:.6g}). Classified as a '{classify_correlation_r(primary_r)}' relationship. "
            f"This is an observed association between {x_label} and {y_label} — it does not "
            "establish that one causes the other; reverse causality or confounding factors "
            "are plausible alternative explanations."
        ),
        "limitation": (
            "Correlation does not establish causation. At this sample size, even a weak "
            "correlation reaches statistical significance."
        ),
    }


def main() -> None:
    df = load_cleaned_data()
    rng = np.random.default_rng(RNG_SEED)

    results: dict[str, Any] = {}

    # Test 1 — Traffic vs. delivery time
    results["test_1_traffic_vs_delivery_time"] = _run_multi_group_test(
        "Does traffic significantly affect delivery time? (Business Questions #3, #13)",
        df, "Traffic", rng,
    )

    # Test 2 — Weather vs. delivery time
    results["test_2_weather_vs_delivery_time"] = _run_multi_group_test(
        "Does weather significantly affect delivery time? (Business Questions #5, #12, #13)",
        df, "Weather", rng,
    )

    # Test 2b — secondary two-group comparison: clear (Sunny) vs adverse (non-Sunny),
    # per STATISTICAL_ANALYSIS.md Test 2's note supporting Business Question #19.
    clear = df.loc[df["Weather"] == "Sunny", "Delivery_Time"].to_numpy()
    adverse = df.loc[df["Weather"] != "Sunny", "Delivery_Time"].to_numpy()
    results["test_2b_clear_vs_adverse_weather"] = _run_two_group_test(
        "Delivery-time delta: clear vs. adverse weather (Business Question #19)",
        clear, "Clear (Sunny)", adverse, "Adverse (non-Sunny)", rng,
    )

    # Test 3 — Agent rating vs. delivery time
    valid_rating = df.loc[df["agent_rating_valid_flag"]]
    results["test_3_agent_rating_vs_delivery_time"] = _run_correlation_test(
        "Relationship between agent rating and delivery time (Business Question #4)",
        valid_rating["Agent_Rating"].to_numpy(), valid_rating["Delivery_Time"].to_numpy(),
        "agent_rating", "delivery_time_minutes",
    )

    # Test 4 — Distance vs. delivery time
    valid_coords = df.loc[df["coordinates_valid_flag"]]
    results["test_4_distance_vs_delivery_time"] = _run_correlation_test(
        "Does distance correlate with delivery time, or is it condition-driven? (Business Question #10)",
        valid_coords["distance_km"].to_numpy(), valid_coords["Delivery_Time"].to_numpy(),
        "distance_km", "delivery_time_minutes",
    )

    # Test 5 — Weekend vs. weekday
    weekday = df.loc[~df["is_weekend"], "Delivery_Time"].to_numpy()
    weekend = df.loc[df["is_weekend"], "Delivery_Time"].to_numpy()
    results["test_5_weekend_vs_weekday"] = _run_two_group_test(
        "Weekend vs. weekday delivery time (Business Question #7)",
        weekday, "Weekday", weekend, "Weekend", rng,
    )

    results["multiple_comparisons_note"] = (
        "No pairwise post-hoc comparisons were performed for Tests 1 or 2, even where the "
        "omnibus test was significant. STATISTICAL_ANALYSIS.md documents omnibus tests only "
        "and does not specify a post-hoc method or multiple-comparison correction for either "
        "test — inventing one (Tukey HSD, Bonferroni, Dunn's test) would itself be an "
        "undocumented methodological choice, which this project's rules prohibit."
    )

    save_json(results, STATISTICAL_TEST_RESULTS_JSON)

    for key, res in results.items():
        if isinstance(res, dict) and "p_value" in res:
            logger.info(
                "%s: test=%s stat=%s p=%.6g effect=%s (%s)",
                key, res["test_selected"], res.get("test_statistic", res.get("correlation_coefficient")),
                res["p_value"], res.get("effect_size_value", res.get("correlation_coefficient")),
                res.get("effect_size_band"),
            )

    logger.info("Module 4 (statistical tests) complete")


if __name__ == "__main__":
    main()
