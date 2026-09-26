# Changelog — RouteIQ Documentation

This file records documentation-level changes that affect business-rule
traceability, per `SLA_METHODOLOGY.md`'s Change Control process and this
project's no-silent-drift standard. It does not record ordinary editorial
edits — only changes that touch how a frozen rule, KPI, or engineered
field is described.

---

## 2026-08-16 — SLA Documentation Consistency Correction

### Changed
Corrected `FEATURE_ENGINEERING.md` (`sla_threshold_minutes`, field 2) so
its stated formula matches the already-frozen `SLA_METHODOLOGY.md`
definition. Also corrected two stale "median" references in the same
section's Edge Cases and Example Calculation bullets. Clarified
`ASSUMPTIONS.md` A7's validation-method note so its illustrative
"category-median + buffer" phrasing cannot be misread as the active rule.

### Previous Documentation Error
`FEATURE_ENGINEERING.md` line 44 stated:

> `sla_threshold_minutes = median(Delivery_Time) within Category group + buffer_minutes`

This is Option B from `SLA_METHODOLOGY.md`'s own Alternatives Considered
table — the option that document explicitly evaluated and marked
**"No" (not selected)**. The line was never updated after
`SLA_METHODOLOGY.md` froze Option C (P75), leaving two documents that
both claim authority over the same field in direct contradiction.

### Correct Frozen Definition (unchanged, per `SLA_METHODOLOGY.md`)
> `sla_threshold_minutes` for a given order = the 75th percentile (P75)
> of `Delivery_Time` within that order's `Category`, calculated once on
> the full cleaned dataset, and frozen before any breach analysis is run.
>
> `sla_breach_flag` = 1 if `Delivery_Time > sla_threshold_minutes`
> (strict greater-than; equality is on-time), else 0.

### Implementation Impact
**None.** The Phase 1 implementation ([python/feature_engineering.py](../python/feature_engineering.py),
[python/constants.py](../python/constants.py)) already used `SLA_PERCENTILE = 0.75`
via `np.percentile`, never a median+buffer construction. This was
independently re-verified as part of this remediation — see
`reports/phase1_remediation_audit.md`.

### Data Impact
**None.** No regeneration was required or performed. `data/cleaned/sla_reference.csv`
and `data/cleaned/cleaned_delivery.csv` were re-checked against the
frozen P75 definition and already matched it exactly; they were left
untouched.

### Validation
- 16/16 category SLA thresholds in `sla_reference.csv` independently
  recomputed as P75 of `Delivery_Time` and matched exactly.
- 43,648/43,648 `sla_breach_flag` values independently recomputed as
  `Delivery_Time > sla_threshold_minutes` and matched exactly (0 mismatches).
- Boundary rule verified: 1,133 rows with `Delivery_Time` exactly equal
  to their category threshold, 0 of them flagged as a breach.
- Overall breach rate reconciled to 23.6620% (matches the figure
  originally reported in `reports/validation_report.md`).

Full detail: `reports/phase1_remediation_audit.md`.

### Documents Corrected
- `FEATURE_ENGINEERING.md` — `sla_threshold_minutes` formula, edge case, and example-calculation text.
- `ASSUMPTIONS.md` — A7 validation-method note clarified as historical/illustrative.

### Documents Inspected, Not Changed
- `SLA_METHODOLOGY.md` — unchanged in substance, per this remediation's explicit constraint. Its
  Alternatives Considered table (Option B, marked "No") and rejection rationale for
  median + buffer are correct as written and were left as-is — they document a
  rejected alternative, not the active rule.
- `PROJECT_CHARTER.md`, `BUSINESS_REQUIREMENTS.md`, `KPI_DEFINITIONS.md`,
  `DATASET_OVERVIEW.md`, `DATA_PROFILING_PLAN.md`, `DATA_CLEANING_PLAN.md`,
  `PYTHON_ANALYSIS_PLAN.md`, `STAR_SCHEMA.md`, `SQL_ANALYSIS_PLAN.md`,
  `STATISTICAL_ANALYSIS.md`, `DAX_MEASURE_PLAN.md`, `DASHBOARD_PLANNING.md`,
  `VALIDATION_CHECKLIST.md`, `TESTING_PLAN.md`, `EXECUTIVE_RECOMMENDATIONS_TEMPLATE.md`
  — no median/buffer/P75 language found requiring correction.
- `reports/profiling_report.md`, `reports/cleaning_log.md`, `reports/validation_report.md`
  — already stated P75 correctly; no rewrite performed.

### Classification
Documentation consistency correction only. Not a change to the frozen
business methodology in `SLA_METHODOLOGY.md`, not a change to the Phase 1
implementation, and not a change to any generated data artifact.
