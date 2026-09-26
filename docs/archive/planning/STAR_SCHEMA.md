# Star Schema Design — RouteIQ

## Table of Contents
1. [Design Philosophy](#design-philosophy)
2. [Grain](#grain)
3. [Fact Table](#fact-table)
4. [Dimension Tables](#dimension-tables)
5. [Keys](#keys)
6. [Relationships](#relationships)
7. [Naming Standards](#naming-standards)
8. [ER Diagram](#er-diagram)
9. [Design Decisions](#design-decisions)
10. [Future Scalability](#future-scalability)

Related documents: `FEATURE_ENGINEERING.md` (source of engineered columns used here), `SLA_METHODOLOGY.md` (frozen threshold stored as a dimension attribute), `DATA_CLEANING_PLAN.md` (defines which rows/flags feed this model)

---

## Design Philosophy

A star schema (not snowflake) is used because this is a BI/reporting workload, not a transactional system: Power BI's DAX engine and typical SQL analytical queries perform best against a small number of wide dimension tables joined directly to one fact table, minimizing join depth. Snowflaking (normalizing dimensions further) would reduce redundancy marginally but cost query simplicity and DAX performance for no benefit at this data volume (43,739 fact rows pre-exclusions).

## Grain

**One row per delivery order** (`Order_ID`) in the fact table. This is the lowest available grain in the source data — there is no sub-order (e.g., per-item) detail — and it matches every business question in the brief, all of which are answered by aggregating or filtering individual delivery events, not by decomposing an order further.

## Fact Table

### `FactDelivery`

| Column | Type | Source / Derivation | Notes |
|---|---|---|---|
| `delivery_key` | surrogate int, PK | Generated | Surrogate key, not `Order_ID`, so the fact table is insulated from any future source-key format change |
| `order_id` | string | `Order_ID` | Natural/business key, unique per profiling (0 duplicates confirmed) |
| `agent_key` | int, FK → `DimAgent` | Derived | See DimAgent design decision below |
| `date_key` | int, FK → `DimDate` | Derived from `Order_Date` | Standard date-dimension surrogate key (YYYYMMDD int) |
| `area_key` | int, FK → `DimArea` | Derived from cleaned `Area` | |
| `category_key` | int, FK → `DimCategory` | Derived from `Category` | |
| `weather_traffic_key` | int, FK → `DimWeatherTraffic` | Derived from cleaned `Weather` + `Traffic` | See design decision on combined dimension below |
| `vehicle_key` | int, FK → `DimVehicle` | Derived from cleaned `Vehicle` | |
| `order_time` | time | Cleaned `Order_Time` | Degenerate attribute (kept on fact, no separate time dimension needed at this grain) |
| `pickup_time` | time | Cleaned `Pickup_Time` | |
| `delivery_time_minutes` | int | `Delivery_Time` | Core measure |
| `prep_time_minutes` | int | Engineered (`FEATURE_ENGINEERING.md` #8) | |
| `distance_km` | numeric, nullable | Engineered (`FEATURE_ENGINEERING.md` #1) | Null for coordinate-invalid rows (Cleaning Step 7) — nullable by design, not defaulted to 0 |
| `sla_threshold_minutes` | numeric | Frozen per `SLA_METHODOLOGY.md`, joined from category-level static reference | Stored on the fact row (not recalculated) so every consumer reads the same frozen value |
| `sla_breach_flag` | boolean | Engineered (`FEATURE_ENGINEERING.md` #3) | Core measure for OTD%/breach-rate KPIs |
| `is_weekend` | boolean | Engineered (`FEATURE_ENGINEERING.md` #5) | |
| `week_number` | int | Engineered (`FEATURE_ENGINEERING.md` #7) | |
| `agent_rating_available_flag` | boolean | Cleaning Step 5 | Distinguishes true-null ratings from valid ones without dropping the row |
| `coordinates_valid_flag` | boolean | Cleaning Step 7 | Distinguishes distance-eligible rows without dropping the row |

## Dimension Tables

### `DimAgent`
| Column | Notes |
|---|---|
| `agent_key` (PK) | Surrogate |
| `agent_age` | With plausibility flag (Cleaning Step 6) |
| `agent_age_valid_flag` | Boolean, from cleaning |
| `agent_rating` | Nullable; excluded from rating KPI per flag, not per null-filter alone |
| `agent_rating_valid_flag` | Boolean, from cleaning Step 4 (catches the 6.0 out-of-range values specifically, distinct from null) |

**Design decision:** the source data has no true `Agent_ID` — age and rating are the only agent attributes available, so `DimAgent` is built as a derived dimension (effectively one row per distinct age+rating combination, or one row per fact row if no natural grouping exists). This is documented explicitly because it means "agent-level" analysis in this project is really "delivery-level attribute analysis," not true individual-rider tracking — stated plainly so it isn't overclaimed in the dashboard or interview.

### `DimDate`
Standard date dimension: `date_key`, `full_date`, `day_of_week`, `is_weekend`, `week_number`, `month`, covering the observed range 2022-02-11 to 2022-04-06 only (not padded to a full year, since there's no business need to model dates outside the data's actual span for this static-dataset project).

### `DimArea`
| Column | Notes |
|---|---|
| `area_key` (PK) | Surrogate |
| `area_name` | Cleaned value (whitespace trimmed) |
| `area_tier_valid_flag` | False for `Other` (Cleaning Step 8), so area-tier comparisons can filter cleanly without deleting the row |

### `DimCategory`
`category_key`, `category_name` — straightforward, no data quality issues found in profiling.

### `DimWeatherTraffic`
| Column | Notes |
|---|---|
| `weather_traffic_key` (PK) | Surrogate |
| `weather` | Cleaned value; excludes the resolved 91-row cluster |
| `traffic` | Cleaned value (post `"NaN "` recode) |

**Design decision — combined vs. separate dimensions:** Weather and Traffic are modeled as a single combined dimension rather than two separate dimensions. Reasoning: the two fields are always observed together for a given delivery (both present or both part of the same missing-91 cluster, per profiling), and the primary business questions (#3, #5, #12, #20 in the brief) analyze weather×traffic combinations, not each independently in most cases. A combined dimension avoids an unnecessary extra join for the most common query pattern. This is a documented trade-off, not an oversight — if independent weather-only or traffic-only slicing becomes a frequent need, this can be split later (see Future Scalability).

### `DimVehicle`
`vehicle_key`, `vehicle_name` — straightforward.

## Keys

- **Primary keys:** every dimension uses a surrogate integer key, generated during load — not the natural/business value — so the model is insulated from source-value changes (e.g., if `Metropolitian` is ever corrected upstream, only the dimension row's attribute changes, not every fact row).
- **Foreign keys:** `FactDelivery` holds one FK per dimension, enforced via standard star-schema referential integrity in PostgreSQL (`FOREIGN KEY` constraints).
- **Business/natural key retained:** `order_id` is kept on the fact table as a non-key attribute for traceability back to the source CSV during debugging/validation — it is not used as the join key.

## Relationships

All relationships are **one-to-many from dimension to fact**, single-directional, at the fact table's `Order_ID` grain — standard star-schema cardinality. No many-to-many relationships exist in this model (each delivery has exactly one agent-attribute-combination, one date, one area, one category, one weather/traffic combination, one vehicle).

## Naming Standards

- Tables: `PascalCase`, prefixed `Fact`/`Dim` (`FactDelivery`, `DimArea`).
- Columns: `snake_case`.
- Surrogate keys: `<entity>_key`.
- Boolean/flag columns: suffixed `_flag`.
- This convention is chosen for direct compatibility with Power BI's default relationship-detection behavior and to keep SQL and DAX naming consistent, reducing translation errors when cross-validating a KPI across both layers (a documented requirement in `KPI_DEFINITIONS.md`).

## ER Diagram

```
                        ┌───────────────┐
                        │   DimDate     │
                        └───────┬───────┘
                                │
┌───────────────┐      ┌───────▼────────┐      ┌────────────────┐
│   DimAgent     │──────▶                ◀──────│   DimArea       │
└───────────────┘      │                │      └────────────────┘
                        │                │
┌───────────────┐      │  FactDelivery  │      ┌────────────────┐
│  DimCategory   │──────▶                ◀──────│ DimWeatherTraffic│
└───────────────┘      │                │      └────────────────┘
                        │                │
                        └───────┬────────┘
                                │
                        ┌───────▼───────┐
                        │  DimVehicle   │
                        └───────────────┘
```

## Design Decisions

| Decision | Rationale |
|---|---|
| Star, not snowflake | BI query/DAX performance priority over storage normalization at this data volume |
| Surrogate keys throughout | Insulates model from source-value changes; standard practice |
| Combined `DimWeatherTraffic` | Matches the dominant query pattern (weather×traffic root-cause questions); documented trade-off |
| `DimAgent` built from attributes, not a true agent entity | No `Agent_ID` exists in source; stated explicitly to avoid overclaiming individual-rider tracking |
| Flags stored on fact/dimension rows rather than rows being silently dropped | Preserves the conditional-exclusion design from `DATA_CLEANING_PLAN.md` — a query can choose to include/exclude based on the flag rather than having already-lost data |
| `sla_threshold_minutes` stored on the fact row, not recalculated per query | Guarantees the frozen SLA value (`SLA_METHODOLOGY.md`) is identical across every SQL query, Python read, and DAX measure |

## Future Scalability

- If a production version of this project connected to a live delivery feed, `DimDate` would be pre-populated for a full multi-year range (not bounded to the observed 8 weeks) and the fact table would be partitioned by date for load performance.
- If a true `Agent_ID` became available, `DimAgent` would convert from an attribute-derived dimension to a genuine slowly-changing dimension (Type 2) tracking rating changes over time.
- `DimWeatherTraffic` could be split into two independent dimensions if a future business need requires slicing by weather independent of traffic frequently enough to justify the extra join.
