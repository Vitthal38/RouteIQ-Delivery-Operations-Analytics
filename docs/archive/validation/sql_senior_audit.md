# SQL Senior Audit — RouteIQ

Generated: 2026-08-16
**Updated: 2026-08-16 — remediation section appended below. All findings
above this notice are the original, unmodified audit and are preserved
as the historical record — nothing above has been edited or erased.**

**This is an independent audit, not a re-run of prior validation.** Every
one of the 22 files in `sql/analysis/` was re-read line-by-line against
`SQL_ANALYSIS_PLAN.md`'s exact question text and `KPI_DEFINITIONS.md`'s
exact formulas. Beyond re-reading, a separate set of read-only diagnostic
queries was run directly against the live database specifically to probe
for tie-handling, determinism, and boundary problems that a
"does-it-execute-and-reconcile" validation pass would not surface. No SQL
file, database object, Python file, or documentation file (other than this
report) was modified during this audit.

---

## Executive Verdict

The RouteIQ SQL layer is well-constructed, and the overwhelming majority
of the 22 queries are correct, clearly aligned to their business
question, and free of denominator or grain errors. This audit found **one
confirmed logic defect** (Q09's `NTILE` tie-handling) and **two
determinism/labeling concerns** (Q14's tied running-total order, Q17's
un-flagged week-gap comparison) that a "does it execute and reconcile"
pass would not surface — which is exactly the class of problem this audit
was commissioned to find. None of these three issues touches a P0 query,
a headline KPI, the frozen SLA logic, or a figure used in
`reports/business_findings.md` or `docs/EXECUTIVE_RECOMMENDATIONS.md`.
No double-counting, no accidental row loss, no denominator error, and no
SLA-methodology violation was found anywhere in the 22 files.

## Overall SQL Score

**9.25 / 10 — Exceptional** (see classification bands below; this score
sits at the low end of that band specifically because of the confirmed
Q09 defect, not despite it).

### SQL Quality Classification

| Band | Label |
|---|---|
| 9.0–10.0 | Exceptional |
| 8.0–8.9 | Strong |
| 7.0–7.9 | Good / resume-ready |
| 6.0–6.9 | Needs improvement |
| <6.0 | Weak |

RouteIQ's SQL layer lands in **Exceptional**, driven by 19 of 22 queries
scoring 9.0+ individually, with the average pulled down specifically by
the one confirmed defect (Q09) and two real-but-bounded determinism
issues (Q14, Q17) — this is a disclosed, evidence-weighted score, not a
rounded-up one.

---

## Query-by-Query Scores

| Query | Score /10 | Status |
|---|---|---|
| Q01 | 9.5 | PASS |
| Q02 | 9.5 | PASS |
| Q03 | 9.5 | PASS |
| Q04 | 9.5 | PASS |
| Q05 | 9.5 | PASS |
| Q06 | 9.5 | PASS |
| Q07 | 10.0 | PASS |
| Q08 | 10.0 | PASS |
| Q09 | 6.0 | **PASS WITH WARNING** |
| Q10 | 9.5 | PASS |
| Q11 | 9.0 | PASS WITH WARNING |
| Q12 | 10.0 | PASS |
| Q13 | 9.5 | PASS |
| Q14 | 8.0 | PASS WITH WARNING |
| Q15 | 9.5 | PASS |
| Q16 | 9.5 | PASS |
| Q17 | 8.5 | PASS WITH WARNING |
| Q18 | 9.5 | PASS |
| Q19 | 9.5 | PASS |
| Q20 | 9.5 | PASS |
| Q21 | 9.5 | PASS |
| Q22 | 9.0 | PASS |

**Average: 203.5 / 22 = 9.25.** No query scored FAIL or BLOCKED.

---

## Query Audit Matrix

| Query | Business Question | Syntax | Logic | Grain | Joins | Denominator | KPI Def. | Edge Cases | Stat./Analytical | Business Relevance | Score | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Q01 | ✅ | ✅ | ✅ | order→area | ✅ 1:many, no fan-out | ✅ per-area own total | ✅ #2 | ✅ Other retained | n/a (descriptive) | High | 9.5 | PASS |
| Q02 | ✅ | ✅ | ✅ | order→area | ✅ | n/a (percentile) | ✅ #4 | ✅ | ✅ PERCENTILE_CONT correct | High | 9.5 | PASS |
| Q03 | ✅ | ✅ | ✅ | order→traffic | ✅ | n/a | n/a (test prep) | ✅ | ✅ no p-value computed (correct scope) | High | 9.5 | PASS |
| Q04 | ✅ | ✅ | ✅ | order→agent attr | ✅ | ✅ n reported explicitly | ✅ #6 | ✅ clean FLOOR bucketing, verified no overlap | ✅ CORR is descriptive only | High | 9.5 | PASS |
| Q05 | ✅ | ✅ | ✅ | order→weather×traffic | ✅ | n/a | ✅ #5 | ✅ no ties found (verified) | n/a | Medium-High | 9.5 | PASS |
| Q06 | ✅ | ✅ | ✅ | order→category | ✅ | n/a | ✅ #3 | ✅ | n/a | Medium | 9.5 | PASS |
| Q07 | ✅ | ✅ | ✅ | order→weekend flag | n/a | n/a | n/a (test prep) | ✅ embedded reconciliation check | ✅ | Medium | 10.0 | PASS |
| Q08 | ✅ | ✅ | ✅ | order→area | ✅ | ✅ | ✅ #1 | ✅ embedded OTD+breach=100 check | n/a | High | 10.0 | PASS |
| Q09 | ⚠️ reframed, correctly caveated | ✅ | ⚠️ **NTILE tie defect** | order→rating quartile | ✅ | ✅ | n/a (exploratory) | ❌ **tie boundary not deterministic (confirmed)** | ⚠️ quartile labels misleading | Medium | 6.0 | **PASS WITH WARNING** |
| Q10 | ✅ | ✅ | ✅ | order→condition | ✅ | ✅ n reported explicitly | n/a (test prep) | ✅ correct mixed-population design | ✅ CORR descriptive only | High | 9.5 | PASS |
| Q11 | ✅ | ✅ | ✅ | order→week | ✅ | n/a | ✅ #3/#4 trend | ⚠️ week-8 gap bridged by LAG, partially mitigated by visible dates | n/a | High | 9.0 | PASS WITH WARNING |
| Q12 | ✅ | ✅ | ✅ | order→weather | ✅ | ✅ | ✅ #2 | ✅ embedded reconciliation check | n/a | High | 10.0 | PASS |
| Q13 | ✅ | ✅ | ✅ | order→weather | ✅ | n/a | n/a (test prep) | ✅ | ✅ no p-value computed | Medium | 9.5 | PASS |
| Q14 | ✅ (disclosed interpretation) | ✅ | ⚠️ **tie order non-deterministic in running SUM** | order→area / order→category | ✅ | ✅ breach-count denominator, matches #7 formula | ✅ #7 | ✅ RANK() ties handled correctly; ⚠️ running total is not | n/a | High | 8.0 | PASS WITH WARNING |
| Q15 | ✅ | ✅ | ✅ | order→agent attr | ✅ | ✅ both flags applied | n/a (correlation prep) | ✅ | ✅ | Medium | 9.5 | PASS |
| Q16 | ✅ | ✅ | ✅ | area (single row) | ✅ reuses Q08 logic exactly | ✅ | ✅ #1 | ⚠️ `LIMIT 1` has no tiebreaker (not triggered by current data) | n/a | High | 9.5 | PASS |
| Q17 | ✅ | ✅ | ✅ | week | ✅ | n/a | ✅ #8 | ⚠️ **week-8 gap bridged, no in-query date evidence** | n/a | Medium | 8.5 | PASS WITH WARNING |
| Q18 | ✅ | ✅ | ✅ | order→category | ✅ | n/a | ✅ same as Q06 | ✅ | n/a | Medium | 9.5 | PASS |
| Q19 | ✅ explicit grouping stated | ✅ | ✅ | order→weather group | ✅ | n/a | ✅ #5 | ✅ | n/a | Medium | 9.5 | PASS |
| Q20 | ✅ | ✅ | ✅ | order→area×traffic | ✅ 2-way, verified row-count sum = 43,648 | ✅ | ✅ #7 | ✅ no invented threshold, row_count disclosed | n/a | High | 9.5 | PASS |
| Q21 | ✅ | ✅ | ✅ | order→vehicle | ✅ | n/a | ✅ #3 | ✅ bicycle absence documented, not fabricated | n/a | Medium | 9.5 | PASS |
| Q22 | ✅ disclosed interpretation | ✅ | ✅ | area (2 rows) | ✅ CROSS JOIN of two guaranteed-1-row CTEs | n/a | n/a (illustrative) | ⚠️ `CEIL(n/2)` not general for even n (not triggered, n=3) | ✅ explicitly labeled illustrative | Medium | 9.0 | PASS |

---

## Q01 Audit

**Business question (`SQL_ANALYSIS_PLAN.md`):** "% of deliveries breaching SLA overall and by area."

The query returns exactly this: an overall rate and an area-grouped rate,
both using `COUNT(*) FILTER (WHERE sla_breach_flag)` over `COUNT(*)` as
the denominator. **Denominator check:** the by-area query denominates each
area's breach rate against that area's *own* row count (not the overall
43,648) — this is business-correct: "breach rate in Urban" must mean
"breaches in Urban / deliveries in Urban," not "breaches in Urban / all
deliveries." **Grain:** one row in, one row counted; the `JOIN` to
`DimArea` is many-to-one (verified in Phase 2: 0 orphans, `area_key`
unique in `DimArea`), so no fan-out is possible. `area_tier_valid_flag`
is exposed rather than filtering `Other` out — this matches
`DATA_CLEANING_PLAN.md` Step 8's "retain, don't silently drop" rule.
**SLA logic:** reads `sla_breach_flag` as stored; no recalculation.

No defect found. Score 9.5/10 (not 10, reserved for queries with an
embedded self-check like Q07/Q08/Q12).

## Q02 Audit

**Business question:** "Worst P90 delivery time by area." Uses
`PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY delivery_time_minutes)` —
continuous interpolation, matching `KPI_DEFINITIONS.md` #4's documented
method exactly (the same method Python's `numpy.percentile` default and
DAX's `PERCENTILEX.INC` are required to match, per that KPI's own
cross-validation note). Grain and denominator identical pattern to Q01,
correct. No defect found.

## Q03 Audit

**Business question:** group-stats prep for the traffic ANOVA/Kruskal-Wallis
test. Correctly produces only `n`, `AVG`, `STDDEV`, and median — **no
p-value or F/H statistic is computed**, which is the correct scope
boundary per `STATISTICAL_ANALYSIS.md`'s explicit split between SQL prep
and the Python-side test. `GROUP BY wt.traffic` alone (not
`weather, traffic`) correctly re-aggregates across all weather values
within each traffic level, since the fact-to-dimension join is 1:1 per
row. No defect found.

## Q04 Audit

**Business question:** "Relationship between agent rating and delivery time."
`agent_rating_valid_flag = TRUE` correctly excludes both the 54 true-null
ratings and any out-of-range value — verified this is *not* a bare
`IS NOT NULL` filter, which the query's own comment explicitly flags as
the wrong approach. **Independently re-verified the rating-band bucketing**
(`FLOOR(agent_rating / 0.5) * 0.5`): ran a live diagnostic
(`min`/`max` per band) and confirmed **zero overlap** between adjacent
bands — e.g., band 4.5 contains ratings 4.5–4.9 exactly, band 5.0
contains only 5.0. This is a clean, deterministic, value-based bucketing
approach — notably *better* engineered than Q09's row-rank-based `NTILE`
for the same kind of "agent rating tier" concept (see Q09 below). `CORR()`
is correctly described in-file as descriptive only, not a hypothesis
test. No defect found.

## Q05 Audit

**Business question:** "Top weather/traffic condition for longest delivery
times." `RANK() OVER (ORDER BY AVG(...) DESC)` — independently queried
the 24 group averages directly and confirmed **no ties exist** at 2-decimal
precision, so `RANK()`'s tie-handling is not actually exercised here and
the ranking is fully deterministic. Grain is correctly the combined
`DimWeatherTraffic` row (not double-grouped). No defect found.

## Q06 Audit

**Business question:** "Categories with highest average delivery time."
Simple, correct `GROUP BY category_name`. Row counts (2,661–2,843 per
category) match the range documented in `DATA_PROFILING_PLAN.md`. No
defect found; correctly makes no claim about *why* Grocery's average is
so much lower (a scale difference already established in Phase 1, not
re-litigated here).

## Q07 Audit

**Business question:** group-stats prep for the weekend/weekday t-test.
Includes an **embedded reconciliation query** (`SELECT COUNT(*) ... total_deliveries`)
directly beneath the main result specifically so a reader can verify
`weekday_n + weekend_n = total_deliveries` without a second file — a
genuinely good defensive-SQL habit, not required by the plan but adding
real validation robustness. `is_weekend` is read from the fact table, not
recomputed. No defect found. **10/10.**

## Q08 Audit

**Business question:** "OTD% by area." This is the strongest single query
in the set from a validation-robustness standpoint: it computes
`otd_rate_pct`, `breach_rate_pct`, **and** their sum
(`otd_plus_breach_check`) in the same row, so a KPI-identity error
(`KPI_DEFINITIONS.md`'s "OTD% + Breach% = 100" requirement, restated
directly in `VALIDATION_CHECKLIST.md`) would be visible immediately in
the query's own output rather than requiring a separate check. No defect
found. **10/10.**

## Q09 Audit — CONFIRMED DEFECT

**Business question:** "Are specific agents outlier-prone, or is delay
evenly distributed?" The in-file comment correctly reframes this as
attribute-tier distribution (no true `Agent_ID` exists) — that part of
the audit passes cleanly, and Step 11's agent-analysis concern (no
individual-agent claim) is satisfied.

**The defect is in the mechanics of `NTILE(4) OVER (ORDER BY ag.agent_rating)`.**
I independently ran this exact window function against the live data and
inspected the actual rating value at each quartile boundary:

```
q | min_r | max_r | n
1 |   2.5 |   4.5 | 10899
2 |   4.5 |   4.7 | 10899
3 |   4.7 |   4.9 | 10898
4 |   4.9 |   5.0 | 10898
```

Rating value **4.5 appears in both quartile 1 (2,875 rows) and quartile 2
(428 rows)**; 4.7 appears in both quartile 2 (3,531) and quartile 3
(3,611); 4.9 appears in both quartile 3 (139) and quartile 4 (6,902).
**This is empirically confirmed, not theoretical:** `NTILE` splits rows
into equal-sized buckets by *row position* in the `ORDER BY` sequence,
and with this many tied `agent_rating` values (only ~26 distinct values
across 43,594 rows), Postgres has to cut *through* a tied value to keep
bucket sizes equal. Because no secondary, deterministic tiebreaker column
was added to the `ORDER BY` (e.g., `ORDER BY ag.agent_rating, ag.agent_key`),
**which specific rows land in quartile 1 vs. quartile 2 for a rating of
exactly 4.5 is not guaranteed stable across query re-executions** (a
different query plan, a parallel scan, or a table re-cluster could
change which 428-of-3,303 rows land on which side of the cut).

**Consequence:** the "quartile" labels are not the clean, reproducible
rating-value cutoffs a reader would reasonably assume from the `min`/`max`
columns shown. The overall directional pattern reported in Phase 4/5
(quartile 1 slower than quartiles 2–4) is very likely robust regardless
— quartile 1 is dominated by ratings 2.5–4.4, which are unambiguously
below the tie zone — but the *exact* row counts and the specific
4.5/4.7/4.9-rated agents' quartile assignment are not something this
query can defend precisely under questioning.

**Contrast with Q04:** Q04's `FLOOR(rating / 0.5) * 0.5` bucketing, which
I also independently verified, has **zero** overlap between bands. The
project already contains the better pattern one query away — Q09 should
have used the same value-based bucketing instead of a row-rank `NTILE`,
or at minimum added `agent_key` as a tiebreaker in the `ORDER BY`.

**Severity: HIGH** (confirmed logic defect, affects interpretability and
reproducibility) but **scoped narrowly**: P2 priority, not a headline
KPI, does not touch SLA logic, and the Phase 4 Python statistical work
that actually feeds the executive recommendations used the clean
`FLOOR`-based banding (`python/analysis/02_segment_comparisons.py`), not
`NTILE` — so this defect did not propagate into
`reports/business_findings.md` or `docs/EXECUTIVE_RECOMMENDATIONS.md`.

**Score: 6.0/10.**

## Q10 Audit

**Business question:** "Does distance correlate with delivery time, or is
it condition-driven?" `coordinates_valid_flag = TRUE` filter is correctly
applied to the `CORR()` query, and the row count (39,997) is reported
explicitly, matching the plan's validation method. **Mixed-population
design in the second query** (average distance filtered to
coordinate-valid rows, average delivery time unfiltered, in the same
`GROUP BY weather, traffic` row) was inspected closely — this is
*intentional and correct*: delivery time is valid for every row
regardless of coordinate validity, while distance is undefined for
invalid-coordinate rows, so each column correctly uses its own maximal
valid population. Not a bug. Minor readability note: a fast reader could
momentarily wonder why one `AVG` is `FILTER`ed and the other isn't; an
inline comment would remove any doubt. No score-affecting defect.

## Q11 Audit

**Business question:** "Trend in delivery time over the observed period."
Grain is correctly week-level via `DimDate.week_number`, joined 1:1 from
the fact table. `distinct_days_observed` is computed from `COUNT(DISTINCT full_date)`
— genuinely computed, not assumed — and correctly flags weeks 6, 7, 9, 12,
14 as partial (verified live: weeks 6 and 14 have exactly 3 distinct
days, matching the query's own logic).

**Concern:** `LAG(avg_delivery_time_minutes) OVER (ORDER BY week_number)`
silently bridges the missing week 8 — I independently confirmed week 7
ends 2022-02-18 and week 9 begins 2022-03-01, an 11-day gap. The
`avg_delta_vs_prior_week` value shown for week 9 is therefore a
comparison across ~2 calendar weeks' worth of gap, not a normal
week-over-week step, yet the column name doesn't distinguish this case
from a normal adjacent-week comparison. **Partial mitigation:** the query
does surface `week_first_observed_date`/`week_last_observed_date` and
`partial_week_flag` in the same row set, so a careful reader comparing
week 7's and week 9's date ranges directly *can* notice the gap — the
raw material to catch this is present, just not an explicit flag on the
delta column itself.

**Severity: MEDIUM.** Score: 9.0/10.

## Q12 Audit

**Business question:** "Weather condition with most SLA breaches." Like
Q07/Q08, includes an embedded reconciliation check (sum of per-weather
breach counts vs. the overall total). Correct grain, correct denominator
(this query reports raw breach *count*, not rate — matching the plan's
own "most SLA breaches" wording, which is about volume, not rate; a
separate rate column is not requested by the plan here and none is
needed to answer this specific question). No defect found. **10/10.**

## Q13 Audit

Same structure and same correct scope boundary as Q03, applied to
weather instead of traffic. No defect found.

## Q14 Audit — DETERMINISM CONCERN

**Business question:** "% of deliveries from top 20% highest-delay
areas/categories (Pareto)." The file's own header discloses that
"areas/categories" is implemented as two separate single-dimension cuts
rather than one pooled ranking — I independently checked
`SQL_ANALYSIS_PLAN.md`'s Expected Output column for Q14, which says
"ranked descending by breach count," confirming breach *count* (not
rate) is the correct ranking metric, and that the plan itself doesn't
specify a pooled cross-dimension ranking — the two-cuts interpretation is
reasonable and correctly disclosed, not a defect.

**The defect is in the running-total window.** I independently checked
for ties in `breach_count` and found one: **Snacks and Electronics both
have exactly 689 breaches.** `RANK() OVER (ORDER BY breach_count DESC)`
correctly assigns both rows rank 2 (verified) — that part is fine, and
critically, it means the `in_top_20_pct_segments` boolean (driven by
`breach_rank <= CEIL(0.2 * segment_count)`) is unaffected by the tie,
since both tied rows get the same rank regardless of physical row order.

However, `SUM(breach_count) OVER (ORDER BY breach_count DESC ROWS BETWEEN
UNBOUNDED PRECEDING AND CURRENT ROW)` **is** order-sensitive at the row
level, and Postgres does not guarantee a stable processing order for two
rows tied on the only `ORDER BY` key. This means the exact
`cumulative_breach_share_pct` value attached to the Snacks row vs. the
Electronics row individually is not guaranteed reproducible across
re-executions — though the running total *after* both tied rows have
been included is always correct, since addition is commutative.

**Consequence:** the final Pareto cutoff and the "top 20%" classification
are unaffected and trustworthy. What is not guaranteed stable is which of
the two tied rows shows the smaller vs. larger intermediate cumulative
percentage — a cosmetic-but-real reproducibility gap for exactly 2 of the
16 category rows.

**Severity: MEDIUM.** Score: 8.0/10.

## Q15 Audit

**Business question:** "Agent age vs. delivery time or rating." Both
correlations correctly filtered to rows passing *both*
`agent_age_valid_flag` and `agent_rating_valid_flag`, exactly as the
plan's validation method specifies (I checked this against the plan's
own text: "Both correlations reported only on rows passing both validity
flags"). No defect found.

## Q16 Audit

**Business question:** "Which area underperforms most on OTD%?" Correctly
reuses Q08's exact computation, restricted to `area_tier_valid_flag = TRUE`,
then `LIMIT 1`. **Latent concern:** if two areas ever tied exactly on
`otd_rate_pct`, `LIMIT 1` without an explicit tiebreaker (e.g.,
`area_name`) would return one of them non-deterministically. This is not
triggered by the current data (Semi-Urban's 0.0000% is uniquely the
lowest of 3 tier-valid areas, verified), so it is a **latent code-quality
note, not an active defect.**

## Q17 Audit — DETERMINISM/LABELING CONCERN

**Business question:** "Week-over-week volatility in delivery time." Same
underlying week-8 gap issue as Q11 (independently confirmed via the same
live date-range check), but **less mitigated here**: Q17's output has no
`week_first_observed_date`/`week_last_observed_date`/`partial_week_flag`
columns at all — only `week_number`, `n`, and the LAG-derived deltas. A
reader looking at Q17's output in isolation has no way to notice that the
week-9 row's "vs. prior week" percentage change actually spans an 11-day
gap, unless they cross-reference Q11's output. The file's header comment
does restate the general 8-week/gap limitation in prose, which is good,
but doesn't flag the specific week-9 transition as different from a
normal adjacent-week comparison.

**Severity: MEDIUM** (same underlying issue as Q11, less mitigated in
this specific file). Score: 8.5/10.

## Q18 Audit

Same base population as Q06 (verified identical row counts), reframed
with `STDDEV`/coefficient-of-variation — matches the plan's own "Same as
Q6" framing for both concept and validation method. No defect found.

## Q19 Audit

**Business question:** "Delivery-time delta: clear vs. adverse weather."
The plan explicitly requires the "adverse" grouping to be stated in the
query comment, not left ambiguous — verified this is done exactly
("Clear" = Sunny, "Adverse" = all other 5 weather values, matching the
plan's own suggested example). `GROUP BY weather_group` on a `CASE`-expression
alias is valid PostgreSQL and correctly implemented. No defect found.

## Q20 Audit

**Business question:** "Area + traffic combination with highest breach
concentration." Independently re-summed the `row_count` column across all
returned rows and confirmed it equals exactly 43,648 — no rows lost or
duplicated across the two-dimension join. The documented decision not to
invent a numeric minimum-sample-size threshold (none is frozen anywhere
in the documentation) and instead expose `row_count` as a visible column
is the correct, disciplined choice given the stated constraint. No defect
found.

## Q21 Audit

**Business question:** "Does vehicle type affect average delivery time?"
Correctly reflects the 3 vehicle types actually present in `DimVehicle`
(verified against Phase 2's schema validation — no 4th row exists, and
none was added here). The file's comment correctly states this is
stronger than "low-confidence" — bicycle cannot be assessed *at all*, not
just assessed with lower confidence — an accurate, not-overstated framing.
No fabrication found. No defect.

## Q22 Audit

**Business question:** "Estimated improvement if worst area matched
median area's delivery time." Explicitly labeled illustrative in its own
output row (`caveat` column), consistent with `ASSUMPTIONS.md` A8. The
"worst"/"median" ranking criterion (OTD%, reusing Q08/Q16's definition)
is disclosed in-file since the plan doesn't fully specify it — reasonable
and consistent with how "worst area" is defined everywhere else in this
project. `ROW_NUMBER()` (not `RANK()`) is the correct choice here since
exactly one row must be selected per CTE, and ties would break a
`RANK()`-based single-row selection; verified no tie exists at the
current 4-decimal-precision OTD% values.

**Latent concern:** `CEIL(area_count::numeric / 2)` correctly identifies
the middle element for the current odd count (n=3 tier-valid areas →
CEIL(1.5)=2, the true middle) but is **not a fully general median
formula** for an even-sized group (which would need an average of two
middle ranks, not a single row) — currently unreachable since exactly 3
areas pass `area_tier_valid_flag = TRUE` in the approved dataset, but
worth noting as a fragility if the area dimension ever changed.

**Severity: LOW** (not triggered by current data). Score: 9.0/10.
Q22 is correctly never presented as stronger evidence than it is — it is
descriptive arithmetic on top of already-validated figures, not
inferential, and every report that cites it (`business_findings.md`,
`executive_recommendations.md`) repeats the illustrative-only caveat.

---

## Critical SQL Defects

| Severity | Query | Defect | Business impact |
|---|---|---|---|
| **HIGH** | Q09 | `NTILE(4)` has no deterministic tiebreaker; confirmed empirically that agent_rating=4.5 splits 2,875/428 across quartiles 1/2 (similarly for 4.7, 4.9) | Quartile boundary labels are not reproducible or precisely meaningful; does **not** affect any headline KPI or the Phase 4/5 executive story (which used a different, correctly-implemented bucketing method in Python) |
| **MEDIUM** | Q14 | Running-total `SUM() OVER` has no tiebreaker for the confirmed tie (Snacks/Electronics, both 689 breaches); exact intermediate cumulative-% value for these 2 rows is not guaranteed stable across re-runs | Does not affect the Pareto ranking, the top-20% classification, or the final 100% cumulative total — cosmetic precision issue for 2 of 16 rows |
| **MEDIUM** | Q17 | Week-over-week delta for week 9 silently spans an 11-day gap (missing week 8) with no in-query flag; Q11 has the same underlying issue but is partially mitigated by visible date columns | Could be misread as a normal 1-week change if Q17's output is viewed without also checking Q11's date columns |
| LOW | Q16 | `LIMIT 1` has no explicit tiebreaker; not triggered by current data | None currently; latent only |
| LOW | Q22 | `CEIL(n/2)` median formula not general for even `n`; not triggered by current data (n=3) | None currently; latent only |

No CRITICAL-severity defect was found — nothing in this audit produces a
wrong headline KPI, a wrong SLA classification, an incorrect ranking that
changes a business conclusion, or a double-counted/lost row.

## High-Priority Improvements (recommended, not applied — this is an audit)

1. Add a deterministic tiebreaker to Q09's `NTILE` window
   (`ORDER BY ag.agent_rating, ag.agent_key`), or replace it with the
   same `FLOOR`-based value bucketing Q04 already uses correctly.
2. Add a tiebreaker to Q14's running-total window
   (`ORDER BY breach_count DESC, area_name` / `category_name`) so the
   per-row cumulative percentage is reproducible for tied segments.
3. Add an explicit `weeks_since_prior_observed` or similar column to Q17
   (or note it inline) so the week-9 gap-spanning comparison is visible
   without cross-referencing Q11.

These are precise, scoped fixes — none requires touching the schema, the
cleaned dataset, or any other query.

---

## Strengths

- **Embedded self-validation is a real, recurring pattern, not a one-off:**
  Q07 (row-count reconciliation), Q08 (`otd_plus_breach_check` = 100
  identity), and Q12 (breach-count reconciliation) each verify their own
  correctness inside the query output itself — a genuinely strong habit
  that goes beyond what the plan required.
- **Consistent, correct SLA discipline across all 22 files:** not one
  query recalculates a percentile, applies a buffer, or redefines the
  breach boundary — every SLA-touching query reads `sla_breach_flag`/
  `sla_threshold_minutes` as stored. Verified by direct inspection of
  every file, not assumed.
- **Denominator discipline:** every rate/percentage query denominates
  against the correct, business-appropriate population (own-segment
  totals for rates, total-breach-volume for Pareto shares) — no instance
  of a segment rate silently denominated against the whole dataset.
- **Honest, disclosed handling of ambiguity:** Q14 and Q19's grouping
  definitions, and Q22's ranking-criterion choice, are stated in-file
  rather than silently resolved — exactly the standard a senior reviewer
  would want to see when a plan's wording underspecifies something.
- **Correct scope discipline on statistical claims:** Q03/Q04/Q10/Q13/Q15
  correctly stop at descriptive statistics (`CORR`, group means) and
  explicitly note that hypothesis testing is out of scope for SQL — no
  query overstates what a `CORR()` or group-average result proves.
- **Flag-based exclusion, never hardcoded filters:** every validity
  exclusion (`agent_rating_valid_flag`, `coordinates_valid_flag`,
  `area_tier_valid_flag`) is applied via its boolean column, matching
  `STAR_SCHEMA.md`'s design principle — no query hardcodes a category
  name to approximate a flag.
- **Q04's rating-band bucketing is genuinely well-engineered** — verified
  zero band overlap — and stands as the correct pattern the project
  should have reused in Q09.

## Weaknesses

- **Q09's `NTILE` tie-handling is a real, confirmed correctness gap**,
  not a style nitpick — it changes what "quartile 1" precisely means at
  its boundary, and would not survive a sharp interview question about
  how ties are handled.
- **Determinism is under-considered in two window-function queries**
  (Q14's running total, and implicitly Q16/Q22's `LIMIT`/rank selection)
  — none of these are wrong in their current output, but none would
  survive a "prove this is reproducible" challenge without a tiebreaker.
- **The week-8 data gap is handled inconsistently across Q11 and Q17** —
  Q11 provides the evidence to notice it, Q17 does not, even though both
  queries share the exact same underlying LAG-over-a-gap mechanism.
- **No post-hoc pairwise SQL view exists for Q03/Q13's omnibus group
  comparisons** — this is a correctly-scoped absence (no method is
  documented in `STATISTICAL_ANALYSIS.md`), but it does mean the SQL
  layer alone cannot answer "which specific traffic pair differs most,"
  only that Python's effect-size result can.

## Business Relevance

Every one of the 22 queries maps to a real, named business question in
`SQL_ANALYSIS_PLAN.md` and produces output a Data Analyst could use for
operational monitoring, segmentation, root-cause investigation, or
prioritization — none exists merely to demonstrate a SQL technique. Q09
is the closest to a "technique-first" query given its defect, but it
still answers a real (if data-limited) business question about delay
distribution, correctly caveated for the `DimAgent` limitation.

## Interview Readiness

20 of 22 queries would hold up cleanly under a "why this denominator,"
"why this join," "what does this prove/not prove" interview
cross-examination — the header comments alone answer most of these
questions before they're asked. **Q09 would not fully hold up** under a
specific, sharp follow-up ("how does `NTILE` handle the many tied rating
values here?") — the honest answer, now that this audit has surfaced it,
is "it doesn't handle them deterministically, and that's a gap." Q14 and
Q17 would hold up under general questioning but would expose their
determinism/gap-labeling issues under the same level of scrutiny this
audit applied.

## Resume Impact

This is genuine, defensible Data Analyst SQL work, not a superficial
demo. The consistent presence of embedded validation, explicit denominator
reasoning, disclosed interpretation choices, and correct statistical
scope discipline (descriptive vs. inferential) are well above typical
fresher-level SQL portfolios, which more commonly show correct syntax
without this level of business/statistical discipline. The one confirmed
defect (Q09) does not erase this — disclosing and correctly bounding it
(as this audit does) is itself a demonstration of analytical maturity,
and is a better resume/interview story than a suspiciously flawless
22-for-22 audit would be.

---

## Hiring Committee Assessment

1. **Does this look like genuine Data Analyst SQL work?** Yes — the
   denominator reasoning, flag-based exclusion discipline, and
   descriptive/inferential scope boundaries are not things a copy-pasted
   or AI-generated-without-review portfolio typically gets this
   consistently right.
2. **Is the SQL depth above typical fresher level?** Yes. Window
   functions (`RANK`, `NTILE`, `LAG`, running `SUM() OVER`), correct
   `PERCENTILE_CONT` usage matched across a documented cross-tool
   consistency requirement, and CTé-staged aggregation-then-ranking
   patterns are not typical fresher fare.
3. **Would a senior Data Analyst trust the calculations?** Yes, for 21 of
   22 — with the explicit, disclosed exception of Q09's quartile
   boundaries, which a senior reviewer would ask to see fixed before
   fully trusting.
4. **Would this survive a technical interview?** Yes, for the large
   majority of the query set — and the candidate who can also explain
   *why* Q09's `NTILE` has a tie-handling gap (rather than being caught
   off guard by the question) would come across stronger, not weaker.
5. **Does it demonstrate business thinking?** Yes — Q16 reusing Q08's
   exact logic rather than recalculating, Q22's explicit illustrative
   labeling, and the consistent "expose the flag, don't hardcode the
   filter" pattern are business-thinking signals, not just SQL syntax
   signals.
6. **Is anything likely to raise a red flag?** Only if presented as
   "22/22 flawless" without disclosure — presented honestly (as this
   audit does), Q09 reads as a normal, bounded imperfection in a large
   body of work, not a red flag.
7. **Would you mention the SQL work prominently on the resume?** Yes.
8. **Would Amazon/Flipkart/Swiggy/Zomato/Walmart-style analytics teams
   consider this relevant?** Yes — the domain (last-mile delivery SLA
   analytics), the grain/denominator discipline, and the Pareto/root-cause
   framing are directly relevant to how those teams' analytics functions
   actually operate.

---

## Final Recommendation

Fix the three MEDIUM/HIGH items (Q09, Q14, Q17) before this SQL layer is
used as the direct source for a live Power BI/DAX build, since a
dashboard would surface Q09's quartile figures and Q14's Pareto chart
directly to stakeholders without the caveats this audit report carries
alongside them. The two LOW latent items (Q16, Q22) do not need to block
anything — they are not wrong today.

---

## Final Decision

# SQL APPROVED WITH MINOR FIXES

Per the stated decision criteria: no critical logical defect exists, KPI
definitions are implemented correctly everywhere checked, denominators
are correct everywhere checked, SLA logic is correct and unchanged
everywhere checked, grain is correct everywhere checked, and no serious
double-counting exists anywhere in the 22 files (independently verified,
not just re-trusted from Phase 3). The confirmed Q09 defect and the Q14/Q17
determinism concerns are real but scoped, non-critical issues that should
be fixed — not because they currently produce a wrong business
conclusion, but because a dashboard build would expose them directly to
an audience without this audit's caveats attached.

**No SQL was modified during this audit. Awaiting explicit approval
before any fix is applied or before proceeding to DAX/Power BI.**

---
---

# REMEDIATION — 2026-08-16

*Everything above this line is the original audit, preserved verbatim.
This section documents the authorized remediation performed after
explicit approval of the three findings above (Q09 HIGH, Q14 MEDIUM,
Q17 MEDIUM). Full validation detail: `reports/sql_remediation_validation.md`.
Final post-remediation score and gate: `reports/sql_final_review.md`.*

## Q09 — Defect (as originally found)

`NTILE(4) OVER (ORDER BY ag.agent_rating)` applied directly to
`FactDelivery` rows. With only ~26 distinct `agent_rating` values across
43,594 rows, `NTILE` cut through tied values to force equal-row-count
buckets — empirically confirmed: rating 4.5 split 2,875/428 across
quartiles 1/2 (similarly 4.7 and 4.9).

## Q09 — Fix

`NTILE(4)` is now applied to the ~26 **distinct** `agent_rating` values
(one row per unique value — no ties possible at that grain), and every
fact row inherits its rating's single assigned tier via a join. Output
column renamed `rating_quartile` → `rating_tier` to avoid implying
equal-population quartiles, since tier row counts are now intentionally
uneven (137 / 995 / 6,892 / 35,570) — a documented trade-off, not a bug.

**Verification:** `SELECT agent_rating, COUNT(DISTINCT rating_tier) ... HAVING COUNT(DISTINCT rating_tier) > 1` returns **0 rows** — no rating value is split across tiers, confirmed directly against the live database.

## Q14 — Defect (as originally found)

Confirmed tie: Snacks and Electronics both at 689 breaches (category
cut). `RANK()` correctly gave both rows rank 2. The running-total
`SUM() OVER (ORDER BY breach_count DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)`
had no secondary sort key, so which of the two tied rows was processed
first — and therefore which showed the smaller vs. larger intermediate
cumulative percentage — was not guaranteed stable across re-runs.

## Q14 — Fix

Added `category_name ASC` (and `area_name ASC` in the area cut, for
consistency, though no tie exists there) as a secondary key **to the
running-total window only**. The `RANK()` window was left untouched, so
tie behavior (both rows sharing rank 2) is unchanged.

**Verification:** Re-ran the query; Electronics (alphabetically first)
now consistently shows `cumulative_breach_share_pct = 13.3811%` and
Snacks consistently shows `20.0523%` — the same two values that existed
before, now deterministically assigned. `breach_count` (689/689), `breach_rank`
(2/2), and the final 100.0000% cumulative total are all unchanged.

## Q17 — Defect (as originally found)

`LAG(avg_delivery_time_minutes) OVER (ORDER BY week_number)` silently
bridged the missing week 8 (zero rows, no orders 2022-02-19 to
2022-02-28) — week 9's "prior week" comparison was actually against week
7, an 11-day-earlier value, with no indication in the query output that
the comparison spanned more than one week.

## Q17 — Fix

No documentation (`FEATURE_ENGINEERING.md` #7, `KPI_DEFINITIONS.md` #8,
`DATASET_OVERVIEW.md`, `ASSUMPTIONS.md`) establishes whether the week-8
gap represents zero business activity or an unavailable reporting
period — this was disclosed, not silently resolved. Both interpretations
require the same SQL treatment regardless (a delivery-time metric cannot
be computed for zero rows under either reading), so `LAG()` was retained
(not replaced) and a `weeks_since_prior_observed_week` column was added.
Every "vs. prior week" column is now `CASE`-guarded to `NULL` whenever
that gap is not exactly 1, with `is_consecutive_week_comparison` exposed
as a visible boolean.

**Verification:** Week 9 now shows `weeks_since_prior_observed_week = 2`,
`is_consecutive_week_comparison = false`, and `NULL` for every delta
column. Weeks 7 and 10–14 (all genuinely adjacent, gap=1) show identical
delta values to the pre-fix output — only week 9's previously-misleading
figure changed.

## Full Regression Results

19 of 22 queries: byte-for-byte identical pre- vs. post-fix output. 3 of
22 (Q09, Q14, Q17) changed exactly as intended, only in the rows/columns
the defect actually affected. Full table: `reports/sql_remediation_validation.md`.

## Business Findings Regression

All 6 spot-checked approved figures (traffic ε²=0.1404, weather
ε²=0.0517, weekend p=0.9658, Metropolitian 83.7335%, Semi-Urban
100.0000%/n=152, overall breach rate 23.6620%) reconcile exactly,
unchanged. No STOP condition was triggered.

## Post-Remediation Status

See `reports/sql_final_review.md` for the final score and gate. The
**original** "SQL APPROVED WITH MINOR FIXES" verdict above reflects the
state of the SQL layer *before* this remediation and is retained as the
historical record of what the audit found and why remediation was
authorized — it is not the current status of the codebase.
