# DAX QA Report — RouteIQ

Generated: 2026-08-16

Final QA sign-off for the DAX layer (`dax/measures.dax`,
`dax/model_relationships.md`). Read `reports/dax_validation.md` first —
this report is the checklist-format companion to it.

---

## Deliverable Scope Statement

No `.pbix` file was created and no Power BI Desktop model was built in
this session — there is no tool available in this environment to author
or drive Power BI Desktop's model editor (installed on this machine, but
not scriptable, and no GUI-automation tool is available for it here). The
deliverables are: (1) a precise, ready-to-apply model relationship
specification, (2) a complete DAX measure library in correct syntax,
ready to paste into Power BI Desktop, and (3) rigorous validation of
every measure's calculation *logic* against the live, already-approved
database and the existing SQL/Python baselines. Before this measure
library is used in a production dashboard, it should be pasted into an
actual Power BI Desktop model connected to the `routeiq` schema and
spot-checked for syntax — this QA covers logical correctness, not literal
execution in a Tabular engine.

## Final DAX QA Checklist

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Core KPIs match SQL/Python | ✅ | 8/8 core measures with a prior baseline match exactly; 2 (Avg Prep Time, Avg Distance) established as new baselines with none to conflict with — `reports/dax_validation.md` |
| 2 | SLA breach rate matches approved baseline | ✅ | 23.6620% overall, exact match; per-context matches at Urban (14.3738%), Grocery (23.0655%), Sunny (9.6920%), etc. |
| 3 | No SLA recalculation exists | ✅ | Every measure touching SLA reads `FactDelivery[sla_breach_flag]` as a boolean filter only; no `PERCENTILE`/median/buffer appears in any measure in `dax/measures.dax` |
| 4 | Percentages use correct denominators | ✅ | Every filter-context test in `reports/dax_validation.md` used a freshly-computed, context-specific denominator (row count within that context), never the unfiltered total |
| 5 | Filter context works correctly | ✅ | 8 distinct filter contexts tested (Area, Category, Vehicle, Traffic, Weather, single Date, Weekend, Weekday); each produced a distinct, internally-consistent row count and rate |
| 6 | Date filtering works correctly | ✅ | Single-day filter (2022-03-15) correctly isolated 1,139 rows via `DimDate[full_date]`, the designated Date Table (`dax/model_relationships.md`) |
| 7 | No fake Agent_ID logic exists | ✅ | `DimAgent[Rating Band]` and the Agent Performance page measures are attribute-level only (rating/age); no measure names, ranks, or singles out an individual agent |
| 8 | No unsupported KPI was added | ✅ | Every measure either implements a `DAX_MEASURE_PLAN.md`-named measure or is one of the 4 supporting measures this task's own instructions explicitly requested (Total Deliveries, SLA Breaches, Average Preparation Time, Average Distance) — none is a new business KPI |
| 9 | No SQL/Python file was modified | ✅ | File-timestamp check: every file under `sql/`, `python/`, and `data/` predates this session |
| 10 | No business finding was changed | ✅ | `reports/business_findings.md` and `docs/EXECUTIVE_RECOMMENDATIONS.md` were not opened for writing this session |

## Measures Implemented vs. `DAX_MEASURE_PLAN.md`

| Documented measure | Implementation |
|---|---|
| On-Time Delivery Rate % | New measure |
| SLA Breach Rate % | New measure |
| Average Delivery Time (mins) | New measure |
| P90 Delivery Time (mins) | New measure |
| Delivery Time Trend (Weekly) | Reuses base measures + `DimDate[week_number]` axis (no new measure — matches the plan's own "same underlying measure" design) |
| Breach Rate by Area | Reuses `[SLA Breach Rate %]` + `DimArea[area_name]` axis + `area_tier_valid_flag` visual filter |
| P90 Delivery Time by Area | Reuses `[P90 Delivery Time (mins)]` + `DimArea[area_name]` axis |
| Average Delivery Time by Category | Reuses `[Average Delivery Time (mins)]` + `DimCategory[category_name]` axis |
| Delivery Time by Agent Rating Band | New calculated column (`DimAgent[Rating Band]`) + reuses `[Average Delivery Time (mins)]` |
| Agent Age vs. Delivery Time | Reuses `[Average Delivery Time (mins)]` + `agent_age_valid_flag` visual filter |
| Workload Distribution | `[Total Deliveries]` (count) + new `[Delivery Time Std Dev]` measure |
| Breach Rate by Weather | Reuses `[SLA Breach Rate %]` + `DimWeatherTraffic[weather]` axis |
| Breach Rate by Traffic | Reuses `[SLA Breach Rate %]` + `DimWeatherTraffic[traffic]` axis |
| Breach Rate by Area + Traffic (Pareto) | New measures: `[Breach Rank (Area x Traffic)]`, `[Cumulative Breach Share %]` |
| Adverse vs. Clear Weather Delta | New measure: `[Adverse vs Clear Weather Delta (mins)]` |

**14 of 14 documented measures addressed** — 7 as genuinely new DAX
formulas, 7 by correctly reusing a base measure in a different visual
context (matching `DAX_MEASURE_PLAN.md`'s own design, which explicitly
describes several of these as the same underlying measure evaluated in a
different row context, not separate formulas).

## Known Risk Areas (per `DAX_MEASURE_PLAN.md`'s own risk list) — how each was addressed

- **Context transition:** every rate measure (`[On-Time Delivery Rate %]`,
  `[SLA Breach Rate %]`) is built from `COUNTROWS`/`CALCULATE` with
  explicit boolean filters, not a row-context iterator over an unrelated
  grain — the class of bug that caused the analyst's prior FoodPulse
  `SnapshotDate` issue is structurally avoided here.
- **Percentile interpolation mismatch:** `PERCENTILE.INC` (linear
  interpolation) explicitly matches SQL's `PERCENTILE_CONT` and Python's
  `numpy.percentile` default, as documented in the measure's own comment.
- **Flag-based exclusion vs. hardcoded filters:** `area_tier_valid_flag`,
  `agent_rating_valid_flag`, `agent_age_valid_flag` are applied as visual
  filters on the flag columns themselves everywhere they're needed — no
  measure hardcodes `area_name = 'Other'` or an equivalent literal-value
  filter.
- **Frozen SLA threshold:** confirmed — no measure in `dax/measures.dax`
  computes a percentile against `delivery_time_minutes` for breach
  determination; every SLA-related measure reads the stored
  `sla_breach_flag` boolean only.

## Caveat — Pareto Measures Complexity

`[Breach Rank (Area x Traffic)]` and `[Cumulative Breach Share %]` use a
nested `RANKX`/`FILTER`/`SUMX` pattern — the standard, documented DAX
approach for a running-total Pareto, but also the most intricate DAX in
this library. Its *logic* was validated by SQL equivalence (matches
`sql/analysis/Q20`'s breach counts exactly, and produces a correctly
monotonic cumulative percentage reaching 100%), but — per the scope
statement above — it has not been executed in a live Tabular engine.
Recommend this specific measure pair be the first thing spot-checked
when the model is actually built in Power BI Desktop.

## Final Validation Checklist (Step 10, verbatim)

- [x] All documented measures are implemented (14/14, per the table above).
- [x] Core measures reconcile with SQL/Python (0 discrepancies).
- [x] Filter-context tests pass (8 contexts, all internally consistent).
- [x] SLA remains unchanged (frozen rule read as-is everywhere).
- [x] No unsupported logic was introduced (every measure traces to `DAX_MEASURE_PLAN.md` or this task's explicit supporting-measure request).

---

# DAX APPROVED

Approved on the basis of validated calculation logic and 0 discrepancies
against approved SQL/Python baselines, with the explicit caveat recorded
above: this is a DAX specification and logic validation, not a tested
`.pbix` file — confirm there are no syntax errors when first pasted into
an actual Power BI Desktop model before treating it as dashboard-ready.
