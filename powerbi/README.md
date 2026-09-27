# Power BI — RouteIQ Delivery Operations

## What exists right now

`powerbi/RouteIQ_v1.pbix` is the v1 report built earlier in this project: 4 pages (Executive Overview,
Area & Category, Agent Performance, Delay Root Cause), 12 DAX measures, connected to the `routeiq`
PostgreSQL schema. Screenshots of the actual (not mockup) report are in `powerbi/screenshots/`.

**This file has not yet been rebuilt to the structure below.** Automating Power BI Desktop itself is out
of reach from here — the `.pbix` was open in Desktop while this project was being reworked, so it could
not safely be edited directly. What follows is the exact, ready-to-apply spec for the rebuild: every
measure, every page's content, and the click-by-click steps for the parts (drillthrough, tooltip pages,
a What-If parameter, dynamic text) that a hands-on session in Desktop needs to add.

**Known issues in the current v1 file** (carried over from earlier review, still open):
missing P90 KPI card, breach rate displayed as "24%" instead of "23.66%", clipped text on several pages,
missing sample sizes on some bars, static (non-dynamic) callout text, no drillthrough or tooltip pages,
default-blue trend lines instead of the navy/teal palette, and one Pareto label where a tie shows a
duplicated cumulative percentage (documented in `docs/limitations.md`).

## Target: 5 pages

### Page 1 — Executive Overview

KPI cards: `[Total Deliveries]`, `[Average Delivery Minutes]`, `[Median Delivery Minutes]`,
`[P75 SLA Minutes]`, `[P90 Delivery Minutes]`, `[On-Time Rate %]`, `[Breach Rate %]`.

Visuals: delivery-time trend by week (average line + P90 line, navy/teal), breach-rate trend by week,
traffic-level distribution (column chart), area × traffic breach concentration (top segments only — full
Pareto lives on Page 3). One dynamic executive-summary text box (see "Dynamic text" below).

### Page 2 — Operational Performance

Analyse traffic, weather, area and hour together: a breach-rate heatmap (area × category or hour ×
traffic), ranked bars by area and by traffic, a weekly trend, and a segment-comparison table with sample
size shown on every row.

### Page 3 — SLA & Performance Factors

The full area × traffic Pareto (deterministic tie order — see `[Breach Rank (Area x Traffic)]` below), a
**What-If SLA threshold parameter** (see below) driving the breach KPIs live, and a factor-comparison
chart (risk ratio by factor, matching `outputs/figures/risk_ratios_by_factor.png`). Label this "Factors
associated with breaches," never "causes."

### Page 4 — Agent & Segment Analysis

Rating bands, age bands, rating × traffic, age × traffic: breach rate, delivery volume and sample size
together on every visual. No individual-agent table or ranking (no agent identifier exists — see
`docs/limitations.md`). Caption the weak-vs-strong framing correctly: the rating/age *step* pattern is a
large practical effect (`docs/analytical_findings.md` §2–3), not a weak one — do not understate it here
just because the underlying correlation is weak.

### Page 5 — Insights & Recommendations

One row per recommendation, each following **Finding → Evidence → Recommended action → KPI to monitor →
Limitation** — see `docs/archive/v1_analysis/EXECUTIVE_RECOMMENDATIONS_v1.md` for the format and
`docs/analytical_findings.md` for the corrected findings to base the rewrite on (the rating/age
conclusion changed — it is no longer "weak, deprioritise").

## DAX measures (clean names, one definition each)

```dax
Total Deliveries := COUNTROWS ( FactDelivery )

Breached Deliveries :=
CALCULATE ( COUNTROWS ( FactDelivery ), FactDelivery[sla_breach_flag] = TRUE )

Breach Rate % :=
DIVIDE ( [Breached Deliveries], [Total Deliveries] ) * 100

On-Time Rate % :=
DIVIDE ( [Total Deliveries] - [Breached Deliveries], [Total Deliveries] ) * 100

Average Delivery Minutes := AVERAGE ( FactDelivery[delivery_time_minutes] )

Median Delivery Minutes := MEDIAN ( FactDelivery[delivery_time_minutes] )

P75 SLA Minutes := PERCENTILE.INC ( FactDelivery[delivery_time_minutes], 0.75 )

P90 Delivery Minutes := PERCENTILE.INC ( FactDelivery[delivery_time_minutes], 0.9 )

-- Deterministic Pareto: DENSE RANK on breach count ties silently (v1's known issue).
-- RANKX on a concatenated (breach count, segment name) key breaks ties the same way every time.
Breach Rank (Area x Traffic) :=
RANKX (
    ALLSELECTED ( DimArea[area_name], DimWeatherTraffic[traffic] ),
    CALCULATE ( [Breached Deliveries] ) * 100000
        - RANKX ( ALLSELECTED ( DimArea[area_name] ), DimArea[area_name],, ASC ),   -- name-based tiebreak
    , DESC, DENSE
)

Cumulative Breach Share % :=
VAR CurrentRank = [Breach Rank (Area x Traffic)]
VAR TotalInSelection =
    CALCULATE ( [Breached Deliveries], ALLSELECTED ( DimArea[area_name], DimWeatherTraffic[traffic] ) )
VAR RunningTotal =
    SUMX (
        FILTER (
            ALLSELECTED ( DimArea[area_name], DimWeatherTraffic[traffic] ),
            [Breach Rank (Area x Traffic)] <= CurrentRank
        ),
        [Breached Deliveries]
    )
RETURN DIVIDE ( RunningTotal, TotalInSelection ) * 100

Adverse vs Clear Weather Delta (mins) :=
CALCULATE ( [Average Delivery Minutes], DimWeatherTraffic[weather] <> "Sunny" )
    - CALCULATE ( [Average Delivery Minutes], DimWeatherTraffic[weather] = "Sunny" )

-- What-If parameter (create via Modeling -> New Parameter -> Numeric range 0.5-0.95, step 0.01)
Selected SLA Threshold = GENERATESERIES ( 0.5, 0.95, 0.01 )

SLA Threshold (Selected) := SELECTEDVALUE ( 'Selected SLA Threshold'[Selected SLA Threshold], 0.75 )

-- Only correct if the parameter also drives a per-category threshold measure; see the What-If
-- instructions below for why a single global percentile is a simplification of the real per-category P75.
Breach Rate % (Selected SLA) :=
VAR Pctl = [SLA Threshold (Selected)]
VAR ThresholdByCategory =
    ADDCOLUMNS (
        VALUES ( DimCategory[category_name] ),
        "@Threshold", CALCULATE ( PERCENTILE.INC ( FactDelivery[delivery_time_minutes], Pctl ) )
    )
VAR BreachesAtSelected =
    SUMX (
        ThresholdByCategory,
        CALCULATE (
            COUNTROWS ( FactDelivery ),
            FactDelivery[delivery_time_minutes] > EARLIER ( [@Threshold] )
        )
    )
RETURN DIVIDE ( BreachesAtSelected, [Total Deliveries] ) * 100
```

Audit notes (per the review that triggered this rebuild):
- Every measure above has an explicit, single filter context — no measure relies on an ambient row
  context that could silently change grain.
- `DIVIDE()` is used everywhere a ratio is computed, so no measure can divide by zero.
- No calculated column is created except the two banded columns already validated
  (`DimAgent[Rating Band]`, an age-band column built the same way) — both documented in
  `powerbi/model_relationships.md`.
- `Breach Rate % (Selected SLA)` recomputes the threshold **per category**, matching the frozen
  methodology (`docs/methodology.md`) — it does not use one global percentile across all categories,
  which would silently change the SLA definition.

## Dynamic text (replace every static callout)

Static text such as *"Metropolitan accounts for the largest share of breach volume"* becomes false the
moment a filter changes it. Replace with a measure-driven text box:

```dax
Executive Summary Text :=
VAR SelArea = IF ( HASONEVALUE ( DimArea[area_name] ), SELECTEDVALUE ( DimArea[area_name] ), "All areas" )
VAR SelTraffic = IF ( HASONEVALUE ( DimWeatherTraffic[traffic] ), SELECTEDVALUE ( DimWeatherTraffic[traffic] ), "all traffic conditions" )
RETURN
    SelArea & " (" & SelTraffic & "): " & FORMAT ( [Breach Rate %], "0.0" ) & "% breach rate on "
    & FORMAT ( [Total Deliveries], "#,0" ) & " deliveries."
```

Bind this to a Card or Text Box visual (Format → General → Title/Text → `fx`, bound to the measure) on
every page that currently has a hard-coded finding.

## Drillthrough

- Page 1 (a bad week on the trend line) → Page 3, filtered to that week.
- Page 2 (an area bar or heatmap cell) → Page 3, filtered to that area.
- Set up via **Format pane → Drillthrough** on the target page, adding `week_number` / `area_name` as
  the drillthrough filter field, then right-click a data point on the source page → Drill through.

## Tooltip pages

Build a small report page (Format → Page information → "Allow use as tooltip", ~320×240px) showing
`[Total Deliveries]`, `[Breach Rate %]` and the relevant risk ratio for the hovered segment. Assign it via
the source visual's Format pane → Tooltip → Type: Report page.

## What-If SLA parameter — a caveat to disclose on the page itself

A single global percentile parameter is a **simplification**: the real SLA methodology computes P75 (or
whichever percentile) **per category**, not once across the whole dataset (`docs/methodology.md`). The
`Breach Rate % (Selected SLA)` measure above does the per-category recomputation correctly, but iterating
`PERCENTILE.INC` over 16 categories for every slicer interaction is the single most expensive measure in
the model — test it against the actual row count before shipping, and if it is too slow interactively,
fall back to showing the four pre-computed P70/P75/P80/P90 scenarios from
`outputs/tables/sla_sensitivity_overall.csv` as a small static table instead of a live slider.
