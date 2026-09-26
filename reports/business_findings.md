# Business Findings — RouteIQ Phase 5

Generated: 2026-08-16

Converts the 7 candidate findings in `reports/validated_findings_candidates.md`
into a prioritized, executive-usable set. Every number below is quoted
from `output/statistical_test_results.json`, `output/eda_summary.json`,
`reports/statistical_analysis_report.md`, `reports/python_eda_report.md`,
or `reports/sql_analysis_validation.md` — none is recalculated here.

Every finding is presented in four separated layers, per this phase's
required distinction:

- **OBSERVATION** — what the dataset shows.
- **STATISTICAL EVIDENCE** — whether it's statistically supported, and how strongly.
- **BUSINESS INTERPRETATION** — why it could matter operationally.
- **RECOMMENDATION** — deferred to `reports/executive_recommendations.md`; not stated here.

---

## Step 1 — Classification of the 7 candidates

| # | Candidate | Classification | Why |
|---|---|---|---|
| 1 | Traffic — strongest observed driver | **A. Executive-ready** | Large effect size (ε²=0.1404), full-dataset n=43,648, directly actionable via dispatch/routing timing |
| 2 | Weather — significant, small effect | **B. Useful, requires qualification** | Statistically real but small (ε²=0.0517); must not be presented at the same weight as traffic |
| 3 | Metropolitian — 83.73% of breach volume | **A. Executive-ready** | This is exactly the Pareto/prioritization framing `PROJECT_CHARTER.md` names as the project's core differentiator; large n, simple and reproducible |
| 4 | Semi-Urban — 100% breach rate | **B. Useful, requires strong qualification** | Striking rate, but n=152 (0.35% of dataset) — too small to carry the same confidence as Metropolitian |
| 5 | Fog+Jam — largest single weather×traffic segment | **B. Useful, requires qualification** | Descriptive Pareto only, no interaction test; substantially explained by Candidates 1-2 already — folded into the traffic/weather story rather than standing alone |
| 6 | Distance / agent rating / agent age — weak correlations | **C. Too weak for a standalone executive recommendation** | r² ≈ 0.065-0.077 each; real but explains under 8% of variance individually — retained only as supporting context and as the evidentiary basis for a "do not over-invest here" recommendation |
| 7 | Weekend vs. weekday — null result | **A. Executive-ready (as a null finding)** | Clean, confident negative result (p=0.9658, d=-0.0013) — valuable precisely because it rules out a resourcing lever with high confidence, not despite being non-significant |

**Not all 7 become standalone recommendations.** Candidates 3 and 5 are
combined into one finding (breach concentration), and Candidate 6 is used
as supporting/limiting context rather than its own action item — quality
over quantity, per Step 1's instruction.

---

## Step 2-8 — Evidence hierarchy per finding

### Finding A — Traffic shows the strongest observed association with delivery time

- **Observation:** Average delivery time rises with traffic congestion — Low 101.35 min, Medium 126.84 min, High 129.42 min, Jam 147.76 min (`sql/analysis/Q03`, `output/eda_summary.json`).
- **SQL evidence:** `sql/analysis/Q03_traffic_group_stats_for_significance_test.sql` — group n's High 4,296 / Jam 13,725 / Low 14,999 / Medium 10,628, sum = 43,648.
- **Statistical evidence:** Kruskal-Wallis H = 6132.4554, p ≈ 0.0 (`reports/statistical_analysis_report.md` Test 1). Non-parametric test used because both normality and homogeneity of variance failed (documented decision tree, not a default choice).
- **Effect size:** ε² = 0.1404 — **large**, per Cohen's conventional bands. This is the largest effect size measured anywhere in Phase 4.
- **Sample size:** n = 43,648 (full dataset).
- **Practical significance:** High. This is the one factor in the entire test suite where the effect size itself, not just significance, supports calling it a meaningful pattern.
- **Limitation:** No pairwise post-hoc test exists (none is documented in `STATISTICAL_ANALYSIS.md`), so which specific traffic-level pairs differ most is not formally tested — only the overall pattern (monotonic in the observed data) is established. This is an **observed association, not a proven causal mechanism** — traffic congestion is a highly plausible mechanical explanation, but the dataset cannot rule out confounding (e.g., certain areas/times having both worse traffic and other slow-down factors simultaneously).
- **Confidence level:** High.

**Step 4 — what this does and does not prove:** The data proves that
delivery time reliably differs across traffic conditions, with a
practically large effect size, not merely a statistically detectable one.
It does **not** prove that traffic congestion *causes* the delay in a
controlled sense — no experiment varied traffic while holding other
conditions fixed. **This is executive-ready.** Appropriate language:
*"Traffic conditions show the strongest observed association with
delivery time in this dataset."* Inappropriate language: *"Traffic
causes delivery delays."*

**Interview defensibility:** I selected this finding because it has the
largest effect size in the entire Phase 4 test suite, not merely the
smallest p-value — with n=43,648, almost every test in this project
reaches statistical significance, so effect size is what actually
separates a meaningful pattern from background noise. I'd defend the
number itself (ε²=0.1404, Kruskal-Wallis because both normality and
equal-variance assumptions failed) precisely, and I'd be upfront that
this is an association: the dataset has no randomized or controlled
comparison, so a genuinely confounded explanation (e.g., certain
high-traffic time windows also coinciding with other slow-down factors)
can't be fully ruled out — I'd say that plainly if asked.

---

### Finding B — Weather is a real but comparatively small factor

- **Observation:** Sunny deliveries average 103.66 min (fastest); Cloudy (138.29 min) and Fog (136.57 min) are slowest — a roughly 34-minute spread across weather types (`output/eda_summary.json`).
- **SQL evidence:** `sql/analysis/Q13_weather_group_stats_for_significance_test.sql`, `Q12_weather_with_most_sla_breaches.sql`.
- **Statistical evidence:** Kruskal-Wallis H = 2262.8928, p ≈ 0.0 (Test 2).
- **Effect size:** ε² = 0.0517 — **small**. Roughly one-third the size of the traffic effect.
- **Sample size:** n = 43,648.
- **Practical significance:** Real but modest — per `STATISTICAL_ANALYSIS.md`'s own interpretation standard, this must be reported as "statistically detectable but operationally small," not a major driver.
- **Secondary comparison:** Clear (Sunny) vs. Adverse (all non-Sunny): Mann-Whitney p ≈ 0.0, Cohen's d = -0.4965 (small, just under the medium threshold) — n Clear=7,078, Adverse=36,570 (Test 2b). This two-group cut shows a somewhat larger standardized effect than the 6-group omnibus test, which is a legitimate and expected pattern (collapsing 5 "adverse" categories into one group can sharpen a two-group contrast even when the full multi-group effect is smaller) — not a contradiction.
- **Limitation:** No post-hoc pairwise test between individual weather types. Association only.
- **Confidence level:** Medium.

**Step 5 — is this actionable?** Yes, but narrowly: the *clear-vs-adverse*
framing (Finding B's secondary comparison) is directly actionable for
proactive customer communication — exactly the decision
`BUSINESS_REQUIREMENTS.md` names for the CX Lead — even though the
full 6-category weather effect is too small to justify a major
operational overhaul on its own.

**Interview defensibility:** I'd highlight that I checked BOTH the full
6-group weather effect (small, ε²=0.0517) and the simpler clear-vs-adverse
cut (larger standardized effect, d≈-0.50) because the business question
that matters most here — "should we message customers proactively in bad
weather?" — is naturally a two-group question. I'd be direct that the
omnibus weather effect is small, not large, and that I'm not
recommending a major resourcing shift on weather alone.

---

### Finding C — SLA breach volume is heavily concentrated in Metropolitian and in Jam-traffic combinations (Pareto/concentration, not a causal claim)

- **Observation:** Metropolitian accounts for 8,648 of the dataset's 10,328 total SLA breaches — 83.7335% of all breach volume — while representing 74.8% of total delivery volume (32,634 of 43,648 rows). Its breach *rate* is 26.50%, elevated but not the highest (Semi-Urban's rate is higher, see Finding D). Within weather×traffic combinations, the single largest breach contributor is Fog/Jam (1,592 breaches, 15.41% of total breach volume), and the top 5 highest-breach combinations are all Jam-traffic (Fog/Jam, Cloudy/Jam, Windy/Jam, Sandstorms/Jam, Stormy/Jam), together accounting for 53.7471% of all breaches.
- **SQL evidence:** `sql/analysis/Q14_pareto_breach_share_area_and_category.sql` (area cut), `Q01_sla_breach_rate_overall_and_by_area.sql`, `Q20_area_traffic_breach_concentration.sql`.
- **Python evidence:** `output/pareto_ranking.csv` (independently reproduced, same figures).
- **Statistical evidence:** This is a **descriptive concentration ranking**, not a hypothesis test — `KPI_DEFINITIONS.md` #7 defines it this way explicitly. No p-value applies to "share of volume."
- **Practical significance:** High, for prioritization purposes specifically — this is the exact Pareto framing `PROJECT_CHARTER.md` Goal 3 calls for ("smallest set of conditions/zones responsible for the largest share of breach volume").
- **Limitation:** **A Pareto ranking describes where breach volume concentrates — it does not identify why those breaches happen or prove a causal driver.** Metropolitian's high volume share is partly mechanical (it is 74.8% of all deliveries); its breach *rate* (26.50%) is only moderately elevated relative to Urban's (14.37%). The Jam-traffic concentration in the top segments is consistent with, and likely substantially explained by, Finding A's traffic effect — but this Pareto table alone does not prove that.
- **Confidence level:** High for the volume-share figures themselves (large n, simple counts, independently cross-validated in SQL and Python); the ranking is not a causal claim at any confidence level.

**Step 8 — concentration vs. causation:** This finding is stated
throughout as *"the largest contributor to breach volume,"* never as
*"the cause of breaches."* The distinction matters operationally too: a
volume-driven concentration (Metropolitian) argues for where to look
first when resourcing triage, while a rate-driven concentration
(Semi-Urban, Finding D) argues for a different, smaller-scale
investigation.

**Interview defensibility:** I'd explain that I deliberately reported
"contributes 83.7% of breach volume" rather than "is the worst-performing
area" — those are different claims, and conflating them is a common
analytical mistake. Metropolitian's breach *rate* is actually
lower than Semi-Urban's; it dominates the Pareto ranking because it's
also 75% of all deliveries. I picked this framing specifically because
Pareto/concentration analysis is what the project brief asked for as the
core differentiator, and because volume-based prioritization is a
legitimate operational lever even without proving causation — it tells
you where the most breach volume physically sits.

---

### Finding D — Semi-Urban has a 100% breach rate, but on a small, low-confidence sample

- **Observation:** All 152 Semi-Urban deliveries breach their category's SLA threshold (100.0000%); average delivery time 238.55 min vs. the 124.91 min dataset average; P90 = 269.50 min, the highest of any area.
- **SQL evidence:** `sql/analysis/Q01_sla_breach_rate_overall_and_by_area.sql`, `Q02_worst_p90_delivery_time_by_area.sql`, `Q16_lowest_otd_area.sql`.
- **Statistical evidence:** Descriptive only — n=152 (0.35% of the dataset) is too small for any of this phase's omnibus tests to isolate an area-specific effect at this granularity; no hypothesis test was run at this specific cut.
- **Practical significance:** Potentially high if real and persistent, but **the sample size caveat must travel with this finding everywhere it's used** — a 100% rate on 152 rows is a very different claim than a 100% rate on 32,634 rows.
- **Limitation:** Small-sample instability. This finding cannot be generalized with the same confidence as Findings A-C.
- **Confidence level:** Medium (the figure is exact and reproducible; its generalizability is limited).

**Interview defensibility:** I'd flag immediately, unprompted, that
n=152 is the smallest area segment in the dataset (0.35% of all rows) —
a striking number that still needs a confidence caveat before being
treated as a stable rate. I'd frame any resulting action as "investigate
first, resource second," specifically because of the sample size, not
despite noticing it.

---

### Finding E — Weekend status does not explain delivery-time differences in this dataset

- **Observation:** Weekday average = 124.8960 min (n=31,627); Weekend average = 124.9631 min (n=12,021) — a difference of 0.07 minutes.
- **SQL evidence:** `sql/analysis/Q07_weekend_vs_weekday_delivery_time.sql` — group counts and means match exactly.
- **Statistical evidence:** Mann-Whitney U = 190,043,643.5, **p = 0.9658 — not significant.**
- **Effect size:** Cohen's d = -0.0013 — **negligible**, reinforcing the non-significant result rather than contradicting it.
- **Sample size:** n = 43,648 (full dataset — this null result is not due to low power).
- **Practical significance:** A confident negative result. Per Step 7, this is treated as a genuinely useful finding, not a failed test.
- **Limitation:** This is bounded to the single ~8-week observation window and does not rule out a weekend effect under different conditions (e.g., holiday season, a different market). It supports *"weekend status alone does not appear to explain delivery-time differences in this dataset,"* not *"weekends never affect delivery performance."*
- **Confidence level:** High — precisely because the effect size is negligible at full-dataset scale, not because the p-value alone is large.

**Interview defensibility:** I'd say this is the finding I'm most
confident presenting as a clean result, because it isn't just
"non-significant" (which can also mean "underpowered") — the effect size
itself is negligible (d=-0.0013) at the full 43,648-row sample, which
rules out the more common failure mode where a real small effect is
just hard to detect. I'd be careful to phrase the conclusion as bounded
to this dataset's ~8-week window, not as a universal claim about weekends.

---

### Finding F (context only, not a standalone recommendation) — Distance, agent rating, and agent age are weakly associated with delivery time

- **Observation / statistical evidence:** distance r=0.2781 (r²=0.0774, n=39,997); agent rating r=-0.2601 Spearman (r²=0.0677, n=43,594); agent age r=0.2585 (r²=0.0668, n=43,594). All p≈0 (large n makes weak correlations significant).
- **Business interpretation:** Individually, none of these explains more than about 8% of delivery-time variance — too weak to justify a standalone operational recommendation (e.g., a rating-based coaching program) on this evidence alone.
- **Limitation:** Attribute-level only (no true `Agent_ID` exists — see `STAR_SCHEMA.md`); reverse causality and confounding (e.g., more experienced agents assigned easier routes) are plausible, untestable-from-this-data alternative explanations.
- **Confidence level:** High for reproducibility (exact SQL/Python match); Low for operational relevance on its own.
- **Role in the final story:** Used as evidence for Recommendation 5 (deprioritization), not as its own action item.

---

## Step 3 — Prioritization (not by p-value or effect size alone)

| Rank | Finding | Why it ranks here |
|---|---|---|
| 1 | Traffic (Finding A) | Largest effect size AND directly actionable AND high confidence — the strongest finding on every dimension simultaneously |
| 2 | Breach concentration — Metropolitian + Jam traffic (Finding C) | Directly matches the project's core prioritization objective; large n; independently cross-validated in SQL and Python |
| 3 | Weekend/weekday null (Finding E) | High confidence, operationally useful as a "don't invest here" redirect, even though it is a non-significant result |
| 4 | Weather (Finding B) | Real and significant, but smaller effect than traffic — ranked below Findings A/C/E despite a "smaller" p-value story, because effect size and actionability, not p-value, drive this ranking |
| 5 | Semi-Urban (Finding D) | Striking but small-sample — ranked below the large-n findings specifically because of confidence, not because the number itself is small |
| 6 | Distance/agent attributes (Finding F) | Real but weak — context/limitation only, not ranked as an actionable finding |

---

## Step 13 — Final Findings Table

| Finding | Evidence | Statistical support | Effect size | Business relevance | Actionability | Confidence | Limitation |
|---|---|---|---|---|---|---|---|
| Traffic strongest driver | `Q03`, Test 1 | Kruskal-Wallis, p≈0.0 | ε²=0.1404 (large) | High | High — dispatch/routing timing | High | Association, not proven causal mechanism; no post-hoc pairwise test |
| Breach volume concentrated in Metropolitian + Jam traffic | `Q14`, `Q20`, `pareto_ranking.csv` | Descriptive Pareto (no test applies) | n/a (83.73% cumulative share) | High | High — zone/condition prioritization | High (figures); n/a (not causal) | Volume share ≠ rate; partly reflects Metropolitian's 74.8% volume share |
| Weekend ≈ weekday (null) | `Q07`, Test 5 | Mann-Whitney, p=0.9658 (not significant) | d=-0.0013 (negligible) | Medium | Medium — redirects away from weekend staffing lever | High | Bounded to this ~8-week window |
| Weather significant, small | `Q13`, `Q12`, Test 2/2b | Kruskal-Wallis, p≈0.0 | ε²=0.0517 (small) / d=-0.4965 (clear-vs-adverse) | Medium | Medium — proactive CX messaging (narrow use) | Medium | No pairwise test; small omnibus effect |
| Semi-Urban 100% breach rate | `Q01`, `Q02`, `Q16` | Descriptive only | n/a | Potentially high, unproven | Low-Medium — investigate before resourcing | Medium | n=152, 0.35% of dataset |
| Distance / agent rating / agent age — weak correlations | `Q04`, `Q10`, `Q15`, Tests 3-4 | Pearson/Spearman, p≈0.0 | r²≈0.065-0.077 each | Low (individually) | Low as standalone levers | High (reproducibility) / Low (relevance) | Attribute-level only; reverse causality/confounding not ruled out |

No recommendation is stated in this document — see `reports/executive_recommendations.md`.
