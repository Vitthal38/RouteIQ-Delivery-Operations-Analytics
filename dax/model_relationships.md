# Power BI Model — Relationships Specification

Generated: 2026-08-16

**Scope note (read first):** this document specifies exactly how the
Power BI semantic model must be built when connected to the approved
`routeiq` PostgreSQL schema. It is a precise, ready-to-apply
specification — not a description of a `.pbix` file that has been built,
since no tool in this environment can author or drive Power BI Desktop's
model editor. Every relationship and column below maps 1:1 to the
already-approved schema in `STAR_SCHEMA.md` / `docs/DATABASE_DATA_DICTIONARY.md`
— nothing here is new or invented.

---

## Data source

Import (or DirectQuery) from the `routeiq` PostgreSQL schema, connecting
directly to `"FactDelivery"` and the six `"Dim*"` tables. Do **not** import
`stg_cleaned_delivery` or `stg_sla_reference` (Phase 2 staging tables,
transient, not part of the star schema).

## Tables to load

| Table | Row count (approved) |
|---|---|
| `FactDelivery` | 43,648 |
| `DimAgent` | 444 |
| `DimArea` | 4 |
| `DimCategory` | 16 |
| `DimDate` | 44 |
| `DimVehicle` | 3 |
| `DimWeatherTraffic` | 24 |

## Relationships

All six relationships are **dimension (1) → FactDelivery (many)**,
**single-direction filtering** (dimension filters fact; fact does not
filter back), matching `STAR_SCHEMA.md`'s documented cardinality exactly.
No bidirectional relationship is created — none is needed, since every
planned visual (`DASHBOARD_PLANNING.md`) filters the fact table from a
dimension slicer/axis, never the reverse.

| # | From (one side) | To (many side) | Cardinality | Cross-filter direction | Active |
|---|---|---|---|---|---|
| 1 | `DimAgent[agent_key]` | `FactDelivery[agent_key]` | 1 : many | Single (Dim → Fact) | Yes |
| 2 | `DimDate[date_key]` | `FactDelivery[date_key]` | 1 : many | Single (Dim → Fact) | Yes |
| 3 | `DimArea[area_key]` | `FactDelivery[area_key]` | 1 : many | Single (Dim → Fact) | Yes |
| 4 | `DimCategory[category_key]` | `FactDelivery[category_key]` | 1 : many | Single (Dim → Fact) | Yes |
| 5 | `DimWeatherTraffic[weather_traffic_key]` | `FactDelivery[weather_traffic_key]` | 1 : many | Single (Dim → Fact) | Yes |
| 6 | `DimVehicle[vehicle_key]` | `FactDelivery[vehicle_key]` | 1 : many | Single (Dim → Fact) | Yes |

**No many-to-many relationship exists or is needed** — every dimension
key is unique in its own table (enforced by the PostgreSQL `PRIMARY KEY`
constraints already validated in Phase 2), and every `FactDelivery` row
carries exactly one value per dimension key (`NOT NULL` + `FOREIGN KEY`
constraints, 0 orphans, verified in `reports/sql_schema_validation.md`).
Mark `FactDelivery` as the model's Fact table (not marked as a date
table); mark `DimDate[full_date]` as the model's official Date table
(`Mark as Date Table`) so time-intelligence functions resolve correctly
against the 44 approved dates only — do not let Power BI auto-generate a
hidden date hierarchy from `FactDelivery[order_time]`/`[pickup_time]`,
since those are degenerate time-of-day attributes, not the delivery date.

## Why not bidirectional

`DASHBOARD_PLANNING.md`'s cross-filtering requirements (e.g., Page 2's
Weather/Traffic slicer affecting the Area heatmap) are satisfied by
single-direction dimension→fact filtering alone: selecting a weather
value filters `FactDelivery` rows, which in turn restricts which
`area_key` values have matching fact rows — the area visual updates
correctly without `DimArea` needing to filter `DimWeatherTraffic`
directly. Bidirectional relationships are not required anywhere in the
documented dashboard plan, and adding one would risk exactly the kind of
context-transition ambiguity `DAX_MEASURE_PLAN.md`'s "Known DAX Risk
Areas" section warns about (the analyst's prior FoodPulse `SnapshotDate`
bug).

## DimAgent — model-level caveat (must be preserved in the model, not just prose)

`DimAgent` is an attribute-derived dimension (distinct `agent_age`/
`agent_rating` combinations) — there is no true `Agent_ID`. In the model:
do not create a hierarchy or a "Agent" display name that implies
individual identity; expose only `agent_age`, `agent_rating`,
`agent_age_valid_flag`, and `agent_rating_valid_flag` as fields. Any
visual built from `DimAgent` must filter to the relevant `*_valid_flag`
before use, per `DAX_MEASURE_PLAN.md`'s explicit warning not to rely on a
bare "not null" filter.

## Column-level notes carried into the model

- `FactDelivery[sla_threshold_minutes]` and `[sla_breach_flag]` are
  imported as-is from the frozen fact table — no calculated column
  recomputes either. See `dax/measures.dax` for the enforcement rule
  applied to every measure that touches them.
- `FactDelivery[distance_km]` imports with native `NULL`s for
  coordinate-invalid rows — `AVERAGE()`/similar DAX aggregations ignore
  blanks by default, which is the correct behavior here (matches
  `FEATURE_ENGINEERING.md` #1's edge case) and requires no special
  handling in the model.
- `DimArea[area_tier_valid_flag]` and `DimVehicle` (3 rows only — no
  `bicycle`) are imported unmodified; no row is added or removed by the
  model layer.
