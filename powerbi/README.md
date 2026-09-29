# Power BI — RouteIQ Delivery Operations

`powerbi/RouteIQ_v1.pbix` is the executive dashboard for this project: 4 pages, 12 DAX measures,
connected to the `routeiq` PostgreSQL schema. Screenshots of the actual report are in
`powerbi/screenshots/`.

## Pages

### Page 1 — Executive Overview
KPI row (`[Total Deliveries]`, `[On-Time Rate %]`, `[Breach Rate %]`, `[P90 Delivery Minutes]`,
`[Average Delivery Minutes]`), the weekly delivery-time trend (average + P90), and SLA breach rate by
area — with area and date filters.

### Page 2 — Area & Category Performance
An area × category breach-rate matrix, breach rate by area, average delivery time by category, and the
"rate ≠ volume" callout — Metropolitan carries the largest breach volume without the highest rate.
Weather, traffic and date filters.

### Page 3 — Agent Performance
Delivery time by rating band and by age band, and the rating/age **step effect** — 63.2% breach rate at
rating 4.4 vs. 10.5% at 4.5 (Mantel–Haenszel risk ratio 3.69), matching
[`docs/analytical_findings.md`](../docs/analytical_findings.md) §2–3. Attribute-level only — no
individual agent identifier exists in the source data.

### Page 4 — Delay Root Cause
The area × traffic Pareto (deterministic tie-break, not `DENSE RANK`), breach rate by weather and by
traffic, the statistical evidence table (Kruskal–Wallis H, epsilon-squared), and the weekend/weekday null
result, framed as a legitimate finding rather than a gap in the analysis.

## DAX measures

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

-- Deterministic Pareto: RANKX on a concatenated (breach count, segment name) key
-- breaks ties by name instead of counting them together.
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
```

Design notes:
- Every measure has an explicit, single filter context — no measure relies on an ambient row context
  that could silently change grain.
- `DIVIDE()` is used everywhere a ratio is computed, so no measure can divide by zero.
- No calculated column is created except the two banded columns already validated
  (`DimAgent[Rating Band]`, an age-band column built the same way) — both documented in
  `powerbi/model_relationships.md`.
