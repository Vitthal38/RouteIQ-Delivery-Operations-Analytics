# Data Cleaning Plan — RouteIQ

## Table of Contents
1. [Purpose](#purpose)
2. [Cleaning Rules (in execution order)](#cleaning-rules-in-execution-order)
3. [Rows to Remove](#rows-to-remove)
4. [Values to Impute](#values-to-impute)
5. [Validation After Cleaning](#validation-after-cleaning)
6. [Cleaning Log Template](#cleaning-log-template)
7. [Rollback Strategy](#rollback-strategy)

Related documents: `DATA_PROFILING_PLAN.md` (source of every issue referenced here), `FEATURE_ENGINEERING.md` (consumes the cleaned output), `ASSUMPTIONS.md`

**Process rule:** every transformation below references a specific finding already documented in `DATA_PROFILING_PLAN.md`. No new issue may be "discovered and fixed" silently during coding — if a future session finds something not listed here, it goes back into the profiling document first.

---

## Cleaning Rules (in execution order)

Order matters — several rules depend on a prior step having run.

### Step 1 — Trim whitespace on all categorical fields
- **Applies to:** `Traffic`, `Vehicle`, `Area` (and defensively, `Weather`, `Category`).
- **Why:** Profiling found trailing whitespace causing category fragmentation (e.g., `"High "` vs a hypothetical `"High"`).
- **Transformation:** `.str.strip()` on each field.
- **Why this exists (business reasoning):** Without this step, every group-by KPI (breach rate by traffic, by area) would be silently wrong — values would look distinct that are actually the same category.

### Step 2 — Recode masked-missing `Traffic` values
- **Applies to:** `Traffic`.
- **Why:** Profiling found the literal string `"NaN "` used in place of a true missing value.
- **Transformation:** After Step 1 trimming, recode the string `"NaN"` to a true null/NA value.
- **Why this exists:** A true null can be counted, filtered, and handled consistently; a string `"NaN"` would otherwise be silently treated as a valid traffic condition category.

### Step 3 — Confirm and handle the 91-row missing-data cluster (Weather / Traffic / Order_Time / Pickup_Time)
- **Applies to:** `Weather`, `Traffic` (post Step 2), `Order_Time`, `Pickup_Time`.
- **Why:** Profiling confirmed 91 rows share missing Weather and masked-missing Traffic; time-field overlap is suspected but not yet confirmed.
- **Transformation:** Confirm overlap via row-index intersection. For confirmed overlapping rows: **exclude from analysis** (documented decision — see rationale below), tagged with a specific exclusion reason in the cleaning log, not silently dropped.
- **Why this exists (business reasoning):** These rows are missing exactly the fields most central to the root-cause analysis (weather/traffic conditions, and potentially timing). Imputing "typical" weather/traffic for a real historical delivery would fabricate a condition that may not have occurred, corrupting the very analysis (weather/traffic significance testing) this project is built around. Exclusion of <0.25% of rows is a low-cost, honest choice versus a higher-risk imputation.

### Step 4 — Resolve `Agent_Rating` bound violation
- **Applies to:** `Agent_Rating`.
- **Why:** Profiling found 53 rows at exactly 6.0, above the assumed 1–5 rating scale.
- **Transformation:** Flag rows where `Agent_Rating > 5` as a data-entry error; **exclude from agent-rating-dependent analysis** (KPI #6 in `KPI_DEFINITIONS.md`) but retain in all other analyses (delivery time, breach rate, etc. do not depend on this field).
- **Why this exists:** A rating of 6.0 is not a legitimate extreme value on a 1–5 scale — it is more consistent with a data-entry error than a real signal, so it should not silently pull the mean/correlation in one KPI while remaining valid for unrelated ones.

### Step 5 — Handle missing `Agent_Rating` (54 true nulls, distinct from Step 4)
- **Applies to:** `Agent_Rating`.
- **Why:** Profiling found 54 true nulls, separate from the 53 out-of-range rows.
- **Transformation:** Retain rows, add an `agent_rating_available` boolean flag; exclude only from the specific agent-rating KPI, same treatment as Step 4.
- **Why this exists:** Delivery-time analysis for these rows is still valid — only the rating-dependent KPI needs to exclude them.

### Step 6 — Validate and flag `Agent_Age`
- **Applies to:** `Agent_Age`.
- **Why:** Profiling found a minimum of 15, implausible for a delivery agent.
- **Transformation:** Apply plausibility bound (e.g., 18–65); flag rows outside bound. Given this is a minor supporting field (not central to any core KPI), flag and report the count rather than excluding rows from the full dataset — exclude only from age-specific analysis (Business Question 15).
- **Why this exists:** An implausible value shouldn't silently distort an age-based finding, but also doesn't warrant losing the row's otherwise-valid delivery-time data.

### Step 7 — Validate coordinates
- **Applies to:** `Store_Latitude/Longitude`, `Drop_Latitude/Longitude`.
- **Why:** Profiling found 8–9% of rows with coordinates outside a plausible India bounding box, including exact `(0,0)` placeholders.
- **Transformation:** Flag rows outside the bounding box; **exclude from `distance_km` calculation and any distance-dependent analysis**; retain for all non-distance analyses (weather/traffic/area/agent breach analysis does not require valid coordinates).
- **Why this exists:** A distance calculated from an invalid coordinate is not "a bad distance," it is a meaningless one — treating it as data would corrupt the distance–delivery-time correlation analysis specifically named in the business questions.

### Step 8 — Decide `Area = "Other"` handling
- **Applies to:** `Area`.
- **Why:** Profiling found 1,138 rows (2.6%) in an undefined `Other` bucket.
- **Transformation:** Retain in the dataset (not excluded — no evidence it's invalid, just unlabeled), but **exclude from area-tier comparisons** (Urban/Metropolitan/Semi-Urban framing) since it cannot be meaningfully placed in that ordinal structure; report its aggregate stats separately if material.
- **Why this exists:** Excluding it entirely would lose real delivery-time observations; folding it into another tier without evidence would misrepresent it.

### Step 9 — Decide `Metropolitian` spelling handling
- **Applies to:** `Area`.
- **Why:** Profiling found this is the dataset's own spelling.
- **Transformation:** **Preserve source spelling** in the underlying data; use "Metropolitan" only in human-readable dashboard labels/documentation prose, with a footnote noting the source data's spelling if the raw value is ever shown directly (e.g., in a data dictionary).
- **Why this exists:** Silently "correcting" source data values (versus display labels) risks a values mismatch between the documented dataset and the actual stored data — cleaner to separate storage value from display label.

## Rows to Remove

| Step | Rows Affected | Reason | Removed From |
|---|---|---|---|
| Step 3 | 91 (pending row-level confirmation) | Missing Weather + masked-missing Traffic (+ possible time-field issues) | Full analysis dataset |

All other flagged issues (Steps 4–9) result in **conditional exclusion from specific analyses**, not full-dataset row removal — this distinction is deliberate and must be preserved in implementation, not collapsed into a single blanket filter.

## Values to Impute

**None.** No field in this plan is imputed with a substitute value. Every missingness/invalidity issue is handled via flagging, conditional exclusion, or full-row exclusion (Step 3 only) — never by filling in an estimated value presented as if observed. This is a deliberate, conservative choice consistent with the project's no-fabrication rule.

## Validation After Cleaning

Re-run the full `DATA_PROFILING_PLAN.md` checklist against the cleaned dataset and confirm:
- [ ] 0 rows with masked-missing `"NaN "` Traffic remaining
- [ ] 0 rows with trailing whitespace in any categorical field
- [ ] 0 rows with `Agent_Rating > 5` included in agent-rating KPI calculations
- [ ] 0 rows with out-of-bounding-box coordinates included in `distance_km`/distance-correlation calculations
- [ ] Row count accounted for: 43,739 (raw) − 91 (Step 3 exclusion) = expected clean-dataset row count, explicitly stated in the cleaning log
- [ ] Every KPI in `KPI_DEFINITIONS.md` recalculated on cleaned data and spot-checked for plausibility (e.g., breach rate is between 0–100%, not negative or >100%)

## Cleaning Log Template

Every cleaning run must produce a log entry in this format (to be stored alongside the cleaned dataset, e.g., `docs/technical/cleaning_log.md` or a run manifest):

```
Cleaning Run: [date/time]
Input rows: 43,739
Step 1 (whitespace trim): applied to [columns], 0 rows removed
Step 2 (Traffic NaN recode): [N] values recoded
Step 3 (91-row cluster exclusion): [N] rows removed, reason: missing Weather/Traffic
Step 4 (Agent_Rating >5 flag): [N] rows flagged, excluded from KPI #6 only
Step 5 (Agent_Rating null flag): [N] rows flagged, excluded from KPI #6 only
Step 6 (Agent_Age implausible flag): [N] rows flagged, excluded from age-specific analysis only
Step 7 (coordinate bounding-box flag): [N] rows flagged, excluded from distance analysis only
Step 8 (Area=Other handling): [N] rows retained, excluded from area-tier comparison only
Step 9 (Metropolitian spelling): preserved in data, display-label mapping applied in [dashboard/docs]
Output rows (full-exclusion applied): [N]
Output rows (available for distance analysis): [N]
Output rows (available for agent-rating analysis): [N]
Validation checklist: [pass/fail per item above]
```

## Rollback Strategy

- The raw, unmodified `amazon_delivery.csv` is retained as-is in `data/raw/` (per the GitHub folder structure in the project brief) and is never overwritten.
- All cleaning transformations are applied to a copy, written to `data/cleaned/`, so the pipeline can be re-run from raw at any time if a cleaning decision is revisited.
- Any change to a cleaning rule after this document is approved must be a new dated entry (not an edit that erases the prior rule), consistent with `CHANGELOG.md` practice — this preserves the audit trail for interview defensibility ("why did you exclude these rows" must always be answerable from the log).
