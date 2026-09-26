# Feature Engineering Plan — RouteIQ

## Table of Contents
1. [Purpose](#purpose)
2. [distance_km](#1-distance_km)
3. [sla_threshold_minutes](#2-sla_threshold_minutes)
4. [sla_breach_flag](#3-sla_breach_flag)
5. [delivery_bucket](#4-delivery_bucket)
6. [day_of_week](#5-day_of_week)
7. [order_hour](#6-order_hour)
8. [week_number](#7-week_number)
9. [prep_time_minutes](#8-prep_time_minutes)
10. [Validation Checklist Summary](#validation-checklist-summary)

Related documents: `DATA_CLEANING_PLAN.md` (this stage's input), `SLA_METHODOLOGY.md` (full detail on the SLA rule referenced in fields 2–3), `KPI_DEFINITIONS.md` (KPIs consuming these fields)

**Process rule:** every field below is derived only from columns already present in the cleaned dataset — no field introduces external or assumed data not traceable to a source column.

---

## 1. `distance_km`

- **Business Logic:** Straight-line (great-circle) distance between store/pickup location and drop/delivery location. Used as a candidate delay driver — does a longer delivery distance explain more of the delay than conditions like weather/traffic.
- **Formula (Haversine):**
  ```
  a = sin²(Δlat/2) + cos(lat1) · cos(lat2) · sin²(Δlon/2)
  c = 2 · atan2(√a, √(1−a))
  distance_km = R · c   (R = 6371 km, Earth's mean radius)
  ```
  where `(lat1, lon1)` = `(Store_Latitude, Store_Longitude)` and `(lat2, lon2)` = `(Drop_Latitude, Drop_Longitude)`.
- **Dependencies:** `Store_Latitude`, `Store_Longitude`, `Drop_Latitude`, `Drop_Longitude`; requires `DATA_CLEANING_PLAN.md` Step 7 (coordinate bounding-box flag) applied first.
- **Validation:**
  - [ ] Result is always ≥ 0.
  - [ ] Result is `NaN`/excluded (not calculated) for any row flagged as having an out-of-bounding-box coordinate.
  - [ ] Spot-check 5 random rows against a manual map-based distance estimate for plausibility.
- **Edge Cases:**
  - Identical store/drop coordinates → `distance_km = 0`, valid (very short/local delivery), not an error.
  - Coordinates flagged in cleaning (e.g., `(0,0)`) → field is left null/excluded, never computed, to avoid a large meaningless distance silently entering the dataset.
- **Example Calculation:** Using row 1 of the dataset (Store: 22.745049, 75.892471; Drop: 22.765049, 75.912471) — a small lat/lon delta (~0.02° in each direction) — the haversine formula yields a distance on the order of a few kilometers, consistent with an intra-city delivery. Exact figure to be computed and recorded during implementation, not pre-stated here.

## 2. `sla_threshold_minutes`

- **Business Logic:** Since no promised-time field exists, this is the analyst-defined delivery-time benchmark used to classify a delivery as on-time or breached. Full derivation, justification, and freeze process are in `SLA_METHODOLOGY.md` — this entry documents only the mechanical formula, and must mirror that document's frozen definition exactly.
- **Formula:** `sla_threshold_minutes = PERCENTILE(Delivery_Time, 0.75) within Category` — the category-level 75th percentile (P75) of `Delivery_Time`, calculated once on the full cleaned dataset and frozen before any breach analysis is run. This is not recalculated after breach results are viewed, and no buffer term is added — see `SLA_METHODOLOGY.md`'s Frozen SLA Definition for the authoritative statement and Alternatives Considered table for why the median + fixed-minute buffer option (Option B) was evaluated and rejected in favor of P75 (Option C).
- **Dependencies:** Cleaned `Delivery_Time`, cleaned `Category`.
- **Validation:**
  - [ ] Threshold is calculated once, on the full cleaned dataset, and frozen — never recalculated after breach results are viewed (hard rule, see `SLA_METHODOLOGY.md`).
  - [ ] Threshold value per category is documented in a static reference table, not recalculated at query time in every dashboard refresh (to guarantee SQL/Python/Power BI consistency), and is the single value `sla_breach_flag` (field 3 below) reads from — never recomputed independently downstream.
- **Edge Cases:** A `Category` with very few observations could produce an unstable P75 — check category-level row counts before finalizing; profiling shows all 16 categories have ~2,650–2,850 rows, so this is not expected to be a practical issue here, but the check is still documented as a safeguard.
- **Example Calculation:** **To be determined after analysis** — the category-level P75 and resulting threshold are computed once cleaning is complete, not estimated in advance.

## 3. `sla_breach_flag`

- **Business Logic:** Boolean flag marking whether a delivery exceeded its category's frozen SLA threshold — the core field the entire breach-rate/OTD% KPI set depends on.
- **Formula:** `sla_breach_flag = 1 if Delivery_Time > sla_threshold_minutes (for that row's Category) else 0`
- **Dependencies:** `sla_threshold_minutes` (must be frozen first), cleaned `Delivery_Time`.
- **Validation:**
  - [ ] `sla_breach_flag` recalculated identically in SQL, Python, and DAX and cross-checked to match row-for-row (or aggregate-for-aggregate) — this is the single most important cross-validation in the whole project, since every headline KPI depends on it.
  - [ ] Overall breach rate is sanity-checked as a plausible percentage (not near 0% or near 100%, which would suggest a threshold-definition error).
- **Edge Cases:** `Delivery_Time` exactly equal to the threshold is classified as **not breached** (`<=` is on-time) — this boundary rule must be applied consistently everywhere the flag is calculated.
- **Example Calculation:** **To be determined after analysis**, once `sla_threshold_minutes` is frozen.

## 4. `delivery_bucket`

- **Business Logic:** Groups `Delivery_Time` into readable bands (e.g., 0–60, 61–120, 121–180, 181+ minutes) for dashboard visuals where a continuous distribution is less readable than discrete bands.
- **Formula:** Fixed-width binning of `Delivery_Time`, exact bin edges to be finalized alongside the EDA histogram review (bin edges should reflect the actual observed distribution shape — min 10, max 270 — not be chosen arbitrarily before seeing it).
- **Dependencies:** Cleaned `Delivery_Time`.
- **Validation:** [ ] Every row falls into exactly one bucket; [ ] bucket boundaries documented once finalized so SQL/Python/Power BI use identical cut points.
- **Edge Cases:** Boundary values (e.g., exactly 60) must consistently fall into one specific bucket (documented as part of the finalized bin definition).
- **Example Calculation:** A `Delivery_Time` of 45 → bucket "0–60 minutes" under the illustrative scheme above; final scheme to be confirmed post-EDA.

## 5. `day_of_week`

- **Business Logic:** Supports the business question "do weekend orders take longer than weekday orders."
- **Formula:** Derived from `Order_Date` (e.g., Monday–Sunday, plus a boolean `is_weekend`).
- **Dependencies:** Cleaned/parsed `Order_Date`.
- **Validation:** [ ] Spot-check a few known dates in the range (e.g., 2022-02-11) against a calendar to confirm correct day-of-week mapping.
- **Edge Cases:** None expected — `Order_Date` had 0 parse failures in profiling.
- **Example Calculation:** 2022-02-11 → Friday (to be confirmed programmatically, not asserted here).

## 6. `order_hour`

- **Business Logic:** Supports time-window-based delay analysis (e.g., is there a specific hour-of-day pattern in breach concentration).
- **Formula:** Extracted hour component from parsed `Order_Time`.
- **Dependencies:** Cleaned `Order_Time` (post `DATA_CLEANING_PLAN.md` Step 3 resolution of the 91-row parsing issue).
- **Validation:** [ ] Value range strictly 0–23; [ ] rows excluded in Step 3 do not silently produce a spurious hour value (e.g., default to 0).
- **Edge Cases:** The 91 rows with unparseable `Order_Time` must be excluded from this field too, not defaulted to midnight or any other placeholder.
- **Example Calculation:** `Order_Time = "11:30:00"` → `order_hour = 11`.

## 7. `week_number`

- **Business Logic:** Supports the week-over-week volatility KPI.
- **Formula:** ISO week number derived from `Order_Date`.
- **Dependencies:** Cleaned/parsed `Order_Date`.
- **Validation:** [ ] Confirm total distinct week count matches the expected span given the observed ~8-week date range (2022-02-11 to 2022-04-06); [ ] first and last week are checked for partial-week bias (a week with only 1–2 days of data could look artificially low/high in a trend chart) and flagged in the trend narrative if relevant.
- **Edge Cases:** Partial first/last weeks — must be either excluded from the week-over-week trend or clearly annotated, not treated as a full week's data.
- **Example Calculation:** 2022-02-11 → ISO week 6 of 2022 (to be confirmed programmatically).

## 8. `prep_time_minutes`

- **Business Logic:** Time between order placement and pickup (`Pickup_Time − Order_Time`) — separates "store/prep delay" from "in-transit delay," refining root-cause attribution beyond `Delivery_Time` alone.
- **Formula:** `prep_time_minutes = Pickup_Time − Order_Time` (in minutes), handling any midnight-crossover cases where `Pickup_Time < Order_Time` by adding 24 hours before subtracting.
- **Dependencies:** Cleaned `Order_Time`, `Pickup_Time`.
- **Validation:** [ ] Result is never negative after midnight-crossover correction is applied; [ ] distribution reviewed for implausibly large values that might indicate a data issue rather than a real long prep time.
- **Edge Cases:** Midnight crossover (e.g., Order_Time 23:50, Pickup_Time 00:05) — explicitly handled, not left as a large negative number. Rows in the 91-row excluded cluster are excluded here too.
- **Example Calculation:** `Order_Time = "11:30:00"`, `Pickup_Time = "11:45:00"` → `prep_time_minutes = 15`.

## Validation Checklist Summary

| Field | Depends On Cleaning Step | Cross-Validation Required (SQL/Python/DAX) |
|---|---|---|
| `distance_km` | Step 7 (coordinates) | Yes — feeds distance-correlation KPI |
| `sla_threshold_minutes` | Steps 1–6 (clean Delivery_Time/Category) | Yes — frozen value must match across all layers |
| `sla_breach_flag` | `sla_threshold_minutes` | Yes — highest priority, feeds every headline KPI |
| `delivery_bucket` | Clean `Delivery_Time` | Yes — bin edges must match exactly |
| `day_of_week` | Clean `Order_Date` | Low risk, spot-check only |
| `order_hour` | Step 3 (Order_Time resolution) | Low risk, spot-check only |
| `week_number` | Clean `Order_Date` | Yes — affects trend KPI, check partial-week bias |
| `prep_time_minutes` | Step 3 (time fields) | Yes — check midnight-crossover handling specifically |
