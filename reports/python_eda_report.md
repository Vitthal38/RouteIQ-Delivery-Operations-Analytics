# Python EDA Report — RouteIQ Phase 4

Generated: 2026-08-16

Source: `data/cleaned/cleaned_delivery.csv` (43,648 rows, approved Phase 1
artifact, read-only). Full machine-readable results:
`output/eda_summary.json`. Figures: `output/figures/`.

This report describes what the data shows. It does not attribute cause,
and it does not convert any observation into a recommendation — that is
explicitly out of scope for this phase.

---

## 1. Dataset Overview

43,648 deliveries, 2022-02-11 to 2022-04-06 (44 distinct dates observed,
with a genuine gap 2022-02-19–2022-02-28 — no orders recorded in that
window). 16 product categories, 4 area types (one, `Other`, undefined and
excluded from tier comparisons), 6 weather conditions, 4 traffic levels,
3 vehicle types (`bicycle` has 0 rows post-cleaning — see §9).

## 2. Delivery Time Distribution

| Statistic | Value |
|---|---|
| Min | 10 min |
| Max | 270 min |
| Mean | 124.91 min |
| Median | 125.0 min |
| Std. dev. | 51.93 min |
| Skewness | 0.1884 (mild right skew) |
| P50 | 125.0 min |
| P75 | 160.0 min |
| P90 | 195.0 min |
| P95 | 215.0 min |

See `output/figures/01_delivery_time_distribution.png`. The distribution
is bimodal-looking rather than a single smooth peak — a low cluster
(~10-55 min, this is where `Grocery`'s much shorter delivery-time scale
sits, already identified in Phase 1) and a broader main cluster (~75-270
min covering the other 15 categories). Mean and median are close (124.91
vs. 125.0), consistent with the mild skew.

## 3. SLA Breach Behavior

Overall breach rate: **23.6620%** (10,328 of 43,648) — reads the frozen
`sla_breach_flag`, unchanged from Phase 1/2/3.

By `delivery_bucket` (the illustrative fixed-width bins from
`FEATURE_ENGINEERING.md` #4):

| Bucket | n | Breach rate |
|---|---|---|
| 0-60 minutes | 4,720 | 13.14% |
| 61-120 minutes | 16,582 | 0.00% |
| 121-180 minutes | 15,945 | 20.74% |
| 181+ minutes | 6,401 | 100.00% |

This pattern is mechanical, not a new finding: most category thresholds
sit at 160 or 165 minutes (P75 of a ~125-min median distribution), so
almost nothing in the 61-120 bucket can exceed its threshold, and almost
everything at 181+ minutes necessarily does. It illustrates how the
bucket boundaries relate to the frozen thresholds — it is not a separate
breach rule.

## 4. Segment Comparisons

**By Area** (`output/figures/02_breach_rate_by_area.png`): Semi-Urban has
the highest average delivery time (238.55 min, n=152 — a small sample)
and the highest breach rate (100%, already established in Phase 3).
Metropolitian (n=32,634, the bulk of the dataset) averages 129.71 min.
Urban and `Other` are both faster and lower-breach.

**By Weather:** Cloudy (138.29 min) and Fog (136.57 min) average the
longest; Sunny is fastest (103.66 min). This ordering matches Test 2's
significant-but-small Kruskal-Wallis result (`reports/statistical_analysis_report.md`).

**By Category** (`output/figures/03_delivery_time_by_category.png`):
Grocery is the outlier category by design (26.54 min average — a
genuinely different, faster-fulfillment product type, not a data error,
per Phase 1's SLA-threshold review). The other 15 categories cluster
tightly around 129-133 min average.

**By Vehicle:** motorcycle (131.03 min) averages the slowest of the 3
present vehicle types; scooter (116.35 min) and van (116.17 min) are
close to each other and faster. `bicycle` cannot be compared — 0 rows
exist post-cleaning (§9).

**Weekend vs. weekday:** 124.90 min vs. 124.96 min — essentially
identical, and Test 5 confirms no statistically significant difference.

## 5. Relationships (Correlation)

| Relationship | r | r² | Strength | n |
|---|---|---|---|---|
| Distance vs. delivery time | 0.2781 | 0.0774 | weak | 39,997 |
| Agent rating vs. delivery time | -0.2601 (Spearman, primary) | 0.0677 | weak | 43,594 |
| Agent age vs. delivery time | 0.2585 | 0.0668 | weak | 43,594 |
| Agent age vs. agent rating | -0.1176 | 0.0138 | negligible-to-weak | 43,594 |

All four relationships are directionally sensible (further = slower,
higher-rated agents somewhat faster, older agent age somewhat slower) but
weak in magnitude — none explains more than about 8% of delivery-time
variance individually. See `reports/statistical_analysis_report.md` for
the formal test results and `output/figures/05_*.png` / `06_*.png` for
the underlying scatter/band plots. **These are observed associations,
not causal claims** — see that report's limitations for each.

## 6. Outlier Findings (Step 4 — descriptive only, no rows modified)

Using a per-category Tukey 1.5×IQR rule (global IQR would be misleading
given Grocery's different scale):

- **143 statistical outliers** (0.328% of the dataset)
- **12** co-occur with an already-known Phase 1 data-quality flag (invalid
  coordinates, out-of-range/null rating, or implausible age)
- **131** carry no such flag — these are treated as **valid extreme
  deliveries**, not errors, consistent with `DATA_PROFILING_PLAN.md`'s
  Outlier Strategy (genuinely long deliveries are retained because the
  tail is exactly what P90 tracking is for)

No row was removed or altered — the approved cleaned dataset is
unmodified; this section only characterizes what is already in it.

## 7. Temporal Patterns

8 distinct ISO weeks observed (6, 7, 9-14 — week 8 has no data at all,
the known gap). Weeks 6 and 14 are partial (3 distinct calendar days
each); weeks 9 and 12 are also short (6 days). See
`output/figures/04_weekly_trend.png` (partial weeks shaded). Average
delivery time ranges 121.54-129.12 min across weeks — a roughly 6%
swing, without a clear directional trend across the 8 weeks. Given the
short window and two fully-partial weeks, this does not support a strong
trend claim in either direction, consistent with `DATASET_OVERVIEW.md`'s
stated limitation.

## 8. Distance Findings

Restricted to `coordinates_valid_flag = true` (39,997 of 43,648 rows,
91.6%). Distance ranges are naturally compressed for `High`/`Low` traffic
conditions relative to `Jam`/`Medium` in the underlying data (see
`output/figures/05_distance_vs_delivery_time_scatter.png`), and distance's
correlation with delivery time (r=0.2781) is weaker than traffic's
observed effect size in `reports/statistical_analysis_report.md` — the
comparison itself, not either figure alone, is Business Question #10's
answer: delivery time in this dataset looks more condition-driven than
distance-driven, in relative terms.

## 9. Known Limitations (restated for this report)

- **Agent analysis is attribute-level only.** No true `Agent_ID` exists;
  every agent finding above describes a rating/age attribute, never an
  identifiable individual agent's performance.
- **`bicycle` is absent, not low-confidence.** All 15 raw bicycle rows
  fell inside the Cleaning Step 3 exclusion cluster — 0 rows exist in
  this dataset for that vehicle type.
- **8-week window, with a real 10-day data gap.** Limits the strength of
  any trend or seasonality claim.
- **SLA methodology is frozen and unchanged** — every SLA figure in this
  report reads the stored `sla_breach_flag`/`sla_threshold_minutes`; none
  is recalculated.
- **`Semi-Urban`'s 100% breach rate is based on only 152 rows** — a real
  figure, but a small sample; its Area-tier comparison exposure is stated
  in every SQL/Python output that touches it.

No recommendation is derived from any finding in this report.
