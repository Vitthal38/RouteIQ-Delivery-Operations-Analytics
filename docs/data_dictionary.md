# Data Dictionary

Source: [Amazon Delivery Dataset](https://www.kaggle.com/datasets/sujalsuthar/amazon-delivery-dataset)
(Kaggle, author sujalsuthar), 43,739 raw rows, 16 columns. Cleaned to 43,648 rows in
`src/routeiq/cleaning/`. See `docs/limitations.md` for why this data is treated as a realistic
synthetic-style dataset rather than real company operations.

## Analytical dataset / view

The controlled input every analysis reads: `data/processed/analytical_deliveries.csv` in Python
(built by `src/routeiq/features/analytical.py`) and `routeiq.vw_analytical_deliveries` in SQL
(`sql/schema/09_create_analytical_view.sql`). Both define every derived column identically.

| Column | Type | Definition |
|---|---|---|
| `order_id` | text | Unique delivery identifier. Traceability only. |
| `order_date` | date | 11 Feb – 6 Apr 2022 (44 distinct dates observed). |
| `week_number` | int | ISO week number of `order_date`. |
| `is_weekend` | 0/1 | 1 if `order_date` is Saturday or Sunday. |
| `order_hour` | int 0–23 | Hour the order was placed, from `Order_Time`. |
| `hour_band` | text | Exploratory band, chosen after inspecting the hourly profile (not a pre-registered cut): `00-07 overnight`, `08-10 morning`, `11-14 midday`, `15-16 afternoon`, `17-18 early evening`, `19-21 evening peak`, `22-23 late evening`. |
| `is_peak_hour` | 0/1 | 1 if `order_hour` is 17–23. Rule: hourly order volume ≥ 2× the median hourly volume — this rule, applied to the data, selects exactly hours 17–23 (checked in `tests/test_features.py`). |
| `prep_time_minutes` | int | Pickup time minus order time, midnight-crossover corrected. Only three values occur: 5, 10, 15, in almost exactly equal thirds — see `docs/limitations.md`. |
| `delivery_time_minutes` | int | The outcome measure: total delivery time in minutes. |
| `sla_threshold_minutes` | numeric | Frozen category-level P75 of `delivery_time_minutes` (analyst-defined benchmark, not a company SLA). |
| `breach_flag` | 0/1 | `1` if `delivery_time_minutes > sla_threshold_minutes` (strict). Recomputed from the threshold and checked against the stored flag — 0 mismatches. |
| `minutes_over_sla` | numeric ≥ 0 | `max(0, delivery_time_minutes − sla_threshold_minutes)`: how late a breach is. |
| `category` | text | Product category (16 values). |
| `traffic` | text | `Low`, `Medium`, `High`, `Jam`. |
| `weather` | text | `Sunny`, `Cloudy`, `Fog`, `Windy`, `Stormy`, `Sandstorms`. |
| `area` | text | `Metropolitian` (spelling as stored in the source data — kept verbatim, not corrected), `Urban`, `Semi-Urban`, `Other` (not a formal tier). |
| `vehicle` | text | `motorcycle`, `scooter`, `van`. `bicycle` is documented in the raw file but has 0 rows after cleaning. |
| `agent_rating` | numeric 1–5, nullable | Rating associated with the delivery record. **Not an individual agent identifier** — no such identifier exists in the source data; every rating-based finding describes an attribute of the delivery, never a specific agent. Null for 54 rows. |
| `rating_lt_4_5` | 0/1, nullable | `1` if `agent_rating < 4.5`. Chosen because it is the single largest jump in breach rate between two adjacent rating values (`docs/analytical_findings.md` §2) — a data-driven cut, not an assumption. Null where `agent_rating` is null. |
| `agent_age` | int 20–39 | Age associated with the delivery record. Same attribute-level caveat as `agent_rating`. |
| `age_ge_30` | 0/1 | `1` if `agent_age >= 30`. Same data-driven-cut reasoning as `rating_lt_4_5`. |
| `distance_km` | numeric ≥ 0, nullable | Haversine store-to-drop distance. Null for the 3,651 rows with invalid store/drop coordinates. |

## Exclusion flags (kept in the data, excluded only from specific comparisons)

| Flag | Rows | Excluded from |
|---|---|---|
| No valid `agent_rating` | 54 | Rating-based comparisons |
| Invalid coordinates (`distance_km` unavailable) | 3,651 | Distance-based analysis |
| `area = Other` | 1,136 | Urban/Metropolitian/Semi-Urban tier comparisons only (still shown in every other cut) |
| `area = Semi-Urban` | 152 | The rating/age analysis population only (100% breach rate makes any stratified comparison degenerate) |

## PostgreSQL star schema

`FactDelivery` (43,648 rows, grain = one delivery) plus six dimensions: `DimAgent` (attribute-derived,
not a true agent entity — 444 distinct age/rating combinations), `DimArea`, `DimCategory`, `DimDate`
(44 rows, the observed dates only), `DimVehicle`, `DimWeatherTraffic` (24 rows, all 6×4 combinations
observed). Full column-level detail: `docs/archive/planning/STAR_SCHEMA.md`. Live-schema validation:
`sql/analysis/Q29_cross_validation_reconciliation.sql`.
