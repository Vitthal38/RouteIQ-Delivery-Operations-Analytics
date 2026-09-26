# Python Analysis Plan — RouteIQ

## Table of Contents
1. [Why the Split Into Two Phases](#why-the-split-into-two-phases)
2. [Phase 1 — Cleaning, Validation, Feature Engineering](#phase-1--cleaning-validation-feature-engineering)
3. [Phase 2 — EDA, Correlation, Statistical Analysis, Insight Generation](#phase-2--eda-correlation-statistical-analysis-insight-generation)
4. [Output Files](#output-files)

Related documents: `DATA_CLEANING_PLAN.md`, `FEATURE_ENGINEERING.md`, `STATISTICAL_ANALYSIS.md`, `SQL_ANALYSIS_PLAN.md` (Phase 2 cross-validates against this)

No Python code is written here — this document specifies what each script/notebook must do and produce, in order, so implementation follows a fixed sequence rather than mixing cleaning and analysis in one pass.

---

## Why the Split Into Two Phases

Mixing cleaning/feature-engineering code with EDA/statistical-testing code in one notebook risks two specific failure modes seen already in this analyst's prior project (FoodPulse): a cleaning bug silently propagating into a "finding" before anyone notices (e.g., the unfiltered `order_status` bug that overstated GMV), and re-running cleaning logic inconsistently between the exploratory and final passes. Splitting into two phases, with Phase 1's output as a frozen, validated artifact that Phase 2 only *reads*, makes each stage independently checkable.

## Phase 1 — Cleaning, Validation, Feature Engineering

**Input:** raw `amazon_delivery.csv` (43,739 rows, read-only — never modified in place, per `DATA_CLEANING_PLAN.md` rollback strategy).

**Steps (mirrors `DATA_CLEANING_PLAN.md` execution order exactly — this plan does not introduce new logic, only sequences the code):**

1. Load raw CSV, run the full `DATA_PROFILING_PLAN.md` checklist programmatically (missingness, duplicates, category value counts, coordinate/datetime validity) and print/log a before-state report.
2. Apply Cleaning Steps 1–9 in order (whitespace trim → Traffic NaN recode → 91-row cluster resolution → Agent_Rating bound/null flags → Agent_Age flag → coordinate flag → Area=Other handling → spelling preservation).
3. Apply Feature Engineering fields 1–8 (`distance_km`, `sla_threshold_minutes`, `sla_breach_flag`, `delivery_bucket`, `day_of_week`, `order_hour`, `week_number`, `prep_time_minutes`), in that dependency order — `sla_threshold_minutes` must be computed and frozen (written to a static reference file) before `sla_breach_flag` is calculated, and never recalculated afterward in Phase 2 or any later run.
4. Re-run the profiling checklist on the cleaned+engineered dataset (after-state report) and diff against the before-state report — every flagged issue from `DATA_PROFILING_PLAN.md` must show as resolved or explicitly and intentionally retained-with-flag (e.g., invalid coordinates are retained with `coordinates_valid_flag = false`, not removed — this must show in the diff as "flagged," not "still broken").
5. Write the cleaned+engineered dataset and the frozen `sla_threshold_minutes` reference table to `data/cleaned/` as the single frozen artifact Phase 2 and the SQL load both read from — guarantees SQL, Python, and Power BI never diverge on cleaning logic.

**Phase 1 validation gate (must pass before Phase 2 begins):**
- [ ] Row count accounted for exactly (43,739 → cleaned count, with the 91-row exclusion documented)
- [ ] Zero rows with masked `"NaN "` Traffic values remain
- [ ] Zero rows with trailing whitespace in any categorical column
- [ ] `sla_threshold_minutes` reference table has exactly 16 rows (one per category, per profiling)
- [ ] Cleaning log entry generated per the `DATA_CLEANING_PLAN.md` template

## Phase 2 — EDA, Correlation, Statistical Analysis, Insight Generation

**Input:** the frozen Phase 1 output only — Phase 2 never re-reads or re-cleans the raw CSV, preventing the two-phases-drift-apart failure mode.

### EDA
- Distribution of `delivery_time_minutes` overall and by `Area`/`Category`/`Weather`/`Traffic` (histograms — needed before finalizing `delivery_bucket` bin edges per `FEATURE_ENGINEERING.md` #4).
- Missingness/exclusion-flag summary (how many rows are excluded from which specific KPI, restated from Phase 1's log so EDA output is self-documenting).

### Correlation
- `distance_km` vs. `delivery_time_minutes` (only on `coordinates_valid_flag = true` rows).
- `agent_rating` vs. `delivery_time_minutes` (only on `agent_rating_valid_flag = true` rows).
- `agent_age` vs. `delivery_time_minutes` and vs. `agent_rating` (only on validity-flagged rows).
- All correlation results reported with the exact row count used, per `SQL_ANALYSIS_PLAN.md` Q10/Q15 validation requirement.

### Statistical Testing
Full test-by-test plan lives in `STATISTICAL_ANALYSIS.md` (hypotheses, assumption checks, decision tree). This script executes that plan and stores results (test statistic, p-value, effect size) as a structured output, not just printed text, so `SQL_ANALYSIS_PLAN.md` cross-validation and dashboard write-up can reference exact figures.

### Insight Generation
- Pareto ranking of breach volume by area/category/weather-traffic combination (cross-validated against `SQL_ANALYSIS_PLAN.md` Q14).
- Insights drafted following the format defined in `BUSINESS_INSIGHTS_TEMPLATE.md` (to be produced separately) — this script's job is to generate the *evidence* (numbers), not the final narrative prose, keeping a clean separation between computed fact and written interpretation.

**Phase 2 validation gate:**
- [ ] Every P0/P1 SQL query result in `SQL_ANALYSIS_PLAN.md` has a matching Python-computed figure, compared and logged as match/mismatch
- [ ] Every statistical test's assumption checks are logged (pass/fail), not skipped
- [ ] No insight is written referencing a number that isn't traceable to a specific Phase 2 output cell/variable

## Output Files

| File | Produced By | Consumed By |
|---|---|---|
| `data/cleaned/cleaned_delivery.csv` | Phase 1 | SQL load, Phase 2, Power BI (via SQL) |
| `data/cleaned/sla_reference.csv` | Phase 1 | SQL, Power BI DAX measures — frozen, read-only downstream |
| `reports/cleaning_log.md` entry | Phase 1 | Reviewer, interview prep |
| `output/eda_summary.json` (or similar structured output) | Phase 2 | Dashboard build, insight write-up |
| `output/statistical_test_results.json` | Phase 2 | `STATISTICAL_ANALYSIS.md` write-up, dashboard footnotes |
| `output/pareto_ranking.csv` | Phase 2 | Dashboard Delay Root Cause page, `EXECUTIVE_RECOMMENDATIONS.md` |
