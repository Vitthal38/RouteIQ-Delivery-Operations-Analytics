# Cleaning Log — RouteIQ

Cleaning Run: 2026-08-16 18:57:14

Follows `DATA_CLEANING_PLAN.md` Steps 1-9 in their documented execution order.

```
Cleaning Run: 2026-08-16 18:57:14
Input rows: 43,739
Step 1 (whitespace trim): applied to ['Traffic', 'Vehicle', 'Area', 'Weather', 'Category'], 0 rows removed
Step 2 (Traffic NaN recode): 91 values recoded
Step 3 (91-row cluster exclusion): 91 rows removed, reason: missing Weather / masked-missing Traffic (confirmed row-level overlap with Order_Time parse failures)
Step 4 (Agent_Rating >5 flag): 0 rows flagged, excluded from KPI #6 only
Step 5 (Agent_Rating null flag): 54 rows flagged, excluded from KPI #6 only
Step 6 (Agent_Age implausible flag, bound=18-65): 0 rows flagged, excluded from age-specific analysis only
Step 7 (coordinate bounding-box flag): 3651 rows flagged, excluded from distance analysis only
Step 8 (Area=Other handling): 1136 rows retained, excluded from area-tier comparison only
Step 9 (Metropolitian spelling): Preserved source spelling 'Metropolitian' in the Area column (no data mutation). Display-label mapping to 'Metropolitan' is deferred to the dashboard/documentation layer, per DATA_CLEANING_PLAN.md Step 9.
Output rows (full-exclusion applied): 43,648
Output rows (available for distance analysis): 39,997
Output rows (available for agent-rating analysis): 43,594
```

**Important note on Step 4/Step 6 counts:** the 91-row cluster excluded in Step 3 happens to contain all 53 raw occurrences of `Agent_Rating = 6.0` and all rows with `Agent_Age < 18` (the dataset's own min/max extremes, 15 and 50, are concentrated in this corrupted-row cluster alongside the missing Weather/Traffic values). This is why Steps 4 and 6 flag 0 *additional* rows in the post-Step-3 dataset — it is a real, observed consequence of applying the documented step order, not a rule change. The raw-dataset counts (53 and 15/50) are preserved as-is in `profiling_report.md`.

## Rows to Remove (full exclusion)

| Step | Rows Affected | Reason | Removed From |
|---|---|---|---|
| Step 3 | 91 | missing Weather / masked-missing Traffic (confirmed row-level overlap with Order_Time parse failures) | Full analysis dataset |

All other flagged issues (Steps 4-8) result in **conditional exclusion from specific analyses only**, per `DATA_CLEANING_PLAN.md` — rows are retained with a boolean flag, not removed from the dataset.

## Values Imputed

**None.** No field was imputed with a substitute value, per `DATA_CLEANING_PLAN.md` > Values to Impute. Every missingness/invalidity issue was handled via flagging, conditional exclusion, or full-row exclusion (Step 3 only).

## Feature Engineering Summary (FEATURE_ENGINEERING.md fields 1-8)

| Metric | Value |
|---|---|
| distance_km_eligible_rows | 39997 |
| distance_km_null_rows | 3651 |
| sla_reference_category_count | 16 |
| overall_sla_breach_rate_pct | 23.66 |
| distinct_iso_weeks | 8 |
| prep_time_negative_count | 0 |

**Note on `delivery_bucket` (field 4):** bin edges use FEATURE_ENGINEERING.md #4's own documented illustrative scheme (0-60, 61-120, 121-180, 181+ minutes), the only concrete scheme provided in that document. Final EDA-based bin-edge confirmation is explicitly deferred to Phase 2 (`PYTHON_ANALYSIS_PLAN.md`), which is out of scope for this Phase 1 implementation — this is flagged here rather than silently finalized.

## Rollback Strategy

The raw `amazon_delivery.csv` is retained unmodified at the project root and archived read-only under `data/raw/`. All transformations above are applied to an in-memory copy and written to `data/cleaned/` — the raw source is never overwritten, per `DATA_CLEANING_PLAN.md`'s Rollback Strategy.
