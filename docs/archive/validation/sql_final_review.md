# SQL Final Review — RouteIQ

Generated: 2026-08-16

Closes the loop opened by `reports/sql_senior_audit.md`. This is the
post-remediation sign-off, after the three authorized fixes (Q09, Q14,
Q17) were applied, independently verified, and regression-tested.

---

## 1. Original Audit Score

**9.25 / 10 — Exceptional (low end).** Identified 1 HIGH-severity
confirmed defect (Q09) and 2 MEDIUM-severity determinism/labeling
concerns (Q14, Q17), plus 2 LOW-severity latent (not-currently-triggered)
notes (Q16, Q22, not authorized for this remediation). Original verdict:
**SQL APPROVED WITH MINOR FIXES**.

## 2. Defects Identified

| Query | Severity | Defect |
|---|---|---|
| Q09 | HIGH | `NTILE(4)` applied to row-ranked `agent_rating` values with heavy ties; empirically confirmed identical ratings (4.5, 4.7, 4.9) split across adjacent quartiles |
| Q14 | MEDIUM | Confirmed tie (Snacks/Electronics, both 689 breaches); running-total `SUM() OVER` had no secondary sort key, so the intermediate cumulative-% shown for each tied row was not guaranteed reproducible |
| Q17 | MEDIUM | `LAG()` silently bridged the missing week 8, presenting week 9's comparison against week 7 (an 11-day-earlier value) without flagging that it wasn't a true adjacent-week comparison |

## 3. Fixes Applied

| Query | Fix | Scope discipline |
|---|---|---|
| Q09 | `NTILE(4)` re-applied to the ~26 **distinct** `agent_rating` values (not rows); every fact row inherits its rating's single tier via join. Column renamed `rating_quartile` → `rating_tier`; uneven tier populations documented as an intentional trade-off, not hidden. | No tiebreaker-only patch used (explicitly rejected per instructions, since that would only make an incorrect split deterministic, not correct) |
| Q14 | `category_name ASC` / `area_name ASC` added as a secondary key to the running-total `SUM() OVER` window **only**. `RANK()` window untouched. | Ranking logic, breach counts, and denominator all explicitly preserved |
| Q17 | `LAG()` retained (not replaced). Added `weeks_since_prior_observed_week`; every "vs. prior week" column `CASE`-guarded to `NULL` when that gap ≠ 1; `is_consecutive_week_comparison` exposed. | Ambiguity in the documentation (zero-activity vs. missing-data interpretation of the gap) explicitly disclosed rather than silently resolved; the SQL fix itself does not depend on resolving it, since both interpretations require the same treatment |

No other query in `sql/analysis/` was modified. No change was made to
`sql/schema/`, `python/`, or `data/` (confirmed by file timestamps —
every other file predates this remediation session).

## 4. Full Regression Results

- **19 of 22 queries: byte-for-byte identical** pre- vs. post-fix output.
- **3 of 22 (Q09, Q14, Q17): changed exactly as intended**, confined to
  the specific rows/columns the defect affected — no unrelated row or
  column changed in any of the three files.
- **Targeted defect verification, run directly against the live database:**
  - Q09: `HAVING COUNT(DISTINCT rating_tier) > 1` → **0 rows** (no rating value split across tiers)
  - Q14: re-ran the fixed query; Electronics/Snacks consistently show 13.3811%/20.0523% in that order; `breach_count` (689/689) and `breach_rank` (2/2) unchanged; final cumulative total still 100.0000%
  - Q17: week 9 now shows `weeks_since_prior_observed_week=2`, `is_consecutive_week_comparison=false`, all deltas `NULL`; weeks 7 and 10–14 unchanged
- **Data integrity:** 43,648 total rows unchanged; 0 duplicate `order_id`; every denominator identical to pre-fix; `sla_breach_flag`/`sla_threshold_minutes` untouched by any of the three fixes.
- **SQL↔Python reconciliation:** unaffected — Q03/Q13 (the group-stats
  inputs Python's tests consume) are byte-for-byte unchanged, and no
  Python file was modified.
- **Business findings regression:** all 6 spot-checked approved figures
  (traffic ε²=0.1404, weather ε²=0.0517, weekend p=0.9658, Metropolitian
  83.7335%, Semi-Urban 100.0000%/n=152, overall breach rate 23.6620%)
  reconcile exactly. No discrepancy, no STOP condition triggered.

Full detail: `reports/sql_remediation_validation.md`.

## 5. Remaining Warnings (not in scope for this remediation, disclosed for completeness)

| Query | Note | Why not fixed here |
|---|---|---|
| Q11 | Same underlying week-8-gap mechanism as Q17 had, but better mitigated (visible date/partial-week columns let a careful reader infer the gap) | Not one of the 3 authorized queries — explicitly excluded from this remediation's scope |
| Q16 | `LIMIT 1` has no explicit tiebreaker; not triggered by current data (Semi-Urban's OTD% is uniquely lowest) | Latent only, not one of the 3 authorized queries |
| Q22 | `CEIL(area_count/2)` is not a fully general median formula for an even-sized group; not triggered by current data (exactly 3 tier-valid areas) | Latent only, not one of the 3 authorized queries |

None of these three is a defect today — they are pre-existing,
already-disclosed characteristics noted in the original audit, left
untouched per the explicit "fix ONLY Q09/Q14/Q17" authorization.

## 6. Final SQL Score

| Query | Pre-fix | Post-fix |
|---|---|---|
| Q01–Q08 | 9.5/9.5/9.5/9.5/9.5/9.5/10/10 | unchanged |
| Q09 | 6.0 | **9.5** |
| Q10 | 9.5 | unchanged |
| Q11 | 9.0 | unchanged (not in scope) |
| Q12–Q13 | 10/9.5 | unchanged |
| Q14 | 8.0 | **9.5** |
| Q15–Q16 | 9.5/9.5 | unchanged |
| Q17 | 8.5 | **9.5** |
| Q18–Q22 | 9.5/9.5/9.5/9.5/9.0 | unchanged |

**New average: 209.5 / 22 = 9.52 / 10 — Exceptional.**

### SQL Quality Classification

| Band | Label |
|---|---|
| 9.0–10.0 | **Exceptional ← current** |
| 8.0–8.9 | Strong |
| 7.0–7.9 | Good / resume-ready |
| 6.0–6.9 | Needs improvement |
| <6.0 | Weak |

## 7. Final SQL Status

- Q09 is now analytically correct: no rating value is split across tiers (verified empirically, 0 rows).
- Q14 is now deterministic: the running-total tie order is fixed and reproducible; ranking, breach counts, and the Pareto conclusion are unchanged.
- Q17 now correctly handles the week gap: it is never silently presented as a normal adjacent-week comparison.
- All 22 queries execute successfully.
- No query outside Q09/Q14/Q17 was changed.
- No KPI definition was changed anywhere.
- SLA logic is unchanged everywhere (untouched by all three fixes).
- SQL↔Python reconciliation is unaffected and remains valid.
- All 6 spot-checked Phase 5 findings remain valid, unchanged.
- No new analytical defect was discovered during remediation or regression testing.

---

# SQL APPROVED FOR POWER BI
