# Executive Recommendations — RouteIQ

Generated: 2026-08-16

This is the populated Recommendation Log for the template defined in
`EXECUTIVE_RECOMMENDATIONS_TEMPLATE.md` (which remains unmodified, per
this phase's rules, as a reusable template). Every recommendation below
passed that template's Pre-Publication Checklist and the four Mandatory
Business Validation Stage questions from `VALIDATION_CHECKLIST.md` before
being added here. Full evidence trail and business story:
`reports/business_findings.md`, `reports/executive_recommendations.md`.

---

### Recommendation 1: Prioritize traffic-aware operational response, especially under Jam conditions

- **Finding:** Traffic condition shows the strongest observed association with delivery time of any factor tested — Kruskal-Wallis H=6132.4554, p≈0.0, ε²=0.1404 (large effect). Average delivery time: Low 101.35 min → Jam 147.76 min. (`reports/statistical_analysis_report.md` Test 1)

- **Evidence:** `sql/analysis/Q03_traffic_group_stats_for_significance_test.sql` (group n's: High 4,296 / Jam 13,725 / Low 14,999 / Medium 10,628); `sql/analysis/Q20_area_traffic_breach_concentration.sql` (top 5 breach segments are all Jam-traffic, 53.7471% of total breach volume); `output/statistical_test_results.json` (`test_1_traffic_vs_delivery_time`)

- **Supporting KPI:** SLA Breach Rate (`KPI_DEFINITIONS.md` #2) and P90 Delivery Time (#4), to move downward for Jam-traffic segments specifically

- **Recommendation:** City Ops Managers treat Jam-traffic periods as the highest-priority condition for daily/weekly triage (dispatch timing, staffing allocation), ahead of any other single condition in this analysis

- **Owner:** City Ops Manager (primary), VP of Operations (resourcing sign-off)

- **Priority:** High — largest effect size measured anywhere in this project, on the full dataset, independently reproduced in SQL and Python

- **Business Impact:** Directional only — no cost/financial field exists in the source data (`ASSUMPTIONS.md` A8). No percentage improvement, savings, or ROI figure is estimated.

- **Confidence Level:** High — large effect size (not significance alone), n=43,648, cross-validated

- **Dependencies:** None

- **Business Validation:**
  - [x] Supported by data (`sql/analysis/Q03`, `Q20`; `output/statistical_test_results.json`)
  - [x] Correlation vs. causation explicitly stated — "observed association," not "traffic causes delay"
  - [x] Defensible in an interview — test, assumption checks, effect size, and limitation all statable without lookup (see `reports/business_findings.md` Finding A)
  - [x] An Operations Manager would act on this — maps directly to the City Ops Manager's named weekly-triage decision (`BUSINESS_REQUIREMENTS.md`)

---

### Recommendation 2: Prioritize Metropolitian for a breach-reduction investigation, starting from its Jam-traffic concentration

- **Finding:** Metropolitian accounts for 83.7335% of total SLA breach volume (8,648 of 10,328) while carrying 74.8% of total delivery volume; its breach rate (26.50%) is elevated but not the highest of any area. (`sql/analysis/Q14_pareto_breach_share_area_and_category.sql` output)

- **Evidence:** `sql/analysis/Q01_sla_breach_rate_overall_and_by_area.sql`, `Q14_pareto_breach_share_area_and_category.sql`, `Q20_area_traffic_breach_concentration.sql`; `output/pareto_ranking.csv`

- **Supporting KPI:** Delay Root-Cause Share / Pareto Concentration (`KPI_DEFINITIONS.md` #7), to reduce Metropolitian's cumulative breach-volume share

- **Recommendation:** VP of Operations directs the first root-cause investigation effort at Metropolitian, using its Jam-traffic concentration as the starting hypothesis

- **Owner:** VP of Operations

- **Priority:** High — matches `PROJECT_CHARTER.md` Goal 3's explicit Pareto-prioritization objective directly

- **Business Impact:** Directional only, per `ASSUMPTIONS.md` A8 — no dollar/rupee figure is estimated

- **Confidence Level:** High for the volume-share figures (large n, cross-validated); not applicable as a causal claim — a Pareto ranking is concentration evidence, not root-cause proof

- **Dependencies:** Complements Recommendation 1 (same Jam-traffic pattern, area-specific lens)

- **Business Validation:**
  - [x] Supported by data (`Q01`, `Q14`, `Q20`)
  - [x] Correlation vs. causation explicitly stated — "largest contributor to breach volume," never "cause of breaches"
  - [x] Defensible in an interview (see `reports/business_findings.md` Finding C)
  - [x] An Operations Manager would act on this — maps directly to `PROJECT_CHARTER.md`'s stated prioritization goal

---

### Recommendation 3: Trigger proactive customer communication during adverse (non-Sunny) weather

- **Finding:** Adverse-weather (non-Sunny) deliveries average 129.03 min vs. 103.66 min for clear (Sunny) weather; Mann-Whitney p≈0.0, Cohen's d=-0.4965 (small, near the medium threshold). Full 6-category weather effect is significant but small (ε²=0.0517). (`reports/statistical_analysis_report.md` Test 2/2b)

- **Evidence:** `sql/analysis/Q19_clear_vs_adverse_weather_delta.sql`, `Q12_weather_with_most_sla_breaches.sql`; `output/statistical_test_results.json` (`test_2b_clear_vs_adverse_weather`)

- **Supporting KPI:** Delivery Time by Weather/Traffic Condition (`KPI_DEFINITIONS.md` #5)

- **Recommendation:** CX Lead uses adverse-weather conditions as a trigger for proactive delay communication to customers

- **Owner:** Customer Experience Lead

- **Priority:** Medium — real, moderate effect, but smaller than Recommendations 1-2's evidence

- **Business Impact:** Directional only — no CSAT or complaint field exists in the source data, so the customer-experience outcome of this recommendation cannot be measured from this dataset

- **Confidence Level:** Medium — statistically significant with a moderate (not large) effect size

- **Dependencies:** None

- **Business Validation:**
  - [x] Supported by data (`Q19`, Test 2b)
  - [x] Correlation vs. causation explicitly stated
  - [x] Defensible in an interview (see `reports/business_findings.md` Finding B)
  - [x] An Operations Manager (CX Lead) would act on this — maps directly to the CX Lead's named decision in `BUSINESS_REQUIREMENTS.md`

---

### Recommendation 4: Investigate Semi-Urban's delivery performance before committing resources

- **Finding:** 100% of Semi-Urban's 152 deliveries breach their SLA threshold; average delivery time 238.55 min vs. 124.91 min dataset-wide; P90 = 269.50 min, the highest of any area. (`sql/analysis/Q01`, `Q02`, `Q16`)

- **Evidence:** `sql/analysis/Q01_sla_breach_rate_overall_and_by_area.sql`, `Q02_worst_p90_delivery_time_by_area.sql`, `Q16_lowest_otd_area.sql`

- **Supporting KPI:** On-Time Delivery Rate % / SLA Breach Rate (`KPI_DEFINITIONS.md` #1, #2), by area

- **Recommendation:** City Ops Manager conducts a targeted, low-cost review of Semi-Urban's operations rather than immediately committing significant resourcing on this figure alone

- **Owner:** City Ops Manager

- **Priority:** Low-Medium — the most extreme figure in the dataset, but on the smallest sample (n=152, 0.35% of all deliveries)

- **Business Impact:** Directional only; no financial figure estimated

- **Confidence Level:** Medium — the figure is exact and reproducible, but small-sample instability cannot be ruled out

- **Dependencies:** None

- **Business Validation:**
  - [x] Supported by data (`Q01`, `Q02`, `Q16`)
  - [x] Correlation vs. causation explicitly stated — descriptive only, no test performed at this small n
  - [x] Defensible in an interview (see `reports/business_findings.md` Finding D) — the sample-size caveat is stated unprompted
  - [x] An Operations Manager would act on this — a bounded, low-cost investigation, not an over-commitment

---

### Recommendation 5: Do not prioritize agent-rating-based coaching or weekend-specific staffing as primary levers, based on current evidence

- **Finding:** Agent rating vs. delivery time is weakly correlated (Spearman r=-0.2601, r²=0.0677, n=43,594). Weekend vs. weekday shows no statistically significant difference (Mann-Whitney p=0.9658) and a negligible effect size (Cohen's d=-0.0013, n=43,648). (`reports/statistical_analysis_report.md` Tests 3, 5)

- **Evidence:** `sql/analysis/Q04_agent_rating_vs_delivery_time.sql`, `Q15_agent_age_vs_delivery_time_and_rating.sql`, `Q07_weekend_vs_weekday_delivery_time.sql`

- **Supporting KPI:** Agent Rating-Delivery Time Relationship (`KPI_DEFINITIONS.md` #6), to remain monitored but not treated as a strong lever pending stronger evidence

- **Recommendation:** Fleet/Rider Manager and VP of Operations do not treat agent-rating coaching or weekend-specific staffing changes as primary delay-reduction investments until stronger evidence emerges; direct resources to Recommendations 1-2 instead

- **Owner:** Fleet/Rider Manager (coaching budget), VP of Operations (weekend staffing)

- **Priority:** Medium — a confident deprioritization, not a low-value finding

- **Business Impact:** Directional only; this recommendation's value is in avoiding low-yield investment, not in a quantified saving

- **Confidence Level:** High for the weekend null result (negligible effect at full sample); Medium for the agent-rating deprioritization (weak but non-zero correlation)

- **Dependencies:** No true `Agent_ID` exists in the source data (`STAR_SCHEMA.md`) — this recommendation is scoped to rating/age attributes only, and would need to be revisited if individual-agent data became available

- **Business Validation:**
  - [x] Supported by data (`Q04`, `Q15`, `Q07`; Tests 3 and 5)
  - [x] Correlation vs. causation explicitly stated; weak/null result explicitly distinguished from "proof of no effect"
  - [x] Defensible in an interview (see `reports/business_findings.md` Finding E and Finding F)
  - [x] An Operations Manager would act on this — a concrete "hold" decision on two specific budget/staffing levers, redirecting effort to Recommendations 1-2

---

## Recommendation Log Summary

| # | Recommendation | Owner | Priority | Confidence | Status |
|---|---|---|---|---|---|
| 1 | Prioritize traffic-aware response, especially Jam conditions | City Ops Manager / VP Ops | High | High | Validated, ready for stakeholder review |
| 2 | Prioritize Metropolitian investigation via Jam-traffic concentration | VP of Operations | High | High (figures) | Validated, ready for stakeholder review |
| 3 | Proactive CX messaging during adverse weather | CX Lead | Medium | Medium | Validated, ready for stakeholder review |
| 4 | Investigate Semi-Urban before resourcing | City Ops Manager | Low-Medium | Medium | Validated, ready for stakeholder review |
| 5 | Deprioritize agent-rating coaching / weekend staffing | Fleet/Rider Manager / VP Ops | Medium | High/Medium | Validated, ready for stakeholder review |

*All 5 rows above were populated only after Phase 3 (SQL) and Phase 4
(Python EDA + statistical analysis) were complete and cross-validated,
per this template's own rule against pre-populating with placeholders.*
