# SQL Schema Validation Report — RouteIQ Phase 2

Generated: 2026-08-16

Scope: PostgreSQL star-schema implementation only (STAR_SCHEMA.md), loaded
from the frozen Phase 1 outputs `data/cleaned/cleaned_delivery.csv` and
`data/cleaned/sla_reference.csv`. **No SQL business-analysis queries were
implemented or run** — every query in this report is a structural/
referential-integrity/reconciliation check, not one of the 22
`SQL_ANALYSIS_PLAN.md` business questions.

All results below are actual output captured from a live execution of
`sql/schema/01_create_schema.sql` through `sql/schema/08_validation.sql`
against a real PostgreSQL instance — nothing in this report is asserted
without a query result to back it.

---

## 1. Database Connection / Setup

| Property | Value |
|---|---|
| Server | PostgreSQL 18.3, x86_64-windows (local Windows service, `postgresql-x64-18`) |
| Host | `localhost`, port 5432 |
| Connecting role | `postgres` (superuser) |
| Database | `postgres` (default maintenance database — no separate database was provisioned; see design note below) |
| Schema | `routeiq` (created by `01_create_schema.sql`) |
| Client | `psql.exe` 18, invoked via `sql/schema/01`–`08` in order |

**Design note:** a dedicated schema (`routeiq`) was created inside the
existing default database rather than provisioning a new database.
`STAR_SCHEMA.md` does not mandate a database name, and `01_create_schema.sql`
is scoped to schema creation, not database provisioning.

**Load mechanism note:** `06_load_dimensions.sql` uses server-side `COPY`
(not the client-side `\copy` meta-command). During this build, `\copy`'s
own argument parser was found not to reliably expand psql's quoted-literal
variable substitution (`:'var'`) for a path containing spaces — server-side
`COPY`, executed as ordinary SQL text via `-f`, does not have this problem.
This requires the PostgreSQL server process to have filesystem read access
to the source CSVs, which was confirmed working for this local install.

## 2. Table Inventory

| Table | Type |
|---|---|
| `DimAgent` | BASE TABLE |
| `DimArea` | BASE TABLE |
| `DimCategory` | BASE TABLE |
| `DimDate` | BASE TABLE |
| `DimVehicle` | BASE TABLE |
| `DimWeatherTraffic` | BASE TABLE |
| `FactDelivery` | BASE TABLE |
| `stg_cleaned_delivery` | BASE TABLE (transient staging table) |
| `stg_sla_reference` | BASE TABLE (transient staging table) |

9 tables total: the 6 documented dimensions + `FactDelivery`, matching
`STAR_SCHEMA.md` exactly, plus 2 staging tables used only to load from CSV
(not part of the documented star schema itself).

## 3. Row Counts

| Table | Row Count | Expected | Match |
|---|---|---|---|
| `DimAgent` | 444 | 444 | ✅ |
| `DimArea` | 4 | 4 | ✅ |
| `DimCategory` | 16 | 16 | ✅ |
| `DimDate` | 44 | 44 | ✅ |
| `DimVehicle` | 3 | 3 (see §14 warning) | ✅ |
| `DimWeatherTraffic` | 24 | 24 | ✅ |
| `FactDelivery` | **43,648** | **43,648** | ✅ |

## 4. Column Counts

| Table | Columns |
|---|---|
| `DimAgent` | 5 (`agent_key`, `agent_age`, `agent_age_valid_flag`, `agent_rating`, `agent_rating_valid_flag`) |
| `DimArea` | 3 (`area_key`, `area_name`, `area_tier_valid_flag`) |
| `DimCategory` | 2 (`category_key`, `category_name`) |
| `DimDate` | 6 (`date_key`, `full_date`, `day_of_week`, `is_weekend`, `week_number`, `month`) |
| `DimVehicle` | 2 (`vehicle_key`, `vehicle_name`) |
| `DimWeatherTraffic` | 3 (`weather_traffic_key`, `weather`, `traffic`) |
| `FactDelivery` | **19** — matches `STAR_SCHEMA.md`'s documented field count exactly; no undocumented column added |

## 5. Primary-Key Validation

Every table has exactly one primary key, on the documented surrogate key column:

| Table | PK Column | Duplicate PK Values |
|---|---|---|
| `DimAgent` | `agent_key` | 0 |
| `DimArea` | `area_key` | 0 |
| `DimCategory` | `category_key` | 0 |
| `DimDate` | `date_key` | 0 |
| `DimVehicle` | `vehicle_key` | 0 |
| `DimWeatherTraffic` | `weather_traffic_key` | 0 |
| `FactDelivery` | `delivery_key` | 0 |

## 6. Foreign-Key Validation

All 6 documented `FactDelivery -> Dim*` relationships exist as enforced FK constraints:

| Constraint | FK Column | References |
|---|---|---|
| `fk_fact_agent` | `agent_key` | `DimAgent.agent_key` |
| `fk_fact_date` | `date_key` | `DimDate.date_key` |
| `fk_fact_area` | `area_key` | `DimArea.area_key` |
| `fk_fact_category` | `category_key` | `DimCategory.category_key` |
| `fk_fact_weather_traffic` | `weather_traffic_key` | `DimWeatherTraffic.weather_traffic_key` |
| `fk_fact_vehicle` | `vehicle_key` | `DimVehicle.vehicle_key` |

## 7. Orphan Checks

| Relationship | Orphan Rows |
|---|---|
| `FactDelivery -> DimAgent` | **0** |
| `FactDelivery -> DimDate` | **0** |
| `FactDelivery -> DimArea` | **0** |
| `FactDelivery -> DimCategory` | **0** |
| `FactDelivery -> DimWeatherTraffic` | **0** |
| `FactDelivery -> DimVehicle` | **0** |

**Result: 0 orphaned fact rows across all 6 relationships.**

## 8. Duplicate Checks

| Check | Duplicate Count |
|---|---|
| `FactDelivery.order_id` | 0 |
| `DimArea.area_name` | 0 |
| `DimCategory.category_name` | 0 |
| `DimVehicle.vehicle_name` | 0 |
| `DimDate.full_date` | 0 |
| `DimWeatherTraffic (weather, traffic)` | 0 |
| `DimAgent (agent_age, agent_rating)`, NULLs treated as equal | 0 |

## 9. SLA Reference Validation

1. **Category count in `sla_reference.csv`:** 16 ✅
2. **Every category has exactly one threshold:** 0 categories with count ≠ 1 ✅
3. **`FactDelivery.sla_threshold_minutes` vs `sla_reference.csv`, per category — 16/16 exact matches, 0 mismatches:**

| Category | Reference Threshold | Fact Threshold | Mismatch |
|---|---|---|---|
| Apparel | 165 | 165 | false |
| Books | 160 | 160 | false |
| Clothing | 160 | 160 | false |
| Cosmetics | 165 | 165 | false |
| Electronics | 160 | 160 | false |
| Grocery | 33 | 33 | false |
| Home | 160 | 160 | false |
| Jewelry | 160 | 160 | false |
| Kitchen | 165 | 165 | false |
| Outdoors | 160 | 160 | false |
| Pet Supplies | 160 | 160 | false |
| Shoes | 160 | 160 | false |
| Skincare | 165 | 165 | false |
| Snacks | 160 | 160 | false |
| Sports | 165 | 165 | false |
| Toys | 160 | 160 | false |

4. **Every category has exactly one distinct threshold value within `FactDelivery`:** 0 categories with >1 distinct value ✅
5. **No `FactDelivery` row lacks an SLA threshold:** 0 rows with NULL `sla_threshold_minutes` ✅

`sla_threshold_minutes` was sourced by joining `stg_sla_reference` (loaded
directly from `sla_reference.csv`) on `Category` during `07_load_fact.sql`
— it was never recalculated as a percentile anywhere in the SQL layer.

## 10. SLA Breach Validation

1. **`sla_breach_flag` mismatches vs. independent recomputation** (`delivery_time_minutes > sla_threshold_minutes`, computed fresh in the validation query): **0 / 43,648**
2. **Boundary rule** (`delivery_time_minutes = sla_threshold_minutes` must mean NOT breached): 1,133 boundary rows, **0 incorrectly flagged as a breach**
3. **Breach count and rate:**

| Total Rows | Total Breaches | Breach Rate |
|---|---|---|
| 43,648 | 10,328 | **23.6620%** |

4. **Reconciliation against the approved Python Phase 1 result (23.6620%): exact match.**

This is also enforced structurally, not just at load time: `04_create_constraints.sql`'s
`chk_sla_breach_flag_matches_rule` CHECK constraint makes it impossible for
any future row (however inserted) to violate `sla_breach_flag = (delivery_time_minutes > sla_threshold_minutes)`.

## 11. Source-to-Fact Reconciliation

| Check | Result |
|---|---|
| Staged cleaned CSV rows vs. `FactDelivery` rows | 43,648 = 43,648 ✅ |
| `FactDelivery` total rows vs. distinct `order_id` | 43,648 = 43,648 (no duplicates) ✅ |
| Staged `Order_ID`s missing from `FactDelivery` | 0 ✅ |
| `FactDelivery` `order_id`s not present in staged source | 0 ✅ |

**Every source row was loaded exactly once; no row was silently dropped, and no fact row was fabricated.**

## 12. Dimension Cardinality

| Dimension | Actual | Expected (Step 1 audit) | Match |
|---|---|---|---|
| `DimAgent` (distinct age/rating combos) | 444 | 444 | ✅ |
| `DimArea` | 4 | 4 | ✅ |
| `DimCategory` | 16 | 16 | ✅ |
| `DimDate` | 44 | 44 | ✅ |
| `DimVehicle` | 3 | 3 | ✅ |
| `DimWeatherTraffic` | 24 | 24 | ✅ |

## 13. Index Inventory

22 indexes total. 14 are created implicitly by `PRIMARY KEY`/`UNIQUE`
constraints (not listed again here — see §5/§8). 8 were explicitly added
in `05_create_indexes.sql`, each with a cited justification:

| Index | Table | Column(s) | Justification |
|---|---|---|---|
| `idx_fact_agent_key` | `FactDelivery` | `agent_key` | FK join column — PostgreSQL does not auto-index the referencing side of a FK |
| `idx_fact_date_key` | `FactDelivery` | `date_key` | FK join column |
| `idx_fact_area_key` | `FactDelivery` | `area_key` | FK join column |
| `idx_fact_category_key` | `FactDelivery` | `category_key` | FK join column |
| `idx_fact_weather_traffic_key` | `FactDelivery` | `weather_traffic_key` | FK join column |
| `idx_fact_vehicle_key` | `FactDelivery` | `vehicle_key` | FK join column |
| `idx_fact_sla_breach_flag` | `FactDelivery` | `sla_breach_flag` | Filtered/grouped in nearly every P0/P1 query in `SQL_ANALYSIS_PLAN.md` (Q1, Q8, Q12-14, Q16, Q20) and every headline KPI (`KPI_DEFINITIONS.md` #1, #2, #7) |
| `idx_fact_week_number` | `FactDelivery` | `week_number` | Drives the weekly trend / week-over-week KPI (`KPI_DEFINITIONS.md` #8; `SQL_ANALYSIS_PLAN.md` Q11, Q17) |

`FactDelivery.order_id` and every dimension natural key already have an
implicit index via their `UNIQUE` constraint — no separate index was added
for them.

Also inventoried: 5 CHECK constraints (`FactDelivery_delivery_time_minutes_check`,
`FactDelivery_prep_time_minutes_check`, `chk_distance_km_non_negative`,
`chk_distance_km_null_iff_coords_invalid`, `chk_sla_breach_flag_matches_rule`).

## 14. Warnings

**W1 — `DimVehicle` has 3 rows, not 4.** Raw source data documents 4 vehicle
types (`motorcycle`, `scooter`, `van`, `bicycle`). All 15 raw `bicycle` rows
fall inside the Cleaning Step 3 91-row exclusion cluster (missing
Weather/Traffic), so 0 `bicycle` rows exist in the cleaned dataset this
schema was built from. This was surfaced to the user before implementation
began ("Finding A") and explicitly approved to proceed with a faithful
3-row `DimVehicle`. It affects a future SQL business question
(`SQL_ANALYSIS_PLAN.md` Q21, which assumes low-confidence `bicycle` data
exists — it does not, post-cleaning), not this phase's schema correctness.

**W2 — `PYTHON_ANALYSIS_PLAN.md` filename drift (pre-existing, reported previously).**
Unrelated to this phase; documented in `reports/phase1_remediation_audit.md`
§13. Not re-litigated here.

No other warnings. Every check in §3–§13 passed with an exact, verified result.

## 15. Final Status

All Phase 2 database-layer validation requirements passed:

- [x] 0 duplicate primary key values, any table
- [x] All 6 documented foreign keys present and enforced
- [x] 0 orphaned fact rows, all 6 relationships
- [x] 0 duplicate natural keys, any dimension
- [x] SLA reference: 16/16 categories, 1 threshold each, 0 mismatches vs. `FactDelivery`
- [x] `sla_breach_flag`: 0 mismatches vs. independent recomputation
- [x] Boundary rule: 1,133/1,133 correctly on-time
- [x] Breach rate reconciles exactly to the approved Python figure (23.6620%)
- [x] Source-to-fact reconciliation: 43,648 = 43,648, 0 missing, 0 extra
- [x] Every dimension's cardinality matches the Step 1 pre-implementation audit

**Database layer validated. See `docs/DATABASE_DATA_DICTIONARY.md`,
`docs/DATABASE_ERD.md`, and the Phase 2 gate verdict for final sign-off.**
