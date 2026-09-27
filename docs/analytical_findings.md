# Analytical Findings

Every figure below is reproduced in `notebooks/02_eda.ipynb`, `03_operational_analysis.ipynb` and
`04_kpi_validation.ipynb`, and independently in `sql/analysis/Q23`–`Q29`. All results are **observed
associations in this dataset** — never causal claims. See `docs/limitations.md` for what cannot be
concluded.

## 1. Overall delivery performance

| Metric | Value |
|---|---|
| Total deliveries | 43,648 |
| Breached deliveries | 10,328 |
| Breach rate | 23.66% |
| On-time rate | 76.34% |
| Average delivery time | 124.91 min |
| Median delivery time | 125.0 min |
| P75 delivery time (the SLA benchmark itself) | 160.0 min |
| P90 delivery time | 195.0 min |
| Average lateness when breached | 34.23 min over the threshold |

**The 76.34% on-time figure is not an independent performance score.** The SLA threshold is each
category's own P75, so close to a quarter of deliveries breach by construction (`docs/methodology.md`,
§ SLA definition). §6 below shows how every other finding holds up if the threshold is changed.

## 2. Agent rating: a step, not a slope

A linear correlation between rating and delivery time looks weak. Breach rate by the **exact** rating
value shows a sharp step instead:

| | Rating 4.4 | Rating 4.5 |
|---|---|---|
| Breach rate | 63.2% (n = 1,361) | 10.5% (n = 3,303) |

This is a **52.7-point** jump — roughly 30× the size of a typical adjacent-value jump elsewhere in the
range (≈1.7 points). Splitting at 4.5: ratings below 4.5 are **18.4%** of rated deliveries but carry
**50.2%** of all breaches (breach rate 64.6% vs. 14.4%, risk ratio 4.5).

**Does it survive controlling for traffic, area and weather?** Yes, though the gap narrows:

| Stratification | Crude risk ratio | Stratified (Mantel–Haenszel) risk ratio | 95% CI |
|---|---|---|---|
| Traffic × Area (12 combinations) | 4.53 | **3.69** | 3.59–3.79 |
| Traffic × Weather (24 combinations) | 4.53 | **3.62** | 3.53–3.72 |

The association is large and points the same way inside every traffic level tested
(`outputs/tables/rating_effect_by_traffic.csv`).

**Limitation:** rating may itself be an **outcome** of delivery performance (a late delivery may simply
earn a lower rating), or a marker of which routes/shifts get assigned. This data cannot distinguish those
explanations from "lower-rated deliveries perform worse." Attribute-level only — no individual agent
identifier exists.

## 3. Agent age: the same step pattern

| | Age 29 | Age 30 |
|---|---|---|
| Breach rate | 14.2% (n = 2,191) | 31.7% (n = 2,226) |

A **17.5-point** jump at exactly age 30, versus a typical 0.6-point step elsewhere. A change at one exact
round number is unusual for a real workforce (`docs/limitations.md`). **Fairness note:** age is a
protected characteristic in most employment contexts; even a genuine pattern here should never be used
as a basis for staffing or performance decisions.

## 4. Where breaches concentrate (volume vs. rate)

| Area | Share of deliveries | Share of breaches | Breach rate |
|---|---|---|---|
| Metropolitian | 74.8% | **83.7%** | 26.5% |
| Urban | 22.3% | 13.5% | 14.4% |
| Semi-Urban | 0.3% | 1.5% | **100.0%** (n = 152) |
| Other | 2.6% | 1.3% | 11.4% |

**Metropolitian's large breach share is mostly volume, not an unusually high rate** (lift 1.12: its
breach share is only slightly above its delivery share). **Semi-Urban's 100% rate rests on only 152
deliveries** — a striking figure that should not be treated as a stable, generalisable rate.

The area × traffic Pareto (`outputs/tables/pareto_area_traffic.csv`, ranking made deterministic — ties
broken by segment name, so no cumulative-percentage label repeats):

| Rank | Segment | Breaches | Cumulative share |
|---|---|---|---|
| 1 | Metropolitian / Jam | 4,877 | 47.2% |
| 2 | Metropolitian / Medium | 2,205 | 68.6% |
| 3 | Metropolitian / High | 799 | 76.3% |
| 4 | Urban / Jam | 782 | **83.9%** |

The top four area×traffic combinations hold 83.9% of all breaches.

## 5. When breaches happen

The 17:00–23:59 evening peak is **72.2%** of deliveries but **88.8%** of breaches (breach rate 29.1% vs.
9.5% off-peak). Hours 19–21 alone are 31.5% of deliveries and **56.1%** of breaches.

**Traffic and time of day overlap almost completely:** 97.5% of deliveries occur in an hour where that
hour's most common traffic level applies; Jam traffic appears only in hours 19–22. Only 4 of 17 observed
hours contain more than one traffic level. Within those few hours, traffic still separates breach rates
(e.g. at 22:00, Jam breaches 42.5% vs. Low's 9.1%); within one traffic level, the evening still carries
more risk than the morning. **Traffic and time of day should be read together, not ranked against each
other** — this dataset cannot cleanly separate them.

**Traffic and weather interact:** Jam traffic combined with Cloudy/Fog weather breaches far more often
than Jam combined with Sunny weather (`outputs/figures/traffic_weather_heatmap.png`).

## 6. Preparation time: no association

| Effect size | Value |
|---|---|
| Cramér's V (breach vs. prep time) | 0.006 (negligible) |
| Epsilon-squared (delivery time vs. prep time) | 0.00003 (negligible) |
| Cohen's d (15 vs. 5 minutes prep) | −0.023 (negligible), 95% CI −0.046 to 0.000 |

Preparation time takes only three values (5, 10, 15 minutes, in almost exactly equal thirds) and shows
no relationship with breach or delivery time in this dataset. **A null result is itself a decision-useful
finding:** preparation time is not a lever worth investigating here.

## 7. One comparable scale for every factor

Comparing an epsilon-squared with an r² (as an earlier version of this project did) is not meaningful —
they are different statistics on different scales. `outputs/figures/risk_ratios_by_factor.png` puts every
factor on one scale: breach rate in the exposed group ÷ breach rate in a reference group, each with a 95%
CI (`outputs/tables/sla_sensitivity_driver_risk_ratios.csv`, P75 column).

Ranked by risk ratio (largest first): **rating < 4.5**, **Jam traffic**, **evening peak hours**,
**Cloudy/Fog weather**, **age ≥ 30**, **motorcycle**, then **preparation time** (risk ratio ≈ 1, no
effect). Because traffic, time of day and weather overlap and interact (§5), this ranking should not be
read as "the single most important factor" — it is one honest, consistent way to compare magnitudes, not
a causal ranking.

## 8. Weekend vs. weekday: a clean null result

Breach rate: 23.6% (weekday) vs. 23.6% (weekend) — practically identical (Cramér's V = 0.001, Cohen's d
on delivery time ≈ 0). This is a genuine null finding over the ~8-week observed window, not a failure to
find an effect.

## 9. SLA sensitivity (P70 / P75 / P80 / P90)

| Percentile | Breach rate |
|---|---|
| P70 | 28.8% |
| P75 (used throughout this project) | 23.7% |
| P80 | 19.0% |
| P90 | 9.2% |

**What is stable across every threshold:** the riskiest level of every factor tested never changes (Jam
traffic, Fog weather, the evening peak, age ≥ 30, rating < 4.5, motorcycle remain the highest-breach group
at P70, P75, P80 and P90 alike). **What is not stable:** the exact size of any single risk ratio — the
rating and Jam-traffic risk ratios shrink or grow several-fold depending on the threshold used
(`outputs/tables/sla_sensitivity_driver_risk_ratios.csv`, `04_kpi_validation.ipynb` §3). **Any quoted
risk ratio should be read together with the SLA percentile it was computed at.**

## 10. Illustrative scenarios (not causal forecasts)

> No cost, revenue or capacity data exists in this dataset, so **no financial impact is estimated**
> anywhere in this project.

| Scenario | Assumption | Theoretical reduction |
|---|---|---|
| Jam-traffic breach rate matches Medium-traffic rate | Every Jam delivery breaches at today's Medium rate, same volume/mix otherwise | ~24% of all breaches |
| Rating < 4.5 breach rate matches rating ≥ 4.5 rate | Every low-rating delivery breaches at today's higher-rating rate | ~39% of all breaches |
| Jam + Cloudy/Fog matches Jam + other adverse weather | The highest-risk combination behaves like the next-highest | ~14% of all breaches |

Each is explicitly **illustrative — not a causal forecast** (`outputs/tables/scenarios.csv` for the exact
figures and stated limitations).
