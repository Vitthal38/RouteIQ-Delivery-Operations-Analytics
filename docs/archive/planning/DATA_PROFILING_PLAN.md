# Data Profiling Plan — RouteIQ

## Table of Contents
1. [Purpose](#purpose)
2. [Missing Values Profiling](#missing-values-profiling)
3. [Duplicate Profiling](#duplicate-profiling)
4. [Outlier Profiling](#outlier-profiling)
5. [Data Type Validation](#data-type-validation)
6. [Categorical Profiling](#categorical-profiling)
7. [Numerical Profiling](#numerical-profiling)
8. [Coordinate Validation](#coordinate-validation)
9. [Datetime Validation](#datetime-validation)
10. [Memory Usage Checks](#memory-usage-checks)
11. [Profiling Checklist](#profiling-checklist)

Related documents: `DATASET_OVERVIEW.md` (findings this plan formalizes), `DATA_CLEANING_PLAN.md` (what happens after profiling), `ASSUMPTIONS.md`

**Process rule this document enforces:** profiling happens in full, and is documented, **before** any row is modified or dropped. `DATA_CLEANING_PLAN.md` may only reference issues that were first identified here.

---

## Purpose

To establish a complete, evidence-based picture of data quality before any transformation, so cleaning decisions are traceable to a specific profiling finding rather than made ad hoc during coding. This also gives any future Claude Code session a fixed reference instead of re-discovering (and potentially re-deciding differently) the same issues.

## Missing Values Profiling

| Column | Missing Count | Missing % | Notes |
|---|---|---|---|
| `Weather` | 91 | 0.21% | True (pandas-recognized) null |
| `Traffic` | 91 (masked) | 0.21% | Not a true null — literal string `"NaN "` used as a category value |
| `Agent_Rating` | 54 | 0.12% | True null |
| All other columns | 0 | 0% | — |

**Confirmed:** the 91 missing `Weather` rows and the 91 `"NaN "` `Traffic` rows are the same 91 rows (100% overlap, verified). **To be determined during cleaning-stage profiling:** whether these same 91 rows also account for the 91 `Order_Time` values that fail strict time parsing (see Datetime Validation) — high likelihood given the pattern, but must be confirmed by row-level join, not assumed from matching counts alone.

**Missing Values Strategy (decision, to be executed in `DATA_CLEANING_PLAN.md`):**
- Recode literal `"NaN "` in `Traffic` to a true missing value first — otherwise it will not be caught by standard null-handling logic.
- Given the very low missingness rate (<0.25% for all three fields) and the confirmed overlap, the default strategy is **row exclusion with logged count and rationale**, not imputation — imputing Weather/Traffic (external, uncontrollable conditions) would fabricate a condition that didn't necessarily occur. `Agent_Rating` missingness may instead be **retained with a "rating unavailable" flag** rather than dropped, since dropping would also lose otherwise-valid delivery-time observations for unrelated analyses. Final decision documented in `DATA_CLEANING_PLAN.md`.

## Duplicate Profiling

| Check | Result |
|---|---|
| Full-row duplicates | 0 |
| Duplicate `Order_ID` | 0 |

**Duplicate Strategy:** No duplicates exist in the current extract. Retain a duplicate-check step in the pipeline regardless (defensive profiling), so any future re-run against an updated extract of this dataset doesn't silently ingest duplicates unnoticed.

## Outlier Profiling

| Field | Method | Finding |
|---|---|---|
| `Delivery_Time` | Range check | Min 10, Max 270, mean ~125, median 125, std ~52 — no zero/negative values; distribution to be visually confirmed (histogram) in EDA, not just described numerically here |
| `Agent_Rating` | Plausible-range check (1–5 scale assumed) | 53 rows at exactly 6.0 — above assumed scale ceiling; 0 rows below 1 |
| `Agent_Age` | Plausible-range check (working-age assumption) | Minimum observed value of 15 is implausible for a delivery agent — needs explicit threshold decision (e.g., flag <18) in cleaning |

**Outlier Strategy:** Outliers are **flagged and reported**, not silently removed, unless they are physically impossible (e.g., Agent_Rating = 6.0 on an assumed 1–5 scale is impossible, not just extreme — this is a data-entry/scale error, not a legitimate outlier). Physically-plausible extreme values (e.g., a genuinely very long `Delivery_Time`) are retained, since removing them would bias the SLA/breach analysis exactly where it matters most (the tail is the point of tracking P90).

## Data Type Validation

| Column | Expected Type | Observed Type | Action Needed |
|---|---|---|---|
| `Order_ID` | string | string (object) | None |
| `Agent_Age` | integer | int64 | None, but apply plausibility bound (see Outlier Profiling) |
| `Agent_Rating` | float, bounded [1,5] | float64, observed max 6.0 | Bound violation to resolve in cleaning |
| `Store_/Drop_Latitude/Longitude` | float, geographic bounds | float64 | Bound-check required (see Coordinate Validation) |
| `Order_Date` | date | string, parses cleanly to datetime | Cast to date type |
| `Order_Time` / `Pickup_Time` | time | string, 91 unparseable | Cast to time type after resolving the 91 masked-missing rows |
| `Weather` / `Traffic` / `Vehicle` / `Area` / `Category` | categorical string | string (object), with whitespace and masked-null issues | Trim + recode before treating as clean categorical |
| `Delivery_Time` | integer (minutes) | int64 | None |

## Categorical Profiling

| Column | Distinct Values (raw, untrimmed) | Notes |
|---|---|---|
| `Weather` | 6 + null | Fog, Stormy, Cloudy, Sandstorms, Windy, Sunny |
| `Traffic` | 4 + masked-null | Low, Jam, Medium, High (all with trailing space) + `"NaN "` |
| `Area` | 4 | Metropolitian [sic], Urban, Semi-Urban, Other — all with trailing space except Other |
| `Vehicle` | 4 | motorcycle, scooter, van, bicycle — trailing space on 3 of 4 |
| `Category` | 16 | Roughly even distribution (~2,650–2,850 rows each), no missing |

**Note on `Metropolitian`:** this is the dataset's own spelling (not a typo introduced by this documentation). Decision needed in `DATA_CLEANING_PLAN.md`: preserve as-is (matches source data, avoids introducing a new inconsistency) versus normalize to "Metropolitan" for readability — either is acceptable if documented, but it must be a stated decision, not silent.

## Numerical Profiling

| Column | Min | Max | Mean | Median | Std |
|---|---|---|---|---|---|
| `Agent_Age` | 15 | 50 | To be finalized in cleaning-stage profiling | — | — |
| `Agent_Rating` | 1.0 | 6.0 | 4.63 | 4.7 | 0.33 |
| `Delivery_Time` | 10 | 270 | 124.9 | 125 | 51.9 |

## Coordinate Validation

Using an approximate India bounding box (latitude 6°–38°N, longitude 68°–98°E) as the plausibility check:

| Field | Rows Outside Bounding Box | % of Dataset |
|---|---|---|
| Store coordinates | 3,693 | 8.4% |
| Drop coordinates | 3,505 | 8.0% |

This includes exact `(0,0)` placeholder coordinates as a subset. **Validation method:** any row with store or drop coordinates outside the bounding box is flagged before `distance_km` is computed (see `FEATURE_ENGINEERING.md`) — computing haversine distance on an invalid coordinate would silently produce a large, meaningless distance value that would corrupt every distance-dependent KPI.

## Datetime Validation

| Field | Parse Failures | Likely Cause |
|---|---|---|
| `Order_Date` | 0 | Clean |
| `Order_Time` | 91 | Suspected to match the 91 rows with masked-missing Weather/Traffic — **to be confirmed by row-level check**, not assumed |
| `Pickup_Time` | To be determined | Same check to be run |

**Validation method:** confirm via direct row-index intersection (not just matching counts) that the Order_Time parse failures are the same 91 rows already identified as missing Weather/Traffic, before deciding whether this is one data-quality event or several independent ones.

## Memory Usage Checks

At 43,739 rows × 16 columns, this dataset is small (low single-digit MB in memory) — no chunked processing, sampling, or distributed compute is needed at any stage. Documented explicitly to preempt an unnecessary Spark/Snowflake tooling decision (see `PROJECT_CHARTER.md` constraints).

## Profiling Checklist

- [ ] Confirm row-level overlap between missing Weather, masked Traffic, and unparseable Order_Time/Pickup_Time
- [ ] Decide and document Agent_Age plausibility bound
- [ ] Decide and document Agent_Rating bound-violation handling (53 rows at 6.0)
- [ ] Decide and document coordinate bounding-box exclusion rule
- [ ] Decide and document whitespace-trim + `Metropolitian` spelling handling
- [ ] Decide and document `Area = Other` handling (retain/exclude/footnote)
- [ ] Re-run this full profile after cleaning and confirm all flagged issues are resolved, with before/after counts recorded in `DATA_CLEANING_PLAN.md`
