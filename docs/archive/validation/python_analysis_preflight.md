# Python Analysis Pre-Flight Audit — RouteIQ Phase 4

Generated: 2026-08-16

Scope: verify the approved Phase 1 dataset is intact and unregenerated,
every field the planned Phase 2 EDA / `STATISTICAL_ANALYSIS.md` tests
require is present, and the SQL results needed for cross-validation exist
— before any analysis code is written.

---

## 1. Dataset integrity

| Check | Result |
|---|---|
| `data/cleaned/cleaned_delivery.csv` exists | ✅ |
| Row count | **43,648** (matches Phase 1/2/3 frozen figure exactly) |
| Column count | **30** |
| File modified timestamp | `2026-08-16 18:57:14` — identical to the original Phase 1 build; **no regeneration occurred** during Phase 2 or Phase 3, and none occurs in this preflight check (read-only) |
| `data/cleaned/sla_reference.csv` exists, unchanged | ✅ (verified in Phase 2/3, re-confirmed by file timestamp) |

## 2. Required columns present, with appropriate dtypes

| Column | dtype | Present |
|---|---|---|
| `Delivery_Time` | int64 | ✅ |
| `Area`, `Category`, `Weather`, `Traffic`, `Vehicle` | str | ✅ |
| `distance_km` | float64 (nullable) | ✅ |
| `coordinates_valid_flag` | bool | ✅ |
| `Agent_Rating` | float64 (nullable) | ✅ |
| `agent_rating_valid_flag` | bool | ✅ |
| `Agent_Age` | int64 | ✅ |
| `agent_age_valid_flag` | bool | ✅ |
| `is_weekend` | bool | ✅ |
| `week_number` | int64 | ✅ |
| `sla_breach_flag` | bool | ✅ |
| `sla_threshold_minutes` | float64 | ✅ |
| `prep_time_minutes` | int64 | ✅ |
| `delivery_bucket` | str | ✅ |
| `order_hour` | int64 | ✅ |
| `day_of_week` | str | ✅ |

No required field for any planned EDA item or statistical test is missing.

## 3. Planned analysis feasibility (`PYTHON_ANALYSIS_PLAN.md` Phase 2 / `STATISTICAL_ANALYSIS.md`)

| Planned item | Required fields | Feasible |
|---|---|---|
| Delivery-time distribution overall + by Area/Category/Weather/Traffic | `Delivery_Time`, `Area`, `Category`, `Weather`, `Traffic` | ✅ |
| Missingness/exclusion-flag summary | all `*_valid_flag`, `agent_rating_available_flag` | ✅ |
| Correlation: `distance_km` vs. `delivery_time_minutes` (coordinate-valid only) | `distance_km`, `coordinates_valid_flag`, `Delivery_Time` | ✅ |
| Correlation: `agent_rating` vs. `delivery_time_minutes` (rating-valid only) | `Agent_Rating`, `agent_rating_valid_flag`, `Delivery_Time` | ✅ |
| Correlation: `agent_age` vs. `delivery_time_minutes` and vs. `agent_rating` (both flags) | `Agent_Age`, `agent_age_valid_flag`, `Agent_Rating`, `agent_rating_valid_flag` | ✅ |
| Test 1 — Traffic vs. delivery time (ANOVA/Kruskal-Wallis) | `Traffic`, `Delivery_Time` | ✅ |
| Test 2 — Weather vs. delivery time (ANOVA/Kruskal-Wallis) | `Weather`, `Delivery_Time` | ✅ |
| Test 3 — Agent rating vs. delivery time (Pearson/Spearman) | `Agent_Rating`, `agent_rating_valid_flag`, `Delivery_Time` | ✅ |
| Test 4 — Distance vs. delivery time (Pearson/Spearman) | `distance_km`, `coordinates_valid_flag`, `Delivery_Time` | ✅ |
| Test 5 — Weekend vs. weekday (t-test/Welch/Mann-Whitney) | `is_weekend`, `Delivery_Time` | ✅ |
| Pareto ranking of breach volume by area/category/weather-traffic | `Area`, `Category`, `Weather`, `Traffic`, `sla_breach_flag` | ✅ — cross-validates against `sql/analysis/Q14_*.sql` and `Q20_*.sql` |
| Vehicle comparison | `Vehicle`, `Delivery_Time` | ✅ — same 3-vehicle limitation as `sql/analysis/Q21_*.sql` (bicycle: 0 rows, documented, not fabricated) |

**No planned analysis is infeasible with the available data. No STOP condition triggered.**

## 4. SQL cross-validation inputs available

| Source | Exists |
|---|---|
| `reports/sql_analysis_validation.md` (cross-validation table, per-question results) | ✅ |
| `reports/sql_analysis_preflight.md` | ✅ |
| `reports/sql_schema_validation.md` | ✅ |
| `docs/SQL_IMPLEMENTATION_GUIDE.md` | ✅ |

Figures available for reconciliation in Phase 4 Step 14: total deliveries
(43,648), distinct `Order_ID` (43,648), overall breach rate (23.6620%),
breach counts/rates by area and weather, category/vehicle/area row counts,
weekday/weekend averages, Pearson r for agent-rating and distance
correlations (Q04, Q10, Q15), Pareto cumulative shares (Q14, Q20).

## 5. Known, carried-forward limitations (not new — restated for this phase)

- **`DimAgent` / agent analysis:** no true `Agent_ID` exists. Every
  agent-related EDA/test item in this phase is attribute-level (age,
  rating), never individual-agent — consistent with `STAR_SCHEMA.md` and
  Phase 3's Q09/Q15 treatment.
- **`Vehicle` = bicycle:** 0 rows in the analysis population (all 15 raw
  rows fell inside the Cleaning Step 3 exclusion cluster). Vehicle
  comparisons in this phase cover only `motorcycle`, `scooter`, `van`.
- **SLA methodology:** frozen at category-level P75, strict `>` for
  breach. This phase reads `sla_threshold_minutes` / `sla_breach_flag` as
  stored — it does not recompute either.
- **8 distinct observed weeks**, with a genuine data gap (2022-02-19 to
  2022-02-28) — limits trend/week-over-week claims, as already stated in
  Phase 1 and Phase 3 outputs.

**Pre-flight audit passed. Proceeding to implementation (`python/analysis/`).**
