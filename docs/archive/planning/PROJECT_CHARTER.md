# Project Charter — RouteIQ: Last-Mile Delivery SLA & Operations Risk Analytics

## Table of Contents
1. [Business Context](#business-context)
2. [Problem Statement](#problem-statement)
3. [Goals](#goals)
4. [Success Criteria](#success-criteria)
5. [KPIs](#kpis)
6. [Stakeholders](#stakeholders)
7. [Business Constraints](#business-constraints)
8. [Risks](#risks)
9. [Assumptions](#assumptions)
10. [Scope](#scope)
11. [Out of Scope](#out-of-scope)
12. [Deliverables](#deliverables)
13. [Timeline](#timeline)

Related documents: `BUSINESS_REQUIREMENTS.md`, `KPI_DEFINITIONS.md`, `ASSUMPTIONS.md`

---

## Business Context

Last-mile delivery is the final and most customer-visible stage of order fulfillment. It is also the stage with the least real-time visibility for operations leadership: once a package leaves the store/warehouse, most companies rely on aggregated end-of-day reports or customer complaints to learn that something went wrong, rather than a live, queryable view of *where*, *when*, and *why* delays are concentrated.

This is why last-mile SLA analytics is treated as a core, recurring dashboard category — not a one-off report — at logistics-heavy organizations (Amazon Logistics, Flipkart Ekart, Swiggy/Zomato/Blinkit dispatch, Walmart Global Tech supply chain). Ops teams at these companies review delay data on a cadence (daily/weekly), not ad hoc, because delay concentration shifts with weather, traffic, and demand seasonality.

**Why this project exists:** to build a self-contained, reproducible analytics artifact that answers the same category of question these teams answer operationally, using a real (not synthetic) delivery dataset, so the resulting portfolio project is defensible in a technical interview rather than being a stylistic dashboard exercise.

## Problem Statement

A delivery-based business has no unified, queryable view of SLA performance. Delay patterns by zone, time window, weather condition, and traffic condition are known anecdotally (via customer complaints) but not quantified. This creates three concrete business costs:
- **Re-delivery / operational cost** from missed delivery windows.
- **Customer experience cost** from complaints and lower repeat-usage likelihood.
- **Resourcing inefficiency** from not knowing which zones/conditions need proactive agent reallocation.

The project's purpose is to build the analytics layer — data model, SQL analysis layer, statistical testing, and executive dashboard — that converts raw delivery event data into an actionable, quantified view of delay drivers.

*Note on scope honesty:* The source dataset does not contain a pre-labeled SLA/promised-time field. This charter and its companion documents treat "SLA breach" as an **analyst-defined business rule**, not ground truth supplied by the data. See `SLA_METHODOLOGY.md` (to be produced in the next documentation pass) for the frozen definition. This is stated explicitly, upfront, so no downstream document implies a false level of certainty.

## Goals

1. Quantify current on-time delivery performance and SLA breach concentration across zone, category, weather, and traffic conditions.
2. Statistically test whether weather and traffic conditions are significant drivers of delivery time (not just visually different).
3. Identify the smallest set of conditions/zones responsible for the largest share of breach volume (Pareto framing), so recommendations are prioritized, not exhaustive.
4. Produce an executive-facing dashboard and a small number of evidence-backed recommendations that a VP of Operations could act on.

## Success Criteria

Success is defined by process rigor and defensibility, not by hitting a predetermined number, since no target SLA or benchmark breach rate is supplied externally:
- Every KPI in `KPI_DEFINITIONS.md` is calculated identically in SQL, Python, and Power BI (cross-validated, not just visually similar).
- The SLA business rule is frozen *before* breach analysis is run, and documented with its rationale (avoids circular/self-fulfilling analysis).
- At least one statistical test (ANOVA or its non-parametric fallback) is run with assumptions checked, not assumed.
- Final recommendations are traceable to a specific, quantified finding — no recommendation is written before the corresponding analysis exists.
- Dashboard and documentation are reviewable by a hiring-manager-level reader in under two minutes and hold up under follow-up questions.

## KPIs

Full definitions live in `KPI_DEFINITIONS.md` (Business Definition, Purpose, Formula, Owner, Frequency, Limitations for each). Summary list:
- On-Time Delivery Rate (OTD%)
- SLA Breach Rate
- Average & P90 Delivery Time
- Delivery Time by Weather/Traffic Condition
- Agent Rating–Delivery Time Relationship
- Delay Root-Cause Share (Pareto concentration)

## Stakeholders

See `BUSINESS_REQUIREMENTS.md` for full stakeholder detail (pain points, decisions, expected usage per role). Summary:

| Stakeholder | Primary Interest |
|---|---|
| VP of Operations | Zone-level resourcing and strategic prioritization |
| City Ops Managers | Daily/weekly triage of underperforming zones |
| Fleet/Rider Managers | Agent-level performance and workload distribution |
| Customer Experience Lead | Proactive communication triggers during adverse conditions |
| Finance (Cost-to-Serve) | Re-delivery and SLA-breach cost exposure |

## Business Constraints

- **Data constraint:** Single static historical dataset (Kaggle, ~43.7K India-based delivery records); no live/streaming feed, no true SLA/promised-time field, no cost field.
- **Tooling constraint:** PostgreSQL, Python, and Power BI only — no distributed compute (Spark/Snowflake), since the project is scoped as descriptive/diagnostic analytics only (see `ASSUMPTIONS.md`).
- **Time constraint:** Solo-analyst project completed on a fresher's timeline (~30–40 hours total).

## Risks

Full register in `RISK_REGISTER.md` (to be produced separately). Top charter-level risks:
- **Circular SLA definition risk:** if the breach threshold is tuned after seeing breach-rate results, findings become self-fulfilling. Mitigated by freezing the rule before analysis (see Assumptions).
- **Correlation-as-causation risk:** ANOVA/statistical significance shows association, not causal delay mechanism. Every insight must state this distinction explicitly.
- **Small-field risk:** derived fields (distance, SLA threshold, breach flag) are only as good as their documented formulas — undocumented derivation is a risk for anyone extending this work later without the source formulas in hand.

## Assumptions

Full list with risk and validation method in `ASSUMPTIONS.md`. This charter assumes the dataset is representative enough of last-mile delivery dynamics generally to support a portfolio-level (not production-level) analysis.

## Scope

- Descriptive and diagnostic analytics on the existing Kaggle dataset: cleaning, feature engineering (distance, SLA threshold, breach flag), SQL analysis layer, Python EDA and statistical testing, and a 4-page Power BI dashboard.
- Documentation sufficient for the project to be reproduced and defended in an interview.

## Out of Scope

- Delay forecasting or ETA estimation — explicitly excluded to keep the project positioned as Data Analyst work.
- Real-time or streaming data pipelines.
- Any cost or revenue figures not derivable from the dataset (no cost column exists; cost-to-serve is referenced as a stakeholder interest, not a calculated KPI, unless a documented proxy is defined in `ASSUMPTIONS.md`).
- Cross-company or cross-dataset benchmarking (no external SLA benchmark is available).

## Deliverables

1. Business documentation set (this charter + companion docs).
2. PostgreSQL star schema and populated database.
3. SQL analysis layer answering the documented business questions.
4. Python cleaning, feature engineering, EDA, and statistical testing scripts/notebooks.
5. 4-page Power BI dashboard.
6. Executive recommendations, each traceable to a specific finding.
7. GitHub repository with full documentation, screenshots, and reproducibility instructions.

## Timeline

Indicative only (detailed day-by-day plan lives outside this charter): Week 1 — data foundation (cleaning, schema, SQL, statistics). Week 2 — dashboard build, cross-validation, documentation, recommendations, publication.
