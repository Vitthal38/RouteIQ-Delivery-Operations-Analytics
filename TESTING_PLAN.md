# Testing Plan — RouteIQ

## Table of Contents
1. [Purpose](#purpose)
2. [Data Quality Tests](#data-quality-tests)
3. [SQL Validation Tests](#sql-validation-tests)
4. [Python Validation Tests](#python-validation-tests)
5. [Dashboard Validation Tests](#dashboard-validation-tests)
6. [Cross-Validation Tests](#cross-validation-tests)
7. [Acceptance Criteria](#acceptance-criteria)

Related documents: `VALIDATION_CHECKLIST.md` (this plan's tests feed that checklist's items), `DATA_CLEANING_PLAN.md`, `SQL_ANALYSIS_PLAN.md`, `PYTHON_ANALYSIS_PLAN.md`, `DAX_MEASURE_PLAN.md`

This document defines *what tests exist and when they run* in the pipeline. `VALIDATION_CHECKLIST.md` defines the pass/fail gate each test result is checked against.

---

## Data Quality Tests

Run against the cleaned dataset (post `DATA_CLEANING_PLAN.md`), before any SQL load or Python analysis.

| Test | Method | Pass Condition |
|---|---|---|
| Row count reconciliation | Count rows pre/post cleaning | Cleaned count = 43,739 − (91-row cluster exclusion), documented exactly |
| No masked-missing values remain | Search for literal `"NaN"`/`"NaN "` strings in all categorical columns | 0 matches |
| No trailing whitespace | Compare each categorical column's values to their `.str.strip()` equivalent | Identical — 0 rows differ |
| SLA reference table completeness | Count rows in the frozen `sla_threshold_minutes` reference table | Exactly 16 (one per `Category`) |
| Flag columns present and non-null | Check `coordinates_valid_flag`, `agent_rating_valid_flag`, `agent_age_valid_flag`, `area_tier_valid_flag` | 0 nulls in any flag column (every row must be explicitly flagged true/false, never left unset) |

## SQL Validation Tests

| Test | Method | Pass Condition |
|---|---|---|
| Referential integrity | Check for fact rows with no matching dimension key | 0 orphaned fact rows across all 6 FK relationships |
| P0/P1 query execution | Run every P0/P1 query from `SQL_ANALYSIS_PLAN.md` | Executes without error, returns a non-empty, plausible result (e.g., breach rate between 0–100%) |
| SLA threshold consistency | Compare `sla_threshold_minutes` values used in SQL against the frozen Python-produced reference table | Exact match, all 16 categories |
| Percentile method check | Confirm `PERCENTILE_CONT` interpolation matches the documented standard in `DAX_MEASURE_PLAN.md` | Method name/type recorded and matches |

## Python Validation Tests

| Test | Method | Pass Condition |
|---|---|---|
| Phase 1 gate | Run the 4-item checklist in `PYTHON_ANALYSIS_PLAN.md` Phase 1 | All 4 items pass before Phase 2 begins |
| Phase 2 gate | Run the 3-item checklist in `PYTHON_ANALYSIS_PLAN.md` Phase 2 | All 3 items pass before insight write-up begins |
| Feature engineering edge cases | Test each engineered field against its documented edge case in `FEATURE_ENGINEERING.md` (e.g., identical store/drop coordinates → distance = 0; midnight-crossover prep time → non-negative) | Each edge case produces the documented expected output, not an error or implausible value |
| Statistical assumption logging | Confirm every test in `STATISTICAL_ANALYSIS.md` has a logged assumption-check result | 100% of the 5 planned tests have logged Shapiro-Wilk/Levene's (or linearity) results, pass or fail |

## Dashboard Validation Tests

| Test | Method | Pass Condition |
|---|---|---|
| Page-plan conformance | Compare built pages against `DASHBOARD_PLANNING.md` page-by-page | Every planned KPI/chart/filter/drillthrough present; no undocumented additions |
| SLA labeling | Inspect every SLA-derived visual title/tooltip | 100% use "SLA (analyst-defined benchmark)" language |
| Sample-size transparency | Inspect every visual filtered by a validity flag | 100% show row count/sample size in tooltip or footnote |
| Drillthrough functionality | Manually click through Page 1→4 and Page 2→4 paths | Both resolve to the correct filtered Page 4 view; "back" link returns correctly |
| Two-minute readability | Time a fresh read-through of Page 1 by someone unfamiliar with the build | Headline finding graspable within ~2 minutes, consistent with `PROJECT_CHARTER.md` success criteria |

## Cross-Validation Tests

The highest-priority test category — this is where the FoodPulse project's real bugs (unfiltered `order_status`, DAX context-transition, SQL/Python boundary mismatch) were actually caught, so this category is treated as non-negotiable, not a nice-to-have.

| Test | Method | Pass Condition |
|---|---|---|
| OTD%/Breach Rate 3-way match | Compare SQL, Python, and DAX outputs for `On-Time Delivery Rate %` at ≥3 filter contexts | Match to the decimal place used in the dashboard, at every tested context |
| P90 3-way match | Same, for `P90 Delivery Time` | Match, with interpolation method explicitly confirmed identical first |
| Pareto/root-cause 3-way match | Compare `SQL_ANALYSIS_PLAN.md` Q14/Q20 output, Python `pareto_ranking.csv`, and the DAX Pareto measure | Ranked order and cumulative % match across all three |
| Statistical test group inputs | Compare the row counts/group means used in SQL prep queries (Q3, Q13) against the exact inputs Python's ANOVA/Kruskal-Wallis used | Identical row counts per group — a mismatch here means the two layers are silently testing different data |
| Flag-based exclusion consistency | For each of the 4 validity flags, compare the excluded row count in SQL, Python, and DAX | Identical exclusion counts across all three layers |

## Acceptance Criteria

The project is considered technically complete and ready for the Mandatory Business Validation Stage (`VALIDATION_CHECKLIST.md`) only when:
- [ ] 100% of Data Quality Tests pass
- [ ] 100% of P0 SQL/Python/DAX cross-validation tests pass exactly; 100% of P1 tests pass or have a documented, explained discrepancy (no undocumented mismatch is acceptable at any priority level)
- [ ] 100% of Dashboard Validation Tests pass
- [ ] Every statistical test has a logged assumption check and effect size
- [ ] No test failure is worked around by quietly changing the underlying business rule (e.g., adjusting the SLA definition to make a number "look right") — per `SLA_METHODOLOGY.md`'s change-control process, any genuine rule change requires the full documented change process, not a silent fix
