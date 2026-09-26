# Validation Checklist — RouteIQ

## Table of Contents
1. [Purpose](#purpose)
2. [Dataset Validation](#dataset-validation)
3. [SQL Validation](#sql-validation)
4. [Python Validation](#python-validation)
5. [Statistics Validation](#statistics-validation)
6. [DAX Validation](#dax-validation)
7. [Power BI Validation](#power-bi-validation)
8. [Business Logic Validation](#business-logic-validation)
9. [Documentation Validation](#documentation-validation)
10. [Mandatory Business Validation Stage](#mandatory-business-validation-stage)

Related documents: every prior document in this set — this checklist is the single gate all of them feed into before publication. Referenced directly by `TESTING_PLAN.md`.

**Process rule:** this checklist must be run and every item explicitly checked (not assumed) before `GITHUB_CHECKLIST.md` or any public-facing publication step begins.

---

## Dataset Validation

- [ ] Raw `amazon_delivery.csv` row/column count matches `DATASET_OVERVIEW.md` (43,739 rows, 16 columns)
- [ ] All missingness figures in `DATA_PROFILING_PLAN.md` reproduced exactly on re-run (91 Weather nulls, 91 masked Traffic, 54 Agent_Rating nulls)
- [ ] Duplicate check reproduced (0 full-row, 0 Order_ID duplicates)
- [ ] Cleaned dataset row count reconciles: 43,739 − 91 (Step 3 exclusion) = documented cleaned count, with all conditional-exclusion flags present and counted separately

## SQL Validation

- [ ] Every P0/P1 query in `SQL_ANALYSIS_PLAN.md` executes without error against the loaded star schema
- [ ] Every query's output row count and key aggregate (e.g., breach rate, avg time) is logged and compared to its Python counterpart
- [ ] Foreign key constraints (`STAR_SCHEMA.md`) enforced and verified — no orphaned fact rows
- [ ] `sla_threshold_minutes` used in SQL is read from the frozen static reference table, not recalculated inline (spot-checked in at least one query)

## Python Validation

- [ ] Phase 1 validation gate (per `PYTHON_ANALYSIS_PLAN.md`) passed: row count, zero masked-NaN Traffic, zero whitespace, 16-row SLA reference table
- [ ] Phase 2 validation gate passed: every P0/P1 SQL figure matched, every statistical assumption check logged
- [ ] Every engineered feature in `FEATURE_ENGINEERING.md` re-checked against its own validation checklist (distance ≥ 0, breach flag boundary rule, midnight-crossover handling, etc.)

## Statistics Validation

- [ ] Every test in `STATISTICAL_ANALYSIS.md` has its assumption checks (normality, variance homogeneity, linearity as applicable) logged as pass/fail, not skipped
- [ ] Fallback test used and reported wherever a primary assumption failed
- [ ] Effect size reported alongside every p-value, per the mandatory standard in `STATISTICAL_ANALYSIS.md`
- [ ] No test result is described as "significant" in any dashboard/doc without its effect size also being stated in the same sentence or immediately adjacent

## DAX Validation

- [ ] Every measure in `DAX_MEASURE_PLAN.md` tested at ≥3 filter contexts (no filter, one area, one category) against SQL/Python
- [ ] Every P90/percentile measure's interpolation method confirmed to match SQL and Python methods
- [ ] Every flag-based exclusion (rating validity, coordinate validity, age validity, area-tier validity) implemented via the boolean flag column, not a hardcoded value filter
- [ ] `[On-Time Delivery Rate %] + [SLA Breach Rate %] = 100` confirmed at ≥3 filter contexts
- [ ] No measure recalculates `sla_threshold_minutes` inline — confirmed by inspecting each measure's dependency chain

## Power BI Validation

- [ ] Every page in `DASHBOARD_PLANNING.md` built matches its planned purpose/audience/KPI set — no undocumented visual added without updating the plan first
- [ ] Every SLA-derived visual is labeled "SLA (analyst-defined benchmark)," not unqualified "SLA"
- [ ] Every visual filtered by a validity flag shows its row count/sample size in a tooltip or footnote
- [ ] Drillthrough paths (Page 1→4, Page 2→4) function as planned; "back" navigation present
- [ ] Dashboard reviewed by a second reader (or a fresh read after a break) for the "readable in under two minutes" success criterion from `PROJECT_CHARTER.md`

## Business Logic Validation

- [ ] SLA definition matches the frozen statement in `SLA_METHODOLOGY.md` exactly, in every layer (SQL, Python, DAX) — no silent drift
- [ ] Every conditional exclusion (coordinates, agent rating, agent age, area=Other) is applied consistently across SQL, Python, and DAX — not applied in one layer and forgotten in another
- [ ] Every KPI's business definition in the dashboard matches its definition in `KPI_DEFINITIONS.md` word-for-word in intent, not just in name

## Documentation Validation

- [ ] Every cross-reference between documents (e.g., "`see ASSUMPTIONS.md A7`") resolves to an entry that actually exists and says what it's cited as saying
- [ ] No document contains a numeric finding that was written before the corresponding analysis was run (spot-check by comparing draft dates/versions if available)
- [ ] `README.md`, `LIMITATIONS.md`, resume bullets, and LinkedIn copy (once produced) are consistent with the frozen KPI/SLA definitions — no separate, looser numbers used in marketing copy than in the technical documents

---

## Mandatory Business Validation Stage

This stage is a **hard gate before publication** — every insight destined for the dashboard, README, or `EXECUTIVE_RECOMMENDATIONS.md` must pass all four questions below, answered explicitly (not implicitly assumed), before it is published anywhere.

| # | Question | What "Pass" Looks Like |
|---|---|---|
| 1 | **Is it supported by data?** | The specific SQL/Python output cell or file the number comes from is identified; the figure is reproducible by re-running the documented query/script, not eyeballed from a chart |
| 2 | **Is it correlation or causation?** | The insight's write-up explicitly states which one it is; if correlation, it does not use causal language ("X causes Y") anywhere, per `STATISTICAL_ANALYSIS.md`'s interpretation standard |
| 3 | **Can it be defended in an interview?** | The analyst can state the exact test/query used, its assumption checks, its effect size, and its main limitation, without needing to look it up — rehearsed against `INTERVIEW_PREPARATION.md` (to be produced) |
| 4 | **Would an Operations Manager actually use this insight?** | The insight maps to a concrete action from `BUSINESS_REQUIREMENTS.md`'s "Expected Decisions" (e.g., reallocate agents, trigger proactive messaging) — not just an interesting-but-inactionable statistic |

**Any insight failing even one of these four questions is either revised, caveated more strongly, or dropped from the final deliverable — it is never published on the basis of "it's interesting" alone.**
