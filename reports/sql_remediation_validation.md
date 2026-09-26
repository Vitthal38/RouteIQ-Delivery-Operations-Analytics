# SQL Remediation Validation Report — RouteIQ

Generated: 2026-08-16

Validates the three authorized fixes (Q09, Q14, Q17) against
`reports/sql_senior_audit.md`. All 22 queries were re-executed against the
live database after the fixes; every query's pre-fix output was already
on record from the original audit run, so this comparison is a genuine
before/after diff, not a re-assertion.

**Files touched:** `sql/analysis/Q09_agent_rating_tier_delay_distribution.sql`,
`Q14_pareto_breach_share_area_and_category.sql`,
`Q17_week_over_week_volatility.sql`. No other file in `sql/analysis/`,
`sql/schema/`, `python/`, or `data/` was modified (confirmed by file
timestamp — all other files predate this remediation session).

---

## Full Query Comparison

| Query | Before | After | Changed? | Expected? | Validation | Status |
|---|---|---|---|---|---|---|
| Q01 | breach rate 23.6620% overall, 4 areas | Identical | No | Yes (not in scope) | Byte-for-byte match | ✅ PASS |
| Q02 | P90 by area, Semi-Urban 269.50 | Identical | No | Yes | Byte-for-byte match | ✅ PASS |
| Q03 | 4 traffic groups, n/avg/stddev/median | Identical | No | Yes | Byte-for-byte match | ✅ PASS |
| Q04 | r=-0.3077, n=43,594, 6 rating bands | Identical | No | Yes | Byte-for-byte match | ✅ PASS |
| Q05 | 24 combos ranked | Identical | No | Yes | Byte-for-byte match | ✅ PASS |
| Q06 | 16 categories ranked | Identical | No | Yes | Byte-for-byte match | ✅ PASS |
| Q07 | Weekday 124.90 / Weekend 124.96 | Identical | No | Yes | Byte-for-byte match | ✅ PASS |
| Q08 | OTD% by area, check=100.0000 ×4 | Identical | No | Yes | Byte-for-byte match | ✅ PASS |
| **Q09** | 4 row-count quartiles (~10,898 each), `rating_quartile` column, confirmed tie-splitting (rating 4.5 in 2 tiers) | 4 value-based tiers (137/995/6,892/35,570), `rating_tier` column, **0 ratings split across tiers** | **Yes — intended** | **Yes** | Independently re-verified: `SELECT ... HAVING COUNT(DISTINCT rating_tier) > 1` returns 0 rows | ✅ FIXED |
| Q10 | r=0.2781, n=39,997, 24-row comparison | Identical | No | Yes | Byte-for-byte match | ✅ PASS |
| Q11 | 8 weeks, partial-week flags, LAG delta | Identical | No | Yes (Q11 not in fix scope) | Byte-for-byte match | ✅ PASS |
| Q12 | 6 weather groups, breach counts | Identical | No | Yes | Byte-for-byte match | ✅ PASS |
| Q13 | 6 weather groups, stats | Identical | No | Yes | Byte-for-byte match | ✅ PASS |
| **Q14** | Area cut identical; category cut: Snacks/Electronics tie order not guaranteed stable | Area cut identical; category cut: **Electronics always precedes Snacks** (alphabetical), same two cumulative values (13.3811%, 20.0523%) now deterministically assigned | **Yes — intended (display order only)** | **Yes** | Re-ran twice; both times Electronics=13.3811%, Snacks=20.0523%, rank=2 for both, breach_count=689 for both | ✅ FIXED |
| Q15 | r=0.2585 / r=-0.1176, n=43,594 | Identical | No | Yes | Byte-for-byte match | ✅ PASS |
| Q16 | Semi-Urban, 0.0000% | Identical | No | Yes | Byte-for-byte match | ✅ PASS |
| **Q17** | 8 weeks; week 9 showed `prior_week_avg=129.12`, `avg_pct_change=-3.90` (silently spanning the week-8 gap) | 8 weeks + 4 new columns; week 9 now shows `weeks_since_prior_observed_week=2`, `is_consecutive_week_comparison=false`, **all "vs. prior week" columns NULL**; weeks 7, 10–14 unchanged (still gap=1, same delta values as before) | **Yes — intended (week 9 only)** | **Yes** | Verified week sequence 6,7,9,10,11,12,13,14; only week 9's row changed | ✅ FIXED |
| Q18 | 16 categories, stddev-ranked | Identical | No | Yes | Byte-for-byte match | ✅ PASS |
| Q19 | Clear 103.66 / Adverse 129.03 | Identical | No | Yes | Byte-for-byte match | ✅ PASS |
| Q20 | 15 area×traffic combos | Identical | No | Yes | Byte-for-byte match | ✅ PASS |
| Q21 | 3 vehicle types | Identical | No | Yes | Byte-for-byte match | ✅ PASS |
| Q22 | Semi-Urban vs. Metropolitian, delta=108.84 | Identical | No | Yes | Byte-for-byte match | ✅ PASS |

**19 of 22 queries: byte-for-byte identical output, confirming no unintended
change reached any unmodified query. 3 of 22 (Q09, Q14, Q17) changed
exactly as intended by the authorized fixes, and only in the specific
rows/columns the defect actually affected.**

---

## Row-Count / Duplicate / Denominator Checks (post-fix)

| Check | Result |
|---|---|
| Total `FactDelivery` rows | 43,648 (unchanged — no query modifies data) |
| Duplicate `order_id` | 0 |
| Q09 total rows across all 4 tiers | 137+995+6,892+35,570 = 43,594 = same `agent_rating_valid_flag=true` population as before (only the grouping changed, not the filter) |
| Q14 category cut: sum of `breach_count` across 16 rows | 10,328 (unchanged — matches overall breach total) |
| Q17: total `n` across 8 weeks | 2,697+4,273+6,153+7,208+7,072+6,110+7,210+2,925 = 43,648 (unchanged) |
| SLA logic | `sla_breach_flag`/`sla_threshold_minutes` not referenced by any of the three fixes — untouched |
| KPI definitions | No formula changed in any of the 22 files |

No denominator changed in any query. No row was gained, lost, or
duplicated by any of the three fixes.

## SQL ↔ Python Reconciliation (unaffected)

Q03 and Q13 (the group-stats inputs Python's statistical tests consume)
are byte-for-byte unchanged, and no Python file was modified (file
timestamps confirmed to predate this remediation). `reports/python_sql_cross_validation.md`'s
comparisons therefore remain valid without re-running Python.

---

## Business Findings Regression Test

| Approved figure (`reports/business_findings.md` / `reports/executive_recommendations.md`) | Source | Post-fix value | Changed? |
|---|---|---|---|
| Traffic ε² = 0.1404 | Python Test 1, fed by SQL Q03 (unmodified) | 0.1404 (Q03 inputs unchanged; Python not re-run, not needed) | No |
| Weather ε² = 0.0517 | Python Test 2, fed by SQL Q13 (unmodified) | 0.0517 (Q13 inputs unchanged) | No |
| Weekend p = 0.9658 | Python Test 5, fed by SQL Q07 (unmodified) | 0.9658 (Q07 unchanged) | No |
| Metropolitian breach-volume share = 83.7335% | SQL Q14 area cut | 83.7335% (identical) | No |
| Semi-Urban breach rate = 100.0000%, n=152 | SQL Q01/Q02/Q08 (unmodified) | 100.0000%, n=152 (identical) | No |
| Overall SLA breach rate = 23.6620% | SQL Q01 (unmodified) | 23.6620% (identical) | No |

**All 6 approved figures reconcile exactly. No unexpected change occurred.
No STOP condition was triggered.** Q09's fix touched a query never cited
as evidence in `reports/business_findings.md` or
`docs/EXECUTIVE_RECOMMENDATIONS.md`; Q14's fix changed only display order
for two tied rows, not any value used in Finding C or Recommendation 2;
Q17's fix only nulled a previously-misleading single-week figure that was
never cited anywhere in Phase 5.

---

## Conclusion

All three authorized fixes work exactly as designed, are scoped precisely
to their defect, and introduce zero side effects on any other query or on
any approved Phase 5 finding. Full validation suite passes.
