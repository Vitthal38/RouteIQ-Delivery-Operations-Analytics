# Validated Findings Candidates — RouteIQ Phase 4

Generated: 2026-08-16

**These are candidate findings, not executive recommendations.** Each one
is a data-supported observation with its evidence trail and limitations
stated. Business impact, action items, and financial figures are
explicitly deferred to a later, separately-reviewed phase
(`EXECUTIVE_RECOMMENDATIONS_TEMPLATE.md`'s process). No candidate below
contains an invented business-impact value or financial savings figure.

---

### Candidate 1 — Traffic is the strongest observed delivery-time driver among the conditions tested

- **Observation:** Delivery time differs across traffic levels with the largest effect size of any test in this phase.
- **Metric:** Kruskal-Wallis H = 6132.4554, ε² = 0.1404 (large)
- **Supporting analysis:** `reports/statistical_analysis_report.md` Test 1; group means Low 101.35 → Jam 147.76 min (`output/eda_summary.json`)
- **Statistical evidence:** p ≈ 0.0 (Kruskal-Wallis, non-parametric — normality and equal-variance both failed)
- **SQL validation reference:** `sql/analysis/Q03_traffic_group_stats_for_significance_test.sql` — group n's match exactly (High 4,296 / Jam 13,725 / Low 14,999 / Medium 10,628)
- **Limitation:** Association, not causation. No pairwise post-hoc comparison performed (undocumented method).
- **Confidence level:** **High** — large effect size, not just significance, at full dataset scale.

### Candidate 2 — Weather is associated with delivery time, but the effect is small relative to traffic

- **Observation:** Weather groups differ significantly, but the effect size is an order of magnitude smaller than traffic's.
- **Metric:** Kruskal-Wallis H = 2262.8928, ε² = 0.0517 (small)
- **Supporting analysis:** `reports/statistical_analysis_report.md` Test 2; Cloudy/Fog slowest (~137-138 min), Sunny fastest (103.66 min)
- **Statistical evidence:** p ≈ 0.0
- **SQL validation reference:** `sql/analysis/Q13_weather_group_stats_for_significance_test.sql`, `Q12_weather_with_most_sla_breaches.sql`
- **Limitation:** "Statistically detectable but operationally small," per `STATISTICAL_ANALYSIS.md`'s own interpretation standard for this exact scenario — must not be overstated as a major driver.
- **Confidence level:** **Medium** — significant and directionally consistent, but small effect size caps how much weight it should carry.

### Candidate 3 — Metropolitian accounts for the large majority of total breach volume

- **Observation:** A single area segment accounts for 83.73% of all SLA breaches.
- **Metric:** 8,648 of 10,328 total breaches (cumulative_breach_share_pct = 83.7335%)
- **Supporting analysis:** `output/pareto_ranking.csv` (area cut); this is also where 32,634 of 43,648 deliveries (74.8%) occur, so high breach share partly reflects high volume share, not purely a higher rate — Metropolitian's breach *rate* (26.50%) is elevated but not the highest (Semi-Urban's is, see Candidate 4)
- **Statistical evidence:** Descriptive Pareto ranking; no hypothesis test attached to this framing
- **SQL validation reference:** `sql/analysis/Q14_pareto_breach_share_area_and_category.sql` (area cut), `Q01_sla_breach_rate_overall_and_by_area.sql`
- **Limitation:** Concentration describes where breach *volume* sits, not why — a Pareto ranking does not identify a root cause, only where effort would touch the most breach volume per `KPI_DEFINITIONS.md` #7's own framing.
- **Confidence level:** **High** for the volume-share figure itself (large n, simple count); **not applicable** as a causal or rate-based claim.

### Candidate 4 — Semi-Urban has a 100% breach rate, but on a very small sample

- **Observation:** Every one of Semi-Urban's deliveries breaches its category's SLA threshold.
- **Metric:** 152/152 breaches (100.0000%), average delivery time 238.55 min vs. the 124.91 min dataset average
- **Supporting analysis:** `output/eda_summary.json` (`delivery_time_by_area`), `output/figures/02_breach_rate_by_area.png`
- **Statistical evidence:** Descriptive only — n=152 is too small for the omnibus tests in this phase to isolate an area-specific effect at this granularity
- **SQL validation reference:** `sql/analysis/Q01_sla_breach_rate_overall_and_by_area.sql`, `Q02_worst_p90_delivery_time_by_area.sql`, `Q16_lowest_otd_area.sql`
- **Limitation:** 152 rows is 0.35% of the dataset — a striking figure that still deserves a small-sample caveat before being treated as a stable, generalizable rate.
- **Confidence level:** **Medium** — the figure itself is exact and reproducible, but the small n limits how confidently it generalizes.

### Candidate 5 — Fog + Jam traffic is the single largest weather×traffic breach segment

- **Observation:** Among all 24 weather×traffic combinations, Fog/Jam contributes the most breach volume of any single combination.
- **Metric:** 1,592 breaches from Fog/Jam (n=2,365 deliveries in that combination), 15.41% of total breach volume; the top 5 Jam-traffic combinations together account for 53.75% of all breaches
- **Supporting analysis:** `output/pareto_ranking.csv` (weather_traffic cut)
- **Statistical evidence:** Descriptive Pareto ranking; Jam traffic's broader association with delivery time is separately supported by Test 1 (Candidate 1)
- **SQL validation reference:** `sql/analysis/Q20_area_traffic_breach_concentration.sql` (area×traffic cut, a related but distinct 2-D combination), `Q05_top_weather_traffic_longest_delivery.sql`
- **Limitation:** Pareto concentration, not a causal claim; the "adverse weather + heavy traffic" combinations dominate this ranking, consistent with Candidates 1-2's individual-factor results, but this does not prove an interaction effect (no interaction test was run — out of scope for the documented test plan).
- **Confidence level:** **Medium** — descriptively strong and reproducible, but not backed by a formal interaction-effect test.

### Candidate 6 — Distance, agent rating, and agent age each show weak but real associations with delivery time

- **Observation:** All three correlations are statistically significant, directionally sensible, but individually explain under 8% of delivery-time variance.
- **Metric:** distance r=0.2781 (r²=0.0774); agent rating r=-0.2601 (r²=0.0677); agent age r=0.2585 (r²=0.0668)
- **Supporting analysis:** `reports/statistical_analysis_report.md` Tests 3-4; `output/figures/05_*.png`, `06_*.png`
- **Statistical evidence:** p ≈ 0.0 for all three (large n makes even weak correlations significant)
- **SQL validation reference:** `sql/analysis/Q04_agent_rating_vs_delivery_time.sql`, `Q10_distance_vs_delivery_time_correlation.sql`, `Q15_agent_age_vs_delivery_time_and_rating.sql` — all three r values match exactly
- **Limitation:** Weak correlations at this n are easy to over-read; reverse causality and confounding (e.g., experienced agents assigned easier routes) are plausible alternative explanations this data cannot rule out. Agent findings are attribute-level only — no true `Agent_ID` exists.
- **Confidence level:** **Low-to-Medium** for operational relevance (statistically real, but individually weak); **High** for reproducibility (exact SQL/Python match).

### Candidate 7 — No meaningful weekend/weekday difference exists

- **Observation:** Weekend and weekday delivery times are statistically indistinguishable.
- **Metric:** Weekday 124.90 min vs. Weekend 124.96 min; Mann-Whitney p=0.9658; Cohen's d=-0.0013 (negligible)
- **Supporting analysis:** `reports/statistical_analysis_report.md` Test 5
- **Statistical evidence:** Failed to reject H0 — the one non-significant result in this phase's test suite
- **SQL validation reference:** `sql/analysis/Q07_weekend_vs_weekday_delivery_time.sql` — group counts and means match exactly
- **Limitation:** A true negative result, not an absence of testing; still bounded by the single ~8-week observation window.
- **Confidence level:** **High** — this is the most confidently-supported finding in the set precisely because it is a clean null result with a negligible effect size, not a borderline one.

---

## Explicitly excluded from this candidate list

- Any claim that an individual delivery agent is under- or over-performing (no true `Agent_ID` exists).
- Any claim that `bicycle` delivery performance differs from other vehicles (0 rows exist for that vehicle post-cleaning).
- Any financial, cost, or "estimated savings" figure (no cost field exists in the source data, per `ASSUMPTIONS.md` A8; `sql/analysis/Q22`'s illustrative figure is not repeated here as a "finding").
- Any causal statement ("X causes delay") anywhere above.
