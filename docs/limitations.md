# Limitations

Being direct about these is more credible than pretending they don't exist.

## Is this real data?

**Treat this as a realistic synthetic-style delivery operations dataset, not verified real company
data.** Provenance cannot be confirmed from the repository — it is a public Kaggle dataset with no stated
generation method. `notebooks/01_data_quality.ipynb` §3 quantifies several patterns that are hard to
explain as organic operations:

| Check | Observed | Evidence of rule-based construction |
|---|---|---|
| Delivery times that are multiples of 5 minutes | 95.0% (89 distinct values, present in the raw file too) | Strong |
| Preparation time values | Only 5, 10 or 15 minutes, in almost exactly equal thirds (33.5% / 33.2% / 33.3%) | Strong |
| Traffic level determined by order hour | 97.5% of deliveries match their hour's most common traffic level; Jam appears only in hours 19–22 | Strong |
| Breach rate step at agent rating 4.5 | 63.2% (rating 4.4) → 10.5% (rating 4.5), a 52.7-point drop | Strong |
| Breach rate step at agent age 30 | 14.1% (< 30) → 33.1% (≥ 30), a 17.5-point jump at one exact round number | Strong |
| Weather effects collapse into three tiers | Sandstorms/Stormy/Windy differ from each other by only 0.4 minutes | Strong |
| A handful of additive rules explain most of delivery time | A simple additive model (traffic + weather + area + vehicle + rating band + age band + category) reaches R² = 0.62 | Moderate |
| Semi-Urban area | 152 deliveries, exactly 100% breach | Strong |
| Raw file defects | 53 ratings of exactly 6.0 (scale is 1–5), 3,505 zero-valued coordinates, ~96% of categorical values padded with whitespace | Weak on its own — but neat, countable defects fit a file prepared for cleaning practice |

None of this proves how the data was made. It is disclosed so every finding is read at the right
confidence level: **these are patterns in this dataset, not verified facts about any real delivery
operation.**

## Agent attributes, not agent identities

The source data has **no agent identifier**. `DimAgent` (and `agent_rating` / `agent_age` in the
analytical dataset) are attributes of the delivery record — a distinct age/rating combination, not a
trackable individual. Every rating- or age-based finding in this project describes an attribute
association, never an individual agent's performance, and none should be used to identify, rank or
evaluate a specific person.

**Rating may be an outcome, not a cause.** A late, poorly executed delivery could itself produce a lower
rating (reverse causation), or rating could simply travel with which routes or shifts get assigned. This
dataset cannot distinguish those explanations from "lower-rated deliveries perform worse," and no finding
in this project claims otherwise.

**Age is a protected characteristic** in most employment contexts. The age-30 step found here
(`docs/analytical_findings.md` §3) is reported because it is present in the data and adds to the
realism discussion above — it is not, and should never be treated as, a basis for a staffing decision.

## Traffic and time of day cannot be separated

97.5% of deliveries occur in an hour matching that hour's single most common traffic level; Jam traffic
appears only in hours 19–22. Any statement of the form "traffic matters more than time of day" (or vice
versa) overstates what this dataset can show — see `docs/analytical_findings.md` §5 for the contrasts
that hold one factor fixed where the data allows it.

## Vehicle

`bicycle` is documented in the raw file's category list but has **0 rows** after cleaning — every raw
`bicycle` row fell inside the Step 3 exclusion cluster. It is absent, not merely low-confidence, and no
comparison in this project includes it.

## SLA benchmark, not a business target

`sla_threshold_minutes` is an **analyst-defined benchmark** (each category's own P75), not a
company-published SLA. No external delivery-time promise exists in the source data. About a quarter of
deliveries breach at P75 by construction — see `docs/methodology.md` and
`docs/analytical_findings.md` §9 for how findings change at P70/P80/P90.

## Small samples

- **Semi-Urban: n = 152** (0.35% of the dataset), 100% breach rate. Real and reproducible, but far too
  small a sample to generalise from confidently.
- The rating scan drops any rating value with fewer than 100 deliveries before looking for the step
  (`outputs/tables/rating_by_value.csv` flags these) — the erratic-looking rates below rating 3.5 rest on
  as few as 6–32 deliveries each and should not be read as precise.

## Statistical scope

- No causal claim appears anywhere in this project. Every result is worded as an observed association.
- No interaction test was run between weather and traffic beyond the descriptive heatmap
  (`outputs/figures/traffic_weather_heatmap.png`) — the interaction is shown, not formally tested.
- No pairwise post-hoc comparison was performed for any multi-group test; none is documented in the
  original test plan (`docs/archive/planning/STATISTICAL_ANALYSIS.md`), and inventing one was avoided.
- Rating and age cut points (4.5, 30) were **found from the data** (the largest adjacent-value jump), not
  assumed in advance — their exact location should be read as descriptive, not as a pre-registered
  hypothesis test.

## Financial impact

No cost, revenue or capacity field exists anywhere in the source data. Every illustrative scenario in
`docs/analytical_findings.md` §10 states its assumption and limitation explicitly and is labelled
**"illustrative scenario — not a causal forecast."** No financial figure is estimated or implied anywhere
in this project.

## Reconciliation, not proof

The cross-layer KPI reconciliation (`docs/methodology.md`) shows that independently written code paths —
plain Python, the pandas pipeline, PostgreSQL, and the v1 Power BI report — reach the same numbers from
the same file. **This rules out an implementation bug in any one layer. It is not proof that the source
data is correct**, which is exactly why the data-realism section above exists as a separate concern.

## Known, disclosed discrepancy

The v1 Power BI report's Pareto chart shows a cumulative-share label of 97% at rank 7, where the
reconciled value is 96.0%. Two segments tie at 131 breaches each; the v1 DAX measure used `DENSE RANK`,
which counts tied ranks together and produces a duplicated cumulative label. The current Python/SQL
Pareto (`docs/methodology.md`) breaks ties deterministically by segment name, so this does not recur.
Documented here rather than silently corrected.

## Resolved: the dashboard's Agent Performance page previously understated the rating/age finding

An earlier build of `powerbi/RouteIQ_v1.pbix`'s "Agent Performance" page reported agent rating and age
via a linear correlation (Spearman R ≈ -0.26, Pearson R ≈ 0.26, R² ≈ 0.07) and labelled the relationship
"weak" — a framing superseded by this project's own analysis: rating and age are each a **step**, not a
weak linear trend — 63.2% breach at rating 4.4 vs. 10.5% at 4.5 (survives controlling for traffic/area,
Mantel–Haenszel risk ratio 3.69), and 14.2% at age 29 vs. 31.7% at age 30
(`docs/analytical_findings.md` §2–3, `docs/recommendations.md` #1). A linear correlation coefficient is
the wrong tool for a step relationship and understates it by construction — R² ≈ 0.07 measures how much
of the variance a straight line explains, not whether a real effect exists.

**Fixed and verified**: the page's callouts now state the step finding directly, confirmed by diffing
the `.pbix` internals before and after the edit (not just a visual check). Recorded here as project
history rather than deleted outright, since it's a useful example of the kind of self-caught correction
this project's methodology is meant to guard against.
