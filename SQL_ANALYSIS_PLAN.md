# SQL Analysis Plan — RouteIQ

## Table of Contents
1. [Purpose](#purpose)
2. [Priority Definitions](#priority-definitions)
3. [Business Question Plan](#business-question-plan)
4. [Shared Validation Strategy](#shared-validation-strategy)

Related documents: `STAR_SCHEMA.md` (tables/keys referenced below), `KPI_DEFINITIONS.md`, `SLA_METHODOLOGY.md`, `BUSINESS_REQUIREMENTS.md` (source of the question list)

No SQL is written here — this document plans *what* each query must produce, *why*, and *how it will be checked*, so implementation has a fixed specification to follow.

---

## Purpose

Each of the brief's 22 business questions is broken down into an implementation-ready spec. This lets a future coding session write the query directly against `STAR_SCHEMA.md` without re-deriving business logic, and lets a reviewer check output plausibility without re-reading the whole brief.

## Priority Definitions

- **P0 — Core KPI:** feeds a headline Executive Summary metric; must be correct before anything else ships.
- **P1 — Root cause:** feeds the Delay Root Cause / Area & Category pages; core to the project's differentiation.
- **P2 — Supporting/exploratory:** useful depth, not load-bearing for the main narrative.

## Business Question Plan

| # | Business Question | Priority | Expected Output | SQL Concepts | Dependencies | Validation Method |
|---|---|---|---|---|---|---|
| 1 | % of deliveries breaching SLA overall and by area | P0 | Single overall % + `Area`-grouped % table | `GROUP BY`, `CASE`/boolean aggregation, `AVG(sla_breach_flag::int)` | Frozen `sla_threshold_minutes`, `DimArea` | Cross-check against Python breach-rate calc on same cleaned data; result between 0–100% |
| 2 | Worst P90 delivery time by area | P0/P1 | `Area`-ranked table by P90 | `PERCENTILE_CONT(0.9) WITHIN GROUP`, `GROUP BY` | `DimArea`, cleaned `delivery_time_minutes` | Spot-check P90 against a manual sort of a sample area's delivery times |
| 3 | Does traffic significantly affect delivery time? | P1 | Group means/medians by traffic (statistical test itself lives in Python, per `STATISTICAL_ANALYSIS.md`) | `GROUP BY`, `AVG`/`STDDEV` as ANOVA input prep | `DimWeatherTraffic` | Group stats match the Python ANOVA input exactly (row counts per group) |
| 4 | Relationship between agent rating and delivery time | P1 | Correlation prep table (rating bucket × avg delivery time) | `GROUP BY`, `CORR()` window/aggregate function | `agent_rating_valid_flag = true` filter | Match Python `CORR()`/Pearson r to 2 decimal places |
| 5 | Top weather/traffic condition for longest delivery times | P1 | Ranked table, weather×traffic combo by avg/P90 delivery time | `GROUP BY`, `RANK()` | `DimWeatherTraffic` | Top result sanity-checked against a manual filter+average |
| 6 | Categories with highest average delivery time | P2 | `Category`-ranked table by avg | `GROUP BY`, `ORDER BY` | `DimCategory` | Row count per category matches profiling (~2,650–2,850 each) |
| 7 | Weekend vs. weekday delivery time | P2 | Two-group comparison (avg, P90) | `CASE WHEN is_weekend`, `GROUP BY` | `is_weekend` flag | Sum of weekend + weekday row counts = total clean row count |
| 8 | OTD% by area | P0 | `Area`-grouped OTD% table | Same as Q1, inverse framing | Same as Q1 | Same as Q1; OTD% + breach% per area sums to 100% |
| 9 | Are specific agents outlier-prone, or is delay evenly distributed? | P2 | Distribution/variance summary by agent-attribute bucket | `STDDEV`, `NTILE()` for performance tiers | `DimAgent`, rating-valid rows only | Distribution shape cross-checked visually in Python EDA before concluding "yes/no" |
| 10 | Does distance correlate with delivery time, or is it condition-driven? | P1 | Correlation coefficient (distance vs. delivery time), separately vs. weather/traffic group means | `CORR()`, `GROUP BY` | `coordinates_valid_flag = true` filter (Cleaning Step 7) | Row count used = only coordinate-valid rows; explicitly stated in output, not silently mixed with excluded rows |
| 11 | Trend in delivery time over the observed period | P0 | Weekly avg/P90 time series | `GROUP BY week_number`, window function for week-over-week delta | `DimDate`, `week_number` | Partial first/last week flagged per `FEATURE_ENGINEERING.md` #7 edge case |
| 12 | Weather condition with most SLA breaches | P1 | `Weather`-grouped breach count/rate | `GROUP BY`, boolean aggregation | Frozen SLA flag, `DimWeatherTraffic` | Sum of per-weather breach counts = total breach count |
| 13 | Is weather statistically significant for delivery time? | P1 | Group stats feeding Python test (test result documented in `STATISTICAL_ANALYSIS.md`, not concluded in SQL) | `GROUP BY`, aggregate stats | `DimWeatherTraffic` | Group means/counts match Python input exactly |
| 14 | % of deliveries from top 20% highest-delay areas/categories (Pareto) | P1 | Cumulative % table, ranked descending by breach count | `RANK()`/`ROW_NUMBER()`, window `SUM() OVER` for running total | Frozen SLA flag | Cumulative % monotonically increases to 100%; top-20%-of-segments cutoff explicitly computed, not eyeballed |
| 15 | Agent age vs. delivery time or rating | P2 | Correlation table (age vs. time, age vs. rating) | `CORR()` | `agent_age_valid_flag = true`, `agent_rating_valid_flag = true` | Both correlations reported only on rows passing both validity flags |
| 16 | Which area underperforms most on OTD% | P0 | Single lowest-OTD% area, from Q1/Q8 output | `ORDER BY ... LIMIT 1` on Q8 result | Q1/Q8 | Must match the minimum value in the Q8 table exactly (no separate recalculation) |
| 17 | Week-over-week volatility in delivery time | P2 | Week-over-week % change series | `LAG()` window function | Q11 output | `LAG()` output re-derivable by manual subtraction of two adjacent weekly values |
| 18 | Are longer delivery times concentrated in specific categories? | P2 | Same as Q6, framed as concentration/variance | `GROUP BY`, `STDDEV` | `DimCategory` | Same as Q6 |
| 19 | Delivery-time delta: clear vs. adverse weather | P1 | Two-group comparison (e.g., Sunny vs. all non-Sunny) | `CASE WHEN`, `GROUP BY` | `DimWeatherTraffic`; "adverse" grouping must be explicitly defined (e.g., all non-Sunny categories) and documented in the query comment, not left ambiguous | Group definition matches what's stated in the dashboard/README |
| 20 | Area + traffic combination with highest breach concentration | P1 | 2-dimensional `GROUP BY` (area × traffic), breach rate | `GROUP BY area, traffic`, `HAVING` for minimum sample size | `DimArea`, `DimWeatherTraffic`, frozen SLA flag | Combinations with very low row counts flagged/excluded to avoid an unstable rate driving a headline claim |
| 21 | Does vehicle type affect average delivery time? | P2 | `Vehicle`-grouped avg/P90 | `GROUP BY` | `DimVehicle` | Note: `bicycle` has only 15 rows in profiling — flagged as low-confidence in output, not presented with equal weight to motorcycle/scooter |
| 22 | Estimated improvement if worst area matched median area's delivery time | P1 | Single illustrative delta figure (worst-area avg − median-area avg) × worst-area volume | Derived from Q2/Q8 outputs, simple arithmetic | Q2, Q8 | Explicitly labeled as an illustrative estimate, not a guaranteed savings figure (ties to `ASSUMPTIONS.md` A8 — no real cost field exists) |

## Shared Validation Strategy

- Every P0/P1 query's output is recalculated independently in Python on the same cleaned dataset and compared — any mismatch is a bug to fix before the number is used anywhere, per `KPI_DEFINITIONS.md` cross-validation requirement.
- Every query that filters on a validity flag (`coordinates_valid_flag`, `agent_rating_valid_flag`, `agent_age_valid_flag`) states the resulting row count explicitly in its output/comment, so a reader can tell whether a finding is based on the full dataset or a subset.
- Any query result that will support a specific number in `EXECUTIVE_RECOMMENDATIONS.md` is treated as P0 for validation rigor regardless of its priority tag above.
