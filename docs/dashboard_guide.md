# Dashboard Guide

The full Power BI specification — pages and DAX measures — lives in
**[`powerbi/README.md`](../powerbi/README.md)**, next to the report file itself.

## Quick orientation

| Page | Answers |
|---|---|
| 1. Executive Overview | Are we meeting the benchmark, and is it trending? |
| 2. Area & Category Performance | Where do breaches concentrate across area and category? |
| 3. Agent Performance | What do the rating/age attribute patterns look like? |
| 4. Delay Root Cause | Which conditions (traffic, weather, time) are associated with breaches, with the statistical evidence shown? |

## Principles carried into every page

- **Color is semantic, not decorative:** navy = structure/primary series, teal = positive/secondary
  series, coral = SLA breach only.
- **Every rate is shown with its sample size where it materially affects interpretation.**
- **No individual-agent visual of any kind** — no identifier exists in the source data
  (`docs/limitations.md`).
- **"Associated with," never "causes."**
