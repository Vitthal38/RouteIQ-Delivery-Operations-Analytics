# Business Requirements — RouteIQ

## Table of Contents
1. [Business Objectives](#business-objectives)
2. [Business Questions](#business-questions)
3. [Decision Makers](#decision-makers)
4. [Pain Points](#pain-points)
5. [Expected Decisions](#expected-decisions)
6. [Business Value](#business-value)
7. [Operational Impact](#operational-impact)
8. [Financial Impact](#financial-impact)
9. [Expected Dashboard Usage](#expected-dashboard-usage)
10. [Business Glossary](#business-glossary)

Related documents: `PROJECT_CHARTER.md` (goals, scope), `KPI_DEFINITIONS.md` (metric formulas), `ASSUMPTIONS.md` (validation of any figure referenced here)

---

## Business Objectives

1. Give operations leadership a single, queryable view of SLA performance instead of relying on anecdotal complaints.
2. Quantify — not just describe — which conditions (zone, weather, traffic, category) drive delay, using statistical testing rather than visual impression alone.
3. Convert that quantification into a small number of prioritized, evidence-backed recommendations (Pareto framing: which minority of conditions drives the majority of breach volume).
4. Do all of the above transparently — every derived business rule (e.g., SLA threshold) documented and frozen before results are seen, so findings are not tuned to a desired conclusion.

## Business Questions

The full 20+ question list is defined in the project brief and will be operationalized query-by-query in `SQL_ANALYSIS_PLAN.md`. At the requirements level, they cluster into five business themes:

| Theme | Representative Questions | Owner Persona |
|---|---|---|
| SLA performance | What % of deliveries breach SLA overall / by area? | VP Ops, City Ops Manager |
| Root cause | Is traffic/weather a statistically significant driver of delay? | City Ops Manager, CX Lead |
| Agent performance | Is agent rating related to delivery time? Are specific agents outlier-prone? | Fleet/Rider Manager |
| Category/area concentration | Which categories or zones account for disproportionate delay share? | VP Ops, Finance |
| Trend | Is delivery time trending up/down week over week? | VP Ops |

## Decision Makers

| Role | Decision They Make Using This Analysis |
|---|---|
| VP of Operations | Where to prioritize agent reallocation and process investment across zones |
| City Ops Manager | Which zone/time-window combinations need daily/weekly triage |
| Fleet/Rider Manager | Whether workload distribution across agents is a delay contributor |
| Customer Experience Lead | Whether to trigger proactive delay communication during specific conditions |
| Finance | Directional understanding of re-delivery/SLA-breach cost exposure (see Financial Impact — no cost figure exists in the source data, so this is directional only unless a documented proxy is defined) |

## Pain Points

- **No unified visibility:** delay knowledge is fragmented across complaint logs and manager intuition, not a single source of truth.
- **No root-cause quantification:** teams can observe "deliveries are slower in bad weather" without knowing whether that's a statistically meaningful effect or how much of total breach volume it explains.
- **No prioritization signal:** without a Pareto-style breakdown, effort gets spread evenly across zones/conditions instead of concentrated where it has the most impact.

## Expected Decisions

The dashboard and underlying analysis should be able to directly support statements such as: "Reallocate agents toward [zone] first" or "Flag [condition] for proactive customer messaging because it accounts for [X]% of breach volume." **Bracketed values are explicitly placeholders** — per the project's no-fabrication rule, they are filled in only after the corresponding SQL/Python analysis is run, never estimated in advance.

## Business Value

- Converts anecdotal ops knowledge into a documented, queryable, and defensible view.
- Enables prioritized (not evenly-spread) operational response.
- Provides a reusable analytical framework (SQL views, star schema, DAX measures) that could, in a production setting, be re-pointed at a live delivery feed.

## Operational Impact

- Ops managers gain a repeatable weekly review artifact (per the dashboard's structure) rather than an ad hoc report.
- Fleet/rider management gains an evidence base for agent workload conversations, distinct from anecdotal performance impressions.

## Financial Impact

**To be determined after analysis**, with an explicit caveat: the source dataset contains no cost, refund, or revenue field. Any financial impact statement in the final deliverable must either (a) be qualitative/directional ("reducing breach concentration in the top zone would materially reduce re-delivery cost, though a dollar/rupee figure is not derivable from this dataset") or (b) rely on a documented, clearly-labeled assumption/proxy defined in `ASSUMPTIONS.md` (e.g., an illustrative average re-delivery cost sourced from public reference material, not treated as measured fact). No specific currency figure will be presented as a measured finding unless it is directly computable from the data.

## Expected Dashboard Usage

- **Cadence:** framed as a weekly ops-review artifact (matching how City Ops Managers actually consume this category of dashboard), even though the underlying dataset is static/historical for this project.
- **Primary page for leadership:** Executive Summary (OTD%, breach rate, P90 trend) — designed to be readable in under a minute.
- **Drill paths:** Area & Category Performance and Delay Root Cause pages are for City Ops Managers and CX leads doing weekly triage; Agent Performance page is for Fleet/Rider Managers.

## Business Glossary

| Term | Definition |
|---|---|
| **SLA (Service Level Agreement)** | A target delivery-time threshold a company commits to. Not present as a labeled field in this dataset — defined here as an analyst-determined business rule (see `SLA_METHODOLOGY.md`), not a company-published target. |
| **SLA Breach** | A delivery whose actual delivery time exceeds the defined SLA threshold. |
| **OTD% (On-Time Delivery Rate)** | The share of deliveries that do *not* breach the defined SLA threshold. |
| **P90 Delivery Time** | The delivery time below which 90% of deliveries fall — used instead of the average because it reflects tail/worst-case customer experience, which drives complaints more than the mean does. |
| **Root Cause Share** | The share of total SLA-breach volume attributable to a specific condition (e.g., a weather type or traffic level), used to prioritize which conditions matter most (Pareto framing). |
| **Cost-to-Serve** | The operational cost of fulfilling a delivery, including re-delivery cost when SLA is missed. Referenced as a stakeholder interest in this project; not a calculated KPI, since no cost data exists in the source dataset. |
| **Zone / Area** | The dataset's `Area` field (Urban / Metropolitan / Semi-Urban), used as the geographic grouping unit for this project in place of true delivery-zone boundaries. |
| **Delay Driver** | Any dataset field hypothesized to influence delivery time (weather, traffic, distance, agent rating, category, vehicle) — "driver" here means statistically associated, not proven causal, unless explicitly qualified. |
