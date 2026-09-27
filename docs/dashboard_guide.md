# Dashboard Guide

The full Power BI specification — DAX measures, the 5-page structure, drillthrough, tooltip pages, the
What-If SLA parameter, and dynamic (measure-driven) text — lives in **[`powerbi/README.md`](../powerbi/README.md)**,
next to the report file itself.

## Quick orientation

| Page | Answers |
|---|---|
| 1. Executive Overview | Are we meeting the benchmark, and is it trending? |
| 2. Operational Performance | Where and when do breaches concentrate (traffic, weather, area, hour)? |
| 3. SLA & Performance Factors | How sensitive is the benchmark, and which factors are associated with breach, on one comparable scale? |
| 4. Agent & Segment Analysis | What do the rating/age attribute patterns look like, with sample size always visible? |
| 5. Insights & Recommendations | What should operations investigate, with evidence and limitations stated for each item (`docs/recommendations.md`)? |

## Current state vs. target

`powerbi/RouteIQ_v1.pbix` is a 4-page report already built and screenshotted
(`powerbi/screenshots/`). It has not yet been rebuilt to the 5-page structure above — `powerbi/README.md`
lists exactly what's open (a missing P90 card, a rounding display issue, static callout text, no
drillthrough or tooltip pages) and gives the exact measures and steps to close each gap in Power BI
Desktop.

## Principles carried into every page

- **Color is semantic, not decorative:** navy = structure/primary series, teal = positive/secondary
  series, coral = SLA breach only.
- **Every rate is shown with its sample size.** A percentage without an `n` next to it is not shown.
- **No static text that a filter could make false.** Replace with a measure-driven text box
  (`powerbi/README.md`, "Dynamic text").
- **No individual-agent visual of any kind** — no identifier exists in the source data
  (`docs/limitations.md`).
- **"Associated with," never "causes."**
