# Validation Report — RouteIQ (Python Phase 1)

Generated: 2026-08-16 18:57:14

**Overall gate: PASS** — 19/19 checks passed.

This report runs every check from `VALIDATION_CHECKLIST.md` / `TESTING_PLAN.md` that applies to Python Phase 1 (cleaning + feature engineering) scope. Checks that depend on a SQL, DAX, or Power BI layer are listed separately as **not applicable** — this Phase 1 scope does not build SQL, DAX, or Power BI per the task boundary.

## Dataset Validation

| Status | Check | Detail |
|---|---|---|
| PASS | Raw row/column count matches DATASET_OVERVIEW.md | Observed shape (43739, 16), expected (43739, 16) |
| PASS | Missingness figures reproduced exactly (91/91/54) | Weather nulls=91, masked Traffic=91, Agent_Rating nulls=54 |
| PASS | Duplicate check reproduced (0 full-row, 0 Order_ID) | full-row dup=0, Order_ID dup=0 |
| PASS | Cleaned row count reconciles (43,739 - Step 3 exclusion) | Cleaned rows=43648, expected=43648 |
| PASS | All conditional-exclusion flags present and non-null | Flags checked: ['coordinates_valid_flag', 'agent_rating_valid_flag', 'agent_age_valid_flag', 'area_tier_valid_flag'] |

## Python Phase 1 Validation Gate

| Status | Check | Detail |
|---|---|---|
| PASS | Zero rows with masked 'NaN' Traffic remain | Remaining masked-null Traffic rows: 0 |
| PASS | Zero rows with trailing whitespace in any categorical column | Remaining rows with whitespace across ['Weather', 'Traffic', 'Vehicle', 'Area', 'Category']: 0 |
| PASS | sla_threshold_minutes reference table has exactly 16 rows | Reference table rows: 16 |
| PASS | Row count accounted for exactly (43,739 -> cleaned count documented) | See Dataset Validation reconciliation check above; cleaned rows=43648 |

## Feature Engineering Edge Cases

| Status | Check | Detail |
|---|---|---|
| PASS | distance_km is always >= 0 (where computed) | Non-negative for all 39997 coordinate-valid rows |
| PASS | distance_km is null exactly for coordinates_valid_flag=False rows | distance_km nullness matches ~coordinates_valid_flag row-for-row |
| PASS | sla_breach_flag boundary rule (Delivery_Time == threshold -> not breached) | 1133 rows exactly at their category threshold; all classified on-time |
| PASS | Aggregate breach rate is a plausible percentage (not near 0% or 100%) | Overall breach rate = 23.66% |
| PASS | prep_time_minutes is never negative after midnight-crossover correction | Min prep_time_minutes observed: 5 |
| PASS | order_hour is strictly within 0-23 | Range observed: 0-23 |
| PASS | Every row falls into exactly one delivery_bucket | Unassigned rows: 0 |

## Business Logic Validation (SLA definition)

| Status | Check | Detail |
|---|---|---|
| PASS | sla_threshold_minutes = category-level P75 of Delivery_Time (frozen definition) | Recomputed P75 per category matches the frozen reference table exactly |
| PASS | sla_breach_flag = Delivery_Time > sla_threshold_minutes (strict >, frozen rule) | Recomputed flag matches stored sla_breach_flag row-for-row |
| PASS | agent_rating_valid_flag correctly excludes both nulls and out-of-range (>5) rows | Flag matches (notna AND 1<=rating<=5) row-for-row |

## Not Applicable to This Phase 1 Run

- SQL Validation — no SQL layer built in this Python Phase 1 run
- DAX Validation — no Power BI model built in this Python Phase 1 run
- Power BI Validation — no dashboard built in this Python Phase 1 run
- Statistics Validation — statistical testing is Phase 2 scope (PYTHON_ANALYSIS_PLAN.md), not run in this Phase 1 implementation

## Acceptance Criteria (TESTING_PLAN.md)

- [x] 100% of Data Quality Tests applicable to Phase 1 pass (see Dataset Validation, Python Phase 1 Validation Gate above)
- [ ] SQL/DAX/Power BI cross-validation — out of scope for this Python Phase 1 run
- [ ] Statistical test assumption logging — Phase 2 scope, not run here
- [x] No test failure was worked around by changing the underlying business rule (SLA definition unchanged from `SLA_METHODOLOGY.md`'s frozen statement)
