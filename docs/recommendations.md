# Recommendations

Every row follows the same structure: **Finding → Evidence → Recommended action → KPI to monitor →
Limitation.** None claims causation. None estimates a financial figure — no cost, revenue or capacity
field exists in the source data (`docs/limitations.md`). This is the corrected set: recommendation 5
below reverses the earlier (incorrect) v1 conclusion that agent rating was "weak" and should be
deprioritised.

---

### 1. Investigate deliveries with agent rating below 4.5, and confirm what the rating attribute reflects before acting on it

- **Finding:** Deliveries with a rating below 4.5 are 18.4% of rated deliveries but carry 50.2% of all
  breaches (breach rate 64.6% vs. 14.4%). The gap is a genuine step (a 52.7-point jump between rating 4.4
  and 4.5), not a gradual slope, and it survives controlling for traffic and area (Mantel–Haenszel risk
  ratio 3.69, 95% CI 3.59–3.79).
- **Evidence:** `docs/analytical_findings.md` §2; `sql/analysis/Q25_rating_threshold_analysis.sql`;
  `outputs/tables/rating_effect_by_traffic.csv`.
- **Recommended action:** before treating this as an agent-coaching opportunity, confirm what the rating
  field actually represents and when it is recorded relative to the delivery. If ratings are assigned
  after the delivery completes, the pattern may describe an outcome of poor delivery performance rather
  than a cause of it.
- **KPI to monitor:** breach rate by rating band, tracked alongside whichever explanation is confirmed.
- **Limitation:** rating may be an outcome of delivery performance (reverse causation) or a marker of
  route/shift assignment, not a lever. No individual agent identifier exists, so this is an
  attribute-level pattern, never an individual-agent finding.

---

### 2. Prioritise the evening peak (17:00–23:59), especially 19:00–21:00, for operational review

- **Finding:** The evening peak is 72.2% of deliveries but 88.8% of breaches (29.1% breach rate vs. 9.5%
  off-peak). Hours 19–21 alone are 31.5% of deliveries and 56.1% of breaches.
- **Evidence:** `docs/analytical_findings.md` §5; `sql/analysis/Q23_time_of_day_breach_analysis.sql`.
- **Recommended action:** review dispatch capacity and staffing specifically for the 17:00–23:59 window,
  and 19:00–21:00 in particular, before any other time-based change.
- **KPI to monitor:** breach rate and breach volume by hour band.
- **Limitation:** traffic level and hour overlap almost completely in this dataset (97.5% of deliveries
  match their hour's dominant traffic level); this recommendation cannot be cleanly separated from
  recommendation 3 below.

---

### 3. Treat Jam-traffic conditions, especially combined with Cloudy/Fog weather, as the highest-priority condition

- **Finding:** Jam traffic shows the highest risk ratio of any traffic level, and the effect is
  substantially larger when combined with Cloudy/Fog weather than with clear weather (traffic and
  weather interact — `outputs/figures/traffic_weather_heatmap.png`). Metropolitian/Jam alone is 47.2% of
  all breaches; the top four area×traffic combinations are 83.9%.
- **Evidence:** `docs/analytical_findings.md` §4–5, §7; `sql/analysis/Q28_driver_segmentation.sql`.
- **Recommended action:** investigate dispatch and routing during Jam-traffic periods, prioritising
  Metropolitian, and specifically the overlap with adverse weather.
- **KPI to monitor:** breach rate and breach volume by area × traffic; the Pareto cumulative share.
- **Limitation:** concentration describes where breach *volume* sits, not why. No interaction-effect
  test was run beyond the descriptive heatmap; this is not a causal claim.

---

### 4. Do not treat Metropolitian's high breach volume as evidence of an unusually bad rate

- **Finding:** Metropolitian holds 74.8% of delivery volume and 83.7% of breach volume — a lift of only
  1.12. Its breach rate (26.5%) is close to the dataset average and well below Semi-Urban's.
- **Evidence:** `docs/analytical_findings.md` §4.
- **Recommended action:** frame any Metropolitian-focused work as "the largest volume of breaches to
  address," not "the worst-performing area" — the second claim is not supported by the rate.
- **KPI to monitor:** breach rate by area (not just breach count) alongside delivery volume, so rate and
  volume are never read as the same thing.
- **Limitation:** none beyond the general observational scope of this dataset.

---

### 5. Investigate Semi-Urban's 100% breach rate as a small, bounded review — not a resourcing priority

- **Finding:** Every one of Semi-Urban's 152 deliveries breaches its threshold. This is 0.35% of the
  dataset.
- **Evidence:** `docs/analytical_findings.md` §4; `sql/analysis/Q29_cross_validation_reconciliation.sql`
  check 12.
- **Recommended action:** a bounded, low-cost review of Semi-Urban's operations, not a resourcing
  commitment based on this figure alone.
- **KPI to monitor:** Semi-Urban breach rate and n, tracked together (never the rate alone).
- **Limitation:** n = 152 is too small to generalise from confidently, and (`docs/limitations.md`)
  Semi-Urban's exact 100% figure is itself one of the patterns flagged as possibly rule-generated.

---

### 6. Do not prioritise preparation-time changes as a delay-reduction lever

- **Finding:** Preparation time (5, 10 or 15 minutes) shows no association with breach or delivery time
  in this dataset (Cramér's V = 0.006, Cohen's d ≈ −0.02).
- **Evidence:** `docs/analytical_findings.md` §6; `sql/analysis/Q24_prep_time_impact.sql`.
- **Recommended action:** direct improvement effort toward recommendations 1–3 instead; revisit
  preparation time only if new data (a wider range of prep times, or a different population) becomes
  available.
- **KPI to monitor:** none needed while the null result holds; re-check if the underlying process
  changes.
- **Limitation:** this is a confidently-supported null result (clean, not borderline), not an absence of
  testing.

---

### 7. Do not treat the weekend/weekday difference as a staffing lever

- **Finding:** Breach rate is practically identical on weekends and weekdays (23.6% vs. 23.6%).
- **Evidence:** `docs/analytical_findings.md` §8.
- **Recommended action:** do not adjust weekend-specific staffing based on this dataset.
- **KPI to monitor:** none needed while the null result holds.
- **Limitation:** based on an approximately 8-week observation window.

---

## What every recommendation above depends on

Before any of these move from "investigate" to "act", the analysis needs, at minimum: a real
customer-facing SLA or delivery-time promise (to replace the analyst-defined P75 benchmark), an agent
identifier with rating timestamps (to test whether rating is a cause or an outcome), and cost/capacity
data (to size any recommended change). None of these exist in the current dataset —
`docs/limitations.md`.
