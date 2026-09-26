# SLA Methodology — RouteIQ

## Table of Contents
1. [Why SLA Is Not Present in the Dataset](#why-sla-is-not-present-in-the-dataset)
2. [Why an Analyst-Defined SLA Is Acceptable](#why-an-analyst-defined-sla-is-acceptable)
3. [Alternative SLA Definitions Considered](#alternative-sla-definitions-considered)
4. [Frozen SLA Definition](#frozen-sla-definition)
5. [Business Justification](#business-justification)
6. [Risks](#risks)
7. [Limitations](#limitations)
8. [Validation Plan](#validation-plan)
9. [Change Control](#change-control)

Related documents: `FEATURE_ENGINEERING.md` (mechanical formula for `sla_threshold_minutes`/`sla_breach_flag`), `KPI_DEFINITIONS.md` (KPIs #1, #2, #7 depend entirely on this document), `ASSUMPTIONS.md` (A7)

---

## Why SLA Is Not Present in the Dataset

The source dataset (`amazon_delivery.csv`) contains no `promised_time`, `SLA_target`, `committed_delivery_time`, or equivalent field. It records only what actually happened (`Delivery_Time`), not what was promised. This is a genuine, common gap in publicly available operational datasets — companies rarely publish their internal SLA commitments alongside raw delivery logs, since that number is itself commercially sensitive. This gap is stated openly rather than worked around silently.

## Why an Analyst-Defined SLA Is Acceptable

Real operations and analytics teams routinely define internal SLA benchmarks *from* observed performance distributions when no external target exists yet, or when validating whether an existing target is realistic (e.g., "is our current promise achievable given what we actually deliver"). Defining a threshold from the data's own distribution is a legitimate, industry-standard analytical technique — the key requirement, which this document enforces, is that the rule must be **defined and frozen before outcome analysis is run**, so it cannot be tuned to produce a desired breach rate. This document exists specifically to make that freeze auditable.

## Alternative SLA Definitions Considered

| Option | Definition | Pros | Cons | Selected? |
|---|---|---|---|---|
| A. Fixed threshold (e.g., 120 min for all orders) | Single company-wide cutoff | Simple, easy to communicate | Ignores that different product categories have legitimately different fulfillment times (e.g., Electronics vs. Grocery) — would misclassify entire categories as systematically breaching | No |
| B. Category-level median + fixed-minute buffer | `median(Delivery_Time) per Category + 30 min` | Accounts for category differences; buffer is easy to explain | The fixed-minute buffer is itself an arbitrary second parameter, doubling the number of undocumented judgment calls | No |
| C. Category-level 75th percentile (P75) | `PERCENTILE(Delivery_Time, 0.75) per Category` | Single parameter, no separate buffer to justify; directly interpretable as "slower than 75% of comparable historical deliveries" | Still arbitrary in *which* percentile is chosen (why 75 and not 70 or 80) | **Yes — selected** |
| D. Overall (non-category) P90 | `PERCENTILE(Delivery_Time, 0.90)` across all orders, ignoring category | Simple, single global number | Ignores category-level variation entirely — would make product categories with legitimately longer fulfillment times (e.g., bulky Home/Kitchen items) look disproportionately breach-prone | No |

## Frozen SLA Definition

> **`sla_threshold_minutes` for a given order = the 75th percentile (P75) of `Delivery_Time` within that order's `Category`, calculated once on the full cleaned dataset.**
>
> **`sla_breach_flag` = 1 if `Delivery_Time > sla_threshold_minutes` (strict greater-than) for that order's category, else 0.**

**This definition is frozen as of this document's approval and must not be changed after any breach-rate, OTD%, or root-cause result has been viewed.** If a change is later genuinely warranted, it must follow the Change Control process below — it cannot be silently edited in this file.

## Business Justification

- **Category-level, not global:** product categories in this dataset (Electronics, Grocery, Jewelry, etc.) plausibly have different legitimate fulfillment-time profiles. A single global threshold would systematically flag naturally-slower categories as "underperforming" rather than surfacing genuine operational delay.
- **P75, not mean or median:** using the 75th percentile as the target reflects a realistic operational framing — "we should be able to match our better three-quarters of historical performance," which is a stricter, more useful ops target than the median (which by definition half of deliveries already exceed) and less extreme than P90/P95 (which would set the bar so high that almost nothing counts as a breach, defeating the purpose of a breach-rate KPI).
- **Single parameter:** choosing one percentile avoids the false precision of picking both a base statistic (median) and a separate buffer value (Option B), which would require justifying two arbitrary numbers instead of one.

## Risks

- **Arbitrary percentile choice:** P75 is a defensible, industry-plausible choice, but it is still a choice — not derived from an external, company-published target. This must be stated every time OTD%/breach-rate figures are presented, not just once in this document.
- **Self-referential ceiling:** because the threshold is derived from the same dataset it's applied to, the aggregate breach rate is mechanically constrained to be roughly 25% *by category* at the moment the threshold is set (a mechanical property of using a percentile of the same data) — the breach-rate KPI is therefore most informative when compared *across* segments (which zone/condition breaches more than others), not as a standalone absolute number implying a 25% company-wide failure rate.
- **Category sample-size sensitivity:** a category with very few rows could produce an unstable P75. Profiling confirms all 16 categories have ~2,650–2,850 rows, so this is not a live risk here, but the check is documented as a safeguard for any future dataset swap.

## Limitations

- This threshold does **not** represent a company-published or customer-facing delivery promise — it is an internally-defined analytical benchmark, and every dashboard/report using it must label it as such (e.g., "SLA (analyst-defined benchmark)" in visual titles, not just "SLA").
- Because of the self-referential mechanical property noted above, the *absolute* breach rate number is less meaningful than the *relative* breach-rate comparison across zones/conditions/categories — the recommendations in `EXECUTIVE_RECOMMENDATIONS.md` should lean on the relative comparison, not the absolute percentage, as the primary evidence.
- This methodology could be revisited if a real company-published SLA becomes available for a production version of this project (see Change Control) — this document explicitly does not claim to be the "correct" universal answer, only a documented, defensible, and frozen one for this analysis.

## Validation Plan

- [ ] Threshold computed once, on the full cleaned dataset (post `DATA_CLEANING_PLAN.md`), and stored as a static per-category reference table — not recalculated live in SQL, Python, or DAX independently (which would risk three slightly different numbers from three slightly different code paths).
- [ ] The same static threshold table is loaded into the SQL analysis layer, the Python analysis, and the Power BI model, and `sla_breach_flag` outputs are cross-checked to match across all three before any dashboard is published.
- [ ] Aggregate breach rate is sanity-checked as plausible (expected to land in a moderate range given the P75-per-category construction; a result near 0% or nowhere close to a plausible range would indicate an implementation bug, not a real finding, and must be investigated before publishing).
- [ ] Every place this KPI appears (dashboard titles, README, resume bullets) uses "SLA (analyst-defined benchmark)" language, not unqualified "SLA."

## Change Control

Any change to the frozen definition above requires:
1. A documented reason (not "the breach rate looked wrong" without a specific methodological justification).
2. A new dated entry in `CHANGELOG.md` explaining the change.
3. Full re-validation per the checklist above before any previously-published figure is updated.
4. This document's "Frozen SLA Definition" section is then updated with a visible revision note — it is never edited to look as though the new definition was there from the start.
