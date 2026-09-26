# Executive Recommendations — RouteIQ Phase 5

Generated: 2026-08-16

Built strictly on `reports/business_findings.md`. Every metric below is
quoted from an approved Phase 3/4 report — none is invented, and no
financial, percentage-improvement, or ROI figure appears anywhere in this
document, per this phase's explicit rule and `ASSUMPTIONS.md` A8 (no cost
field exists in the source data).

---

## Business Story

**Problem:** Operations leadership has no unified, quantified view of
where and why SLA performance breaks down — decisions have relied on
anecdote (`BUSINESS_REQUIREMENTS.md` Pain Points).

**Evidence:** 43,648 deliveries analyzed; SLA breach rate 23.6620%
against the frozen, analyst-defined category-P75 benchmark
(`SLA_METHODOLOGY.md`). Five formal statistical tests and a Pareto
concentration analysis were run, each with assumptions checked before
interpretation (`reports/statistical_analysis_report.md`).

**Key driver/pattern:** Traffic condition shows the strongest observed
association with delivery time of anything tested (ε²=0.1404, large) —
larger than weather (ε²=0.0517, small), distance, or agent attributes
(r²≈0.07 each). Breach volume is heavily concentrated: Metropolitian
alone accounts for 83.73% of all breaches, and Jam-traffic conditions
within it account for over half of that. Two commonly-assumed levers —
weekend staffing and agent-rating-based coaching — show no or weak
evidence of relevance in this data.

**Operational implication:** Effort concentrated on traffic-aware
response in Metropolitian, and on adverse-weather customer communication,
is better supported by the evidence than effort spread evenly across all
zones/conditions, or aimed at agent- or weekend-specific levers.

**Recommended action:** Five recommendations below, each tied to a
specific stakeholder decision already named in `BUSINESS_REQUIREMENTS.md`
or `DASHBOARD_PLANNING.md`.

**Measurement:** Every recommendation is measured by re-running the same
already-validated SQL queries (`sql/analysis/Q01`-`Q22`) on a rolling
basis — no new measurement infrastructure is required, and no target
percentage is asserted in advance.

---

## Recommendation 1 (Priority: High) — Prioritize traffic-aware operational response, especially under Jam conditions

### Recommendation
City Ops Managers should treat Jam-traffic periods as the highest-priority
condition for daily/weekly triage — e.g., reviewing dispatch timing or
staffing allocation specifically when Jam conditions are forecast or
observed — ahead of any other single condition in this analysis.

### Evidence
Traffic shows the largest effect size measured in this project: Kruskal-Wallis
H=6132.4554, p≈0.0, ε²=0.1404 (large). Average delivery time rises from
101.35 min (Low traffic) to 147.76 min (Jam) (`sql/analysis/Q03`). Within
the breach-concentration Pareto, the top 5 highest-breach segments are
all Jam-traffic combinations, together accounting for 53.7471% of total
breach volume (`sql/analysis/Q20`, `output/pareto_ranking.csv`).

### Business rationale
This is the single strongest, most defensible pattern in the entire
analysis — large effect size, full dataset (n=43,648), independently
reproduced in both SQL and Python. It maps directly to the City Ops
Manager's named weekly-triage decision (`BUSINESS_REQUIREMENTS.md`).

### Stakeholder
City Ops Manager (primary), VP of Operations (resourcing sign-off)

### Expected direction
If effective, SLA breach rate and P90 delivery time **specifically within
Jam-traffic segments** should decline in subsequent periods relative to
the levels established in this analysis. No specific percentage target is
asserted — none is derivable from this dataset.

### Measurement plan
Re-run `sql/analysis/Q03_traffic_group_stats_for_significance_test.sql`
and `Q20_area_traffic_breach_concentration.sql` on a rolling (weekly)
basis; monitor Jam-traffic breach rate and P90 delivery time as the
tracking metric.

### Limitation
This is an observed association, not a proven causal mechanism — no
controlled comparison (e.g., a dispatch-timing experiment) exists in this
data. No pairwise post-hoc test isolates exactly which traffic-level
differences are most reliable.

---

## Recommendation 2 (Priority: High) — Prioritize Metropolitian for a breach-reduction investigation, starting from its Jam-traffic concentration

### Recommendation
VP of Operations should direct the first root-cause investigation effort
at Metropolitian, using its Jam-traffic breach concentration as the
starting hypothesis to investigate — not because it necessarily has the
single worst rate, but because it carries the largest share of total
breach volume.

### Evidence
Metropolitian accounts for 8,648 of 10,328 total breaches — **83.7335%
of all breach volume** — while carrying 74.8% of total delivery volume
(32,634 of 43,648 rows); its breach rate (26.50%) is elevated but not the
highest (`sql/analysis/Q01`, `Q14`).

### Business rationale
Matches `PROJECT_CHARTER.md` Goal 3 exactly: identify "the smallest set
of conditions/zones responsible for the largest share of breach volume"
so effort is concentrated, not spread evenly.

### Stakeholder
VP of Operations

### Expected direction
A successful intervention should reduce Metropolitian's share of total
breach volume in subsequent Pareto re-runs, and/or narrow the gap between
its breach rate (26.50%) and Urban's (14.37%).

### Measurement plan
Re-run `Q01`, `Q14`, and `Q20` periodically; track Metropolitian's breach
rate and cumulative breach-volume share over time.

### Limitation
**A Pareto ranking identifies where breach volume concentrates — it does
not identify why.** This recommendation is to investigate, not to assume
the root cause is already known. Metropolitian's high volume share is
partly mechanical (it is also the largest area by delivery count).

---

## Recommendation 3 (Priority: Medium) — Trigger proactive customer communication during adverse (non-Sunny) weather, particularly Cloudy/Fog

### Recommendation
CX Lead should use adverse-weather conditions (any non-Sunny weather
value, with Cloudy and Fog as the slowest) as a trigger for proactive
delay communication to customers.

### Evidence
Clear (Sunny) vs. Adverse (non-Sunny): Mann-Whitney p≈0.0, Cohen's
d=-0.4965 (small, near the medium threshold). Cloudy averages 138.29 min
and Fog 136.57 min vs. Sunny's 103.66 min (`sql/analysis/Q19`, Test 2b).

### Business rationale
Directly matches the CX Lead's named decision in `BUSINESS_REQUIREMENTS.md`:
"trigger proactive delay communication during specific conditions."

### Stakeholder
Customer Experience Lead

### Expected direction
If adopted, delay-related customer complaints/contacts during adverse
weather should decrease — **this cannot be measured from RouteIQ's own
data, since no complaint or CSAT field exists in the source dataset**
(`ASSUMPTIONS.md`, Missing Columns). The delivery-time pattern itself
(breach rate by weather) can continue to be monitored here.

### Measurement plan
CX Lead tracks complaint/contact volume in their own systems,
before/after adoption. RouteIQ-side: continue monitoring
`sql/analysis/Q12`/`Q19` breach rate and average delivery time by weather
as the underlying operational signal.

### Limitation
The full 6-category weather effect is small (ε²=0.0517), not large — this
recommendation rests on the more targeted clear-vs-adverse cut, which
shows a larger but still moderate effect. This dataset has no way to
measure the actual customer-experience outcome of adopting this
recommendation.

---

## Recommendation 4 (Priority: Low-Medium) — Investigate Semi-Urban's delivery performance before committing resources

### Recommendation
City Ops Manager should conduct a targeted, low-cost review of
Semi-Urban's operations (e.g., manually reviewing the 152 underlying
orders) rather than immediately committing significant resourcing based
on its headline breach rate.

### Evidence
100% of Semi-Urban's 152 deliveries breach their SLA threshold; average
delivery time 238.55 min (vs. 124.91 min dataset-wide); P90 = 269.50 min,
the highest of any area (`sql/analysis/Q01`, `Q02`, `Q16`).

### Business rationale
The magnitude is the most extreme in the dataset, but n=152 is only 0.35%
of all deliveries — striking enough to warrant a look, too small to
justify major resourcing on this evidence alone.

### Stakeholder
City Ops Manager

### Expected direction
The investigation should either confirm the pattern persists as more data
accumulates, or reveal it as substantially a small-sample artifact.

### Measurement plan
Re-run `Q01`/`Q02` as more Semi-Urban data becomes available; treat the
100% figure as provisional, not final, until the sample grows materially.

### Limitation
The current data volume cannot distinguish "a real, severe local
operational issue" from "small-sample instability."

---

## Recommendation 5 (Priority: Medium) — Do not prioritize agent-rating-based coaching or weekend-specific staffing as primary levers, based on current evidence

### Recommendation
Fleet/Rider Manager and VP of Operations should not treat agent-rating
coaching or weekend-specific staffing changes as primary delay-reduction
investments until stronger evidence emerges — resources are better
directed at Recommendations 1-2.

### Evidence
Agent rating vs. delivery time: Spearman r=-0.2601, r²=0.0677 (weak,
n=43,594). Weekend vs. weekday: Mann-Whitney p=0.9658 (**not
significant**), Cohen's d=-0.0013 (negligible, n=43,648)
(`sql/analysis/Q04`, `Q07`, `Q15`; Tests 3 and 5).

### Business rationale
Directly answers the Fleet/Rider Manager's named decision in
`DASHBOARD_PLANNING.md` Page 3: "whether rating-based coaching is a
plausible lever... or whether delay is better explained by external
conditions." The evidence favors external conditions (Recommendations
1-3) over agent attributes or day-of-week.

### Stakeholder
Fleet/Rider Manager (coaching-budget decision), VP of Operations (weekend
staffing decision)

### Expected direction
This is a deprioritization, not an elimination — success looks like
resources flowing instead to Recommendations 1-2, revisited only if a
future re-analysis (e.g., with a longer date range or a true `Agent_ID`)
shows a materially stronger relationship.

### Measurement plan
Re-run `Q04`/`Q15`/`Q07` if/when a longer observation window or a true
agent identifier becomes available; revisit this recommendation only on a
material change in effect size, not on p-value alone.

### Limitation
Weak/null evidence for an effect is not proof of no effect. No true
`Agent_ID` exists in the source data (`STAR_SCHEMA.md`), so individual
agent performance cannot be assessed at all — this recommendation is
scoped to rating/age *attributes*, not individual agents.

---

## Step 14 — Recommendation Table

| Priority | Recommendation | Evidence | Owner | KPI to monitor | Measurement approach | Limitation |
|---|---|---|---|---|---|---|
| High | Prioritize traffic-aware response, especially Jam conditions | ε²=0.1404 (large), Kruskal-Wallis p≈0.0; Jam=147.76min vs Low=101.35min | City Ops Manager / VP Ops | Breach rate & P90 by traffic (`KPI_DEFINITIONS.md` #2, #4) | Rolling re-run of `Q03`/`Q20` | Association, not proven causal; no post-hoc test |
| High | Prioritize Metropolitian investigation via Jam-traffic concentration | 83.7335% of breach volume; 26.50% breach rate | VP of Operations | Breach-volume Pareto share, breach rate by area (`KPI_DEFINITIONS.md` #7, #2) | Rolling re-run of `Q01`/`Q14`/`Q20` | Concentration ≠ root cause |
| Medium | Proactive CX messaging during adverse weather | Clear vs Adverse d=-0.4965; Cloudy/Fog ~137min vs Sunny 103.66min | CX Lead | Breach rate & avg time by weather (`KPI_DEFINITIONS.md` #5) | CX's own complaint tracking + rolling `Q12`/`Q19` | No CSAT/complaint field in this dataset |
| Low-Medium | Investigate Semi-Urban before resourcing | 100% breach rate, n=152 | City Ops Manager | Breach rate & P90 by area (small-sample flagged) | Manual review + re-run `Q01`/`Q02` as data grows | n=152, 0.35% of dataset |
| Medium | Deprioritize agent-rating coaching / weekend staffing | Agent rating r²=0.0677; Weekend p=0.9658 (not significant), d=-0.0013 | Fleet/Rider Manager / VP Ops | Agent-rating correlation, weekend/weekday delta (`KPI_DEFINITIONS.md` #6) | Re-run `Q04`/`Q15`/`Q07` if data scope expands | Weak/null ≠ proof of no effect |

**No fabricated impact estimate (percentage improvement, cost savings,
ROI, headcount, conversion/retention uplift) appears in this table or
anywhere in this document.**

---

## Step 10 — Recommendation Quality Test (applied to all 5)

| Test | R1 | R2 | R3 | R4 | R5 |
|---|---|---|---|---|---|
| Connected to a validated finding? | ✅ | ✅ | ✅ | ✅ | ✅ |
| Realistically controllable by the stakeholder? | ✅ (dispatch/triage timing) | ✅ (investigation prioritization) | ✅ (messaging trigger) | ✅ (review scope) | ✅ (budget/staffing allocation) |
| Specific? | ✅ | ✅ | ✅ | ✅ | ✅ |
| Measurable? | ✅ (breach rate/P90 by traffic) | ✅ (Pareto share/breach rate) | ✅ (breach rate by weather; CX metrics external) | ✅ (re-run at larger n) | ✅ (re-run if scope expands) |
| Supported by data? | ✅ | ✅ | ✅ | ✅ (with caveat) | ✅ (as a null/weak result) |
| Avoids causal overclaiming? | ✅ | ✅ | ✅ | ✅ | ✅ |
| Acknowledges missing cost/customer data? | ✅ (limitation stated) | ✅ (limitation stated) | ✅ (explicit — no CSAT field) | ✅ | ✅ |
| Would an ops manager understand the action? | ✅ | ✅ | ✅ | ✅ | ✅ |

All 5 recommendations pass all 8 checks. No recommendation was rejected
at this stage, but Candidate 6 (distance correlation alone) was excluded
from becoming its own recommendation at Step 1/9 for failing the
"specific and actionable on its own" bar — it is used only as supporting
evidence within Recommendation 5.
