# Assumptions Register — RouteIQ

## Table of Contents
1. [Purpose](#purpose)
2. [Data Assumptions](#data-assumptions)
3. [Business Rule Assumptions](#business-rule-assumptions)
4. [Scope Assumptions](#scope-assumptions)
5. [Statistical Assumptions](#statistical-assumptions)

Related documents: `PROJECT_CHARTER.md` (risks these assumptions feed into), `KPI_DEFINITIONS.md` (KPIs dependent on these assumptions), `BUSINESS_REQUIREMENTS.md` (financial-impact assumption)

## Purpose

Every assumption below is documented so no future SQL, Python, DAX, or narrative work introduces an undocumented business rule. Each entry states **why the assumption exists**, **what risk it introduces**, and **how it will be validated**. Values below marked as observed come from direct profiling of the uploaded dataset (`amazon_delivery.csv`, 43,739 rows) run on 2026-08-05; anything not yet profiled is marked "To be determined after analysis."

---

## Data Assumptions

### A1 — The dataset is representative enough for portfolio-level analysis
- **Why it exists:** No alternative real dataset with comparable field coverage (geo-coordinates + weather + traffic + agent rating) was available; this is the standard, widely-used public dataset for this analysis type.
- **Risk introduced:** Findings may not generalize to a real company's actual delivery network (single geography mix, single time window: observed date range is **2022-02-11 to 2022-04-06, ~8 weeks**).
- **Validation method:** State the date range and scope explicitly in `DATASET_OVERVIEW.md` and `LIMITATIONS.md`; frame all findings as "based on this dataset" rather than universal claims.

### A2 — `Area` values are treated as a proxy for delivery zone
- **Why it exists:** No true zone/geofence field exists. Observed `Area` values (after trimming whitespace) are `Urban`, `Metropolitian` [sic, dataset's own spelling], `Semi-Urban`, and `Other`.
- **Risk introduced:** `Other` is an ambiguous bucket (unclear what it represents); using it in area-level comparisons could produce a misleading segment.
- **Validation method:** Report the row count and share of `Other` during profiling; decide (and document in `DATA_CLEANING_PLAN.md`) whether to retain, exclude, or footnote it — do not silently drop without disclosure.

### A3 — Some coordinate values are invalid and must be handled before distance calculation
- **Why it exists:** Observed: **3,505 rows** have `Store_Latitude` (and correspondingly `Store_Longitude`) equal to exactly `0`, which is not a valid location for this dataset's real-world geography (India-based delivery routes) and is a known placeholder/error pattern rather than a true coordinate. `Drop_Latitude` shows 0 invalid rows by this same check.
- **Risk introduced:** Computing haversine distance on a `(0,0)` coordinate produces a nonsensical distance value that would corrupt `distance_km` and any downstream correlation analysis.
- **Validation method:** Flag rows where store or drop coordinates equal `(0,0)` or fall outside a plausible India bounding box; document exclusion count and rationale in `DATA_CLEANING_PLAN.md` before any distance-based KPI is calculated.

### A4 — Missing values exist in `Agent_Rating`, `Weather`, and `Traffic` and require an explicit strategy
- **Why it exists:** Observed: `Agent_Rating` has 54 missing values; `Weather` has 91 true nulls; `Traffic` has no true nulls but contains an explicit literal string `"NaN "` (with trailing space) as a category value rather than a missing-value marker, which pandas will not treat as missing by default.
- **Risk introduced:** If the literal `"NaN "` string in `Traffic` is not recoded to a true missing value, it will silently be treated as a valid traffic category in group-by analysis and DAX measures, understating true missingness and distorting condition-level breach shares.
- **Validation method:** Explicit recoding step documented in `DATA_CLEANING_PLAN.md`; post-cleaning null counts re-verified and stated in `DATA_PROFILING_PLAN.md` before proceeding to feature engineering.

### A5 — `Agent_Age` contains at least one implausible value
- **Why it exists:** Observed minimum `Agent_Age` is **15**, which is below plausible working age for a delivery agent in this context; observed maximum is 50.
- **Risk introduced:** Implausible ages could indicate a data entry error and would distort any age-based agent analysis if not flagged.
- **Validation method:** Apply a documented plausible-range check (e.g., 18–65) during profiling; report count of rows outside range before deciding whether to exclude or retain with a caveat.

### A6 — All category/text fields require whitespace trimming
- **Why it exists:** Observed values in `Traffic`, `Vehicle`, and `Area` contain trailing whitespace (e.g., `"High "`, `"Metropolitian "`), which would cause `GROUP BY`/DAX category splits to silently fragment (e.g., `"High"` and `"High "` treated as two different groups).
- **Risk introduced:** Undercounting or duplicating categories in every grouped KPI (breach rate by traffic, by area, etc.) if not corrected before analysis.
- **Validation method:** Trim step included as the first transformation in `DATA_CLEANING_PLAN.md`; validated by re-listing unique values per categorical column post-cleaning.

---

## Business Rule Assumptions

### A7 — SLA threshold is analyst-defined, not company-published
- **Why it exists:** The dataset has no `promised_time`, `SLA`, or `target_delivery_time` field. A threshold must be defined to calculate OTD%/breach-rate KPIs at all.
- **Risk introduced:** Any specific numeric threshold chosen is inherently arbitrary unless clearly justified and frozen before results are examined; changing it after seeing breach-rate results would make findings circular/self-fulfilling.
- **Validation method:** The exact rule will be defined and frozen in a dedicated `SLA_METHODOLOGY.md` **before** any breach-rate analysis is run, and never altered afterward. This is a hard process rule, not a suggestion. *(Earlier drafting note, retained for audit-trail purposes only: at the time this assumption was first written, "category-median delivery time + a documented buffer" was floated only as an illustrative example of the kind of rule that might be chosen — it was never itself the frozen rule. `SLA_METHODOLOGY.md` has since been finalized and is the sole authoritative source: the frozen definition is category-level P75 (75th percentile) of `Delivery_Time`, not a median-plus-buffer construction. Any conflict between this note and `SLA_METHODOLOGY.md` is resolved in `SLA_METHODOLOGY.md`'s favor.)*

### A8 — No cost/financial field exists; financial impact is directional only
- **Why it exists:** The dataset contains no cost, refund, or revenue column.
- **Risk introduced:** Presenting a specific currency figure for "cost of breaches" without a real cost field would be fabrication.
- **Validation method:** Any financial statement in final deliverables is either qualitative ("breach concentration in Zone X materially increases re-delivery cost") or, if a numeric illustration is desired, uses a clearly labeled external reference figure explicitly marked as an illustrative assumption, never presented as a measured finding from this dataset.

---

## Scope Assumptions

### A9 — ML/predictive modeling is intentionally excluded
- **Why it exists:** The project is positioned for Data Analyst (not Data Scientist/ML Engineer) roles; the brief's own scoring explicitly downgraded an ML-leaning idea for this reason.
- **Risk introduced:** None to the analysis itself; the risk this assumption manages is *positioning* risk — including ML work could blur the target role fit.
- **Validation method:** Statistical testing (ANOVA/correlation) is used for rigor instead of predictive modeling; documented explicitly in `README.md` and `INTERVIEW_PREPARATION.md` as a deliberate scope decision, not a capability gap.

## Statistical Assumptions

### A10 — ANOVA assumptions (normality, homogeneity of variance) are not assumed to hold and must be tested
- **Why it exists:** Real-world delivery-time data is typically right-skewed, which can violate ANOVA's normality and equal-variance assumptions.
- **Risk introduced:** Running ANOVA without checking assumptions could produce an invalid p-value and an overstated claim of significance.
- **Validation method:** Assumption checks (e.g., Shapiro-Wilk, Levene's test) run and documented in `STATISTICAL_ANALYSIS.md` before interpreting ANOVA results; a non-parametric fallback (Kruskal-Wallis) used and reported if assumptions fail.
