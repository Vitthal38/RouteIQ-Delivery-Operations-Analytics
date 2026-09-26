# Database Data Dictionary — RouteIQ Phase 2

Generated: 2026-08-16

Schema: `routeiq` (PostgreSQL 18). Reflects the actual implemented schema
as inspected live via `information_schema.columns` — every type/nullability
value below is what PostgreSQL reports, not a re-statement of intent.
Business meanings are taken directly from `STAR_SCHEMA.md`,
`FEATURE_ENGINEERING.md`, `DATA_CLEANING_PLAN.md`, and `SLA_METHODOLOGY.md`
— none are invented here.

---

## `DimAgent`

**ATTRIBUTE-DERIVED DIMENSION — NOT A TRUE AGENT ENTITY.** The source
dataset has no `Agent_ID`. `agent_key` is a technical surrogate for a
distinct `(agent_age, agent_rating)` combination only, per `STAR_SCHEMA.md`'s
explicit design decision. It must never be read as an individual delivery
agent identifier, and supports no longitudinal per-agent performance
tracking.

| Column | Type | Nullable | PK | FK | Source Column | Derivation | Business Meaning |
|---|---|---|---|---|---|---|---|
| `agent_key` | integer | No | Yes | — | *(generated)* | `SERIAL`, one per distinct `(agent_age, agent_rating)` pair (`NULLS NOT DISTINCT` so NULL ratings collapse correctly) | Technical surrogate key for an attribute combination — **not** an agent identity |
| `agent_age` | smallint | No | — | — | `Agent_Age` | Copied as-is | Delivery agent's age, as recorded in source |
| `agent_age_valid_flag` | boolean | No | — | — | *(derived)* | `Agent_Age BETWEEN 18 AND 65` (Cleaning Step 6) | True if age falls within the documented plausible working-age bound |
| `agent_rating` | numeric(2,1) | Yes | — | — | `Agent_Rating` | Copied as-is; NULL preserved for the 54 true-null rows (Cleaning Step 5) | Agent's rating on the dataset's native scale |
| `agent_rating_valid_flag` | boolean | No | — | — | *(derived)* | `Agent_Rating IS NOT NULL AND Agent_Rating BETWEEN 1 AND 5` (Cleaning Steps 4-5) | True only if the rating is both present and within the plausible 1-5 scale — excludes both the 54 nulls and the (pre-Step-3-exclusion) out-of-range 6.0 rows from rating-dependent analysis |

## `DimDate`

Standard date dimension, covering only the 44 dates actually observed
(2022-02-11 to 2022-04-06) — not padded to a full calendar range, per
`STAR_SCHEMA.md`'s Future Scalability note (full-range padding is described
there as a hypothetical production enhancement, not a current requirement).

| Column | Type | Nullable | PK | FK | Source Column | Derivation | Business Meaning |
|---|---|---|---|---|---|---|---|
| `date_key` | integer | No | Yes | — | `Order_Date` | `TO_CHAR(Order_Date, 'YYYYMMDD')::INTEGER` | Standard YYYYMMDD date surrogate key |
| `full_date` | date | No | — | — | `Order_Date` | Cast to `date` | Calendar date the order was placed |
| `day_of_week` | varchar(9) | No | — | — | `day_of_week` (Python, `FEATURE_ENGINEERING.md` #5) | Carried over from Phase 1 | Day name (Monday-Sunday) |
| `is_weekend` | boolean | No | — | — | `is_weekend` (Python, `FEATURE_ENGINEERING.md` #5) | Carried over from Phase 1 | True if `day_of_week` is Saturday or Sunday |
| `week_number` | smallint | No | — | — | `week_number` (Python, `FEATURE_ENGINEERING.md` #7) | Carried over from Phase 1 | ISO week number |
| `month` | smallint | No | — | — | *(derived)* | `EXTRACT(MONTH FROM Order_Date)` | Calendar month (1-12); not a Phase 1 Python field — plain calendar arithmetic on an already-known date, not a business rule |

## `DimArea`

| Column | Type | Nullable | PK | FK | Source Column | Derivation | Business Meaning |
|---|---|---|---|---|---|---|---|
| `area_key` | integer | No | Yes | — | *(generated)* | `SERIAL` | Surrogate key |
| `area_name` | varchar(20) | No | — | — | `Area` | Trimmed (Cleaning Step 1); `Metropolitian` spelling preserved verbatim (Cleaning Step 9) | Delivery area type: `Urban`, `Metropolitian`, `Semi-Urban`, or `Other` |
| `area_tier_valid_flag` | boolean | No | — | — | *(derived)* | `Area <> 'Other'` (Cleaning Step 8) | False only for `Other` — excludes it from Urban/Metropolitan/Semi-Urban tier comparisons without dropping the row |

## `DimCategory`

| Column | Type | Nullable | PK | FK | Source Column | Derivation | Business Meaning |
|---|---|---|---|---|---|---|---|
| `category_key` | integer | No | Yes | — | *(generated)* | `SERIAL` | Surrogate key |
| `category_name` | varchar(30) | No | — | — | `Category` | Copied as-is (no data-quality issue found in profiling) | Product category (16 values) |

## `DimVehicle`

| Column | Type | Nullable | PK | FK | Source Column | Derivation | Business Meaning |
|---|---|---|---|---|---|---|---|
| `vehicle_key` | integer | No | Yes | — | *(generated)* | `SERIAL` | Surrogate key |
| `vehicle_name` | varchar(20) | No | — | — | `Vehicle` | Trimmed (Cleaning Step 1) | Delivery vehicle type. **Populated with 3 values** (`motorcycle`, `scooter`, `van`) — raw data documents a 4th (`bicycle`, 15 rows), but all 15 fall inside the Cleaning Step 3 91-row exclusion cluster; see `reports/sql_schema_validation.md` §14 |

## `DimWeatherTraffic`

Combined dimension per `STAR_SCHEMA.md`'s explicit design decision — not
split into separate Weather/Traffic dimensions.

| Column | Type | Nullable | PK | FK | Source Column | Derivation | Business Meaning |
|---|---|---|---|---|---|---|---|
| `weather_traffic_key` | integer | No | Yes | — | *(generated)* | `SERIAL` | Surrogate key |
| `weather` | varchar(20) | No | — | — | `Weather` | Trimmed (Cleaning Step 1); the 91-row cluster with missing Weather already excluded before this dimension is built | Weather condition (6 values) |
| `traffic` | varchar(10) | No | — | — | `Traffic` | Trimmed (Cleaning Step 1); literal `"NaN"` recoded to true null then excluded via the Step 3 cluster (Cleaning Step 2-3) | Traffic condition (4 values) |

24 rows populated — all 6×4 combinations are actually observed in the data; none is invented.

## `FactDelivery`

Grain: **one row per delivery order** (`Order_ID`). 19 columns, exactly
matching `STAR_SCHEMA.md`'s documented `FactDelivery` field list — no
additional column added.

| Column | Type | Nullable | PK | FK | Source Column | Derivation | Business Meaning |
|---|---|---|---|---|---|---|---|
| `delivery_key` | bigint | No | Yes | — | *(generated)* | `BIGSERIAL` | Surrogate key, insulates the fact table from any future `Order_ID` format change |
| `order_id` | varchar(20) | No | — | — | `Order_ID` | Copied as-is | Natural/business key, retained for source traceability only — not used as a join key |
| `agent_key` | integer | No | — | `DimAgent.agent_key` | *(resolved)* | Joined on `(Agent_Age, Agent_Rating)`, `IS NOT DISTINCT FROM` for the nullable rating | Links to the agent-attribute combination |
| `date_key` | integer | No | — | `DimDate.date_key` | *(resolved)* | Joined on `Order_Date` | Links to the order date |
| `area_key` | integer | No | — | `DimArea.area_key` | *(resolved)* | Joined on `Area` | Links to the delivery area |
| `category_key` | integer | No | — | `DimCategory.category_key` | *(resolved)* | Joined on `Category` | Links to the product category |
| `weather_traffic_key` | integer | No | — | `DimWeatherTraffic.weather_traffic_key` | *(resolved)* | Joined on `(Weather, Traffic)` | Links to the weather/traffic condition |
| `vehicle_key` | integer | No | — | `DimVehicle.vehicle_key` | *(resolved)* | Joined on `Vehicle` | Links to the delivery vehicle |
| `order_time` | time | No | — | — | `Order_Time` | Cast to `time` | Time the order was placed |
| `pickup_time` | time | No | — | — | `Pickup_Time` | Cast to `time` | Time the order was picked up |
| `delivery_time_minutes` | smallint | No | — | — | `Delivery_Time` | Copied as-is; `CHECK > 0` | Actual delivery time in minutes — the core outcome measure |
| `prep_time_minutes` | smallint | No | — | — | `prep_time_minutes` (Python, `FEATURE_ENGINEERING.md` #8) | Carried over from Phase 1; `CHECK >= 0` | Pickup time minus order time, midnight-crossover corrected |
| `distance_km` | double precision | Yes | — | — | `distance_km` (Python, `FEATURE_ENGINEERING.md` #1) | Carried over from Phase 1; NULL iff `coordinates_valid_flag = false` (enforced by CHECK) | Haversine distance, store to drop location |
| `sla_threshold_minutes` | double precision | No | — | — | `sla_reference.csv` | **Joined from the frozen `sla_reference.csv` by `Category` at load time — never recalculated in SQL** | Category-level P75 of `Delivery_Time`, frozen per `SLA_METHODOLOGY.md` |
| `sla_breach_flag` | boolean | No | — | — | *(computed)* | `delivery_time_minutes > sla_threshold_minutes` (strict `>`, computed once at load, and enforced identically by a CHECK constraint) | True if the delivery breached its category's frozen SLA threshold |
| `is_weekend` | boolean | No | — | — | `is_weekend` (Python) | Carried over from Phase 1 | True if the order date is Saturday/Sunday |
| `week_number` | smallint | No | — | — | `week_number` (Python) | Carried over from Phase 1 | ISO week number of the order date |
| `agent_rating_available_flag` | boolean | No | — | — | *(derived)* | `Agent_Rating IS NOT NULL` (Cleaning Step 5) | Distinguishes true-null ratings from valid ones without dropping the row |
| `coordinates_valid_flag` | boolean | No | — | — | *(derived)* | Store and drop coordinates both within the India bounding box (Cleaning Step 7) | Distinguishes distance-eligible rows without dropping the row |

---

## Type Decisions Worth Noting

- **`sla_threshold_minutes`, `distance_km` → `double precision`, not `numeric(n,m)`.**
  Both are Python `float64` values (a percentile and a haversine
  computation). `double precision` preserves the source value exactly;
  rounding to a fixed decimal scale risked a validation mismatch against
  the frozen CSV for no benefit.
- **`agent_rating` → `numeric(2,1)`, not `double precision`.** Verified
  every observed value is an exact one-decimal multiple (e.g. `4.9`), so a
  fixed-scale exact type is both correct and more space-efficient than
  float storage for a bounded rating scale.
- **`delivery_time_minutes`, `prep_time_minutes`, `week_number`,
  `agent_age` → `smallint`.** All have small, well-bounded observed ranges
  (10-270, ≥0, 6-14, 15-50 respectively) — `smallint` is sufficient and
  avoids over-provisioning `integer`/`bigint` for values that will never
  approach those ranges.
- **`order_id` → `varchar(20)`, not `text`.** Every observed value is
  exactly 13 characters; 20 gives headroom without hardcoding the exact
  observed length as a hard constraint.
- **Boolean flags stay `boolean`, never `varchar`/`integer`.** No flag
  column's semantics were converted to text or 0/1 integers anywhere in
  the schema.
- **`DimAgent` `UNIQUE NULLS NOT DISTINCT (agent_age, agent_rating)`**
  (PostgreSQL 15+ feature) — ordinary SQL `UNIQUE` treats every `NULL` as
  distinct, which would have let duplicate `(age, NULL-rating)` dimension
  rows through; `NULLS NOT DISTINCT` closes that gap.
