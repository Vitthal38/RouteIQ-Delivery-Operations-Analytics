# Profiling Report — RouteIQ (Raw Dataset)

Generated: 2026-08-16 18:57:13

Source: `amazon_delivery.csv` (raw, unmodified). This report runs every check documented in `DATA_PROFILING_PLAN.md` programmatically and records the result — no row was modified or dropped to produce this report.

## Shape

| Property | Value |
|---|---|
| rows | 43739 |
| columns | 16 |

## Missing Values Profiling

| Column | Missing Count | Missing % |
|---|---|---|
| `Agent_Rating` | 54 | 0.12% |
| `Weather` | 91 | 0.21% |

**Masked-missing `Traffic` (`"NaN "` literal):** 91 rows

## Duplicate Profiling

| Check | Result |
|---|---|
| full_row_duplicates | 0 |
| order_id_duplicates | 0 |

## Outlier Profiling

- `Delivery_Time`: min=10.0, max=270.0, mean=124.91, median=125.0, std=51.92, zero/negative rows=0
- `Agent_Rating`: rows above valid ceiling (>5.0)=53, rows below valid floor (<1.0)=0
- `Agent_Age`: min=15, max=50, below plausible bound=38, above plausible bound=0

## Data Type Validation

| Column | Observed dtype |
|---|---|
| Order_ID | str |
| Agent_Age | int64 |
| Agent_Rating | float64 |
| Store_Latitude | float64 |
| Store_Longitude | float64 |
| Drop_Latitude | float64 |
| Drop_Longitude | float64 |
| Order_Date | str |
| Order_Time | str |
| Pickup_Time | str |
| Weather | str |
| Traffic | str |
| Vehicle | str |
| Area | str |
| Delivery_Time | int64 |
| Category | str |

## Categorical Profiling

### `Weather`

Distinct values: 6 | Rows with leading/trailing whitespace: 0

| Value | Count |
|---|---|
| `'Fog'` | 7440 |
| `'Stormy'` | 7374 |
| `'Cloudy'` | 7288 |
| `'Sandstorms'` | 7245 |
| `'Windy'` | 7223 |
| `'Sunny'` | 7078 |

### `Traffic`

Distinct values: 5 | Rows with leading/trailing whitespace: 43739

| Value | Count |
|---|---|
| `'Low '` | 14999 |
| `'Jam '` | 13725 |
| `'Medium '` | 10628 |
| `'High '` | 4296 |
| `'NaN '` | 91 |

### `Area`

Distinct values: 4 | Rows with leading/trailing whitespace: 42601

| Value | Count |
|---|---|
| `'Metropolitian '` | 32698 |
| `'Urban '` | 9751 |
| `'Other'` | 1138 |
| `'Semi-Urban '` | 152 |

### `Vehicle`

Distinct values: 4 | Rows with leading/trailing whitespace: 40181

| Value | Count |
|---|---|
| `'motorcycle '` | 25527 |
| `'scooter '` | 14639 |
| `'van'` | 3558 |
| `'bicycle '` | 15 |

### `Category`

Distinct values: 16 | Rows with leading/trailing whitespace: 0

| Value | Count |
|---|---|
| `'Electronics'` | 2849 |
| `'Books'` | 2824 |
| `'Jewelry'` | 2802 |
| `'Toys'` | 2781 |
| `'Skincare'` | 2772 |
| `'Snacks'` | 2770 |
| `'Outdoors'` | 2747 |
| `'Apparel'` | 2726 |
| `'Sports'` | 2719 |
| `'Grocery'` | 2691 |
| `'Pet Supplies'` | 2690 |
| `'Home'` | 2685 |
| `'Cosmetics'` | 2677 |
| `'Kitchen'` | 2673 |
| `'Clothing'` | 2667 |
| `'Shoes'` | 2666 |

## Numerical Profiling

| Column | Count | Min | Max | Mean | Median | Std |
|---|---|---|---|---|---|---|
| `Agent_Age` | 43739 | 15.0 | 50.0 | 29.57 | 30.0 | 5.82 |
| `Agent_Rating` | 43685 | 1.0 | 6.0 | 4.63 | 4.7 | 0.33 |
| `Delivery_Time` | 43739 | 10.0 | 270.0 | 124.91 | 125.0 | 51.92 |

## Coordinate Validation

Approximate India bounding box: latitude 6°-38°N, longitude 68°-98°E (per `DATA_PROFILING_PLAN.md`).

| Check | Result |
|---|---|
| store_outside_bounding_box | 3693 |
| store_outside_bounding_box_pct | 8.44 |
| drop_outside_bounding_box | 3505 |
| drop_outside_bounding_box_pct | 8.01 |
| combined_outside_bounding_box | 3693 |
| combined_outside_bounding_box_pct | 8.44 |
| store_exact_zero_zero | 3505 |
| drop_exact_zero_zero | 0 |

## Datetime Validation

| Check | Result |
|---|---|
| order_date_parse_failures | 0 |
| order_date_min | 2022-02-11 |
| order_date_max | 2022-04-06 |
| order_date_unique_days | 44 |
| order_time_parse_failures | 91 |
| pickup_time_parse_failures | 0 |
| weather_null_equals_traffic_masked | True |
| weather_null_equals_order_time_fail | True |
| cluster_row_count | 91 |

## Memory Usage

| Property | Value |
|---|---|
| rows | 43739 |
| columns | 16 |
| total_memory_mb | 23.987 |

## Profiling Checklist (DATA_PROFILING_PLAN.md)

- [x] Confirm row-level overlap between missing Weather, masked Traffic, and unparseable Order_Time: Weather<->Traffic overlap = True, Weather<->Order_Time overlap = True
- [x] Agent_Age plausibility bound documented (see `DATA_CLEANING_PLAN.md` Step 6: 18-65)
- [x] Agent_Rating bound-violation handling documented (see `DATA_CLEANING_PLAN.md` Step 4)
- [x] Coordinate bounding-box exclusion rule documented (see `DATA_CLEANING_PLAN.md` Step 7)
- [x] Whitespace-trim + `Metropolitian` spelling handling documented (see `DATA_CLEANING_PLAN.md` Steps 1 & 9)
- [x] `Area = Other` handling documented (see `DATA_CLEANING_PLAN.md` Step 8)
- [ ] Re-run this full profile after cleaning — done separately in `validation_report.md` (STEP 7), which diffs against these before-state figures
