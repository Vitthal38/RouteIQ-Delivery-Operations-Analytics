# Dashboard Planning — RouteIQ

## Table of Contents
1. [Design Principles](#design-principles)
2. [Page 1 — Executive Summary](#page-1--executive-summary)
3. [Page 2 — Area & Category Performance](#page-2--area--category-performance)
4. [Page 3 — Agent Performance](#page-3--agent-performance)
5. [Page 4 — Delay Root Cause](#page-4--delay-root-cause)
6. [Cross-Page Navigation](#cross-page-navigation)

Related documents: `DAX_MEASURE_PLAN.md` (measures referenced below), `STAR_SCHEMA.md`, `SLA_METHODOLOGY.md` (label requirement), `KPI_DEFINITIONS.md`

**Process rule:** this document plans the dashboard; no `.pbix` work begins until this plan and `VALIDATION_CHECKLIST.md` are both approved.

---

## Design Principles

- One primary business question per page — no page tries to answer everything (see `PROJECT_CHARTER.md` success criteria: reviewable in under two minutes).
- Every visual showing `sla_breach_flag`-derived data is titled or footnoted "SLA (analyst-defined benchmark)" per `SLA_METHODOLOGY.md`'s labeling requirement — never unqualified "SLA."
- Every visual filtered by a validity flag (`coordinates_valid_flag`, `agent_rating_valid_flag`, `agent_age_valid_flag`, `area_tier_valid_flag`) states the resulting row count/sample size in a tooltip or footnote, so a viewer can tell when they're looking at a subset.

---

## Page 1 — Executive Summary

- **Purpose:** Single-glance answer to "are we meeting our (analyst-defined) delivery commitment, and is it trending better or worse."
- **Audience:** VP of Operations (primary), all other stakeholders (secondary landing page).
- **Business Question:** #1, #8, #11 (overall/area OTD%, trend over the observed period).
- **KPIs:** `On-Time Delivery Rate %`, `SLA Breach Rate %`, `Average Delivery Time (mins)`, `P90 Delivery Time (mins)`, `Delivery Time Trend (Weekly)`.
- **Charts:** 4 KPI cards (OTD%, breach rate, avg time, P90 time) + one weekly trend line chart (avg and P90 as two series).
- **Filters:** Date range slicer (bounded to the observed 2022-02-11–2022-04-06 range), Area slicer.
- **Drillthrough:** Clicking a low point on the trend line drills through to Page 4 (Delay Root Cause) filtered to that week, so a viewer investigating a bad week can immediately see the condition mix driving it.
- **Navigation:** Landing page; persistent nav bar to Pages 2–4.
- **Tooltips:** Trend line tooltip shows the week's row count (flags partial first/last week per `FEATURE_ENGINEERING.md` #7); KPI cards show "SLA = category-level P75, analyst-defined" on hover.
- **Expected User Decisions:** VP of Operations decides whether current performance warrants escalation to the ops team, and which week/area to investigate further via drillthrough.

## Page 2 — Area & Category Performance

- **Purpose:** Identify which zones and product categories underperform, to prioritize resourcing.
- **Audience:** City Ops Managers (primary), VP of Operations (secondary).
- **Business Question:** #1, #2, #6, #8, #16, #18 (area/category breach rate, P90, worst performer).
- **KPIs:** `Breach Rate by Area`, `P90 Delivery Time by Area`, `Average Delivery Time by Category`.
- **Charts:** Heatmap matrix (Area × Category, colored by breach rate), ranked bar chart (worst-to-best area by breach rate), ranked bar chart (category by avg delivery time).
- **Filters:** Weather/Traffic slicer (cross-filter to see area performance under specific conditions), Date range.
- **Drillthrough:** Clicking an area in the heatmap drills through to Page 4 filtered to that area, to see its specific root-cause mix.
- **Navigation:** Nav bar; "back to Executive Summary" link.
- **Tooltips:** Heatmap cell tooltip shows the underlying row count for that Area×Category combination and flags if it's below a minimum-sample-size threshold (per `SQL_ANALYSIS_PLAN.md` Q20 low-count caveat).
- **Expected User Decisions:** City Ops Manager decides which specific area needs a triage conversation this week; identifies whether a category-level issue (e.g., handling delay) needs escalation to a different team than a pure zone issue.

## Page 3 — Agent Performance

- **Purpose:** Assess whether agent-level factors (rating, age) relate to delivery time, and whether workload is evenly distributed.
- **Audience:** Fleet/Rider Manager (primary).
- **Business Question:** #4, #9, #15.
- **KPIs:** `Delivery Time by Agent Rating Band`, `Agent Age vs. Delivery Time`, `Workload Distribution`.
- **Charts:** Scatter plot (rating band vs. avg delivery time), scatter plot (age vs. delivery time), distribution/box plot (delivery time spread, checking for outlier-prone patterns).
- **Filters:** None beyond the global date range — this page is intentionally kept simple since `DimAgent` has no true individual-agent identifier (per `STAR_SCHEMA.md` design decision), so slicing further would imply a precision the data doesn't support.
- **Drillthrough:** None — this page is a terminal analytical view, not a drill target, consistent with the "no true Agent_ID" limitation.
- **Navigation:** Nav bar; explicit on-page caption stating "agent-level" here means attribute-level (age/rating), not individual-rider tracking — prevents the page from being read as something it isn't.
- **Tooltips:** Scatter point tooltips show the excluded-row count (53 out-of-range ratings, 54 nulls) so the visual's scope is transparent at a glance.
- **Expected User Decisions:** Fleet/Rider Manager decides whether rating-based coaching is a plausible lever (per the correlation strength found in `STATISTICAL_ANALYSIS.md` Test 3) or whether delay is better explained by external conditions, directing effort accordingly.

## Page 4 — Delay Root Cause

- **Purpose:** Answer "which conditions, and how much of breach volume, should we prioritize fixing" — the project's core differentiator.
- **Audience:** City Ops Manager, CX Lead (primary); VP of Operations (for prioritization sign-off).
- **Business Question:** #3, #5, #12, #13, #14, #19, #20.
- **KPIs:** `Breach Rate by Weather`, `Breach Rate by Traffic`, `Breach Rate by Area + Traffic (Pareto)`, `Adverse vs. Clear Weather Delta`.
- **Charts:** Pareto chart (ranked breach share by weather×traffic combination with cumulative % line), bar chart (breach rate by weather), bar chart (breach rate by traffic), statistical-significance annotation panel showing p-value/effect size from `STATISTICAL_ANALYSIS.md` Tests 1–2 for the currently selected condition.
- **Filters:** Area slicer (cross-filter root cause within one zone), Category slicer.
- **Drillthrough:** From Page 2's area click; no further drillthrough target from this page (terminal page for root-cause investigation).
- **Navigation:** Nav bar; "back to Area & Category Performance" link (since this page is a common drill target from Page 2).
- **Tooltips:** Pareto bar tooltip shows exact breach count, breach share %, and cumulative % for that segment; statistical panel tooltip explains "statistically significant ≠ operationally large — see effect size" per `STATISTICAL_ANALYSIS.md`'s interpretation standard.
- **Expected User Decisions:** CX Lead decides which specific condition (e.g., a named traffic level) should trigger proactive customer messaging; City Ops Manager decides which condition×area combination to prioritize first, using the Pareto cutoff rather than spreading effort evenly.

## Cross-Page Navigation

```
Page 1 (Executive Summary) ──drillthrough (bad week)──▶ Page 4 (Delay Root Cause)
Page 2 (Area & Category)   ──drillthrough (area click)─▶ Page 4 (Delay Root Cause)
Page 4 ──"back" link──▶ Page 2
All pages ──persistent nav bar──▶ Page 1
Page 3 is a standalone leaf page (no drillthrough in/out) per its intentional scope limit
```
