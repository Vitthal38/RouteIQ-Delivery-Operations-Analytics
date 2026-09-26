# Python Phase 2 (Analysis) Validation Report — RouteIQ Phase 4

Generated: 2026-08-16

Master validation report for Phase 4 (Python EDA + Statistical Analysis).
Consolidates the preflight, EDA, statistical testing, and cross-validation
work into a single sign-off document, per Step 19's final validation suite
requirement.

---

## 1. Preflight Result

`reports/python_analysis_preflight.md` — **passed**. Dataset intact
(43,648 rows, unmodified since the original Phase 1 build, `mtime`
verified), all required columns present with appropriate dtypes, all
planned EDA/statistical items confirmed feasible, no blocking gap found.

## 2. EDA Completion

All items from `PYTHON_ANALYSIS_PLAN.md` Phase 2 EDA scope were completed:

| Item | Module | Status |
|---|---|---|
| Delivery-time distribution (overall + central tendency/spread/percentiles) | `01_eda_overview.py` | ✅ |
| Distribution by Area/Category/Weather/Traffic/Vehicle | `01_eda_overview.py` | ✅ |
| SLA breach distribution (overall + by bucket) | `01_eda_overview.py` | ✅ |
| Outlier analysis (descriptive, no rows modified) | `01_eda_overview.py` | ✅ |
| Missingness/exclusion-flag summary | `01_eda_overview.py` | ✅ |
| Weekend/weekday comparison | `02_segment_comparisons.py` | ✅ |
| Temporal (weekly) pattern, partial-week flagging | `02_segment_comparisons.py` | ✅ |
| Agent-attribute (rating band, age band) comparisons | `02_segment_comparisons.py` | ✅ |
| Correlation analysis (distance, rating, age) | `03_correlation_and_pareto.py` | ✅ |
| Pareto ranking (area, category, weather×traffic) | `03_correlation_and_pareto.py` | ✅ |
| Analytical visualizations (7 figures, each plan-justified) | `06_visualizations.py` | ✅ |

Full report: `reports/python_eda_report.md`. Structured evidence:
`output/eda_summary.json`, `output/pareto_ranking.csv`, `output/figures/`.

## 3. Statistical Test Inventory

All 5 documented tests (+ Test 2's secondary two-group comparison)
executed, with test selection driven by the documented decision tree, not
assumed:

| Test | Selected (via assumption checks) | Significant | Effect Size |
|---|---|---|---|
| 1 — Traffic | Kruskal-Wallis | Yes | ε²=0.1404 (large) |
| 2 — Weather | Kruskal-Wallis | Yes | ε²=0.0517 (small) |
| 2b — Clear vs. adverse | Mann-Whitney | Yes | d=-0.4965 (small) |
| 3 — Agent rating (correlation) | Spearman (linearity failed) | Yes | r²=0.0677 (weak) |
| 4 — Distance (correlation) | Pearson (linearity held) | Yes | r²=0.0774 (weak) |
| 5 — Weekend vs. weekday | Mann-Whitney | **No** | d=-0.0013 (negligible) |

Full test-by-test writeup: `reports/statistical_analysis_report.md`.
Structured evidence: `output/statistical_test_results.json`.

## 4. Assumption Checks

Every test's assumption checks were run and logged, not assumed or
skipped:

- **Normality:** Shapiro-Wilk on a random 5,000-row (or full-group-if-smaller)
  sample per group, since scipy's implementation is both size-limited and,
  at full group sizes (thousands of rows), oversensitive per
  `STATISTICAL_ANALYSIS.md`'s own documented caveat. **Every group in every
  test rejected normality** — consistent with the plan's stated expectation
  that real-world delivery-time data is right-skewed.
- **Homogeneity of variance:** Levene's test, run on full (non-sampled)
  groups. Failed for Tests 1, 2, 2b, and 5.
- **Linearity (correlation tests):** Pearson-vs-Spearman gap diagnostic +
  scatter/band plots (`output/figures/05_*.png`, `06_*.png`) for direct
  visual review. Held for Test 4 (distance); did not hold well enough for
  Test 3 (agent rating), which used Spearman as a result.

**Every documented non-parametric/fallback path was used exactly where
its trigger condition was met — never applied by default, and never
skipped when triggered.**

## 5. SQL ↔ Python Reconciliation

`reports/python_sql_cross_validation.md` — **0 discrepancies** across 40+
individually checked figures: total rows, distinct Order_IDs, overall and
per-area breach rates, all 16 category counts, all vehicle/weather/traffic
counts, weekday/weekend metrics, breach counts by weather, all 4 correlation
coefficients, and validity-flag row counts. Every Python figure was
computed fresh from the CSV, not copied from any SQL report text.

## 6. Data Integrity Checks

| Check | Result |
|---|---|
| Row count | 43,648 |
| `cleaned_delivery.csv` file-modified timestamp | Unchanged since the original Phase 1 build (`2026-08-16 18:57:14`) — confirmed both before and after this phase's work |
| `amazon_delivery.csv` (raw) file-modified timestamp | Unchanged since `2026-08-05` |
| Duplicate `Order_ID` | 0 |
| Row-count sum reconciles across every group-by (area/category/vehicle/weather/traffic/weekend) | 43,648 in every case |
| Fresh `sla_breach_flag` recomputation vs. stored | 0 mismatches |
| `sql/schema/`, `sql/analysis/Q01-Q22`, PostgreSQL database | Not touched this phase |

## 7. Known Limitations

- **Agent analysis is attribute-level only** — no true `Agent_ID` exists;
  every rating/age finding is a rating/age-attribute association, never an
  individual-agent claim.
- **`bicycle` has 0 rows** in the analysis population — absent, not
  merely low-confidence, and not fabricated anywhere in this phase.
- **8 distinct observed weeks with a real 10-day gap** — limits trend
  claims.
- **No post-hoc pairwise comparisons** were performed for the two
  significant omnibus tests (Traffic, Weather) — `STATISTICAL_ANALYSIS.md`
  documents no post-hoc method or multiple-comparison correction, and none
  was invented.
- **Correlation is not causation** anywhere in this phase's outputs —
  stated explicitly in every relevant report section.
- **SLA methodology is frozen and unchanged** — every SLA-derived figure
  in this phase reads `sla_breach_flag`/`sla_threshold_minutes` as stored.

## 8. Candidate Findings

7 candidate findings documented in `reports/validated_findings_candidates.md`,
each with observation, metric, supporting analysis, statistical evidence,
SQL validation reference, limitation, and confidence level. **None is a
final executive recommendation; none contains a fabricated business-impact
or financial figure.**

## 9. Unresolved Issues

**None.** No planned analysis was infeasible, no cross-validation
discrepancy required investigation, and no assumption-check failure
lacked a documented fallback.

---

## Final Validation Checklist (Step 19)

- [x] 43,648 rows confirmed (preflight, EDA, statistical tests, cross-validation — all four independently confirm)
- [x] No source data modification (`amazon_delivery.csv`, `cleaned_delivery.csv` timestamps unchanged)
- [x] SLA unchanged (fresh recomputation = 0 mismatches; no percentile/threshold recalculated anywhere)
- [x] SQL/Python core KPI reconciliation (0 discrepancies, `reports/python_sql_cross_validation.md`)
- [x] No accidental filtering (every group-by sums to 43,648)
- [x] No duplicate inflation (0 duplicate `Order_ID`; no joins used in this phase — single flat DataFrame throughout)
- [x] Correct denominators (every rate states its exact filtered `n`)
- [x] Correct statistical tests (decision tree followed programmatically per test, not assumed)
- [x] Assumptions checked (Shapiro-Wilk, Levene's, linearity diagnostic — logged for every test, not skipped)
- [x] p-values correctly interpreted (reported alongside effect size, never alone; Test 5's non-significant result reported as such, not glossed over)
- [x] Effect sizes correctly interpreted (Cohen's conventional bands applied consistently; Test 1 vs. Test 2 explicitly contrasted by effect size, not just significance)
- [x] No causal overclaiming (every test/correlation interpretation uses "associated with," never "causes")
- [x] No fake Agent_ID (DimAgent/CSV `Agent_Age`/`Agent_Rating` used as attributes only, stated explicitly wherever used)
- [x] No fabricated bicycle data (0 rows, documented as absent, not filled in)
- [x] No undocumented feature engineering (rating/age "bands" used in Module 2 are transient, in-memory groupings for descriptive tables only — never written back to any dataset or treated as a new persisted feature)
- [x] No Power BI work
- [x] No DAX
- [x] No executive recommendations yet (candidate findings only, explicitly labeled as such)

**All items pass.**

---

# PHASE 4 APPROVED
