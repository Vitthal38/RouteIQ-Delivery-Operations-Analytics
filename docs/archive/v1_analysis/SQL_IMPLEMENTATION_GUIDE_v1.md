# SQL Implementation Guide — RouteIQ Phase 3

Generated: 2026-08-16

Documents how each of the 22 business questions in `SQL_ANALYSIS_PLAN.md`
is implemented in `sql/analysis/`. This guide records *how* each query
works and *how it was validated* — it does not draw business conclusions
from the results (see `reports/sql_analysis_validation.md` for captured
outputs, and the Phase 3 scope boundary: insights and recommendations are
explicitly deferred to a later phase).

---

### Q01 — % of deliveries breaching SLA overall and by area
- **File:** `Q01_sla_breach_rate_overall_and_by_area.sql`
- **Tables:** `FactDelivery`, `DimArea`
- **Concepts:** `GROUP BY`, `FILTER` (boolean aggregation)
- **KPI(s):** SLA Breach Rate (`KPI_DEFINITIONS.md` #2)
- **Validation:** Result must be 0-100%; cross-checked against the Phase 1 Python breach rate (23.6620% overall) — exact match, see `reports/sql_analysis_validation.md`
- **Limitations:** None

### Q02 — Worst P90 delivery time by area
- **File:** `Q02_worst_p90_delivery_time_by_area.sql`
- **Tables:** `FactDelivery`, `DimArea`
- **Concepts:** `PERCENTILE_CONT(0.9) WITHIN GROUP`
- **KPI(s):** P90 Delivery Time (`KPI_DEFINITIONS.md` #4)
- **Validation:** Interpolation method (`PERCENTILE_CONT`, continuous) matches the method documented in `KPI_DEFINITIONS.md` #4 and `DAX_MEASURE_PLAN.md`'s cross-validation requirement
- **Limitations:** None

### Q03 — Does traffic significantly affect delivery time? (group-stats prep)
- **File:** `Q03_traffic_group_stats_for_significance_test.sql`
- **Tables:** `FactDelivery`, `DimWeatherTraffic`
- **Concepts:** `GROUP BY`, `AVG`, `STDDEV`, `PERCENTILE_CONT(0.5)`
- **KPI(s):** Feeds `STATISTICAL_ANALYSIS.md` Test 1 input; not itself a headline KPI
- **Validation:** Group `n` values will be matched against Python's ANOVA input row counts in a future phase
- **Limitations:** No p-value/test statistic computed — statistical testing is explicitly out of scope for Phase 3

### Q04 — Relationship between agent rating and delivery time
- **File:** `Q04_agent_rating_vs_delivery_time.sql`
- **Tables:** `FactDelivery`, `DimAgent`
- **Concepts:** `CORR()`, `GROUP BY` (rating band via `FLOOR`)
- **KPI(s):** Agent Rating-Delivery Time Relationship (`KPI_DEFINITIONS.md` #6)
- **Validation:** r = -0.3077, n = 43,594 (filtered to `agent_rating_valid_flag = true`) — row count will be cross-checked against Python's Test 3 input in a future phase
- **Limitations:** Correlation only; no causal claim. `DimAgent` is attribute-derived (see Step 6 note) — this measures the rating attribute, not individual-agent performance over time

### Q05 — Top weather/traffic condition for longest delivery times
- **File:** `Q05_top_weather_traffic_longest_delivery.sql`
- **Tables:** `FactDelivery`, `DimWeatherTraffic`
- **Concepts:** `GROUP BY`, `RANK()`
- **KPI(s):** Delivery Time by Weather/Traffic Condition (`KPI_DEFINITIONS.md` #5)
- **Validation:** 24 combinations returned, matching the 24 rows in `DimWeatherTraffic`
- **Limitations:** None

### Q06 — Categories with highest average delivery time
- **File:** `Q06_categories_highest_avg_delivery_time.sql`
- **Tables:** `FactDelivery`, `DimCategory`
- **Concepts:** `GROUP BY`, `ORDER BY`
- **KPI(s):** Average Delivery Time (`KPI_DEFINITIONS.md` #3), by Category
- **Validation:** 16 categories returned, row counts (2,661-2,843) match `DATA_PROFILING_PLAN.md`'s documented range and Phase 1's category counts exactly
- **Limitations:** Grocery's much lower average (26.54 min) is expected — already established as a genuine category-scale difference during Phase 1 SLA-threshold review, not a data error

### Q07 — Weekend vs. weekday delivery time
- **File:** `Q07_weekend_vs_weekday_delivery_time.sql`
- **Tables:** `FactDelivery`
- **Concepts:** `CASE WHEN`, `GROUP BY`
- **KPI(s):** Feeds `STATISTICAL_ANALYSIS.md` Test 5 input
- **Validation:** 31,627 (weekday) + 12,021 (weekend) = 43,648 total, checked explicitly in-file
- **Limitations:** No t-test performed — Phase 2/Python scope

### Q08 — OTD% by area
- **File:** `Q08_otd_rate_by_area.sql`
- **Tables:** `FactDelivery`, `DimArea`
- **Concepts:** `FILTER`, `GROUP BY`
- **KPI(s):** On-Time Delivery Rate % (`KPI_DEFINITIONS.md` #1), by area
- **Validation:** `otd_plus_breach_check` = exactly 100.0000 for all 4 areas, computed in-query
- **Limitations:** None

### Q09 — Are specific agents outlier-prone, or is delay evenly distributed?
- **File:** `Q09_agent_rating_tier_delay_distribution.sql`
- **Tables:** `FactDelivery`, `DimAgent`
- **Concepts:** `NTILE()`, `STDDEV`
- **KPI(s):** Not a headline KPI; supports Business Question #9
- **Validation:** 4 roughly-equal quartiles (~10,898-10,899 rows each), confirming `NTILE` split correctly
- **Limitations:** **Cannot identify individual outlier-prone agents — no true `Agent_ID` exists in the source data (`STAR_SCHEMA.md` DimAgent design decision).** Reframed as agent-rating-quartile delay distribution; must never be narrated as individual-agent tracking

### Q10 — Does distance correlate with delivery time, or is it condition-driven?
- **File:** `Q10_distance_vs_delivery_time_correlation.sql`
- **Tables:** `FactDelivery`, `DimWeatherTraffic`
- **Concepts:** `CORR()`, `GROUP BY`
- **KPI(s):** Feeds `STATISTICAL_ANALYSIS.md` Test 4 input
- **Validation:** n = 39,997, restricted to `coordinates_valid_flag = true`, stated explicitly per the plan's requirement
- **Limitations:** Correlation only; comparison to condition group means is descriptive, not a formal test of "which explains more"

### Q11 — Trend in delivery time over the observed period
- **File:** `Q11_delivery_time_trend_weekly.sql`
- **Tables:** `FactDelivery`, `DimDate`
- **Concepts:** `GROUP BY week_number`, `LAG()`
- **KPI(s):** Delivery Time Trend (Weekly) (`KPI_DEFINITIONS.md` #3/#4 trend view)
- **Validation:** `distinct_days_observed` computed from `DimDate`, not assumed; weeks 6 and 14 correctly flagged partial (3 distinct days each)
- **Limitations:** Only 8 distinct weeks observed, with a genuine data gap (no orders 2022-02-19 to 2022-02-28) — limits trend-strength claims, per `DATASET_OVERVIEW.md`'s stated limitation

### Q12 — Weather condition with most SLA breaches
- **File:** `Q12_weather_with_most_sla_breaches.sql`
- **Tables:** `FactDelivery`, `DimWeatherTraffic`
- **Concepts:** `GROUP BY`, `FILTER`
- **KPI(s):** SLA Breach Rate (`KPI_DEFINITIONS.md` #2), by weather
- **Validation:** Sum of per-weather breach counts (10,328) = total breach count, checked explicitly in-file
- **Limitations:** None

### Q13 — Is weather statistically significant for delivery time? (group-stats prep)
- **File:** `Q13_weather_group_stats_for_significance_test.sql`
- **Tables:** `FactDelivery`, `DimWeatherTraffic`
- **Concepts:** `GROUP BY`, aggregate stats
- **KPI(s):** Feeds `STATISTICAL_ANALYSIS.md` Test 2 input
- **Validation:** 6 weather groups, row counts to be matched against Python's test input in a future phase
- **Limitations:** No p-value/test statistic computed here

### Q14 — % of deliveries from top 20% highest-delay areas/categories (Pareto)
- **File:** `Q14_pareto_breach_share_area_and_category.sql`
- **Tables:** `FactDelivery`, `DimArea`, `DimCategory`
- **Concepts:** `RANK()`, `SUM() OVER` (running total window)
- **KPI(s):** Delay Root-Cause Share / Pareto Concentration (`KPI_DEFINITIONS.md` #7)
- **Validation:** Both cuts' cumulative share reach exactly 100.0000%; `top_20_pct_segment_cutoff` computed via `CEIL()`, not eyeballed
- **Limitations:** Implemented as two separate single-dimension cuts (area, category) rather than one pooled ranking — plan wording did not specify which, disclosed in-file and in `reports/sql_analysis_preflight.md`

### Q15 — Agent age vs. delivery time or rating
- **File:** `Q15_agent_age_vs_delivery_time_and_rating.sql`
- **Tables:** `FactDelivery`, `DimAgent`
- **Concepts:** `CORR()`
- **KPI(s):** Feeds Business Question #15; not a headline KPI
- **Validation:** n = 43,594, filtered to both `agent_age_valid_flag` and `agent_rating_valid_flag`, per the plan's explicit requirement
- **Limitations:** Attribute-based only, same `DimAgent` caveat as Q09

### Q16 — Which area underperforms most on OTD%?
- **File:** `Q16_lowest_otd_area.sql`
- **Tables:** `FactDelivery`, `DimArea`
- **Concepts:** `ORDER BY ... LIMIT 1`, reusing Q08's exact computation
- **KPI(s):** On-Time Delivery Rate % (`KPI_DEFINITIONS.md` #1), single minimum
- **Validation:** Result (Semi-Urban, 0.0000%) matches Q08's minimum row exactly — no independent recalculation
- **Limitations:** Restricted to `area_tier_valid_flag = true` (excludes `Other`), consistent with every other area-tier ranking in this project

### Q17 — Week-over-week volatility in delivery time
- **File:** `Q17_week_over_week_volatility.sql`
- **Tables:** `FactDelivery`, `DimDate`
- **Concepts:** `LAG()`
- **KPI(s):** Week-over-Week Delivery Time Volatility (`KPI_DEFINITIONS.md` #8)
- **Validation:** `LAG()` output re-derivable by manual subtraction of two adjacent weekly values (spot-checked in `reports/sql_analysis_validation.md`)
- **Limitations:** Same short-window caveat as Q11

### Q18 — Are longer delivery times concentrated in specific categories?
- **File:** `Q18_category_delivery_time_concentration.sql`
- **Tables:** `FactDelivery`, `DimCategory`
- **Concepts:** `GROUP BY`, `STDDEV`
- **KPI(s):** Same as Q06, variance-framed
- **Validation:** Same population as Q06 (same 16 categories, same row counts)
- **Limitations:** None beyond Q06's

### Q19 — Delivery-time delta: clear vs. adverse weather
- **File:** `Q19_clear_vs_adverse_weather_delta.sql`
- **Tables:** `FactDelivery`, `DimWeatherTraffic`
- **Concepts:** `CASE WHEN`, `GROUP BY`
- **KPI(s):** Delivery Time by Weather/Traffic Condition (`KPI_DEFINITIONS.md` #5); feeds `STATISTICAL_ANALYSIS.md` Test 2's secondary comparison
- **Validation:** 7,078 + 36,570 = 43,648, checked implicitly against Q13's Sunny row count
- **Limitations:** "Adverse" defined as all non-Sunny weather values, stated explicitly in-file per the plan's own example

### Q20 — Area + traffic combination with highest breach concentration
- **File:** `Q20_area_traffic_breach_concentration.sql`
- **Tables:** `FactDelivery`, `DimArea`, `DimWeatherTraffic`
- **Concepts:** `GROUP BY area, traffic`
- **KPI(s):** Delay Root-Cause Share / Pareto Concentration (`KPI_DEFINITIONS.md` #7), 2-D cut
- **Validation:** 15 of 16 possible area×traffic combinations observed (Semi-Urban×Low does not occur in the data); `row_count` exposed per combination
- **Limitations:** No numeric minimum-sample-size threshold is imposed (none is frozen in the documentation) — `row_count` is shown instead, per the disclosed policy in `reports/sql_analysis_preflight.md`

### Q21 — Does vehicle type affect average delivery time?
- **File:** `Q21_vehicle_type_avg_delivery_time.sql`
- **Tables:** `FactDelivery`, `DimVehicle`
- **Concepts:** `GROUP BY`
- **KPI(s):** Average Delivery Time (`KPI_DEFINITIONS.md` #3), by vehicle
- **Validation:** 3 vehicle types, matching `DimVehicle`'s 3 rows exactly (Phase 2)
- **Limitations:** **`bicycle` cannot be included at all — 0 rows exist in the cleaned/loaded dataset** (all 15 raw rows fell inside the Cleaning Step 3 exclusion cluster). This is stronger than the plan's original "low-confidence" framing; documented, not fabricated

### Q22 — Estimated improvement if worst area matched median area's delivery time
- **File:** `Q22_illustrative_improvement_worst_vs_median_area.sql`
- **Tables:** `FactDelivery`, `DimArea`
- **Concepts:** Arithmetic derived from Q08/Q16's own ranking
- **KPI(s):** Illustrative only — ties to KPI #1 and #7 concepts, per `ASSUMPTIONS.md` A8
- **Validation:** `worst_area` matches Q16's result (Semi-Urban) exactly
- **Limitations:** **Explicitly illustrative, not a measured or guaranteed savings figure** — no cost/financial field exists in the source data (`ASSUMPTIONS.md` A8). "Worst"/"median" area defined by the Q08/Q16 OTD% ranking, disclosed in-file since the plan does not fully specify the ranking criterion

---

## Cross-cutting notes

- **SLA logic:** every question touching breach/on-time status reads
  `FactDelivery.sla_breach_flag` / `sla_threshold_minutes` as stored —
  no query in this phase recalculates a percentile, median, or buffer.
- **DimAgent:** Q04, Q09, Q15 are attribute-based analyses of age/rating,
  never individual-agent tracking — no `Agent_ID` exists in the source data.
- **DimVehicle:** Q21 reflects only the 3 vehicle types present in the
  approved cleaned dataset; `bicycle` is absent, not fabricated.
- **No insights or recommendations appear in this guide or in
  `reports/sql_analysis_validation.md`** — per the Phase 3 scope boundary,
  these are deferred to a later, separately-reviewed phase.
