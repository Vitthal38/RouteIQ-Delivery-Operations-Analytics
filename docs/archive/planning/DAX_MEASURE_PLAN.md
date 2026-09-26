# DAX Measure Plan — RouteIQ

## Table of Contents
1. [Purpose](#purpose)
2. [Measures — Executive Summary Page](#measures--executive-summary-page)
3. [Measures — Area & Category Performance Page](#measures--area--category-performance-page)
4. [Measures — Agent Performance Page](#measures--agent-performance-page)
5. [Measures — Delay Root Cause Page](#measures--delay-root-cause-page)
6. [Cross-Cutting Validation Requirement](#cross-cutting-validation-requirement)
7. [Known DAX Risk Areas](#known-dax-risk-areas)

Related documents: `STAR_SCHEMA.md`, `KPI_DEFINITIONS.md`, `DASHBOARD_PLANNING.md` (to be produced separately), `SLA_METHODOLOGY.md`

No DAX code is written here — this is the specification each measure's implementation must satisfy, including how it will be validated against SQL/Python, before any `.pbix` work begins.

**Prior-project context this plan is designed to prevent recurring:** the analyst's FoodPulse project had a documented DAX context-transition bug (`SnapshotDate` resolving per-customer instead of at the intended grain). Every measure below explicitly states its intended evaluation context/grain for that reason.

---

## Measures — Executive Summary Page

### `On-Time Delivery Rate %`
- **Purpose:** Headline KPI — matches `KPI_DEFINITIONS.md` #1.
- **Business Logic:** Share of deliveries in current filter context where `sla_breach_flag = false`.
- **Intended Grain/Context:** Evaluates over whatever filter context the visual/slicer applies (e.g., all deliveries, or filtered to one area) — must **not** silently resolve at a different grain (e.g., per-category) than the visual implies. This is the exact class of bug flagged in FoodPulse's `SnapshotDate` issue.
- **Dependencies:** `FactDelivery.sla_breach_flag`, which itself depends on the frozen `sla_threshold_minutes` reference table (`SLA_METHODOLOGY.md`) — this measure must never recompute a threshold inline; it only reads the pre-computed flag.
- **Validation:** Card-visual value at "no filter" context must equal the Python-computed overall OTD% from `PYTHON_ANALYSIS_PLAN.md` Phase 2, to the decimal place used in the dashboard.

### `SLA Breach Rate %`
- **Purpose:** Matches `KPI_DEFINITIONS.md` #2; inverse framing of the measure above, shown separately since it drives the root-cause pages.
- **Business Logic:** `100 - [On-Time Delivery Rate %]`, or independently calculated as share where `sla_breach_flag = true` — both must agree exactly.
- **Dependencies:** Same as above.
- **Validation:** `[On-Time Delivery Rate %] + [SLA Breach Rate %] = 100` at every filter context, tested across at least 3 different slicer states (overall, one area, one category) before publishing.

### `Average Delivery Time (mins)`
- **Purpose:** Matches `KPI_DEFINITIONS.md` #3.
- **Business Logic:** Simple average of `delivery_time_minutes` in context.
- **Dependencies:** `FactDelivery.delivery_time_minutes`.
- **Validation:** Matches SQL `AVG()` output (`SQL_ANALYSIS_PLAN.md`) at the same filter context.

### `P90 Delivery Time (mins)`
- **Purpose:** Matches `KPI_DEFINITIONS.md` #4 — the tail-latency metric prioritized over the average for customer-experience framing.
- **Business Logic:** 90th percentile of `delivery_time_minutes` in context, using Power BI's `PERCENTILEX.INC` (or equivalent) with an explicitly stated interpolation method.
- **Dependencies:** `FactDelivery.delivery_time_minutes`.
- **Validation:** Interpolation method matched explicitly against the SQL `PERCENTILE_CONT` and Python `numpy.percentile` methods used elsewhere — percentile calculations are the single most likely source of a silent 3-way (SQL/Python/DAX) mismatch if this isn't checked deliberately, so it is called out here rather than assumed.

### `Delivery Time Trend (Weekly)`
- **Purpose:** Matches `KPI_DEFINITIONS.md` #3/#4 trend view, feeds Business Question #11.
- **Business Logic:** Average or P90 delivery time by `DimDate.week_number`, plotted as a line.
- **Intended Grain:** Explicitly grouped by week, not silently re-aggregated to month or day by a visual-level default — set explicitly in the visual's axis binding.
- **Dependencies:** `DimDate`, same underlying measure as above.
- **Validation:** First/last (partial) week flagged per `FEATURE_ENGINEERING.md` #7 — either excluded from the trend line or visually annotated, decision made explicit in `DASHBOARD_PLANNING.md`.

## Measures — Area & Category Performance Page

### `Breach Rate by Area`
- **Purpose:** Matches Business Questions #1, #8, #16.
- **Business Logic:** `[SLA Breach Rate %]` evaluated in `Area` filter/row context (e.g., in a matrix or bar chart by `DimArea.area_name`).
- **Dependencies:** `DimArea.area_tier_valid_flag` — `Other` area rows must be excluded from area-tier comparisons per `DATA_CLEANING_PLAN.md` Step 8; this exclusion must be applied via the flag, not by hardcoding an area-name filter that would silently break if a new area value is ever added.
- **Validation:** Matches `SQL_ANALYSIS_PLAN.md` Q1/Q8 output row-for-row per area.

### `P90 Delivery Time by Area`
- **Purpose:** Matches Business Question #2.
- **Business Logic:** `[P90 Delivery Time (mins)]` in `Area` row context.
- **Dependencies:** Same as above.
- **Validation:** Same percentile-method consistency requirement as the Executive Summary P90 measure.

### `Average Delivery Time by Category`
- **Purpose:** Matches Business Questions #6, #18.
- **Business Logic:** `[Average Delivery Time (mins)]` in `Category` row context.
- **Dependencies:** `DimCategory`.
- **Validation:** Matches `SQL_ANALYSIS_PLAN.md` Q6.

## Measures — Agent Performance Page

### `Delivery Time by Agent Rating Band`
- **Purpose:** Matches Business Question #4/#9.
- **Business Logic:** `[Average Delivery Time (mins)]` grouped by a rating band (e.g., banded `agent_rating` in 0.5-point increments), filtered to `agent_rating_valid_flag = true` only.
- **Dependencies:** `DimAgent.agent_rating_valid_flag` — the 53 out-of-range (6.0) and 54 null rows must be excluded here specifically, not just filtered loosely by `agent_rating IS NOT NULL` (which would still include the 6.0 rows).
- **Validation:** Row count used in this visual matches the row count the Python correlation test (Test 3, `STATISTICAL_ANALYSIS.md`) used — stated as a footnote/tooltip on the visual.

### `Agent Age vs. Delivery Time`
- **Purpose:** Matches Business Question #15.
- **Business Logic:** Scatter or binned comparison, filtered to `agent_age_valid_flag = true`.
- **Dependencies:** `DimAgent.agent_age_valid_flag`.
- **Validation:** Same cross-check standard as above.

### `Workload Distribution`
- **Purpose:** Supports Business Question #9 (are specific agents outlier-prone, or evenly distributed).
- **Business Logic:** Row count / variance of delivery time by agent-attribute bucket.
- **Dependencies:** `DimAgent`.
- **Validation:** Distribution shape matches the Python EDA histogram (`PYTHON_ANALYSIS_PLAN.md` Phase 2) visually and in summary statistics (mean, std).

## Measures — Delay Root Cause Page

### `Breach Rate by Weather`
- **Purpose:** Matches Business Questions #5, #12.
- **Business Logic:** `[SLA Breach Rate %]` in `DimWeatherTraffic.weather` row context.
- **Dependencies:** `DimWeatherTraffic`.
- **Validation:** Matches `SQL_ANALYSIS_PLAN.md` Q12.

### `Breach Rate by Traffic`
- **Purpose:** Matches Business Question #3.
- **Business Logic:** `[SLA Breach Rate %]` in `DimWeatherTraffic.traffic` row context.
- **Dependencies:** `DimWeatherTraffic`.
- **Validation:** Matches `SQL_ANALYSIS_PLAN.md` Q3 group breakdown.

### `Breach Rate by Area + Traffic (Pareto)`
- **Purpose:** Matches Business Questions #14, #20 — the primary root-cause-concentration visual.
- **Business Logic:** Combined `Area` × `Traffic` breach count, ranked descending, with a running cumulative % measure alongside it (`Cumulative Breach Share %`, using `RANKX` + a running-total pattern).
- **Intended Grain:** Explicitly two-dimensional (area × traffic combination), not silently collapsed to one dimension by a visual default — set explicitly in the matrix/chart binding.
- **Dependencies:** Frozen `sla_breach_flag`, `DimArea`, `DimWeatherTraffic`.
- **Validation:** Matches `SQL_ANALYSIS_PLAN.md` Q14/Q20 exactly, including the minimum-sample-size exclusion noted there (low-row-count combinations flagged, not silently included with equal visual weight).

### `Adverse vs. Clear Weather Delta`
- **Purpose:** Matches Business Question #19.
- **Business Logic:** Difference between average delivery time for `Weather = "Sunny"` vs. all non-Sunny rows — the exact grouping definition must be pulled from `SQL_ANALYSIS_PLAN.md` Q19's documented definition, not redefined independently in DAX.
- **Dependencies:** `DimWeatherTraffic`.
- **Validation:** Matches SQL Q19 output.

## Cross-Cutting Validation Requirement

Every measure above that has a direct SQL counterpart in `SQL_ANALYSIS_PLAN.md` must be tested at a minimum of three filter contexts (no filter / one area / one category) and must match the SQL and Python outputs before the corresponding dashboard page is considered complete. This is the same three-way cross-validation discipline noted as a strength in the analyst's prior FoodPulse project and is treated as a hard gate here, not an optional nice-to-have.

## Known DAX Risk Areas

Documented in advance so implementation watches for these specifically, based on the general DAX failure modes noted in `DATA_PROFILING_PLAN.md`/prior-project history:

- **Context transition:** any measure using `CALCULATE()` around a row-context iterator must be checked for whether the filter context it's evaluated in matches the visual's intended grain (the FoodPulse `SnapshotDate` bug pattern).
- **Percentile interpolation mismatch:** flagged explicitly above for every P90 measure.
- **Flag-based exclusion vs. hardcoded filters:** every measure that should exclude invalid/flagged rows uses the boolean flag columns from `STAR_SCHEMA.md`, not a hardcoded value filter, so the logic doesn't silently break if a new category value appears.
- **Frozen SLA threshold:** no measure recalculates `sla_threshold_minutes` — every measure reads the pre-computed `sla_breach_flag` only, per `SLA_METHODOLOGY.md`'s change-control rule.
