# Power BI Mockup — Design Review

Generated: 2026-08-16

Reviews `docs/POWERBI_DASHBOARD_MOCKUP.md` against the approved evidence
base (`reports/business_findings.md`, `reports/executive_recommendations.md`,
`reports/dax_validation.md`) and this project's design principles. No
`.pbix` exists yet — this reviews the blueprint only.

---

## Scored Review

| # | Dimension | Score /10 | Rationale |
|---|---|---|---|
| 1 | Business relevance | 9 | Every visual on every page traces to a named `SQL_ANALYSIS_PLAN.md` business question; nothing exists to demonstrate a chart type. Page 3's inherently weak evidence (r²≈0.07) caps this slightly — the page is relevant but structurally minor. |
| 2 | Executive clarity | 9 | Page 1 holds to 5 KPI cards + 1 chart + 1 evidence strip; the Executive Takeaway on every page is a specific, numbered sentence, not a vague summary. |
| 3 | Visual hierarchy | 9 | Consistent TOP/MIDDLE/BOTTOM, LEFT/CENTER/RIGHT zoning across all 4 pages using the same 5-zone canvas grid. |
| 4 | KPI selection | 9.5 | Zero invented KPIs; every "No documented target" is stated explicitly rather than fabricated; Page 3 deliberately omits KPI cards given weak effect sizes rather than padding the page. |
| 5 | Chart selection | 9 | No pie/3D/gauge anywhere; heatmap and Pareto combo chart used where they're the analytically correct form. One explicit, justified deviation (binned bars instead of a literal 43K-point scatter on Page 3) — deviation disclosed, not hidden. |
| 6 | Storytelling | 9 | Clear page-to-page narrative matching the *actual* approved page order (not the generic 4-question arc suggested as an example, which didn't fit and wasn't forced). |
| 7 | Interactivity | 8 | Slicers, cross-filtering, and drillthrough are all grounded in real single-direction relationships. Page 4's click-driven Statistical Significance Panel is the one interaction whose implementation is non-trivial — flagged below, not swept under the rug. |
| 8 | Analytical integrity | 9.5 | Strongest dimension: sample sizes attached to every instance of Semi-Urban's 100% figure (including a gap caught and fixed during this review — see Critical Review), the weekend null result preserved rather than hidden, no causal language anywhere, weak correlations explicitly labeled weak. |
| 9 | Power BI implementability | 8 | Most visuals are native Power BI chart types (bar, line, matrix, combo). Two specific risk areas flagged below (heatmap column count, Pareto panel interactivity) keep this from a 9+. |
| 10 | Hiring-manager appeal | 9.5 | The explicit "no documented target" discipline, the flagged/fixed gap, and the deliberate under-design of Page 3 read as senior BI judgment, not a template fill-in. |

## Overall Mockup Score

**(9 + 9 + 9 + 9.5 + 9 + 9 + 8 + 9.5 + 8 + 9.5) / 10 = 9.0 / 10**

---

## Critical Review (ruthless, as instructed)

### Found and fixed during this review

**Page 1 mini-bar was missing its sample-size tooltip.** The Breach Rate
by Area mini-bar shows Semi-Urban's 100% figure — exactly the kind of
potentially misleading rate this task's instructions call out by name —
but the first draft of the Tooltip Design section did not specify `n`
for that visual. **Corrected in `docs/POWERBI_DASHBOARD_MOCKUP.md`**
(tooltip spec and wireframe both updated to show `n=152` etc. inline)
before this review was finalized. Flagging this here rather than quietly
fixing it and saying nothing, since a design review that never finds
anything wrong with its own subject is not a credible review.

### Flagged, not fixed — implementation-risk notes for the eventual `.pbix` build

**Page 4's "Weather bar click → Statistical Significance Panel updates"
interaction is more complex than it looks.** As specified, clicking a
weather bar to dynamically swap the panel to that test's statistics
requires either a small disconnected lookup table of the 4 test results
(not part of the approved star schema or `dax/measures.dax`) driving a
`SELECTEDVALUE()`-based measure, or a bookmark-based manual toggle. This
is buildable, but it is the single most DAX-engineering-intensive
interaction in the entire mockup, and it was not validated in
`reports/dax_validation.md` (that report validates the 14 approved
measures, not a hypothetical selection-driven lookup pattern). **Recommendation:**
simplify to a static side-by-side panel showing all relevant test results
at once (Traffic, Weather, Clear/Adverse, Weekend) with no click-driven
behavior — everything a viewer needs is 4 short rows of text; the dynamic
version adds implementation risk for a marginal presentation gain. This
is a simplification recommendation, not a defect — the page still
functions correctly as a static panel.

**The Area × Category heatmap (Page 2) has 16 category columns.** At the
allotted ~320px main-analysis-area height on a 1280×720 canvas, 16
columns is workable but tight — cell labels will be small, and Power BI's
Matrix visual may need horizontal scrolling or a reduced font size to fit
without truncation. **Recommendation:** when built, test at actual
canvas size before finalizing; if crowded, consider a Top-N category
filter (e.g., top 8 by breach rate, with the rest folded into "Other
categories") rather than shrinking all 16 to illegibility. Not a redesign
of the page — the heatmap is still the right visual — just a build-time
sizing caution.

### Considered and explicitly rejected as unnecessary

- **A 6th KPI card on Page 1** (e.g., week-over-week delta as its own
  card) — rejected: would push past the 5–6 card guidance's comfortable
  zone and duplicates information already on the trend line immediately
  below it.
- **A KPI card row on Page 3** — rejected, and defended above (dimension
  4): given r²≈0.07 for both rating and age, a card row would visually
  overstate these as headline-strength findings. The weak-effect-size
  caption inside each chart is more honest than a card would be.
- **A pie chart for "share of breach volume by area" on Page 1 or Page 2**
  — rejected: would invite exactly the rate-vs-volume confusion the
  Executive Takeaway sections are written to prevent (Metropolitan is
  high-*volume*, Semi-Urban is high-*rate* — a single pie cannot show
  both, and would likely be misread as "Metropolitan is the worst area").
- **An individual-agent table or leaderboard** — never considered;
  excluded by hard rule (no true `Agent_ID` exists).
- **A bicycle row/category anywhere** — never considered; excluded by
  hard rule (0 rows exist post-cleaning).

### What would make this look like a typical fresher project (and why this mockup avoids it)

A typical fresher dashboard mockup would: (1) put 8+ KPI cards on the
landing page regardless of whether each has a real denominator behind it,
(2) use a pie chart for every part-to-whole question regardless of
whether it's the right form, (3) present every statistically significant
result as equally important, (4) quietly drop the weekend null result
because "it didn't find anything," (5) never mention what a chart does
*not* prove. This mockup does none of those — the 5-card discipline on
Page 1, the explicit "no documented target" statements, the deliberately
sparse Page 3, and the preserved weekend null result are the specific,
checkable differences.

---

## Final Gate

All findings above are either already corrected in the mockup document
or are non-blocking implementation-risk notes for the build phase, not
defects in the design itself. No unsupported claim, no hidden sample
size, no invented KPI, and no causal language survived this review.

# MOCKUP APPROVED FOR POWER BI

Two carried-forward build-time notes (Page 4 panel interactivity,
Page 2 heatmap column count) should be re-checked once actual Power BI
Desktop work begins — noted in `docs/POWERBI_DASHBOARD_MOCKUP.md` and
here, not silently dropped.
