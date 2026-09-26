# Dataset Overview — RouteIQ

## Table of Contents
1. [Dataset Source](#dataset-source)
2. [Dataset License](#dataset-license)
3. [Structure](#structure)
4. [Column Descriptions](#column-descriptions)
5. [Dataset Quality Summary](#dataset-quality-summary)
6. [Expected Limitations](#expected-limitations)
7. [Missing Columns (vs. Business Need)](#missing-columns-vs-business-need)
8. [How Missing Fields Will Be Handled](#how-missing-fields-will-be-handled)

Related documents: `DATA_PROFILING_PLAN.md`, `DATA_CLEANING_PLAN.md`, `ASSUMPTIONS.md`, `SLA_METHODOLOGY.md`

All figures in this document are from a direct profiling run against the uploaded file `amazon_delivery.csv` (43,739 rows), not estimated or recalled from memory.

---

## Dataset Source

- **Name:** Amazon Delivery Dataset
- **Author:** sujalsuthar (Kaggle)
- **Link:** https://www.kaggle.com/datasets/sujalsuthar/amazon-delivery-dataset
- **Nature:** Real (not synthetic) last-mile e-commerce delivery records, India-based geography.
- **File used in this project:** `amazon_delivery.csv`, 43,739 rows, 16 columns (verified directly, not taken from the Kaggle listing description).

## Dataset License

**To be determined after analysis** — confirm the exact license (e.g., CC or Kaggle's default terms) directly on the Kaggle dataset page before publishing this project publicly on GitHub, and cite it explicitly in the repository README. Do not assume permissive reuse without checking.

## Structure

| Property | Value |
|---|---|
| Row count | 43,739 |
| Column count | 16 |
| Duplicate rows (full-row) | 0 |
| Duplicate `Order_ID` values | 0 (Order_ID is a reliable unique key) |
| Date range (`Order_Date`) | 2022-02-11 to 2022-04-06 (44 unique days, ~8 weeks) |

## Column Descriptions

| Column | Type (observed) | Description | Data Quality Notes |
|---|---|---|---|
| `Order_ID` | string | Unique order identifier | No duplicates observed; usable as primary key |
| `Agent_Age` | int64 | Delivery agent's age | Observed range needs plausibility check (see `DATA_PROFILING_PLAN.md`) |
| `Agent_Rating` | float64 | Agent's rating | 54 missing values; 53 rows have rating = 6.0, above a typical 1–5 scale ceiling |
| `Store_Latitude` / `Store_Longitude` | float64 | Pickup location coordinates | 3,693 rows fall outside a plausible India bounding box (includes `(0,0)` placeholder values) |
| `Drop_Latitude` / `Drop_Longitude` | float64 | Delivery location coordinates | 3,505 rows fall outside a plausible India bounding box |
| `Order_Date` | string (date) | Date order was placed | Clean, parses without error |
| `Order_Time` | string (time) | Time order was placed | 91 values fail strict `%H:%M:%S` parsing — these are the same rows with missing Weather/Traffic (see below) |
| `Pickup_Time` | string (time) | Time order was picked up | Same 91-row pattern to be confirmed during profiling |
| `Weather` | string (category) | Weather condition at delivery time | 91 true nulls (6 categories otherwise: Fog, Stormy, Cloudy, Sandstorms, Windy, Sunny) |
| `Traffic` | string (category) | Traffic condition | No true (pandas) nulls, but 91 rows contain the **literal string `"NaN "`** as a category value — this is a masked-missing pattern, not a real "NaN traffic" category |
| `Vehicle` | string (category) | Delivery vehicle type | 4 categories: motorcycle, scooter, van, bicycle; all have trailing whitespace |
| `Area` | string (category) | Delivery area type | 4 categories: Metropolitian [dataset's spelling], Urban, Semi-Urban, Other; all have trailing whitespace; `Other` (1,138 rows) is an ambiguous bucket |
| `Delivery_Time` | int64 | Actual delivery time in minutes (target/outcome field) | No zero/negative values; range 10–270 minutes, mean ~125, median 125 |
| `Category` | string (category) | Product category | 16 roughly evenly-distributed categories (~2,650–2,850 rows each) |

**Confirmed pattern:** the 91 rows with missing `Weather` and the 91 rows with `"NaN "` in `Traffic` are the **exact same 91 rows** (100% overlap) — this is a single missing-data event affecting both fields together, not two independent issues. Same rows are the likely source of the 91 `Order_Time` parse failures; this must be confirmed in `DATA_PROFILING_PLAN.md` before cleaning.

## Dataset Quality Summary

| Dimension | Finding |
|---|---|
| Completeness | High overall (16 columns, only Weather/Traffic/Agent_Rating have missingness, all under 0.2% of rows) |
| Uniqueness | Clean — no duplicate rows or Order_IDs |
| Validity | Moderate concerns — invalid coordinates (~8–9% of rows), an out-of-range Agent_Rating ceiling (53 rows at 6.0), trailing whitespace on every categorical field |
| Consistency | Category value spelling is internally consistent but contains a non-standard spelling (`Metropolitian`) that must be preserved as-is or explicitly normalized and documented, not silently "corrected" without a note |
| Timeliness | Not applicable — static historical dataset (Feb–Apr 2022), not live data |

## Expected Limitations

- **No SLA/promised-time field** — addressed in `SLA_METHODOLOGY.md`.
- **No cost/financial field** — financial impact statements must remain directional (per `ASSUMPTIONS.md`, A8).
- **Short date range (~8 weeks)** — limits the strength of any "trend" claim; week-over-week volatility findings must note the limited number of observable weeks.
- **Single geography style** — Indian metro/urban delivery context only; findings should not be generalized to other markets without caveat.
- **`Other` Area category is undefined** — 1,138 rows (2.6%) cannot be confidently assigned to Urban/Metropolitan/Semi-Urban.

## Missing Columns (vs. Business Need)

| Business Need | Column Required | Present? | Handling |
|---|---|---|---|
| SLA compliance measurement | `promised_time` / SLA target | **No** | Analyst-defined threshold — see `SLA_METHODOLOGY.md` |
| Cost-to-serve / financial impact | `cost`, `refund_amount` | **No** | Directional statements only — see `ASSUMPTIONS.md` A8 |
| Distance | `distance_km` | **No** (derivable from lat/long) | Engineered field — see `FEATURE_ENGINEERING.md` |
| True delivery zone | `zone_id` / geofence | **No** (proxy: `Area`) | Documented proxy — see `ASSUMPTIONS.md` A2 |
| Customer satisfaction / complaint flag | `complaint_flag`, `csat_score` | **No** | Out of scope — cannot be derived or fabricated |

## How Missing Fields Will Be Handled

No missing business field will be fabricated or estimated as if it were observed data. Where a field is required for a KPI defined in `KPI_DEFINITIONS.md`, it is either (a) engineered from existing fields with a documented formula (`FEATURE_ENGINEERING.md`), (b) replaced with an explicitly labeled analyst-defined business rule frozen before analysis (`SLA_METHODOLOGY.md`), or (c) the corresponding business question is answered qualitatively/directionally with the limitation stated plainly, never presented as a measured figure.
