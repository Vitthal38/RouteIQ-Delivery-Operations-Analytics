# Phase 1 Remediation Audit — RouteIQ

Generated: 2026-08-16

Scope: controlled documentation-consistency remediation of the
`sla_threshold_minutes` formula conflict identified in the prior Phase 1
audit. No SQL, DAX, Power BI, EDA, or Phase 2 work was performed. No
dataset regeneration was performed.

---

## 1. Issue Identified

`FEATURE_ENGINEERING.md` (field 2, `sla_threshold_minutes`) stated its
"Formula" as:

> `sla_threshold_minutes = median(Delivery_Time) within Category group + buffer_minutes`

`SLA_METHODOLOGY.md`'s Frozen SLA Definition states:

> `sla_threshold_minutes` = the 75th percentile (P75) of `Delivery_Time`
> within that order's `Category`, calculated once on the full cleaned dataset.

`SLA_METHODOLOGY.md`'s own Alternatives Considered table lists the
median + fixed-minute buffer construction as **Option B, explicitly
rejected ("No")**, in favor of Option C (P75, "Yes — selected"). The two
documents therefore directly contradicted each other over which formula
is the active business rule.

## 2. Root Cause

`FEATURE_ENGINEERING.md`'s `sla_threshold_minutes` entry was drafted
before `SLA_METHODOLOGY.md` finalized and froze the P75 selection.
`FEATURE_ENGINEERING.md`'s own text says it "documents only the
mechanical formula" and defers derivation/justification to
`SLA_METHODOLOGY.md` — but its formula line was never updated to mirror
that freeze once it happened, leaving stale Option-B language in a
document that was supposed to be a pure mechanical restatement of the
frozen rule.

## 3. Documents Affected

| Document | Status |
|---|---|
| `FEATURE_ENGINEERING.md` | **Corrected** (formula, edge-case, and example-calculation text) |
| `ASSUMPTIONS.md` (A7) | **Corrected** (clarified as historical/illustrative, deferred to `SLA_METHODOLOGY.md`) |
| `SLA_METHODOLOGY.md` | **Inspected, unchanged** (already correct and frozen; this document was the audit's authority, not its target) |
| `docs/CHANGELOG.md` | **Created** (new — audit trail of this correction) |
| `python/constants.py`, `python/feature_engineering.py` | **Inspected, unchanged** (already implemented P75) |
| `data/cleaned/cleaned_delivery.csv`, `data/cleaned/sla_reference.csv` | **Inspected, unchanged** (already matched frozen definition; no regeneration performed) |
| `reports/profiling_report.md`, `reports/cleaning_log.md`, `reports/validation_report.md` | **Inspected, unchanged** (already stated P75 correctly) |

## 4. Documentation Changes Made

### `FEATURE_ENGINEERING.md` (field 2, lines 43–50)
- **Formula** line replaced: now states `PERCENTILE(Delivery_Time, 0.75) within Category`, explicitly notes no buffer term is added, and points to `SLA_METHODOLOGY.md`'s Alternatives Considered table for why median + buffer (Option B) was evaluated and rejected — the rejected alternative is referenced, not erased.
- **Business Logic** line: added "must mirror that document's frozen definition exactly" to prevent future drift.
- **Validation** bullet: added that the reference-table value is the single value `sla_breach_flag` reads from, never recomputed independently downstream.
- **Edge Cases** bullet: "unstable median" → "unstable P75" (the statistic actually at risk of instability under the frozen rule).
- **Example Calculation** bullet: "category-level median" → "category-level P75".
- Field 3 (`sla_breach_flag`) required no change — it already correctly stated the strict-`>`, equality-is-on-time rule.

### `ASSUMPTIONS.md` (A7)
- The validation-method note's illustrative "e.g., category-median delivery time + a documented buffer" phrasing was retained for audit-trail purposes but wrapped in an explicit clarifying note: it was only ever an illustrative example at drafting time, never the frozen rule, and `SLA_METHODOLOGY.md`'s P75 definition is the sole current authority. Any conflict is stated to resolve in `SLA_METHODOLOGY.md`'s favor.

### `docs/CHANGELOG.md` (new file)
- Created with a dated entry recording the issue, root cause, the correct frozen definition, implementation impact (none), data impact (none), and full validation results.

## 5. Confirmation — `SLA_METHODOLOGY.md` Not Changed

Not opened with Edit or Write at any point in this remediation. Its
Alternatives Considered table (Option B marked "No", Option C marked
"Yes — selected") and Frozen SLA Definition remain exactly as they were
audited previously. **Confirmed unchanged.**

## 6. Confirmation — Implementation Not Changed

`python/constants.py` and `python/feature_engineering.py` were not
opened with Edit or Write at any point in this remediation. File
modification timestamps for every file in `python/` predate this
remediation session (all dated within the original Phase 1 build
window). `SLA_PERCENTILE = 0.75` and the `np.percentile(s, SLA_PERCENTILE * 100)`
call remain exactly as originally implemented. A grep of `python/` for
`median|buffer` finds only the pre-existing, unrelated descriptive-statistics
`median()` calls in `profiling.py`'s routine numerical profiling (Agent_Age,
Agent_Rating, Delivery_Time distributions) — these have nothing to do with
the SLA threshold and were correct before and remain correct now.
**Confirmed unchanged.**

## 7. Confirmation — Data Artifacts Not Changed

`data/cleaned/cleaned_delivery.csv` and `data/cleaned/sla_reference.csv`
file modification timestamps predate this remediation session and were
not written to. No regeneration was performed, per the explicit
instruction to only regenerate if inspection proved the existing
artifacts wrong — inspection proved the opposite. **Confirmed unchanged.**

## 8. Independent SLA Threshold Validation (post-remediation, freshly recomputed)

Recomputed `PERCENTILE(Delivery_Time, 75)` per `Category` directly from
`cleaned_delivery.csv` and compared against `sla_reference.csv`:

| Category | sla_reference.csv | Recomputed P75 | Match |
|---|---|---|---|
| Apparel | 165.0 | 165.0 | ✅ |
| Books | 160.0 | 160.0 | ✅ |
| Clothing | 160.0 | 160.0 | ✅ |
| Cosmetics | 165.0 | 165.0 | ✅ |
| Electronics | 160.0 | 160.0 | ✅ |
| Grocery | 33.0 | 33.0 | ✅ |
| Home | 160.0 | 160.0 | ✅ |
| Jewelry | 160.0 | 160.0 | ✅ |
| Kitchen | 165.0 | 165.0 | ✅ |
| Outdoors | 160.0 | 160.0 | ✅ |
| Pet Supplies | 160.0 | 160.0 | ✅ |
| Shoes | 160.0 | 160.0 | ✅ |
| Skincare | 165.0 | 165.0 | ✅ |
| Snacks | 160.0 | 160.0 | ✅ |
| Sports | 165.0 | 165.0 | ✅ |
| Toys | 160.0 | 160.0 | ✅ |

**Result: 16/16 match.** `sla_reference.csv` contains exactly 16 rows (one per `Category`), as required.

## 9. `sla_breach_flag` Validation (post-remediation, freshly recomputed)

Recomputed `Delivery_Time > sla_threshold_minutes` for all rows in
`cleaned_delivery.csv` and compared against the stored `sla_breach_flag` column.

- Rows checked: **43,648**
- Mismatches: **0**

**Result: 43,648 / 43,648 match.**

## 10. Boundary Validation

Rows where `Delivery_Time == sla_threshold_minutes`: **1,133**
Of those, rows incorrectly flagged as a breach: **0**

**Result: boundary rule (`<=` is on-time) holds for every row.**

## 11. Breach-Rate Reconciliation

- Freshly recomputed overall breach rate: **23.6620%**
- Previously reported (validation_report.md, prior audit): **23.6620%**

**Result: reconciles exactly.**

## 12. Documentation Search Results (post-remediation)

Searched the full project (all `.md` files) for `median`, `buffer`,
`category-median`, `median(Delivery_Time)`, and `median delivery time +`:

| File | Line | Content | Classification |
|---|---|---|---|
| `SLA_METHODOLOGY.md` | 31 | Alternatives table, Option B (median+buffer), marked "No" | Correctly documents rejected alternative — **left unchanged** |
| `SLA_METHODOLOGY.md` | 47 | Rationale for rejecting median+buffer in favor of P75 | Correctly documents rejection rationale — **left unchanged** |
| `FEATURE_ENGINEERING.md` | 44 | References median+buffer only as the rejected Option B, pointing to `SLA_METHODOLOGY.md` | Now correctly contextualized as historical/rejected, active formula is P75 — **corrected** |
| `ASSUMPTIONS.md` | 57 | Illustrative drafting-time example, now explicitly labeled as superseded by `SLA_METHODOLOGY.md` | **corrected** (clarified) |
| `docs/CHANGELOG.md` | multiple | Quotes the old erroneous text for audit-trail purposes | Expected in a changelog — not a live claim |

**No document currently presents median + buffer as the active or
current SLA definition.** Every remaining reference either (a)
documents the rejected alternative inside `SLA_METHODOLOGY.md` itself,
(b) is explicitly labeled historical/superseded, or (c) is a changelog
entry quoting the historical error for the record.

`reports/profiling_report.md`, `reports/cleaning_log.md`, and
`reports/validation_report.md` were also searched — none contain
`median`/`buffer` language tied to the SLA definition; `validation_report.md`
already stated P75 correctly and was left unchanged.

## 13. Remaining Known Non-Blocking Issues

One additional, unrelated documentation drift was discovered while
scanning for other contradictions (per Step 9's instruction to report
rather than fix). It is **not** an SLA-methodology or data-correctness
issue and is reported here without modification, per the "do not expand
scope into an uncontrolled rewrite" constraint:

- **`PYTHON_ANALYSIS_PLAN.md`'s Output Files table (lines 68–70)** names
  planned artifacts as `data/cleaned/deliveries_clean.csv`,
  `data/cleaned/sla_threshold_reference.csv`, and
  `docs/technical/cleaning_log.md`. The actual generated artifacts are
  named `cleaned_delivery.csv`, `sla_reference.csv`, and
  `reports/cleaning_log.md` — the exact filenames and folder structure
  explicitly specified by this project's own Phase 1 implementation
  instructions (STEPs 5, 6, and 8). This is a naming/pathing mismatch
  between one planning document's illustrative table and the actual
  build, not a business-rule or data conflict. It does not affect SLA
  correctness, breach-rate correctness, or any figure in this audit.
  **Flagged for a future, separately-scoped documentation pass — not
  corrected here.**

No other contradictions were found in engineered feature names, row
counts, exclusion counts, flag columns, category counts, dataset
dimensions, or date range — all were cross-checked against the current
generated outputs during this remediation and matched.

## 14. Final Phase 1 Status

All required gate conditions were independently re-verified in this
remediation:

- [x] `FEATURE_ENGINEERING.md` matches the frozen SLA methodology
- [x] No active documentation claims median + buffer is the SLA
- [x] `SLA_METHODOLOGY.md` remains unchanged
- [x] Code still implements P75 (unchanged, re-inspected)
- [x] 16/16 SLA thresholds match independently
- [x] `sla_breach_flag` matches independently (43,648/43,648)
- [x] Boundary rule passes (1,133/1,133 correctly on-time)
- [x] Breach rate reconciles (23.6620%)
- [x] No additional *blocking* documentation conflict exists (one
      non-blocking naming drift reported separately, per §13)
- [x] Phase 1 validation requirements remain satisfied

---

# PHASE 1 APPROVED
