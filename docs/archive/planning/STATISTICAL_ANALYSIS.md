# Statistical Analysis Plan — RouteIQ

## Table of Contents
1. [Purpose](#purpose)
2. [Test 1 — Traffic Condition vs. Delivery Time](#test-1--traffic-condition-vs-delivery-time)
3. [Test 2 — Weather Condition vs. Delivery Time](#test-2--weather-condition-vs-delivery-time)
4. [Test 3 — Agent Rating vs. Delivery Time (Correlation)](#test-3--agent-rating-vs-delivery-time-correlation)
5. [Test 4 — Distance vs. Delivery Time (Correlation)](#test-4--distance-vs-delivery-time-correlation)
6. [Test 5 — Weekend vs. Weekday Delivery Time](#test-5--weekend-vs-weekday-delivery-time)
7. [General Decision Tree for Test Selection](#general-decision-tree-for-test-selection)
8. [Effect Size Reporting Standard](#effect-size-reporting-standard)
9. [Interpretation Standard](#interpretation-standard)

Related documents: `PYTHON_ANALYSIS_PLAN.md` (Phase 2 executes this plan), `KPI_DEFINITIONS.md` (KPI #5, #6 depend on these results), `ASSUMPTIONS.md` (A10)

**Process rule:** for every test below, assumption checks are run and logged *before* the test's p-value is interpreted or reported anywhere. A test run without its assumption check being logged is not considered complete per this project's standard.

---

## Test 1 — Traffic Condition vs. Delivery Time

- **Business Question Addressed:** #3, #13 (does traffic significantly affect delivery time)
- **Null Hypothesis (H₀):** Mean delivery time is equal across all `Traffic` categories (Low, Jam, Medium, High — post-cleaning categories, per `DATASET_OVERVIEW.md`).
- **Alternative Hypothesis (H₁):** At least one `Traffic` category's mean delivery time differs from the others.
- **Test Selection (primary):** One-way ANOVA — appropriate for comparing means across more than two independent groups.
- **Assumption Checks Required Before Trusting ANOVA:**
  - Normality of `delivery_time_minutes` within each traffic group (Shapiro-Wilk, or visual QQ-plot given large group sizes where Shapiro-Wilk is oversensitive).
  - Homogeneity of variance across groups (Levene's test).
- **Fallback Test:** Kruskal-Wallis H-test (non-parametric, rank-based) if either assumption fails — this does not require normal distributions or equal variances and tests for differences in distribution/rank rather than mean directly.
- **Effect Size:** Eta-squared (η²) for ANOVA, or epsilon-squared for Kruskal-Wallis — reported alongside the p-value, since with n≈43,700 even a trivially small difference can be statistically significant; effect size is what determines whether the finding is *operationally* meaningful.
- **Interpretation:** A significant result (p < 0.05) with a meaningful effect size supports treating traffic as a genuine delay driver worth operational action; a significant result with a negligible effect size (plausible at this sample size) should be reported as "statistically detectable but operationally small" — not overstated as a major driver.

## Test 2 — Weather Condition vs. Delivery Time

- **Business Question Addressed:** #5, #12, #13, #19
- **Null Hypothesis (H₀):** Mean delivery time is equal across all `Weather` categories (Sunny, Cloudy, Fog, Sandstorms, Stormy, Windy).
- **Alternative Hypothesis (H₁):** At least one weather category's mean delivery time differs from the others.
- **Test Selection:** Same structure as Test 1 — one-way ANOVA primary, Kruskal-Wallis fallback.
- **Assumption Checks:** Same as Test 1, run independently for the weather grouping (group sizes are roughly even per profiling — ~7,000–7,400 rows per category — so assumption failure risk is lower than for an imbalanced grouping, but the check is still mandatory, not skipped on that assumption).
- **Effect Size:** η² / epsilon-squared, same standard as Test 1.
- **Interpretation:** Same standard as Test 1. Additionally supports Business Question #19 (clear vs. adverse weather delta) as a secondary, simpler two-group comparison — see decision tree below for why that sub-question uses a different (two-group) test rather than reusing the multi-group ANOVA output directly.

## Test 3 — Agent Rating vs. Delivery Time (Correlation)

- **Business Question Addressed:** #4
- **Null Hypothesis (H₀):** There is no linear relationship between `agent_rating` and `delivery_time_minutes` (population correlation ρ = 0).
- **Alternative Hypothesis (H₁):** ρ ≠ 0.
- **Test Selection (primary):** Pearson correlation coefficient — appropriate if both variables are approximately linearly related and reasonably continuous (rating is technically ordinal/bounded, but treated as quasi-continuous here per standard practice for 1–5-type rating scales).
- **Assumption Checks:** Linearity (scatterplot review), no extreme outlier distortion (the 53 rows with `Agent_Rating = 6.0` must be excluded per `DATA_CLEANING_PLAN.md` Step 4 *before* this test runs, not filtered out reactively because they look like outliers in the correlation plot).
- **Fallback Test:** Spearman's rank correlation if linearity assumption fails or if the relationship looks monotonic-but-nonlinear.
- **Effect Size:** The correlation coefficient (r or ρ) itself is the effect size measure here — no separate calculation needed. Reported with r² (variance explained) for interpretability.
- **Interpretation:** A statistically significant but weak correlation (e.g., |r| < 0.2) should be reported as "a detectable but weak relationship — agent rating alone does not explain much delivery-time variance" rather than implied as a strong lever, consistent with the causality caveat in `KPI_DEFINITIONS.md` KPI #6.

## Test 4 — Distance vs. Delivery Time (Correlation)

- **Business Question Addressed:** #10
- **Null Hypothesis (H₀):** No linear relationship between `distance_km` and `delivery_time_minutes` (ρ = 0).
- **Alternative Hypothesis (H₁):** ρ ≠ 0.
- **Test Selection:** Pearson primary, Spearman fallback — same logic as Test 3.
- **Assumption Checks:** Run only on `coordinates_valid_flag = true` rows (per `FEATURE_ENGINEERING.md` #1 edge-case handling) — including invalid-coordinate rows here would inject the exact distance-computation error the cleaning plan was designed to prevent.
- **Effect Size:** r / r², same standard as Test 3.
- **Interpretation:** This test directly informs Business Question #10's "is it distance-driven or condition-driven" framing — if distance shows a weak correlation while Tests 1–2 show a stronger/more significant effect for traffic or weather, that comparison itself (not just each test in isolation) is the reportable insight, and should be stated as a comparison, not two disconnected findings.

## Test 5 — Weekend vs. Weekday Delivery Time

- **Business Question Addressed:** #7
- **Null Hypothesis (H₀):** Mean delivery time is equal for weekend vs. weekday orders.
- **Alternative Hypothesis (H₁):** Mean delivery time differs between weekend and weekday orders.
- **Test Selection (primary):** Independent samples t-test (two groups only, unlike Tests 1–2's multi-group ANOVA).
- **Assumption Checks:** Normality per group, equal variance (Levene's) — determines Welch's t-test (unequal variance) vs. standard t-test.
- **Fallback Test:** Mann-Whitney U test (non-parametric two-group comparison) if normality fails.
- **Effect Size:** Cohen's d.
- **Interpretation:** Same standard as above — statistical significance alone (likely, given n≈43,700) is not sufficient to declare a meaningful weekend effect; Cohen's d must support a real-world-relevant gap.

## General Decision Tree for Test Selection

```
Is the comparison between exactly 2 groups, or more than 2?
│
├── 2 groups (e.g., weekend vs. weekday, clear vs. adverse weather)
│    │
│    ├── Normality holds (both groups) AND variances roughly equal
│    │      → Independent samples t-test
│    ├── Normality holds, variances unequal
│    │      → Welch's t-test
│    └── Normality fails
│           → Mann-Whitney U test
│
├── More than 2 groups (e.g., Traffic: 4 categories, Weather: 6 categories)
│    │
│    ├── Normality holds (per group) AND variances roughly equal (Levene's)
│    │      → One-way ANOVA, report η²
│    └── Either assumption fails
│           → Kruskal-Wallis H-test, report epsilon-squared
│
└── Relationship between two continuous/quasi-continuous variables (rating, age, distance vs. delivery time)
     │
     ├── Linear relationship, no extreme outlier distortion
     │      → Pearson correlation, report r / r²
     └── Nonlinear-but-monotonic or linearity assumption fails
            → Spearman's rank correlation
```

This decision tree is the single reference every test above follows — no test in this document deviates from it without a documented reason.

## Effect Size Reporting Standard

Every test in this document reports an effect size alongside its p-value, without exception, for one specific reason: at this dataset's scale (n≈43,700, per group typically several thousand), even operationally trivial differences will frequently reach statistical significance (p < 0.05). Reporting only the p-value would risk overstating minor differences as major operational findings. The effect-size threshold used to judge "meaningful" (e.g., Cohen's conventional small/medium/large bands) is stated explicitly wherever a finding is written up in `BUSINESS_INSIGHTS_TEMPLATE.md`, not left implicit.

## Interpretation Standard

Every statistical finding in this project is written up with three explicit components, in this order: (1) the statistical result (test, p-value, effect size), (2) what it does and does not establish (association, not causation, unless a controlled/quasi-experimental design is separately justified — none is planned here), and (3) the operational implication, scoped to the effect size, not just the presence of significance. This standard applies uniformly across all five tests above and any additional test added later.
