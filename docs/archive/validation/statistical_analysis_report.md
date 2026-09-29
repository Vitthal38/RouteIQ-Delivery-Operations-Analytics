# Statistical Analysis Report — RouteIQ Phase 4

Generated: 2026-08-16

Implements `STATISTICAL_ANALYSIS.md` Tests 1-5 exactly as documented,
executed in `python/analysis/04_statistical_tests.py` against the approved
`data/cleaned/cleaned_delivery.csv` (43,648 rows). Full machine-readable
results: `output/statistical_test_results.json`.

**Interpretation standard applied throughout, per `STATISTICAL_ANALYSIS.md`:**
every result states (1) the statistical result, (2) what it does and does
not establish — association, not causation — and (3) the operational
scope, bounded by effect size, not significance alone. No result in this
report claims that any variable *causes* a delivery-time outcome.

---

## Test 1 — Traffic vs. Delivery Time

- **Business question:** Does traffic significantly affect delivery time? (Business Questions #3, #13)
- **H0:** Mean/distribution of `delivery_time_minutes` is equal across all `Traffic` groups.
- **H1:** At least one `Traffic` group's `delivery_time_minutes` differs.
- **Dependent variable:** `delivery_time_minutes`
- **Groups:** High (n=4,296), Jam (n=13,725), Low (n=14,999), Medium (n=10,628)
- **Sample size:** n = 43,648

**Assumption checks:**
- Normality (Shapiro-Wilk on a random sample, max 5,000/group — full group sizes make Shapiro-Wilk oversensitive per the documented caveat): **all 4 groups reject normality** (p < 1e-14 in every group)
- Homogeneity of variance (Levene's): statistic = 689.3356, p ≈ 0.0 → **variances not equal**

**Test selected:** Kruskal-Wallis H-test (non-parametric fallback — both assumptions failed, per the documented decision tree)

- **Test statistic:** H = 6132.4554
- **p-value:** ≈ 0.0 (< 1e-300; reported as 0.0 due to float underflow at this sample size)
- **Significant at α=0.05:** Yes
- **Effect size:** ε² = 0.1404 → **large** (Cohen's conventional bands)

**Interpretation:** Traffic condition shows a statistically significant and
practically large association with delivery time. Unlike several other
tests in this report, this is not a "significant but trivial" case — the
effect size itself supports treating traffic as a meaningful observed
delay factor, consistent with `KPI_DEFINITIONS.md` #5's framing. This
describes an association, not a causal mechanism.

**Limitations:** No pairwise post-hoc comparison is performed —
`STATISTICAL_ANALYSIS.md` documents the omnibus test only and specifies no
post-hoc method or multiple-comparison correction; inventing one here
would itself be an undocumented methodological choice.

---

## Test 2 — Weather vs. Delivery Time

- **Business question:** Does weather significantly affect delivery time? (Business Questions #5, #12, #13)
- **H0:** Mean/distribution of `delivery_time_minutes` is equal across all `Weather` groups.
- **H1:** At least one `Weather` group's `delivery_time_minutes` differs.
- **Dependent variable:** `delivery_time_minutes`
- **Groups:** Cloudy (7,288), Fog (7,440), Sandstorms (7,245), Stormy (7,374), Sunny (7,078), Windy (7,223)
- **Sample size:** n = 43,648

**Assumption checks:**
- Normality: **all 6 groups reject normality** (Sunny especially: skewness = 0.7754, the most right-skewed group)
- Homogeneity of variance (Levene's): statistic = 240.7436, p ≈ 1.5e-254 → **variances not equal**

**Test selected:** Kruskal-Wallis H-test (non-parametric fallback)

- **Test statistic:** H = 2262.8928
- **p-value:** ≈ 0.0
- **Significant at α=0.05:** Yes
- **Effect size:** ε² = 0.0517 → **small**

**Interpretation:** Weather shows a statistically significant but
practically small association with delivery time — a real, detectable
pattern, but a materially smaller one than traffic's. This must be
reported as "statistically detectable but operationally small," per
`STATISTICAL_ANALYSIS.md`'s explicit interpretation standard for exactly
this scenario, not overstated as a major driver.

**Limitations:** Same post-hoc scope note as Test 1.

### Test 2b — Clear (Sunny) vs. Adverse (non-Sunny) Weather

Secondary two-group comparison, per `STATISTICAL_ANALYSIS.md` Test 2's
note supporting Business Question #19. "Adverse" = all non-Sunny weather
values, matching `sql/analysis/Q19_*.sql`'s documented grouping.

- **H0:** Mean `delivery_time_minutes` is equal between Clear and Adverse.
- **H1:** Mean `delivery_time_minutes` differs.
- **Groups:** Clear/Sunny (n=7,078), Adverse/non-Sunny (n=36,570)
- **Assumption checks:** both groups reject normality; Levene's p ≈ 2.0e-83 → unequal variance
- **Test selected:** Mann-Whitney U test
- **Test statistic:** U = 88,955,306.0
- **p-value:** ≈ 0.0
- **Effect size:** Cohen's d = -0.4965 → **small** (just under the medium threshold of 0.5)
- **Interpretation:** Adverse-weather deliveries are, on average, meaningfully slower than clear-weather deliveries, and the effect is on the larger end of "small" — a real but moderate difference, not a dramatic one.
- **Limitation:** Cohen's d is a mean-based effect size; it is reported here because `STATISTICAL_ANALYSIS.md` specifies Cohen's d for this comparison without conditioning on which significance test is used, even though the significance test itself (Mann-Whitney) is rank-based. This is noted for transparency, not hidden.

---

## Test 3 — Agent Rating vs. Delivery Time (Correlation)

- **Business question:** Relationship between agent rating and delivery time (Business Question #4)
- **H0:** No linear relationship between `agent_rating` and `delivery_time_minutes` (ρ = 0)
- **H1:** ρ ≠ 0
- **Variables:** `agent_rating`, `delivery_time_minutes`
- **Sample size:** n = 43,594 (`agent_rating_valid_flag = true` only — excludes both the 54 true-nulls and the pre-Step-3 out-of-range 6.0 rows)

**Assumption checks (linearity):** Pearson r = -0.3077, Spearman r =
-0.2601, gap = -0.0476 (exceeds the 0.03 diagnostic threshold) → **linear
assumption did not hold well enough**; Spearman used as the primary result.

**Test selected:** Spearman correlation (fallback)

- **Correlation coefficient:** r = -0.2601 (r² = 0.0677)
- **p-value:** ≈ 0.0
- **Significant at α=0.05:** Yes
- **Effect size:** the coefficient itself → **weak**

**Interpretation:** Higher-rated agents are associated with somewhat
shorter delivery times, but the relationship is weak (r² ≈ 0.068 — agent
rating explains under 7% of delivery-time variance). Consistent with
`KPI_DEFINITIONS.md` #6's explicit caution: this must be reported as "a
detectable but weak relationship," not implied as a strong lever.
Reverse causality (faster deliveries → better ratings) or confounding
(experienced agents assigned easier routes) remain plausible alternative
explanations that this correlation cannot rule out.

**Limitation:** Attribute-level only — `DimAgent`/`Agent_Rating` reflects
a rating attribute, not a trackable individual agent (no true `Agent_ID`
exists in the source data). This result must never be read as a claim about
a specific agent's individual delivery times.

---

## Test 4 — Distance vs. Delivery Time (Correlation)

- **Business question:** Does distance correlate with delivery time, or is it condition-driven? (Business Question #10)
- **H0:** No linear relationship between `distance_km` and `delivery_time_minutes` (ρ = 0)
- **H1:** ρ ≠ 0
- **Variables:** `distance_km`, `delivery_time_minutes`
- **Sample size:** n = 39,997 (`coordinates_valid_flag = true` only)

**Assumption checks (linearity):** Pearson r = 0.2781, Spearman r =
0.2853, gap = 0.0071 (well within the 0.03 diagnostic threshold) →
**linear relationship is a reasonable approximation.**

**Test selected:** Pearson correlation (primary)

- **Correlation coefficient:** r = 0.2781 (r² = 0.0774)
- **p-value:** ≈ 0.0
- **Significant at α=0.05:** Yes
- **Effect size:** the coefficient itself → **weak**

**Interpretation:** Distance is positively associated with delivery time,
but weakly (r² ≈ 0.077 — distance explains under 8% of delivery-time
variance). Comparing this to Tests 1-2: **traffic's effect size (ε²=0.1404,
large) and even weather's (ε²=0.0517, small) are larger than distance's
correlation strength (r²=0.0774)** — this comparison itself, per
`STATISTICAL_ANALYSIS.md` Test 4's explicit framing, is the reportable
finding for Business Question #10: delivery time in this dataset appears
more condition-driven (traffic especially) than distance-driven, based on
relative effect magnitude, not distance alone being unimportant.

**Limitation:** Correlational, not causal. Restricted to the 91.6% of
rows with valid coordinates (`coordinates_valid_flag = true`); the
excluded 8.4% cannot be assessed for this relationship at all.

---

## Test 5 — Weekend vs. Weekday Delivery Time

- **Business question:** Weekend vs. weekday delivery time (Business Question #7)
- **H0:** Mean `delivery_time_minutes` is equal between Weekday and Weekend.
- **H1:** Mean `delivery_time_minutes` differs.
- **Dependent variable:** `delivery_time_minutes`
- **Groups:** Weekday (n=31,627), Weekend (n=12,021)
- **Sample size:** n = 43,648

**Assumption checks:** both groups reject normality (Shapiro-Wilk on
sample); Levene's test result available in `output/statistical_test_results.json`
(both groups fail normality, triggering the non-parametric path
regardless of the variance-homogeneity outcome).

**Test selected:** Mann-Whitney U test

- **Test statistic:** U = 190,043,643.5
- **p-value:** 0.9658
- **Significant at α=0.05:** **No**
- **Effect size:** Cohen's d = -0.0013 → **negligible**

**Interpretation:** There is **no statistically significant difference**
in delivery time between weekend and weekday orders, and the effect size
is negligible regardless. This is the one test in this report where the
null hypothesis is not rejected — weekend/weekday is not a meaningful
delay factor in this dataset.

**Limitation:** None beyond the general dataset scope (single ~8-week
window).

---

## Multiple Comparisons (Step 8)

No pairwise post-hoc comparisons were performed anywhere in this report,
even for the two significant omnibus tests (Traffic, Weather).
`STATISTICAL_ANALYSIS.md` documents omnibus tests only (ANOVA/Kruskal-Wallis
"at least one group differs") and does not specify a post-hoc method or
multiple-comparison correction (Tukey HSD, Bonferroni, Dunn's test, etc.)
anywhere in its 5 tests or general decision tree. Per this project's rule
— if no alternative methodology is documented, stop and report rather than
invent one — none was added here.

## Summary Table

| Test | Comparison | Test Used | Statistic | p-value | Effect Size | Band | Significant |
|---|---|---|---|---|---|---|---|
| 1 | Traffic (4 groups) | Kruskal-Wallis | H=6132.4554 | ≈0 | ε²=0.1404 | large | Yes |
| 2 | Weather (6 groups) | Kruskal-Wallis | H=2262.8928 | ≈0 | ε²=0.0517 | small | Yes |
| 2b | Clear vs. Adverse weather | Mann-Whitney | U=88,955,306.0 | ≈0 | d=-0.4965 | small | Yes |
| 3 | Agent rating vs. time | Spearman | r=-0.2601 | ≈0 | r²=0.0677 | weak | Yes |
| 4 | Distance vs. time | Pearson | r=0.2781 | ≈0 | r²=0.0774 | weak | Yes |
| 5 | Weekend vs. weekday | Mann-Whitney | U=190,043,643.5 | 0.9658 | d=-0.0013 | negligible | **No** |

**No recommendation is derived from this table in this document** — per
the Phase 4 scope boundary, statistical results are not yet converted into
executive recommendations.
