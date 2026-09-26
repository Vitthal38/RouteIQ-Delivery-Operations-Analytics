# JupyterLab Conversion Validation Report — RouteIQ

Generated: 2026-08-17

Documents the conversion of the already-approved Phase 4 Python EDA and
statistical analysis (`python/analysis/01-06*.py`) into a recruiter/
interviewer-friendly JupyterLab presentation layer. **This is a
presentation-layer conversion, not a new analysis** — no calculation,
statistical methodology, SLA rule, SQL, DAX, or Power BI artifact was
created, changed, or reinterpreted. Every number below was either read
directly from an already-approved output file or recomputed fresh using
the existing, approved `python/analysis/*.py` functions, imported and
called directly (never reimplemented).

---

## 1. Notebooks Created

All 6 requested notebooks were created in `python/notebooks/`:

| Notebook | Business question | Reuses |
|---|---|---|
| `01_eda_overview.ipynb` | What does the dataset look like at a glance, and what is the shape of `Delivery_Time`? | `01_eda_overview.py`: `describe_delivery_time`, `sla_breach_distribution`, `outlier_analysis`, `missingness_exclusion_summary` |
| `02_delivery_time_analysis.ipynb` | How does delivery time vary by area, category, weather, traffic, vehicle, and day type? | `01_eda_overview.py`: `describe_by_segment`; `02_segment_comparisons.py`: `weekend_vs_weekday`, `weekly_temporal_pattern` |
| `03_sla_analysis.ipynb` | Where does SLA breach *rate* concentrate, by area and category? | Direct reads of the frozen `sla_breach_flag` / `sla_threshold_minutes` columns |
| `04_root_cause_analysis.ipynb` | Where does SLA breach *volume* concentrate (Pareto), and which conditions are associated with it? | `03_correlation_and_pareto.py`: `pareto_ranking` |
| `05_statistical_analysis.ipynb` | Which observed patterns are statistically significant, and how large is each effect? | `04_statistical_tests.py`: `_run_multi_group_test`, `_run_two_group_test`, `_run_correlation_test` (same fixed RNG seed and call order as the approved script's `main()`) |
| `06_sql_cross_validation.ipynb` | Do the Python-computed KPIs reconcile exactly with the independently-built SQL layer from Phase 3? | Mirrors `05_cross_validation.py`'s calculations; SQL-side figures quoted from the approved `reports/python_sql_cross_validation.md` |

A shared helper, `python/notebooks/_nb_theme.py`, holds only path setup
(`setup_paths()`) and the RouteIQ matplotlib theme (`apply_theme()`) —
**no analytical logic**. Every calculation in every notebook is imported
from the existing `python/analysis/*.py` modules via `importlib`, not
rewritten.

## 2. Execution Status

All 6 notebooks were executed top to bottom via
`python -m nbconvert --to notebook --execute --inplace` (`jupyter nbconvert`
was not on `PATH` in this environment; the equivalent `python -m nbconvert`
invocation was used instead — identical execution engine).

| Notebook | Cells | Executed | Error cells |
|---|---|---|---|
| `01_eda_overview.ipynb` | 19 | ✅ | 0 |
| `02_delivery_time_analysis.ipynb` | 21 | ✅ | 0 |
| `03_sla_analysis.ipynb` | 11 | ✅ | 0 |
| `04_root_cause_analysis.ipynb` | 16 | ✅ | 0 |
| `05_statistical_analysis.ipynb` | 31 | ✅ | 0 |
| `06_sql_cross_validation.ipynb` | 19 | ✅ | 0 |

**0 errors across all 6 notebooks**, confirmed by parsing every cell's
`outputs` for an `error` output type after execution (not just checking the
`nbconvert` exit message).

## 3. Figures Reproduced

Every chart type on the approved list was produced, each tied to a
documented business/analytical question (no chart added merely to
increase the visual count):

- Delivery-time distribution (01)
- Delivery time by category, by traffic, by weather, by vehicle (02)
- Weekday vs. weekend comparison (02)
- Weekly trend, partial-week flagged (02)
- SLA breach rate by area, by category (03)
- Area × Traffic breach concentration (Pareto, dual-axis) (04)
- SLA breach rate by traffic, by weather (04)
- Statistical-test supporting visuals: agent rating vs. delivery time,
  agent age band, distance vs. delivery time scatter with linear fit (05)

All charts use the approved RouteIQ palette (Navy `#123B5D` = primary
analytical series, Teal `#00A6A6` = positive/secondary series, Coral
`#E45756` = SLA breach/risk only) with sample sizes captioned on every
chart showing a rate or mean. No 3D charts, no pie charts, no dual-axis
chart other than the one already-approved Pareto pattern, no decorative
chart added.

## 4. Key KPI Reconciliation

Every KPI the task specified for verification was independently confirmed,
either by direct computation in the notebooks or by reading the approved
output files:

| KPI | Required value | Notebook result | Match |
|---|---|---|---|
| Total rows | 43,648 | 43,648 (`01`, `06`) | ✅ |
| Overall SLA breach rate | 23.6620% | 23.6620% (`03`, `06`) | ✅ |
| Traffic effect size (ε²) | 0.1404 | 0.1404, Kruskal-Wallis H=6132.4554 (`05`, Test 1) | ✅ |
| Weather effect size (ε²) | 0.0517 | 0.0517, Kruskal-Wallis H=2262.8928 (`05`, Test 2) | ✅ |
| Weekend vs. weekday p-value | 0.9658 | 0.965772 → 0.9658 (`05`, Test 5) | ✅ |
| Metropolitian breach-volume concentration | 83.7335% | 83.7335% (`04`, `06`) | ✅ |
| Semi-Urban breach rate | 100%, n=152 | 100.0000%, n=152 (`03`) | ✅ |

*(`Metropolitian` — not "Metropolitan" — is the actual spelling stored in
the source data and preserved verbatim throughout, per
`DATABASE_DATA_DICTIONARY.md`'s explicit note; it is not a typo introduced
in this conversion.)*

**No discrepancy was found for any of the 7 required figures.** No value
was adjusted, re-rounded, or silently reconciled — every notebook figure
above is the first result each computation produced.

## 5. Statistical-Result Reconciliation

`05_statistical_analysis.ipynb` calls the exact test functions from
`04_statistical_tests.py` (not a reimplementation) with the same fixed RNG
seed (42) and the same call order as that script's own `main()`, so the
Shapiro-Wilk subsampling draws are identical. The notebook's final cell
loads the approved `output/statistical_test_results.json` (read-only) and
compares `p_value`, `effect_size_value`, and `significant_at_alpha_0.05`
for all 6 tests (1, 2, 2b, 3, 4, 5) against the notebook's freshly computed
results.

**Notebook output:**
```
ALL RESULTS MATCH output/statistical_test_results.json EXACTLY
```

0 mismatches across all 6 tests × 3 fields = 18 checked values.

## 6. SQL Cross-Validation Status

`06_sql_cross_validation.ipynb` recomputes, fresh from
`data/cleaned/cleaned_delivery.csv`, every figure previously reconciled in
`reports/python_sql_cross_validation.md`: total rows, breach rate, breach
rate by area (4/4), category counts (16/16), vehicle counts (3/3), weather
counts (6/6), traffic counts (4/4), weekday/weekend counts and averages,
all 4 correlation coefficients, and the Metropolitian Pareto concentration
figure. The SQL-side values are quoted from the approved report (this
notebook does not connect to PostgreSQL or re-run any `sql/analysis/*.sql`
file).

**Notebook output:**
```
Category counts: 16 categories checked, 0 mismatches
Vehicle counts: 3 types checked, 0 mismatches
Weather counts: 6 conditions checked, 0 mismatches
Traffic counts: 4 levels checked, 0 mismatches
Python-computed Metropolitian cumulative breach share: 83.7335%
SQL (Q14) documented figure: 83.7335%
MATCH
ALL CHECKS PASS
```

**0 discrepancies**, consistent with `reports/python_sql_cross_validation.md`'s
original conclusion.

## 7. Discrepancies Found

**None.** Every figure checked — the 7 required KPIs, the 18 statistical
result fields, and the 40+ figures in the SQL cross-validation notebook —
matched the approved source exactly on first computation. No STOP condition
was triggered.

## 8. Confirmation: No Source/SQL/DAX/Power BI Artifacts Modified

Verified by file-modification timestamp, both before and after the
notebook build/execution work (all protected files retain their original
2026-08-16 timestamps from prior phases — unchanged by this conversion,
run on 2026-08-17):

| File / directory | Status |
|---|---|
| `data/cleaned/cleaned_delivery.csv` | Unchanged (`mtime` 2026-08-16 18:57:14) |
| `data/cleaned/sla_reference.csv` | Unchanged (`mtime` 2026-08-16 18:57:14) |
| `output/eda_summary.json` | Unchanged (`mtime` 2026-08-16 22:27:28) |
| `output/statistical_test_results.json` | Unchanged (`mtime` 2026-08-16 22:26:43) |
| `output/pareto_ranking.csv` | Unchanged (`mtime` 2026-08-16 22:25:14) |
| `output/figures/*.png` (7 files) | Unchanged — no file newer than the notebook build |
| `sql/` (schema + all 22 analysis queries) | Untouched — no file newer than the notebook build |
| `dax/` (model relationships + measures) | Untouched — no file newer than the notebook build |
| `docs/POWERBI_DASHBOARD_MOCKUP.md`, `output/dashboard_mockups/` | Untouched |
| Existing `reports/*.md` (all prior-phase reports) | Untouched — this report is a new addition, not an edit to any existing report |

**Why the output files are untouched despite the notebooks calling the
approved analysis functions:** every `python/analysis/*.py` module
separates its pure calculation functions (e.g. `describe_delivery_time()`,
`pareto_ranking()`, `_run_multi_group_test()`) from its `main()` function,
and only `main()` writes to disk (`save_json()` / `to_csv()`). Every
notebook in this conversion imports and calls the pure functions directly
and **never calls any module's `main()`** — so no approved output artifact
was ever at risk of being overwritten, even with identical, deterministic
values. Where a notebook needed a number `main()` alone assembles (Module
5's cross-validation dict, Module 6's saved figures), the notebook
recomputes the same expressions inline and renders charts with `plt.show()`
instead of the file-writing `save()` helper — nothing is written to
`output/figures/` by any notebook.

## 9. Known, Carried-Forward Limitations (unchanged from Phase 4)

Restated, not reinterpreted, in every notebook where relevant:

- Agent analysis is attribute-level only — no true `Agent_ID` exists; no
  notebook performs or implies individual-agent tracking.
- `bicycle` has 0 rows in the cleaned dataset — absent, not fabricated,
  in every vehicle comparison.
- 8 distinct observed weeks with a genuine 10-day gap (19–28 Feb) limits
  trend-strength claims.
- No pairwise post-hoc comparisons were added for the two significant
  omnibus tests (Traffic, Weather) — none is documented in
  `STATISTICAL_ANALYSIS.md`, and inventing one was avoided, per the
  project's standing rule.
- No causal language appears anywhere in any notebook — every statistical
  and correlational result is reported as an "observed association."
- `sla_threshold_minutes` is an analyst-defined benchmark, not a
  company-published SLA target — stated wherever a breach/OTD figure
  appears.

---

## Final Gate

- [x] All 6 notebooks created in `python/notebooks/`
- [x] All 6 notebooks executed top to bottom with 0 errors
- [x] Every required chart type reproduced, each tied to a documented question
- [x] All 7 required KPIs verified exactly (§4)
- [x] All 6 statistical tests reconciled exactly against the approved JSON (§5)
- [x] SQL cross-validation reproduced with 0 discrepancies (§6)
- [x] No discrepancy found anywhere in this conversion (§7)
- [x] No source data, SQL, DAX, Power BI, or existing report/output artifact modified (§8)
- [x] No new finding, recommendation, business metric, or methodology introduced

# JUPYTERLAB CONVERSION APPROVED
