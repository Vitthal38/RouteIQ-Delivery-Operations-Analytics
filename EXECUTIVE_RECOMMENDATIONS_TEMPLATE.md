# Executive Recommendations Template — RouteIQ

## Table of Contents
1. [Purpose](#purpose)
2. [Recommendation Entry Format](#recommendation-entry-format)
3. [Pre-Publication Checklist (per recommendation)](#pre-publication-checklist-per-recommendation)
4. [Recommendation Log](#recommendation-log)

Related documents: `VALIDATION_CHECKLIST.md` (Mandatory Business Validation Stage — every recommendation below must pass it), `BUSINESS_INSIGHTS_TEMPLATE.md` (to be produced separately — this template is for the recommendation layer built on top of a validated insight), `KPI_DEFINITIONS.md`

**This document contains no recommendations.** It defines the required structure so that, once real analysis is complete, every recommendation is written consistently and defensibly. Filling in a row here without a corresponding validated finding is a direct violation of this project's no-fabrication rule.

---

## Purpose

Executive recommendations are the most-read part of any analytics deliverable and the easiest place to accidentally overstate a finding. This template forces five things to exist for every recommendation before it is written: the evidence, the KPI it moves, the business impact, an owner, and a stated confidence level — so a recommendation is never just an opinion dressed as an insight.

## Recommendation Entry Format

Each recommendation must be filled in using this exact structure:

```
### Recommendation [N]: [One-line action statement]

- **Finding:** [The specific, quantified result this recommendation is based on —
   must reference an exact figure from a specific SQL query / Python output /
   dashboard visual, e.g., "SQL_ANALYSIS_PLAN.md Q20 output" or
   "STATISTICAL_ANALYSIS.md Test 1 result" — never a vague paraphrase]

- **Evidence:** [The exact source: which query, which script output file,
   which statistical test result, with the specific number(s)]

- **Supporting KPI:** [Which KPI from KPI_DEFINITIONS.md this recommendation
   is meant to move, and in what direction]

- **Recommendation:** [The specific, actionable statement — who should do
   what, framed per BUSINESS_REQUIREMENTS.md's "Expected Decisions"]

- **Owner:** [Which stakeholder role from BUSINESS_REQUIREMENTS.md is
   accountable for acting on this]

- **Priority:** [High / Medium / Low — based on the effect size and Pareto
   share the finding represents, not on how interesting the finding sounds]

- **Business Impact:** [Stated directionally unless a real cost/volume figure
   is computable from the dataset — per ASSUMPTIONS.md A8, no fabricated
   currency figure is permitted]

- **Confidence Level:** [High / Medium / Low — driven by: statistical
   significance AND effect size (not significance alone), sample size behind
   the finding, and whether any validity-flag exclusion materially limits the
   population the finding is based on]

- **Dependencies:** [Any other recommendation or finding this one assumes /
   builds on]

- **Business Validation (mandatory — see VALIDATION_CHECKLIST.md):**
  - [ ] Supported by data (specific reproducible source cited above)
  - [ ] Correlation vs. causation explicitly stated
  - [ ] Defensible in an interview (test/query, assumptions, effect size, limitation all statable without lookup)
  - [ ] An Operations Manager would actually act on this (maps to a concrete Expected Decision in BUSINESS_REQUIREMENTS.md)
```

## Pre-Publication Checklist (per recommendation)

Before any recommendation entry is added to the Recommendation Log below, or copied into a README/resume/dashboard, it must satisfy all of the following:

- [ ] The **Finding** and **Evidence** fields reference a real, already-executed query or script output — not a projected or illustrative number.
- [ ] The **Confidence Level** reflects the effect size from `STATISTICAL_ANALYSIS.md`, not just whether p < 0.05 (a statistically significant but tiny effect must not be labeled "High" confidence for business impact).
- [ ] The **Business Impact** field contains no fabricated currency or volume-savings figure unless it is directly computable from the dataset; if illustrative, it is labeled as such per `ASSUMPTIONS.md` A8.
- [ ] All four Business Validation questions are checked and genuinely answered, not left as unchecked boxes with the recommendation published anyway.
- [ ] The recommendation's **Priority** is consistent with its position in the Pareto/root-cause ranking (`SQL_ANALYSIS_PLAN.md` Q14/Q20) where applicable — a recommendation about a segment representing 2% of breach volume should not be labeled "High" priority ahead of one representing 40%.

## Recommendation Log

**Empty by design.** This table is populated only after Phase 2 analysis (`PYTHON_ANALYSIS_PLAN.md`) and full cross-validation (`VALIDATION_CHECKLIST.md`, `TESTING_PLAN.md`) are complete. No row exists here yet.

| # | Recommendation | Owner | Priority | Confidence | Status |
|---|---|---|---|---|---|
| — | *To be determined after analysis* | — | — | — | Not started |

*Rows will be added here, each fully expanded using the format above, once real findings exist. This log is never pre-populated with placeholder recommendations to "show structure" — an empty, honestly-labeled table is preferable to a fabricated example that could be mistaken for a real finding later.*
