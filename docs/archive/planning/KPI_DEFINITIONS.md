# KPI Definitions — RouteIQ

## Table of Contents
1. [On-Time Delivery Rate (OTD%)](#1-on-time-delivery-rate-otd)
2. [SLA Breach Rate](#2-sla-breach-rate)
3. [Average Delivery Time](#3-average-delivery-time)
4. [P90 Delivery Time](#4-p90-delivery-time)
5. [Delivery Time by Weather/Traffic Condition](#5-delivery-time-by-weathertraffic-condition)
6. [Agent Rating–Delivery Time Relationship](#6-agent-ratingdelivery-time-relationship)
7. [Delay Root-Cause Share (Pareto Concentration)](#7-delay-root-cause-share-pareto-concentration)
8. [Week-over-Week Delivery Time Volatility](#8-week-over-week-delivery-time-volatility)

Related documents: `BUSINESS_REQUIREMENTS.md` (why these matter), `ASSUMPTIONS.md` (SLA threshold assumption underlying #1–2, #5, #7), `SQL_ANALYSIS_PLAN.md` / `DAX_MEASURE_PLAN.md` (implementation, to be produced separately)

**Grounding note:** the source dataset (`amazon_delivery.csv`, 43,739 rows) contains `Order_ID, Agent_Age, Agent_Rating, Store_Latitude, Store_Longitude, Drop_Latitude, Drop_Longitude, Order_Date, Order_Time, Pickup_Time, Weather, Traffic, Vehicle, Area, Delivery_Time, Category`. `Delivery_Time` is in minutes and is the only outcome field available — every KPI below is derived from it plus documented business rules. No KPI in this document references a field that does not exist in the raw or engineered dataset.

---

### 1. On-Time Delivery Rate (OTD%)

- **Business Definition:** The percentage of deliveries whose actual delivery time is at or below the defined SLA threshold.
- **Business Purpose:** Primary headline metric for ops leadership; the single number that answers "are we meeting our delivery promise."
- **Formula:** `OTD% = (COUNT(deliveries WHERE Delivery_Time <= sla_threshold_minutes) / COUNT(all deliveries)) * 100`
- **Owner:** VP of Operations (headline accountability); calculated/maintained by the analytics function.
- **Frequency:** Weekly (matches the ops-review cadence this dashboard is designed to emulate).
- **Limitations:** `sla_threshold_minutes` is an analyst-defined business rule (see `SLA_METHODOLOGY.md`), not a company-published SLA. OTD% is therefore relative to a documented internal benchmark, not an externally validated target — this must be stated wherever OTD% is presented.

### 2. SLA Breach Rate

- **Business Definition:** The inverse of OTD% — the percentage of deliveries exceeding the defined SLA threshold.
- **Business Purpose:** Framed separately from OTD% because "breach rate by segment" is the more actionable cut for root-cause work (it's what feeds the Pareto/root-cause analysis), whereas OTD% is the headline number.
- **Formula:** `SLA Breach Rate = 100 - OTD%`, or directly: `COUNT(Delivery_Time > sla_threshold_minutes) / COUNT(all deliveries) * 100`
- **Owner:** City Ops Managers (per-zone), rolled up by VP of Operations.
- **Frequency:** Weekly, with drill-down by area/category/condition available on demand.
- **Limitations:** Same SLA-threshold dependency as OTD%. Also sensitive to how missing/invalid rows (bad coordinates, missing weather) are handled in cleaning — breach rate must be recalculated identically across SQL, Python, and Power BI to be trustworthy (see `VALIDATION_CHECKLIST.md`).

### 3. Average Delivery Time

- **Business Definition:** Mean `Delivery_Time` (minutes) across deliveries, overall or by segment.
- **Business Purpose:** Baseline reference metric; used mainly as a comparison point for P90 (the gap between mean and P90 reveals how "tail-heavy" delay is).
- **Formula:** `AVG(Delivery_Time)`
- **Owner:** Analytics function (supporting metric, not a standalone headline KPI).
- **Frequency:** Weekly.
- **Limitations:** Sensitive to outliers/skew; not the primary metric for customer-experience-driven decisions (see P90 below) because a small number of very late deliveries can be masked by a large number of on-time ones.

### 4. P90 Delivery Time

- **Business Definition:** The delivery time value below which 90% of deliveries fall (90th percentile).
- **Business Purpose:** Reflects tail/worst-case delivery experience, which is what actually drives customer complaints — a strong average can coexist with a bad tail. This is the metric ops teams at Amazon/Swiggy/Flipkart-scale companies actually track for exactly this reason.
- **Formula:** `PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY Delivery_Time)` (SQL), `numpy.percentile(Delivery_Time, 90)` (Python), `PERCENTILE.INC` equivalent DAX measure.
- **Owner:** City Ops Managers (zone-level), VP of Operations (headline trend).
- **Frequency:** Weekly trend line on the Executive Summary page.
- **Limitations:** Percentile calculation method (interpolation type) must match across SQL, Python, and Power BI or the three will disagree — this is a documented cross-validation requirement, not optional.

### 5. Delivery Time by Weather/Traffic Condition

- **Business Definition:** Average and P90 `Delivery_Time`, grouped by `Weather` and by `Traffic` category values.
- **Business Purpose:** Foundation for the root-cause page; identifies which conditions are associated with the longest delivery times, before statistical testing confirms whether the difference is significant.
- **Formula:** `AVG(Delivery_Time) GROUP BY Weather`, `AVG(Delivery_Time) GROUP BY Traffic` (and P90 equivalents).
- **Owner:** City Ops Managers, CX Lead (for proactive-communication triggers).
- **Frequency:** Weekly, with statistical significance re-checked when the underlying dataset changes (not applicable to this static historical dataset, but documented for production continuity).
- **Limitations:** This KPI shows association only. Statistical testing (ANOVA or its non-parametric fallback, documented in `STATISTICAL_ANALYSIS.md`) is required before this is described as a "driver" rather than a "pattern."

### 6. Agent Rating–Delivery Time Relationship

- **Business Definition:** The statistical relationship (correlation coefficient) between `Agent_Rating` and `Delivery_Time`.
- **Business Purpose:** Tests whether higher-rated agents are meaningfully faster — informs whether agent performance management is a viable lever for reducing delay, versus delay being driven entirely by external conditions (weather/traffic/distance).
- **Formula:** `CORR(Agent_Rating, Delivery_Time)` (Pearson, with a non-parametric fallback such as Spearman documented if the linearity assumption fails).
- **Owner:** Fleet/Rider Manager.
- **Frequency:** One-time/periodic analytical finding rather than a live weekly-tracked number, since it's a relationship test, not a count-based metric.
- **Limitations:** Correlation does not establish that agent rating *causes* faster delivery — reverse causality (faster deliveries → better ratings) or confounding (experienced agents assigned to easier routes) are plausible alternative explanations and must be stated alongside any finding.

### 7. Delay Root-Cause Share (Pareto Concentration)

- **Business Definition:** The percentage of total SLA-breach volume attributable to the top N conditions (specific area, category, weather, or traffic values, ranked by breach count).
- **Business Purpose:** Converts a long list of breach statistics into a prioritization tool — answers "if we could only fix a few things, which ones matter most."
- **Formula:** `(SUM(breach_count for top-N conditions, ranked descending) / SUM(total breach_count)) * 100`
- **Owner:** VP of Operations (prioritization decision), City Ops Managers (execution).
- **Frequency:** Recalculated whenever the underlying breach data changes; static for this project's historical dataset.
- **Limitations:** Depends entirely on the SLA threshold definition (same dependency as OTD%/breach rate) and on how "condition" is bucketed (e.g., combined Area+Traffic vs. single-dimension cuts) — the specific cut used for any published Pareto figure must be stated alongside the number.

### 8. Week-over-Week Delivery Time Volatility

- **Business Definition:** The variation in average/P90 `Delivery_Time` from one week to the next, based on `Order_Date`.
- **Business Purpose:** Distinguishes a one-off bad week from a sustained trend, which affects whether a finding warrants a recommendation at all.
- **Formula:** `Delivery_Time metric for week(t) - Delivery_Time metric for week(t-1)`, expressed as absolute or percentage change.
- **Owner:** VP of Operations (trend interpretation).
- **Frequency:** Weekly by definition.
- **Limitations:** The dataset's date range determines how many weeks of trend are available — **to be determined after profiling** `Order_Date` range in `DATASET_OVERVIEW.md`. A short date range limits how much can be said about genuine trend versus noise, and this limitation must be disclosed if the range turns out to be only a few weeks.
