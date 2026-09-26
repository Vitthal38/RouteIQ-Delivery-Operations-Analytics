# RouteIQ — Power BI Dashboard Mockup / Wireframe Blueprint

Generated: 2026-08-16

Scope: visual design specification only. **No `.pbix` was created, no
Power BI Desktop work was performed, and no DAX was written in this
document** — every measure referenced below already exists in
`dax/measures.dax` and is cited by name, not redefined. Page structure
follows the approved `DASHBOARD_PLANNING.md` exactly, with any deviation
explicitly flagged (see below) rather than silently applied.

---

## Flags Against the Approved `DASHBOARD_PLANNING.md` (raised, not silently resolved)

**FLAG 1 — Business Question #7 (weekend vs. weekday) has no designated
page.** None of the 4 approved pages' chart lists includes a
weekend/weekday visual, yet Phase 4/5 produced a specific, approved,
citable finding for it (`p = 0.9658`, not significant, Cohen's
`d = -0.0013`, negligible) that this task's own instructions require the
dashboard not to hide. **Proposed fix (flagged for sign-off, not silently
applied):** add one small supporting visual to Page 4 (Delay Root Cause),
next to the existing statistical-significance annotation panel, since
Page 4 already hosts the other `STATISTICAL_ANALYSIS.md` test results.
This is a minimal, additive change to Page 4's supporting-evidence area —
it does not add a new page, new KPI, or new measure.

**FLAG 2 — Page 3 (Agent Performance) carries real but structurally weak
evidence.** Now that Phase 4/5 are complete, Page 3's underlying findings
are: agent rating r²=0.0677 (weak), and the approved executive
recommendation is explicitly to **deprioritize** rating-based coaching
investment. The page still answers a legitimate, documented business
question (Fleet/Rider Manager's decision) and should not be removed, but
its visual weight must be modest and must not imply a stronger pattern
than r²=0.0677 supports. Addressed below by keeping the page to 3 visuals
and explicitly captioning the weak-effect-size context on the page itself
— see Page 3 spec and the Critical Review in
`reports/powerbi_mockup_review.md` for the full reasoning.

**No other structural gap or redundancy was found.** The 4-page count,
page order, and per-page primary business question in
`DASHBOARD_PLANNING.md` are otherwise sound and are followed as-is.

---

## Design System

### Color Palette (semantic, not decorative)

| Token | Hex | Use |
|---|---|---|
| Primary | `#1F4E5F` (deep slate-teal) | Page headers, nav bar, primary chart series, active slicer state |
| Secondary | `#6E8C9C` (muted steel-blue) | Secondary chart series (e.g., P90 line vs. Average line), inactive UI |
| Neutral background | `#F4F5F7` | Page canvas |
| Neutral surface | `#FFFFFF` | KPI cards, chart backgrounds |
| Neutral text | `#2B2E33` (near-black) / `#6B7280` (secondary text/captions) | Titles / labels |
| **On-time (positive)** | `#2E8540` (green) | On-time / OTD% only — never used decoratively |
| **Breach (negative)** | `#C0392B` (red) | Breach rate / SLA breach only — never used decoratively |
| **Warning / caution** | `#E8A33D` (amber) | Small-sample-size flags, partial-week flags, `area_tier_valid_flag = false` rows |
| Gridline | `#E2E4E8` | Chart gridlines only, minimal weight |

Green and red are reserved **exclusively** for on-time/breach semantics —
never used for anything else on the dashboard (e.g., a category ranking
never uses red/green, only the Primary/Secondary palette), so color
always carries the same meaning everywhere a viewer sees it.

### Typography

- **Titles / page headers:** Segoe UI Semibold, 20pt (page title), 14pt (section title) — Segoe UI is Power BI's native font, chosen specifically because it is guaranteed to render identically in Power BI Desktop without a custom font install.
- **KPI card numbers:** Segoe UI Semibold, 32pt, tabular figure alignment.
- **KPI card labels:** Segoe UI, 10pt, uppercase, letter-spacing, `#6B7280`.
- **Body / axis labels:** Segoe UI, 9–10pt.
- **Footnotes / methodology captions:** Segoe UI Italic, 8pt, `#6B7280`.

### KPI Card Treatment

White card (`#FFFFFF`) on the `#F4F5F7` canvas, 1px `#E2E4E8` border, no
drop shadow (flat, not skeuomorphic). Big number top, label beneath. A
small directional indicator (▲/▼) is used **only** where a documented
trend/delta exists (e.g., week-over-week) — never a decorative sparkline
with no measure behind it.

### Chart Treatment

Minimal gridlines (`#E2E4E8`, 0.5pt), no 3D, no pie charts (categorical
comparisons use bar/column; part-to-whole is shown via the Pareto
cumulative-% line, not a pie). Direct data labels are used on bar/column
charts where the category count is small enough to stay legible (≤ 6–8
categories); legends are used only for line charts with 2+ series.

### Slicer Treatment

Horizontal button slicers for low-cardinality fields (Area: 4 values,
Vehicle: 3 values, Weekend/Weekday: 2 values) — single click, no dropdown
needed. Dropdown slicers for higher-cardinality fields (Category: 16
values, Weather: 6, Traffic: 4). A slider/between control for the Date
range, bounded to the observed 2022-02-11–2022-04-06 range only (per
`DASHBOARD_PLANNING.md`'s own filter spec) — never allowing a date outside
the observed data.

### Canvas

16:9, 1280×720 design grid (Power BI Desktop default). Every page uses
the same five horizontal zones: **Header** (top, ~60px) → **KPI row**
(~120px) → **Main analysis area** (~320px) → **Supporting analysis**
(~150px) → **Footer / methodology note** (~40px).

---

# PAGE 1 — EXECUTIVE OVERVIEW

## Business Purpose
Answer, in under 30 seconds: are we meeting our (analyst-defined)
delivery commitment, and is it trending better or worse — with an
immediate pointer to where the biggest concentration of the problem sits.

## Target Audience
VP of Operations (primary); every other stakeholder (secondary landing
page — this is the app's home page).

## Primary Business Question
Business Questions #1, #8, #11 (`SQL_ANALYSIS_PLAN.md`): overall/area
OTD%, trend over the observed period.

## Secondary Questions
Where does the largest share of breach volume concentrate? (Sets up
Page 4 without answering it here.)

## Executive Takeaway
*"23.66% of deliveries breach the analyst-defined SLA benchmark.
Metropolitan carries the largest share of that breach volume. Traffic
condition shows the strongest observed association with delivery time of
anything tested."* — three sentences, each backed by a specific approved
figure, none of them causal.

## Visual Hierarchy

- **TOP:** Page header + global Date range slicer (right-aligned) + persistent nav bar.
- **MIDDLE (upper):** 5 KPI cards in a single row — this is what the eye hits first.
- **MIDDLE (main):** One large chart — Weekly Delivery Time Trend (Average + P90 lines) — the single largest visual on the page, since trend-over-time is the page's core narrative device.
- **BOTTOM:** A two-column supporting-evidence strip: (LEFT) SLA Breach Rate by Area mini-bar, (RIGHT) a neutral "where to look next" evidence callout pointing at the Metropolitan/Jam concentration, captioned as evidence, not a directive.
- **FOOTER:** SLA methodology note + last-refreshed date.

## KPI Section

*(5 cards — within the task's 5–6 maximum, and distinctly separated below
from "diagnostic evidence," per the requirement not to blur the two.)*

| KPI | Measure | Why It Exists | Baseline | Target/Benchmark | Visual Type |
|---|---|---|---|---|---|
| Total Deliveries | `[Total Deliveries]` | Denominator context for every rate on the page — a rate without its `n` is not trustworthy | 43,648 | No documented target. | KPI card |
| On-Time Delivery Rate % | `[On-Time Delivery Rate %]` | Headline KPI (`KPI_DEFINITIONS.md` #1) | 76.34% | No documented target — this is an analyst-defined benchmark, not a company-published commitment (`SLA_METHODOLOGY.md`). | KPI card, green accent |
| SLA Breach Rate % | `[SLA Breach Rate %]` | Headline KPI #2; drives the root-cause pages | 23.66% | No documented target. | KPI card, red accent |
| Average Delivery Time (mins) | `[Average Delivery Time (mins)]` | Baseline reference, comparison point for P90 | 124.91 min | No documented target. | KPI card |
| P90 Delivery Time (mins) | `[P90 Delivery Time (mins)]` | Tail/worst-case experience — what actually drives complaints (`KPI_DEFINITIONS.md` #4) | 195.00 min | No documented target. | KPI card |

*No KPI on this page has a documented numeric target — every card states
the current baseline only, per `SLA_METHODOLOGY.md`'s explicit warning
that this SLA is an internal benchmark, not an externally validated
commitment. Do not add a green/red "vs. target" indicator to any of these
five cards; none is supported by the documentation.*

## Visual Section

| Visual | Chart Type | X Axis | Y Axis | Legend | Measure | Filters | Business Question | Reason |
|---|---|---|---|---|---|---|---|---|
| Weekly Trend | Line chart | `DimDate[week_number]` | Minutes | Series: Average / P90 | `[Average Delivery Time (mins)]`, `[P90 Delivery Time (mins)]` | Date range, Area | #11 | Directly shows "is performance improving or worsening" — the page's core narrative visual |
| Breach Rate by Area (mini) | Horizontal bar | `[SLA Breach Rate %]` | `DimArea[area_name]` | none | `[SLA Breach Rate %]` | Date range | #1, #8 | Sets up "where" without duplicating Page 2's full heatmap — deliberately small and secondary here |
| Evidence Callout | Card/text visual (not a chart) | — | — | — | Static text referencing `[Cumulative Breach Share %]` at the Metropolitan/Jam segment (83.73% area share; Jam-traffic combinations dominate the Pareto top ranks, per `reports/business_findings.md` Finding C) | Date range | Points toward Page 4 | Distinguishes **diagnostic evidence** from the KPI row above and from any recommendation — phrased as an observation ("Metropolitan accounts for the largest share of breach volume"), never as an instruction |

## Slicer Design

| Slicer | Field | Purpose | Select | Affects |
|---|---|---|---|---|
| Date Range | `DimDate[full_date]` | Bound to the observed 2022-02-11–2022-04-06 range only | Range (between) | All visuals on page |
| Area | `DimArea[area_name]` | Lets a viewer check "is this pattern true for my zone" without leaving the landing page | Multi-select | All visuals on page |

*No Category/Weather/Traffic/Vehicle slicer on this page — Page 1's job
is the headline number and the trend, not a full diagnostic surface
(that's Pages 2 and 4). Adding more slicers here would violate the
"understand in 30 seconds" requirement.*

## Cross-Filtering

```
Date Range slicer ↓ all 3 visuals (KPI cards, trend line, mini-bar)
Area slicer        ↓ all 3 visuals
```

Single-direction, dimension→fact, per `dax/model_relationships.md` — no
bidirectional relationship required for either slicer.

## Tooltip Design

- **Weekly Trend line points:** week number, date range covered, row
  count (`[Total Deliveries]`) for that week, and a "partial week" flag
  if the week has fewer than 7 distinct observed days (per
  `FEATURE_ENGINEERING.md` #7) — reusing the same underlying logic
  already validated in `sql/analysis/Q11`.
- **KPI cards:** hover caption: *"SLA = category-level P75, analyst-defined benchmark — see SLA_METHODOLOGY.md."*
- **Breach Rate by Area mini-bar:** `[Total Deliveries]` (row count) for
  that area alongside the breach rate — mandatory specifically because
  Semi-Urban's 100% figure appears on this bar and must never be shown
  without its `n=152` alongside it, per this task's explicit sample-size
  requirement (caught during design self-review — see
  `reports/powerbi_mockup_review.md`).

## Drillthrough

Clicking a low point (worse P90) on the Weekly Trend line drills through
to **Page 4 (Delay Root Cause)**, filtered to that week — per
`DASHBOARD_PLANNING.md`'s existing spec. No other drillthrough on this
page.

## What Should NOT Be on This Page
- No agent-level content (wrong page, wrong audience).
- No category-level breakdown (Page 2's job).
- No numeric financial/savings figure (none exists in the source data — `ASSUMPTIONS.md` A8).
- No causal language anywhere in the Evidence Callout or tooltips.
- No 6th+ KPI card — five is enough; a sixth would dilute the "30 second" read.

## Wireframe

```
┌──────────────────────────────────────────────────────────────────────┐
│ ROUTEIQ — EXECUTIVE OVERVIEW                    [Date Range: ▓▓▓▓▓░░] │
│ VP of Operations view                                     [Area: ▾]  │
├────────────┬────────────┬────────────┬────────────┬─────────────────┤
│ Deliveries │   OTD %    │ Breach %   │ Avg Time   │   P90 Time      │
│  43,648    │  76.34%    │  23.66%    │ 124.9 min  │  195.0 min      │
│            │  (green)   │  (red)     │            │                 │
├────────────┴────────────┴────────────┴────────────┴─────────────────┤
│                                                                      │
│              WEEKLY DELIVERY TIME TREND — Avg vs. P90                │
│     min                                                              │
│  200 ┤                    ╭─╮           ╭─╮                          │
│  150 ┤──╮   ╭──╮       ╭──╯ ╰──╮     ╭──╯ ╰──                        │
│  100 ┤  ╰───╯  ╰───────╯       ╰─────╯                               │
│      └──────────────────────────────────────────────  week 6 → 14   │
│                                                                      │
├───────────────────────────────┬──────────────────────────────────────┤
│ BREACH RATE BY AREA (mini)    │ WHERE TO LOOK — evidence, not a       │
│ Semi-Urban  ████████████ 100% (n=152) │ directive                     │
│ Metropolitan████████░░░░  27% (n=32,634) │ Metropolitan accounts for  │
│ Urban       ████░░░░░░░░  14% (n=9,726) │ the largest share of SLA   │
│ Other       ███░░░░░░░░░  11% (n=1,136) │ breach volume. Traffic     │
│                                │ shows the strongest observed  │
│                                │ association with delivery time of     │
│                                │ any factor tested (see Page 4).       │
├───────────────────────────────┴──────────────────────────────────────┤
│ SLA = category-level P75, analyst-defined benchmark (not a company-  │
│ published target). Data: 2022-02-11 to 2022-04-06.                   │
└──────────────────────────────────────────────────────────────────────┘
```

## Visual Priority

| Visual | Priority |
|---|---|
| 5 KPI cards | P0 |
| Weekly Trend line | P0 |
| Breach Rate by Area mini-bar | P1 |
| Evidence Callout | P1 |

4 meaningful visual groups total — well under the 8–10 challenge
threshold.

---

# PAGE 2 — AREA & CATEGORY PERFORMANCE

## Business Purpose
Identify which zones and product categories underperform, to prioritize
resourcing — the "where" page.

## Target Audience
City Ops Managers (primary); VP of Operations (secondary).

## Primary Business Question
Business Questions #1, #2, #6, #8, #16, #18.

## Secondary Questions
Is a given zone's underperformance concentrated in specific categories,
or spread evenly?

## Executive Takeaway
*"Semi-Urban has the highest breach rate (100%) but on a small sample
(n=152, 0.35% of deliveries). Metropolitan is lower-rate (26.5%) but
carries 74.8% of total volume — the largest absolute concentration of
breach volume in the dataset."*

## Visual Hierarchy

- **TOP:** Page header, Weather/Traffic slicer, Date range, "back to Page 1" link.
- **MIDDLE:** Area × Category heatmap (breach rate) — the single largest visual, center-anchored.
- **BOTTOM (left):** Ranked bar — worst-to-best area by breach rate (with `n` labeled).
- **BOTTOM (right):** Ranked bar — category by average delivery time.
- **FOOTER:** Sample-size / SLA methodology note.

## KPI Section

| KPI | Measure | Why It Exists | Baseline | Target/Benchmark | Visual Type |
|---|---|---|---|---|---|
| Breach Rate by Area | `[SLA Breach Rate %]` (Area row context) | Core page KPI — identifies which zone(s) need triage | Semi-Urban 100.00% (n=152) / Metropolitan 26.50% (n=32,634) / Urban 14.37% (n=9,726) / Other 11.44% (n=1,136) | No documented target. | Part of the heatmap + ranked bar, not a standalone card |
| P90 Delivery Time by Area | `[P90 Delivery Time (mins)]` (Area row context) | Tail-experience view by zone | Semi-Urban 269.50 min (n=152) / Metropolitan 200.00 min | No documented target. | Table column (see below) |
| Average Delivery Time by Category | `[Average Delivery Time (mins)]` (Category row context) | Identifies category-level effects independent of zone | Range 26.54 min (Grocery) to 132.90 min (Cosmetics) | No documented target. | Ranked bar |

*No standalone KPI cards on this page — Page 1 already carries the
headline numbers; Page 2's job is the breakdown, delivered entirely
through the heatmap and ranked bars below, avoiding redundant cards.*

## Visual Section

| Visual | Chart Type | X Axis | Y Axis | Legend | Measure | Filters | Business Question | Reason |
|---|---|---|---|---|---|---|---|---|
| Area × Category Heatmap | Matrix (conditional-formatted) | `DimCategory[category_name]` (columns) | `DimArea[area_name]` (rows) | Color scale: green (low breach) → red (high breach) | `[SLA Breach Rate %]` | Weather, Traffic, Date | #1, #2, #6 | The one visual that answers "is a zone's problem category-specific or zone-wide" at a glance |
| Worst-to-Best Area (ranked bar) | Horizontal bar, sorted descending | `[SLA Breach Rate %]` | `DimArea[area_name]` | none | `[SLA Breach Rate %]`, `[Total Deliveries]` (data label) | Weather, Traffic, Date | #1, #8, #16 | Direct answer to "which area underperforms most," with `n` printed on each bar so Semi-Urban's small sample is never shown unqualified |
| Category by Avg Delivery Time (ranked bar) | Vertical bar, sorted descending | `DimCategory[category_name]` | `[Average Delivery Time (mins)]` | none | `[Average Delivery Time (mins)]` | Weather, Traffic, Date | #6, #18 | Direct answer to "which categories run longest" |

## Slicer Design

| Slicer | Field | Purpose | Select | Affects |
|---|---|---|---|---|
| Weather | `DimWeatherTraffic[weather]` | Cross-filter to see area performance under a specific condition | Multi-select dropdown | All 3 visuals |
| Traffic | `DimWeatherTraffic[traffic]` | Same, for traffic | Multi-select dropdown | All 3 visuals |
| Date Range | `DimDate[full_date]` | Consistent with Page 1 | Range | All 3 visuals |

*`area_tier_valid_flag` is not a slicer — "Other" is retained and shown
in the heatmap/ranked bar (per `DATA_CLEANING_PLAN.md` Step 8), with its
row visually distinguishable (see Tooltip Design), not hidden behind a
filter a viewer has to know to set.*

## Cross-Filtering

```
Weather / Traffic slicers ↓ Heatmap, both ranked bars
Date Range slicer          ↓ Heatmap, both ranked bars
Heatmap cell click         ↓ (drillthrough, see below)
```

## Tooltip Design

- **Heatmap cell:** exact breach count, breach rate %, row count (`n`)
  for that Area×Category combination, and a visible flag if `n` is below
  a threshold the viewer should treat with caution (per
  `SQL_ANALYSIS_PLAN.md` Q20's documented "expose row_count, don't invent
  a hard cutoff" policy — the tooltip shows the number, it does not hide
  or auto-suppress a cell for being small).
- **Ranked bar (area):** breach count, breach rate %, `n`, and
  `area_tier_valid_flag` status (so "Other" is never mistaken for a tier).

## Drillthrough

Clicking an area in the heatmap or the ranked bar drills through to
**Page 4 (Delay Root Cause)**, filtered to that area — per
`DASHBOARD_PLANNING.md`'s existing spec.

## What Should NOT Be on This Page
- No agent content.
- No raw scatter of all 43,648 individual deliveries (illegible at this
  volume; the heatmap and ranked bars are the correct aggregation level).
- No pie chart for area share of volume — a pie would invite confusing
  "share of volume" with "breach rate," which is exactly the distinction
  this page must keep clear (see Executive Takeaway).

## Wireframe

```
┌──────────────────────────────────────────────────────────────────────┐
│ ROUTEIQ — AREA & CATEGORY PERFORMANCE      [Weather ▾][Traffic ▾]     │
│ ← Back to Executive Overview                      [Date: ▓▓▓▓▓░░]    │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│        AREA × CATEGORY BREACH RATE HEATMAP                          │
│               Electronics Grocery Jewelry ... (16 cols)              │
│  Metropolitan   ▓▓▓▓       ░░       ▓▓▓                              │
│  Urban          ▓▓         ░░       ▓▓                               │
│  Semi-Urban     ▓▓▓▓▓      ▓▓▓▓▓    ▓▓▓▓▓   (n=152, flagged small)   │
│  Other          ▓▓         ░        ▓▓                               │
│                                                                      │
├───────────────────────────────┬──────────────────────────────────────┤
│ WORST → BEST AREA (breach %)  │ CATEGORY BY AVG DELIVERY TIME         │
│ Semi-Urban   ██████████ 100%  │ Cosmetics   ████████████ 132.9 min    │
│  n=152 ⚠ small sample         │ Kitchen     ███████████  132.4 min    │
│ Metropolitan ███░░░░░░░  27%  │ ...                                   │
│  n=32,634                     │ Grocery     ██            26.5 min    │
│ Urban        ██░░░░░░░░░  14% │  (different fulfillment scale)        │
│ Other        █░░░░░░░░░░  11% │                                       │
├───────────────────────────────┴──────────────────────────────────────┤
│ SLA (analyst-defined benchmark). "Other" area retained, excluded from│
│ tier comparisons only. Sample sizes shown on every bar.               │
└──────────────────────────────────────────────────────────────────────┘
```

## Visual Priority

| Visual | Priority |
|---|---|
| Area × Category Heatmap | P0 |
| Worst-to-Best Area ranked bar | P0 |
| Category by Avg Delivery Time ranked bar | P1 |

3 visuals — well under the challenge threshold.

---

# PAGE 3 — AGENT PERFORMANCE

## Business Purpose
Assess whether agent-**attribute** factors (rating, age) relate to
delivery time, and whether delay is evenly distributed across rating
tiers — explicitly attribute-level, never individual-agent, per
`STAR_SCHEMA.md`'s design decision.

## Target Audience
Fleet/Rider Manager (primary).

## Primary Business Question
Business Questions #4, #9, #15.

## Secondary Questions
Is agent-rating coaching a plausible investment, or is delay better
explained by external conditions (covered on Page 4)?

## Executive Takeaway
*"Agent rating is weakly associated with delivery time (r²=0.0677) —
higher-rated agents are somewhat faster, but rating explains under 7% of
delivery-time variance. This is real but modest; it should not be read as
a strong lever on its own"* — directly reflecting the approved
Recommendation 5 (deprioritize rating-based coaching pending stronger
evidence), stated as evidence, not as the recommendation itself (which
lives in `docs/EXECUTIVE_RECOMMENDATIONS.md`).

## Visual Hierarchy

- **TOP:** Page header + explicit on-page caption (see below) + Date range only.
- **MIDDLE (left):** Delivery Time by Agent Rating Band (bar, not scatter — see Visual Section reasoning).
- **MIDDLE (right):** Agent Age vs. Delivery Time (binned bar, same reasoning).
- **BOTTOM:** Workload Distribution (row count + spread by rating band).
- **FOOTER:** Excluded-row-count caption + attribute-level disclaimer.

## KPI Section

*No KPI cards on this page.* Given the weak effect sizes (r²=0.0677 for
rating, r²=0.0668 for age), a card row implying these are headline
numbers would overstate their operational weight — the findings belong in
context, inside the charts, with their `n` and effect size visible, not
elevated to card status. This is a deliberate design choice, not an
oversight (see `reports/powerbi_mockup_review.md` Critical Review).

| KPI (chart-embedded, not a card) | Measure | Why It Exists | Baseline | Target/Benchmark | Visual Type |
|---|---|---|---|---|---|
| Agent Rating correlation | *(reported as a caption, not a DAX measure — `CORR()` is a SQL/Python descriptive statistic, per `reports/statistical_analysis_report.md` Test 3; no DAX equivalent is defined in `dax/measures.dax`, and none should be invented here)* | Grounds the page's Executive Takeaway in the actual test result | r = -0.2601 (Spearman), r² = 0.0677, n = 43,594 | No documented target — descriptive/inferential statistic, not a KPI. | Static caption on the page, sourced from `output/statistical_test_results.json` |

## Visual Section

| Visual | Chart Type | X Axis | Y Axis | Legend | Measure | Filters | Business Question | Reason |
|---|---|---|---|---|---|---|---|---|
| Delivery Time by Agent Rating Band | Clustered column (not scatter) | `DimAgent[Rating Band]` | `[Average Delivery Time (mins)]` | none | `[Average Delivery Time (mins)]`, `[Total Deliveries]` (label) | `agent_rating_valid_flag = true` (baked into the `Rating Band` column, which returns blank for invalid rows) | #4 | A raw scatter of 43,594 points would overplot into an unreadable smear at this volume; the rating-band bar (already validated exactly against `sql/analysis/Q04`) is the readable, correct aggregation |
| Agent Age vs. Delivery Time | Clustered column, age binned in 5-year groups (18–25, 26–35, 36–45, 46–65, matching the age-band grouping already used in `python/analysis/02_segment_comparisons.py`) | Age band | `[Average Delivery Time (mins)]` | none | `[Average Delivery Time (mins)]` | `agent_age_valid_flag = true` | #15 | Same overplotting reasoning as above; DAX_MEASURE_PLAN.md's "scatter" language is honored in spirit (showing the relationship shape) without the literal 43K-point scatter that would be unreadable and slow to render |
| Workload Distribution | Column + line combo: bars = `[Total Deliveries]` per rating band, line = `[Delivery Time Std Dev]` per band | `DimAgent[Rating Band]` | Bars: count; Line: minutes (std dev) | 2 series | `[Total Deliveries]`, `[Delivery Time Std Dev]` | `agent_rating_valid_flag = true` | #9 | Answers "is delay evenly spread or concentrated" directly — bar shows population size per band, line shows spread within it |

**Deviation from `DAX_MEASURE_PLAN.md`'s literal "scatter plot"
description, flagged explicitly:** a true point-scatter of all 43,594
individual deliveries is not implementable in a readable way in Power BI
at this row volume (severe overplotting). The binned-bar approach
preserves the same analytical question (does the metric vary with the
attribute) while remaining legible — this mirrors the same "value-based
bucketing over raw row-level display" principle already used
successfully in the approved `DimAgent[Rating Band]` calculated column
and `sql/analysis/Q04`.

## Slicer Design

| Slicer | Field | Purpose | Select | Affects |
|---|---|---|---|---|
| Date Range | `DimDate[full_date]` | Consistency with other pages | Range | All 3 visuals |

*No Area/Category/Weather/Traffic slicer here — per `DASHBOARD_PLANNING.md`'s
own design ("kept simple since `DimAgent` has no true individual-agent
identifier... slicing further would imply a precision the data doesn't
support"). This is preserved exactly, not weakened.*

## Cross-Filtering

```
Date Range slicer ↓ all 3 visuals (only interaction on this page)
```

## Tooltip Design

- **Rating Band bar:** `n` for that band, `[Average Delivery Time (mins)]`, and the page-level r/r² caption repeated for convenience.
- **Age Band bar:** `n` for that band, `[Average Delivery Time (mins)]`.
- Every tooltip on this page states: **excluded rows: 53 out-of-range ratings (>5.0), 54 null ratings** — per `DASHBOARD_PLANNING.md`'s existing tooltip spec, preserved exactly.

## Drillthrough
**No drillthrough required.** This is an intentional terminal leaf page —
`DimAgent` has no individual identity to drill into, and no other page's
grain matches "rating band" in a way that would make a drillthrough
meaningful. (Matches `DASHBOARD_PLANNING.md`'s existing spec exactly.)

## What Should NOT Be on This Page
- **No individual agent leaderboard, best/worst agent, or any visual
  implying a rankable individual identity** — hard rule, no true
  `Agent_ID` exists.
- No raw point-scatter (overplots at this volume — see above).
- No KPI card implying rating is a strong, headline-level driver — the
  effect size does not support that framing.
- No Area/Category/Vehicle slicer (would imply a false precision).

## Wireframe

```
┌──────────────────────────────────────────────────────────────────────┐
│ ROUTEIQ — AGENT PERFORMANCE                        [Date: ▓▓▓▓▓░░]   │
│ Fleet/Rider Manager view — attribute-level only, not individual      │
│ agents (no Agent_ID exists in source data)                           │
├───────────────────────────────┬──────────────────────────────────────┤
│ DELIVERY TIME BY RATING BAND  │ DELIVERY TIME BY AGE BAND             │
│ min                           │ min                                   │
│ 180┤██                        │ 180┤                                  │
│ 150┤██ ██                     │ 150┤  ██  ██                          │
│ 120┤██ ██ ██ ██ ██            │ 120┤  ██  ██  ██  ██                  │
│    └──────────────────        │    └──────────────────                │
│    2.5 3.0 3.5 4.0 4.5 5.0     │    18-25 26-35 36-45 46-65            │
│  r = -0.26, r² = 0.068         │  r = 0.26, r² = 0.067                 │
│  (weak — see caption below)    │  (weak — see caption below)           │
├───────────────────────────────┴──────────────────────────────────────┤
│ WORKLOAD DISTRIBUTION — deliveries (bars) & delivery-time spread(line)│
│  n  8k┤██        ██   ██   ██   ██          std.dev                  │
│      4k┤██   ██   ██   ██   ██   ──●───●───●───●───●──               │
│        └────────────────────────────────────────────                │
├──────────────────────────────────────────────────────────────────────┤
│ Attribute-level analysis only — no individual Agent_ID exists.        │
│ Excludes 53 out-of-range ratings and 54 null ratings from rating-band │
│ views. Weak correlations (r²<0.1): not a strong standalone lever.     │
└──────────────────────────────────────────────────────────────────────┘
```

## Visual Priority

| Visual | Priority |
|---|---|
| Delivery Time by Agent Rating Band | P1 |
| Agent Age vs. Delivery Time | P1 |
| Workload Distribution | P2 |

3 visuals, none P0 — deliberately: this page supports a real but
secondary business question, and no visual on it should be mistaken for
a headline finding.

---

# PAGE 4 — DELAY ROOT CAUSE

## Business Purpose
Answer "which conditions, and how much of breach volume, should we
prioritize" — the project's core analytical differentiator.

## Target Audience
City Ops Manager, CX Lead (primary); VP of Operations (prioritization
sign-off).

## Primary Business Question
Business Questions #3, #5, #12, #13, #14, #19, #20.

## Secondary Questions
*(Added per Flag 1 above)* Does weekend vs. weekday matter as a
condition? (Answer, to be shown directly: no — not statistically
significant.)

## Executive Takeaway
*"Traffic shows the strongest observed association with delivery time
(ε²=0.1404, large); weather is statistically significant but the effect
is small (ε²=0.0517). Weekend vs. weekday shows no significant
difference (p=0.9658) — day-of-week is not a meaningful lever here. The
Metropolitan/Jam-traffic combination concentrates the largest single
share of breach volume."*

## Visual Hierarchy

- **TOP:** Page header, Area slicer, Category slicer, "back to Page 2" link.
- **MIDDLE (large, center):** Pareto chart — Area × Traffic breach concentration, ranked bars + cumulative-% line.
- **MIDDLE (below, two columns):** (LEFT) Breach Rate by Weather bar, (RIGHT) Breach Rate by Traffic bar.
- **BOTTOM (two columns):** (LEFT) Statistical-significance annotation panel (Traffic/Weather/Weekend test results), (RIGHT) Adverse vs. Clear Weather Delta card + small weekend/weekday card *(Flag 1 addition)*.
- **FOOTER:** "Statistically significant ≠ operationally large — see effect size" methodology note (verbatim from `DASHBOARD_PLANNING.md`).

## KPI Section

| KPI | Measure | Why It Exists | Baseline | Target/Benchmark | Visual Type |
|---|---|---|---|---|---|
| Breach Rate by Weather | `[SLA Breach Rate %]` (Weather row context) | Core root-cause KPI | Fog 37.04% (highest) → Sunny 9.69% (lowest) | No documented target. | Bar chart, not a card |
| Breach Rate by Traffic | `[SLA Breach Rate %]` (Traffic row context) | Core root-cause KPI | Jam 42.58% (highest) → Low ~7% | No documented target. | Bar chart, not a card |
| Cumulative Breach Share % | `[Cumulative Breach Share %]` | The Pareto/prioritization number | Top combination (Metropolitan/Jam) alone = 47.22% of all breaches; top 4 combinations = 83.88% | No documented target — this is a descriptive concentration measure, not a benchmark. | Line over the Pareto bar chart |
| Adverse vs. Clear Weather Delta | `[Adverse vs Clear Weather Delta (mins)]` | Direct answer to Business Question #19 | +25.36 min (Adverse slower) | No documented target. | KPI card |
| *(Flag 1 addition)* Weekend vs. Weekday | *(no DAX card measure — reported as a static caption)* | Prevents the null result from being silently omitted, per this task's explicit instruction | p = 0.9658 (not significant), Cohen's d = -0.0013 (negligible) | Not applicable — this is a hypothesis-test result, not a rate/KPI. | Small text card, neutral styling (not red/green) |

## Visual Section

| Visual | Chart Type | X Axis | Y Axis | Legend | Measure | Filters | Business Question | Reason |
|---|---|---|---|---|---|---|---|---|
| Area × Traffic Pareto | Combo: bar (breach count) + line (cumulative %) | Area × Traffic combination, ranked descending | Bars: breach count; Line: cumulative % | 2 series | `[SLA Breaches]`, `[Breach Rank (Area x Traffic)]`, `[Cumulative Breach Share %]` | Area, Category, Date | #14, #20 | The project's signature visual — directly operationalizes the Pareto/prioritization framing named in `PROJECT_CHARTER.md` |
| Breach Rate by Weather | Vertical bar, sorted descending | `DimWeatherTraffic[weather]` | `[SLA Breach Rate %]` | none | `[SLA Breach Rate %]` | Area, Category, Date | #5, #12 | Direct, simple answer to "which weather condition breaches most" |
| Breach Rate by Traffic | Vertical bar, sorted descending | `DimWeatherTraffic[traffic]` | `[SLA Breach Rate %]` | none | `[SLA Breach Rate %]` | Area, Category, Date | #3 | Direct, simple answer to "which traffic level breaches most" |
| Statistical Significance Panel | Table / card grid (not a chart) | — | — | — | Static values sourced from `reports/statistical_analysis_report.md` (Tests 1, 2, 2b, 5) | Reacts to Weather/Traffic bar selection where feasible; otherwise static | #13 | Surfaces the actual test statistic, p-value, and effect size for the currently-relevant condition, so "significant" is never shown without its effect size beside it |

## Slicer Design

| Slicer | Field | Purpose | Select | Affects |
|---|---|---|---|---|
| Area | `DimArea[area_name]` | Root-cause investigation within one zone | Multi-select button | All 3 charts |
| Category | `DimCategory[category_name]` | Root-cause investigation within one product category | Multi-select dropdown | All 3 charts |

## Cross-Filtering

```
Area slicer     ↓ Pareto chart, Weather bar, Traffic bar
Category slicer ↓ Pareto chart, Weather bar, Traffic bar
Weather bar click ↓ Statistical Significance Panel (updates to show Test 2 detail)
Traffic bar click ↓ Statistical Significance Panel (updates to show Test 1 detail)
```

## Tooltip Design

- **Pareto bar:** exact breach count, breach share %, cumulative %, and
  `row_count` (total deliveries) for that Area×Traffic segment — low-`n`
  segments are visible via this row count, never auto-hidden (matches
  `sql/analysis/Q20`'s documented no-invented-threshold policy).
- **Statistical panel:** *"Statistically significant ≠ operationally
  large — see effect size."* (verbatim methodology caption, per
  `DASHBOARD_PLANNING.md`).

## Drillthrough
Entry point **from** Page 1 (bad week click) and Page 2 (area click), per
`DASHBOARD_PLANNING.md`'s existing spec. **No further drillthrough out**
of this page — it is the terminal root-cause page. "Back to Area &
Category Performance" link provided (existing spec, preserved).

## What Should NOT Be on This Page
- No causal language anywhere ("traffic causes delays" is prohibited;
  "traffic shows the strongest observed association" is required).
- No fabricated interaction-effect claim between weather and traffic
  beyond what the Pareto concentration itself shows (no interaction test
  was run — `reports/business_findings.md` Finding C explicitly notes
  this).
- No financial/cost figure.

## Wireframe

```
┌──────────────────────────────────────────────────────────────────────┐
│ ROUTEIQ — DELAY ROOT CAUSE                  [Area ▾]  [Category ▾]   │
│ ← Back to Area & Category Performance                                │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   AREA × TRAFFIC BREACH CONCENTRATION (Pareto)          cumulative % │
│   count                                                     100 ┤    │
│  5000┤██                                          ╭────────────╯    │
│  3000┤██  ██                                ╭─────╯                 │
│  1000┤██  ██  ██  ██  ██  ▓  ▓  ▓  ▓  ▓  ▓  ▓                       │
│      └───────────────────────────────────────────────────  0        │
│      Metro/  Metro/  Metro/  Urban/  Metro/  ... (15 combos)         │
│      Jam     Med     High    Jam     Low                            │
├───────────────────────────────┬──────────────────────────────────────┤
│ BREACH RATE BY WEATHER        │ BREACH RATE BY TRAFFIC                │
│ Fog     ████████ 37.0%        │ Jam    ████████ 42.6%                 │
│ Cloudy  ███████░ 36.4%        │ Medium ████░░░░ 25%ish                │
│ Windy   ████░░░░ 20.1%        │ High   ███░░░░░ ~23%                  │
│ Sunny   ██░░░░░░  9.7%        │ Low    █░░░░░░░  ~7%                  │
├───────────────────────────────┼──────────────────────────────────────┤
│ STAT SIGNIFICANCE PANEL       │ CONDITION DELTAS                      │
│ Traffic: H=6132.5 p≈0         │ Adverse vs Clear Weather: +25.36 min  │
│  ε²=0.1404 (LARGE)            │ Weekend vs Weekday: p=0.9658          │
│ Weather: H=2262.9 p≈0         │  NOT significant (d=-0.0013)          │
│  ε²=0.0517 (small)            │  → not a meaningful lever here        │
├───────────────────────────────┴──────────────────────────────────────┤
│ Significant ≠ operationally large — see effect size. SLA = analyst-  │
│ defined benchmark.                                                   │
└──────────────────────────────────────────────────────────────────────┘
```

## Visual Priority

| Visual | Priority |
|---|---|
| Area × Traffic Pareto | P0 |
| Breach Rate by Weather | P0 |
| Breach Rate by Traffic | P0 |
| Statistical Significance Panel | P1 |
| Adverse vs. Clear Weather Delta card | P1 |
| Weekend vs. Weekday caption (Flag 1 addition) | P2 |

6 visual groups — at the upper end of comfortable but still under the
8–10 challenge threshold, appropriate given this page carries the
project's core differentiator content.

---

## Executive Story — Actual Approved Page Order

```
PAGE 1 — Executive Overview
"How are we performing, and is it improving?"
        ↓ (drillthrough on a bad week, or simply navigate)
PAGE 2 — Area & Category Performance
"Where is the problem — which zone, which category?"
        ↓ (drillthrough on an area)
PAGE 4 — Delay Root Cause
"Why is that zone's problem occurring — which conditions concentrate it?"
        ↓ (back link)
PAGE 2 (return)

PAGE 3 — Agent Performance (standalone leaf, reached via nav bar only)
"Is agent rating/age a plausible lever, or is delay better explained by
conditions?" — answered directly: conditions (Pages 2/4) explain more
than agent attributes do.
```

This is `DASHBOARD_PLANNING.md`'s own approved journey (Page 3 is
explicitly a leaf, not part of the 1→2→4 drill chain) — not the generic
four-question arc suggested as an example in this task's instructions,
which does not fit this project's actual page order and was not forced
onto it.
