# DAX Validation Report — RouteIQ

Generated: 2026-08-16

**Methodology note (read first):** no Power BI Desktop model or live
Tabular/DAX engine is available in this environment to execute the
measures in `dax/measures.dax` directly. Each measure's calculation logic
is instead validated by translating it into an equivalent SQL query, run
against the same live, already-approved `routeiq` PostgreSQL database the
measures would connect to in Power BI, and compared against the existing
approved SQL (`sql/analysis/Q01`–`Q22`) and Python
(`output/eda_summary.json`, `output/statistical_test_results.json`)
baselines. Because DAX and SQL express the same aggregation logic over
the same underlying rows, a query that reproduces a measure's formula
exactly and matches the approved baseline is strong evidence the DAX
measure is correct — it does not substitute for opening the model in
Power BI Desktop and confirming there is no syntax error, which is
recommended before production use (noted again in `reports/dax_qa_report.md`).

---

## Core Measures — Unfiltered (whole dataset, n = 43,648)

| Measure | DAX Result (SQL-equivalent) | SQL Baseline | Python Baseline | Difference | Status |
|---|---|---|---|---|---|
| Total Deliveries | 43,648 | 43,648 (`sql/analysis/Q07`) | 43,648 (`output/eda_summary.json`) | 0 | ✅ MATCH |
| SLA Breaches | 10,328 | 10,328 (`Q01`, `Q12`) | 10,328 (`05_cross_validation.py`) | 0 | ✅ MATCH |
| SLA Breach Rate % | 23.6620% | 23.6620% (`Q01`) | 23.6620% (`05_cross_validation.py`) | 0 | ✅ MATCH |
| On-Time Delivery Rate % | 76.3380% | 76.3380% (`_final_test_suite.sql` Test 5) | — (100 − 23.6620, consistent) | 0 | ✅ MATCH |
| Average Delivery Time (mins) | 124.9145 (rounds to 124.91) | 124.91 (`Q02` area avg roll-up), 124.91 (`output/eda_summary.json`) | 124.91 | 0 (rounding-precision only) | ✅ MATCH |
| P90 Delivery Time (mins) | 195.0000 | 195.00 (`output/eda_summary.json`) | 195.00 | 0 | ✅ MATCH |
| Average Preparation Time (mins) | 9.9913 | *(no prior headline baseline existed — see note)* | *(none)* | n/a | ✅ COMPUTED, NEW BASELINE |
| Average Distance (km) | 9.7163 | *(no prior headline baseline existed — see note)* | *(none)* | n/a | ✅ COMPUTED, NEW BASELINE |
| Delivery Time Std Dev | 51.9326 | 51.93 (`output/eda_summary.json` std) | 51.93 | 0 | ✅ MATCH |

**Note on Average Preparation Time / Average Distance:** these two are
supporting measures this task's own instructions requested for
validation, but neither was previously reported as a headline figure in
any Phase 1–5 approved report (`prep_time_minutes`/`distance_km` were
used as correlation *inputs*, e.g. Test 4, never as a standalone average
KPI). There is no discrepancy to report because there is no prior figure
to disagree with — this validation run establishes them as the first
approved baseline for these two supporting measures.

**8 of 8 core measures with a prior baseline match exactly. 0 discrepancies.**

---

## Filter-Context Testing

Each context below was computed independently via SQL, not derived from
the unfiltered figures, to prove the numerator and denominator both
genuinely change with the filter (not just the numerator, which is the
classic context-transition bug class `DAX_MEASURE_PLAN.md` warns about).

| Filter Context | Total Deliveries | SLA Breach Rate % | Avg Delivery Time | Cross-check |
|---|---|---|---|---|
| *(none — baseline)* | 43,648 | 23.6620% | 124.91 | — |
| Area = Urban | 9,726 | 14.3738% | 109.44 | Matches `sql/analysis/Q01`/`Q02` Urban row exactly |
| Category = Grocery | 2,688 | 23.0655% | 26.54 | n and avg match `Q06`/`Q14` Grocery row exactly (breach count 620 matches `Q14` exactly) |
| Vehicle = scooter | 14,607 | 18.1283% | 116.35 | n and avg match `Q21` scooter row exactly |
| Traffic = Jam | 13,725 | 42.5792% | 147.76 | n and avg match `Q03` Jam row exactly |
| Weather = Sunny | 7,078 | 9.6920% | 103.66 | n matches `Q13`; breach rate matches `Q12` Sunny row exactly (9.6920%) |
| Date = 2022-03-15 (single day) | 1,139 | 11.0623% | 110.59 | New — a single-day slice was never previously reported; internally consistent (denominator ≠ any other tested context) |
| Weekend = true | 12,021 | 23.6087% | 124.96 | n and avg match `Q07` Weekend row exactly |
| Weekday (Weekend = false) | 31,627 | 23.6823% | 124.90 | n and avg match `Q07` Weekday row exactly |

**Numerator/denominator correctness confirmed:** every context above has
a distinct row count (denominator) that sums correctly with its
complement where applicable (Weekend 12,021 + Weekday 31,627 = 43,648),
and each breach rate is freshly computed as `breaches in context / rows
in context` — never the unfiltered rate reused, and never the unfiltered
denominator applied to a filtered numerator.

## KPI Identity Check — OTD% + Breach Rate % = 100 (3 contexts, per `DAX_MEASURE_PLAN.md`'s explicit requirement)

| Context | OTD% | Breach Rate % | Sum |
|---|---|---|---|
| No filter | 76.3380 | 23.6620 | **100.0000** |
| Area = Urban | 85.6262 | 14.3738 | **100.0000** |
| Category = Grocery | 76.9345 | 23.0655 | **100.0000** |

Identical to `sql/analysis/_final_test_suite.sql` Test 5's already-approved
result at the same three contexts — the DAX pair `[On-Time Delivery Rate %]`
/ `[SLA Breach Rate %]` will hold this identity for the same reason the
SQL layer does: both read `sla_breach_flag` from the same stored column,
partitioned only by `TRUE`/`FALSE`, so every row is counted in exactly
one side.

## Agent Rating Band — cross-check against `sql/analysis/Q04`

| Rating Band | n | Avg Delivery Time | Matches Q04 |
|---|---|---|---|
| 2.5 | 102 | 175.45 | ✅ |
| 3.0 | 121 | 177.47 | ✅ |
| 3.5 | 1,106 | 174.08 | ✅ |
| 4.0 | 6,695 | 165.06 | ✅ |
| 4.5 | 31,574 | 114.82 | ✅ |
| 5.0 | 3,996 | 120.98 | ✅ |

**All 6 bands match `Q04`'s already-approved output exactly** — confirms
the `DimAgent[Rating Band]` calculated column's `FLOOR`-based logic (the
same value-based pattern validated defect-free in the SQL remediation) is
correctly specified.

## Pareto Measures — `[Breach Rank (Area x Traffic)]` / `[Cumulative Breach Share %]`

| Rank | Area | Traffic | Breach Count | Cumulative % |
|---|---|---|---|---|
| 1 | Metropolitian | Jam | 4,877 | 47.2211% |
| 2 | Metropolitian | Medium | 2,205 | 68.5709% |
| 3 | Metropolitian | High | 799 | 76.3071% |
| 4 | Urban | Jam | 782 | 83.8788% |
| 5 | Metropolitian | Low | 767 | 91.3052% |

Every `breach_count` value matches `sql/analysis/Q20_area_traffic_breach_concentration.sql`'s
corresponding row exactly (e.g., Metropolitian/Jam = 4,877 breaches in
both). The rank + cumulative-% layer is new arithmetic on top of already-
approved counts, computed correctly (monotonically increasing, reaches
100% across all 15 observed combinations — verified beyond the top 5
shown here).

## Adverse vs. Clear Weather Delta

| | Clear (Sunny) | Adverse (non-Sunny) | Delta |
|---|---|---|---|
| Avg delivery time | 103.6645 (rounds to 103.66) | 129.0273 (rounds to 129.03) | 25.3629 |

Both group averages match `sql/analysis/Q19_clear_vs_adverse_weather_delta.sql`
exactly (103.66 / 129.03). The delta itself (25.3629 minutes) is new
arithmetic, correctly computed as `Adverse − Clear`.

---

## Summary

**0 discrepancies found across 8 core measures, 8 filter contexts, the
3-context KPI identity check, the 6-band agent rating cross-check, the
Pareto measures, and the weather-delta measure — every figure with a
prior approved baseline matches it exactly.**
