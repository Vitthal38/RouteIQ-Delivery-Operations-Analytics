# SQL Analysis Pre-Flight Audit — RouteIQ Phase 3

Generated: 2026-08-16

Scope: verify every one of the 22 business questions in `SQL_ANALYSIS_PLAN.md`
can be answered from the approved, live `routeiq` PostgreSQL schema
(Phase 2, `PHASE 2 APPROVED`) before any analytical query is written.

**Live schema re-confirmed before this audit:** `FactDelivery` = 43,648 rows,
`DimAgent` = 444, `DimVehicle` = 3 (`motorcycle`, `scooter`, `van`) — matches
`reports/sql_schema_validation.md` exactly; nothing has drifted since
Phase 2 sign-off.

**Result: all 22 questions are implementable from the approved schema.
No question requires an invented column, a schema change, or a fabricated
value. Four questions carry a disclosed interpretive note or documented
limitation (Q9, Q14, Q19, Q21, Q22) — flagged individually below, none
blocking.**

---

## Column availability reference

Every column below was verified present via `information_schema` during
Phase 2 and is unchanged. No question in this plan references a column
outside this set.

- **`FactDelivery`**: `delivery_key`, `order_id`, `agent_key`, `date_key`, `area_key`, `category_key`, `weather_traffic_key`, `vehicle_key`, `order_time`, `pickup_time`, `delivery_time_minutes`, `prep_time_minutes`, `distance_km`, `sla_threshold_minutes`, `sla_breach_flag`, `is_weekend`, `week_number`, `agent_rating_available_flag`, `coordinates_valid_flag`
- **`DimAgent`**: `agent_key`, `agent_age`, `agent_age_valid_flag`, `agent_rating`, `agent_rating_valid_flag`
- **`DimDate`**: `date_key`, `full_date`, `day_of_week`, `is_weekend`, `week_number`, `month`
- **`DimArea`**: `area_key`, `area_name`, `area_tier_valid_flag`
- **`DimCategory`**: `category_key`, `category_name`
- **`DimVehicle`**: `vehicle_key`, `vehicle_name` (3 rows — see Q21 note)
- **`DimWeatherTraffic`**: `weather_traffic_key`, `weather`, `traffic`

## Project-wide policy decisions applied consistently below

- **Area-tier exclusion:** every area-grouped query returns `area_tier_valid_flag`
  as a visible column rather than silently dropping `Other` — consistent with
  `DATA_CLEANING_PLAN.md` Step 8 ("retain... report its aggregate stats
  separately if material") and the flag-based-exclusion principle in
  `DAX_MEASURE_PLAN.md`. No query hardcodes an area-name filter.
- **Minimum sample size (Q20):** `SQL_ANALYSIS_PLAN.md` asks for low-count
  combinations to be "flagged/excluded" but freezes no numeric threshold
  anywhere in the documentation set. Inventing one would violate the
  no-invented-business-rule rule, so every count-sensitive result exposes
  its `row_count` as a visible column instead of a fabricated cutoff —
  the reader applies their own judgment to a disclosed number rather than
  an undocumented one of mine.
- **SLA logic:** every question touching breach/on-time status reads
  `FactDelivery.sla_breach_flag` and `sla_threshold_minutes` as-is. No
  query recalculates a percentile, a median, or a buffer anywhere in this
  phase.
- **DimAgent framing:** every agent-attribute question is worded as
  attribute-based (rating/age buckets), never as identifiable individual
  agents, per `STAR_SCHEMA.md`'s explicit design decision.

---

## Question-by-question audit

| ID | Business Question | Required Tables | Required Columns | SQL Concepts | Expected Output | Validation Method | Status |
|---|---|---|---|---|---|---|---|
| Q01 | % of deliveries breaching SLA overall and by area | `FactDelivery`, `DimArea` | `sla_breach_flag`, `area_name`, `area_tier_valid_flag` | `GROUP BY`, boolean aggregation | Overall % + area-grouped % | Breach % between 0-100; cross-check vs Phase 1 breach rate | Ready |
| Q02 | Worst P90 delivery time by area | `FactDelivery`, `DimArea` | `delivery_time_minutes`, `area_name` | `PERCENTILE_CONT(0.9) WITHIN GROUP` | Area-ranked P90 table | Spot-check one area's P90 by manual sort | Ready |
| Q03 | Does traffic affect delivery time? (group-stats prep for Python) | `FactDelivery`, `DimWeatherTraffic` | `delivery_time_minutes`, `traffic` | `GROUP BY`, `AVG`/`STDDEV` | Group means/stddev/counts by traffic | Row counts match Python ANOVA input | Ready — **no p-value computed here**, per scope boundary |
| Q04 | Relationship between agent rating and delivery time | `FactDelivery`, `DimAgent` | `agent_rating`, `agent_rating_valid_flag`, `delivery_time_minutes` | `GROUP BY` rating band, `CORR()` | Rating-bucket avg table + Pearson r | Match Python `CORR()` to 2 decimals | Ready |
| Q05 | Top weather/traffic condition for longest delivery times | `FactDelivery`, `DimWeatherTraffic` | `weather`, `traffic`, `delivery_time_minutes` | `GROUP BY`, `RANK()` | Ranked weather×traffic table | Sanity-check top result by manual filter | Ready |
| Q06 | Categories with highest average delivery time | `FactDelivery`, `DimCategory` | `category_name`, `delivery_time_minutes` | `GROUP BY`, `ORDER BY` | Category-ranked avg table | Row count per category ≈ 2,650-2,850 | Ready |
| Q07 | Weekend vs. weekday delivery time | `FactDelivery` | `is_weekend`, `delivery_time_minutes` | `CASE WHEN`, `GROUP BY` | Two-group avg/P90 comparison | Weekend + weekday counts = total | Ready |
| Q08 | OTD% by area | `FactDelivery`, `DimArea` | Same as Q01, inverse framing | Same as Q01 | Area-grouped OTD% table | OTD% + breach% per area = 100% | Ready |
| Q09 | Are specific agents outlier-prone, or is delay evenly distributed? | `FactDelivery`, `DimAgent` | `agent_rating`, `agent_rating_valid_flag`, `delivery_time_minutes` | `STDDEV`, `NTILE()` | Distribution/variance by rating tier | Cross-checked visually in future Python EDA | Ready — **reframed as attribute-tier distribution, not individual-agent tracking**; see Step 6 note below |
| Q10 | Does distance correlate with delivery time, or is it condition-driven? | `FactDelivery`, `DimWeatherTraffic` | `distance_km`, `coordinates_valid_flag`, `delivery_time_minutes`, `weather`, `traffic` | `CORR()`, `GROUP BY` | Correlation coefficient + condition group means | Row count = coordinate-valid rows only, stated explicitly | Ready |
| Q11 | Trend in delivery time over the observed period | `FactDelivery`, `DimDate` | `week_number`, `delivery_time_minutes`, `full_date` | `GROUP BY week_number`, `LAG()` | Weekly avg/P90 series + delta | Partial first/last week flagged via distinct-day count | Ready |
| Q12 | Weather condition with most SLA breaches | `FactDelivery`, `DimWeatherTraffic` | `weather`, `sla_breach_flag` | `GROUP BY`, boolean aggregation | Weather-grouped breach count/rate | Sum of per-weather breaches = total breaches | Ready |
| Q13 | Is weather statistically significant for delivery time? (group-stats prep) | `FactDelivery`, `DimWeatherTraffic` | `weather`, `delivery_time_minutes` | `GROUP BY`, aggregate stats | Group means/counts/stddev by weather | Row counts match Python test input exactly | Ready — **no p-value computed here** |
| Q14 | % of deliveries from top 20% highest-delay areas/categories (Pareto) | `FactDelivery`, `DimArea`, `DimCategory` | `area_name`, `category_name`, `sla_breach_flag` | `RANK()`, `SUM() OVER` running total | Cumulative % table, area cut + category cut | Cumulative % reaches 100% monotonically | Ready — **"areas/categories" read as two separate single-dimension Pareto cuts** (disclosed in `Q14_*.sql` header); `SQL_ANALYSIS_PLAN.md`'s own text does not specify a pooled ranking, and Q20 already owns the combined area×traffic cut |
| Q15 | Agent age vs. delivery time or rating | `FactDelivery`, `DimAgent` | `agent_age`, `agent_age_valid_flag`, `agent_rating`, `agent_rating_valid_flag` | `CORR()` | Two correlation results | Both computed only on rows passing both validity flags | Ready |
| Q16 | Which area underperforms most on OTD%? | `FactDelivery`, `DimArea` | Same as Q08 | `ORDER BY ... LIMIT 1` on Q08's own logic | Single lowest-OTD% area | Must equal the minimum in Q08's own table exactly | Ready |
| Q17 | Week-over-week volatility in delivery time | `FactDelivery`, `DimDate` | `week_number`, `delivery_time_minutes` | `LAG()` | Week-over-week % change series | Re-derivable by manual subtraction of two adjacent weeks | Ready |
| Q18 | Are longer delivery times concentrated in specific categories? | `FactDelivery`, `DimCategory` | Same as Q06 | `GROUP BY`, `STDDEV` | Same cut as Q06, variance-framed | Same as Q06 | Ready |
| Q19 | Delivery-time delta: clear vs. adverse weather | `FactDelivery`, `DimWeatherTraffic` | `weather`, `delivery_time_minutes` | `CASE WHEN`, `GROUP BY` | Two-group comparison | Group definition stated in the query comment | Ready — **"adverse" = all non-Sunny weather values**, per the plan's own example, stated explicitly in `Q19_*.sql` |
| Q20 | Area + traffic combination with highest breach concentration | `FactDelivery`, `DimArea`, `DimWeatherTraffic` | `area_name`, `traffic`, `sla_breach_flag` | `GROUP BY area, traffic`, `HAVING` | 2-D breach-rate table | Low-count combinations visibly flagged via `row_count`, not silently equal-weighted | Ready — see minimum-sample-size policy above |
| Q21 | Does vehicle type affect average delivery time? | `FactDelivery`, `DimVehicle` | `vehicle_name`, `delivery_time_minutes` | `GROUP BY` | Vehicle-grouped avg/P90 | — | Ready **with a documented limitation**: `DimVehicle` has 3 members (`motorcycle`, `scooter`, `van`). `bicycle` cannot be included — its 15 raw rows fell entirely inside the Cleaning Step 3 exclusion cluster (Phase 2 finding, already approved). This question **cannot** be answered for bicycle at all; it is not merely low-confidence as the plan's original note anticipated. See Step 7. |
| Q22 | Estimated improvement if worst area matched median area's delivery time | `FactDelivery`, `DimArea` | Derived from Q02/Q08's own logic | Simple arithmetic on Q02/Q08 outputs | Single illustrative delta figure | Explicitly labeled illustrative, not a guaranteed savings figure (`ASSUMPTIONS.md` A8) | Ready — **"worst"/"median" area defined by OTD% ranking (Q08/Q16's own criterion, for project-wide consistency), then that ranking's average delivery time is used for the delta** — disclosed in `Q22_*.sql` header since the plan does not fully specify the ranking criterion |

## Blocking issues found

**None.** No question requires a column, table, or relationship absent
from the approved Phase 2 schema. No question requires reintroducing
excluded rows or fabricating a value.

## Non-blocking notes carried into implementation

1. **Q09** — will be delivered as agent **attribute-tier** distribution
   (by rating band), not individual-agent outlier detection, per
   `STAR_SCHEMA.md`'s explicit "no true Agent_ID" design decision.
2. **Q14** — implemented as two independent Pareto cuts (area, category),
   not a single pooled ranking; reasoning stated in the SQL file.
3. **Q19** — "adverse weather" explicitly defined as all non-Sunny values
   in the SQL file, per the plan's own suggested example.
4. **Q20** — no numeric minimum-sample-size threshold is invented;
   `row_count` is exposed instead.
5. **Q21** — `bicycle` is absent from the analysis population entirely
   (0 rows), not merely low-confidence as originally anticipated in
   `SQL_ANALYSIS_PLAN.md`. Documented as a limitation, not fabricated.
6. **Q22** — "worst"/"median" area defined via the Q08/Q16 OTD% ranking,
   for consistency with how "worst area" is already defined elsewhere in
   this project, and stated explicitly in the file.

**Pre-flight audit passed. Proceeding to implementation (sql/analysis/).**
