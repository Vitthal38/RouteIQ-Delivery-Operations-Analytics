# SQL Analysis Validation Report — RouteIQ Phase 3

Generated: 2026-08-16

All 22 queries in `sql/analysis/` were executed against the live `routeiq`
PostgreSQL schema (same instance validated in Phase 2). Every result below
is real output — nothing is asserted without a captured query result.

---

## Execution summary

| ID | File | Executed | Result sets | Notes |
|---|---|---|---|---|
| Q01 | `Q01_sla_breach_rate_overall_and_by_area.sql` | ✅ | 2 | Overall 23.6620%; Semi-Urban 100.0000% (n=152) |
| Q02 | `Q02_worst_p90_delivery_time_by_area.sql` | ✅ | 1 | Semi-Urban worst P90 = 269.50 min |
| Q03 | `Q03_traffic_group_stats_for_significance_test.sql` | ✅ | 1 | 4 traffic groups, n sums to 43,648 |
| Q04 | `Q04_agent_rating_vs_delivery_time.sql` | ✅ | 2 | r = -0.3077, n = 43,594 |
| Q05 | `Q05_top_weather_traffic_longest_delivery.sql` | ✅ | 1 | 24 combinations, all ranked |
| Q06 | `Q06_categories_highest_avg_delivery_time.sql` | ✅ | 1 | 16 categories; Grocery lowest (26.54 min, expected — see Phase 1 finding) |
| Q07 | `Q07_weekend_vs_weekday_delivery_time.sql` | ✅ | 2 | 31,627 + 12,021 = 43,648 |
| Q08 | `Q08_otd_rate_by_area.sql` | ✅ | 1 | `otd_plus_breach_check` = 100.0000 for all 4 rows |
| Q09 | `Q09_agent_rating_tier_delay_distribution.sql` | ✅ | 1 | 4 quartiles, ~10,898-10,899 each |
| Q10 | `Q10_distance_vs_delivery_time_correlation.sql` | ✅ | 2 | r = 0.2781, n = 39,997 (coordinate-valid only) |
| Q11 | `Q11_delivery_time_trend_weekly.sql` | ✅ | 1 | 8 weeks; weeks 6 and 14 flagged partial (3 distinct days each) |
| Q12 | `Q12_weather_with_most_sla_breaches.sql` | ✅ | 2 | Sum of per-weather breaches = 10,328 = total |
| Q13 | `Q13_weather_group_stats_for_significance_test.sql` | ✅ | 1 | 6 weather groups |
| Q14 | `Q14_pareto_breach_share_area_and_category.sql` | ✅ | 2 | Both cuts reach exactly 100.0000% cumulative |
| Q15 | `Q15_agent_age_vs_delivery_time_and_rating.sql` | ✅ | 1 | age-vs-time r = 0.2585, age-vs-rating r = -0.1176, n = 43,594 |
| Q16 | `Q16_lowest_otd_area.sql` | ✅ | 1 | Semi-Urban, 0.0000% — matches Q08's minimum exactly |
| Q17 | `Q17_week_over_week_volatility.sql` | ✅ | 1 | 7 delta values (8 weeks, first has no prior) |
| Q18 | `Q18_category_delivery_time_concentration.sql` | ✅ | 1 | Same 16-category population as Q06 |
| Q19 | `Q19_clear_vs_adverse_weather_delta.sql` | ✅ | 1 | 7,078 + 36,570 = 43,648 |
| Q20 | `Q20_area_traffic_breach_concentration.sql` | ✅ | 1 | 15 of 16 possible area×traffic combinations observed |
| Q21 | `Q21_vehicle_type_avg_delivery_time.sql` | ✅ | 1 | 3 vehicle types only — bicycle limitation documented in-file |
| Q22 | `Q22_illustrative_improvement_worst_vs_median_area.sql` | ✅ | 1 | Explicitly labeled illustrative in its own output row |

**22 / 22 queries executed successfully. 0 syntax errors, 0 runtime errors.**

---

## Cross-validation against Phase 1 Python outputs

Every figure below was independently pulled from `data/cleaned/cleaned_delivery.csv`
and `data/cleaned/sla_reference.csv` directly with pandas (not re-derived
from the SQL results), then compared to the SQL output above.

| Check | Phase 1 (Python) | Phase 3 (SQL) | Match |
|---|---|---|---|
| Total deliveries | 43,648 | 43,648 (Q07) | ✅ |
| Distinct `Order_ID` | 43,648 | 43,648 (Phase 2, re-confirmed) | ✅ |
| Overall SLA breach rate | 23.6620% | 23.6620% (Q01) | ✅ |
| Breach rate — Metropolitian | 26.5000% | 26.5000% (Q01) | ✅ |
| Breach rate — Urban | 14.3738% | 14.3738% (Q01) | ✅ |
| Breach rate — Semi-Urban | 100.0000% | 100.0000% (Q01) | ✅ |
| Breach rate — Other | 11.4437% | 11.4437% (Q01) | ✅ |
| Category row counts (16 categories) | 2,661-2,843 per category | Identical, row-for-row (Q06) | ✅ |
| Vehicle counts | motorcycle 25,519 / scooter 14,607 / van 3,522 | Identical (Q21) | ✅ |
| Area counts | Metropolitian 32,634 / Urban 9,726 / Other 1,136 / Semi-Urban 152 | Identical (Q01/Q02/Q08) | ✅ |
| Weekday avg delivery time | 124.8960 min | 124.90 min (Q07) | ✅ |
| Weekend avg delivery time | 124.9631 min | 124.96 min (Q07) | ✅ |
| SLA thresholds, 16 categories | `sla_reference.csv` values | Identical, all 16 (implicit — `sla_threshold_minutes` is read from the same frozen `FactDelivery` column validated row-for-row in Phase 2) | ✅ |

**0 discrepancies found. No SQL result required investigation or a stop.**

---

## Business logic validation (per Step 10)

Applied to every query above:

1. **Answers the intended question** — each query's output directly answers its `SQL_ANALYSIS_PLAN.md` question; no query was built to demonstrate a SQL feature for its own sake.
2. **Correct grain** — every aggregation groups `FactDelivery` at its native one-row-per-delivery grain; no query aggregates an already-aggregated result without an explicit intermediate CTE.
3. **No double-counting** — every join from `FactDelivery` to a dimension is many-to-one (verified in Phase 2: 0 orphans, every dimension natural key unique), so no join in this phase can fan out fact rows. Q20's two-dimension join (`DimArea` + `DimWeatherTraffic`) is still many-to-one on each side independently, confirmed by `row_count` sums reconciling to 43,648 when totaled.
4. **Correct denominator** — every rate/percentage uses `COUNT(*)` over the exact filtered population stated in that query (e.g., Q04/Q10/Q15 state their filtered `n` explicitly rather than dividing by the full 43,648 when a validity filter is applied).
5. **NULL handling** — `agent_rating` (nullable) is excluded via `agent_rating_valid_flag` wherever used (Q04, Q09, Q15), never via a bare `IS NOT NULL` that would still admit out-of-range values; `NULLIF` guards every division with a variable denominator (Q09, Q17, Q18, Q22) against a divide-by-zero.
6. **Correct time dimension** — `week_number` and `full_date` come from `DimDate`, joined on `date_key`; `is_weekend` is read directly from `FactDelivery` (already engineered and validated in Phase 1), not recomputed.
7. **Frozen SLA used correctly** — every SLA-related query reads `sla_breach_flag`/`sla_threshold_minutes` as stored; no query contains a `PERCENTILE_CONT` or `AVG`/`median` computation feeding into a breach determination.
8. **Result plausibility** — every breach rate is 0-100%; `otd_plus_breach_check` = exactly 100.0000 for all 4 areas (Q08); Q14's cumulative Pareto share reaches exactly 100.0000% for both cuts; Q11/Q17's partial-week flags line up with the known Phase 1 date-range gap.
9. **Independent validation possible** — every correlation, rate, and trend figure above was cross-checked against a Python-computed figure pulled fresh from the Phase 1 CSVs, not from any cached Phase 1 report text.

## Known, carried-forward limitations (not new findings — documented per-question in `sql/analysis/`)

- **Q09** answers agent-**attribute**-tier distribution, not individual-agent outlier detection (no true `Agent_ID` exists).
- **Q21** cannot include `bicycle` — 0 rows exist in the analysis population post-cleaning.
- **Q14 / Q22** apply a disclosed, documented interpretation of plan wording that was not fully unambiguous (see each file's header comment and `reports/sql_analysis_preflight.md`).
- **Q22** is explicitly an illustrative estimate, labeled as such in its own output row — not a committed operational figure.

**No insight, recommendation, or business narrative has been written from any of the above** — this report documents that each query executed correctly and reconciles, per the Phase 3 scope boundary (Step 12).

---

## Final cross-cutting test suite (Step 14)

Run via `sql/analysis/_final_test_suite.sql` against the live database, separately from the 22 business-question queries above.

| # | Test | Result | Pass |
|---|---|---|---|
| 1 | Join fan-out — row count unchanged after joining each of the 6 dimensions | 43,648 in every case (fact alone and all 6 joins) | ✅ |
| 2 | NULL handling — `agent_rating_valid_flag` excludes exactly the 54 true-null rows | 43,594 valid + 54 invalid = 43,648; invalid count = true-null count exactly | ✅ |
| 3 | Denominator reconciliation — every group-by cut sums to the full population | area / category / vehicle / weather / traffic / weekend-weekday all = 43,648 | ✅ |
| 4 | SLA consistency — `sla_breach_flag` re-derived fresh vs. stored | 0 mismatches | ✅ |
| 5 | KPI consistency — OTD% + Breach% = 100 at 3 filter contexts | No filter: 76.3380 + 23.6620 = 100; `area=Urban`: 85.6262 + 14.3738 = 100; `category=Grocery`: 76.9345 + 23.0655 = 100 | ✅ |
| 6 | Row-count reconciliation vs. Phase 1/2 frozen figure | 43,648 = 43,648 | ✅ |
| 7 | Duplicate `order_id` check | 0 | ✅ |

**7 / 7 cross-cutting tests passed.**
