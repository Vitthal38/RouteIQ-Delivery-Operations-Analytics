# Methodology

## Scope

RouteIQ is a **Data Analyst / Business Intelligence** project: data cleaning, SQL, descriptive and
diagnostic analysis, and a Power BI report. It deliberately excludes machine learning, predictive
modelling and causal inference. Every conclusion in this project is an **observed pattern in this
dataset**, reported with an effect size and its limitation — never a cause, and never a prediction.

## Pipeline

```
Raw data (amazon_delivery.csv, 43,739 rows)
    -> Python cleaning + feature engineering  (src/routeiq/cleaning/)
    -> Cleaned dataset (data/processed/cleaned_delivery.csv, 43,648 rows)
    -> PostgreSQL star schema                 (sql/schema/)
    -> Controlled analytical view              (sql/schema/09_create_analytical_view.sql,
                                                 src/routeiq/features/analytical.py)
    -> SQL analysis (Q01-Q29)                 (sql/analysis/)
    -> Python descriptive/diagnostic analysis (src/routeiq/analysis/, notebooks/)
    -> Cross-layer KPI reconciliation          (src/routeiq/validation/)
    -> Power BI report                         (powerbi/)
```

The **analytical dataset/view** is the single controlled input every layer reads: it derives
`breach_flag`, `hour_band`, `is_peak_hour`, `rating_lt_4_5` and `age_ge_30` exactly once, in Python
(`src/routeiq/features/analytical.py`) and in SQL (`sql/schema/09_create_analytical_view.sql`), so no
script can silently analyse a different population. `tests/test_reconciliation.py` checks the two
definitions agree.

## SLA definition

- **`sla_threshold_minutes`** — the 75th percentile (P75) of `delivery_time_minutes`, computed once per
  product category on the full cleaned dataset. This is an **analyst-defined benchmark**, not a
  company-published SLA — no such target exists in the source data.
- **`breach_flag`** — `1` if `delivery_time_minutes > sla_threshold_minutes` (strict greater-than;
  equal to the threshold counts as on time), else `0`. Never recomputed differently anywhere in this
  project.
- Because the threshold is each category's own P75, roughly a quarter of deliveries breach **by
  construction**. See `docs/analytical_findings.md` §6 and `notebooks/04_kpi_validation.ipynb` for the
  P70/P75/P80/P90 sensitivity analysis this implies.

## Why a PostgreSQL star schema

The project uses one fact table (`FactDelivery`) and six dimensions
(`sql/schema/`, `docs/archive/planning/STAR_SCHEMA.md`). To be direct about this: a single flat table
would work equally well analytically for this dataset's size and shape. The star schema is included to
demonstrate dimensional modelling, key/constraint discipline and BI-model design — a skill this project
is meant to show, not a requirement the data itself created. Every dimension's primary key, every
`FactDelivery` foreign key, and every relationship's cardinality and cross-filter direction were
validated (0 orphan rows, 0 duplicate dimension keys — `sql/analysis/Q29_cross_validation_reconciliation.sql`,
check IDs 1–3).

## Descriptive and diagnostic methods used

| Question | Method | Why this, not something else |
|---|---|---|
| Is factor X related to breach? | Breach rate by segment, with a 95% Wilson confidence interval | Simplest, most defensible way to compare a rate across groups |
| Is the relationship a slope or a step? | Breach rate by **exact** value; the largest jump between adjacent values (`largest_single_step`) | A linear correlation understates a genuine step; this locates the step directly instead of assuming a shape |
| Does the pattern survive other factors? | Stratified rate comparison and Mantel–Haenszel common risk/odds ratio, controlling for traffic × area or traffic × weather | Compares like-for-like within each combination, without fitting a model |
| How large is the difference, on one scale? | Risk ratio (`notebooks/03_operational_analysis.ipynb` §5) | Lets rating, traffic, weather, age, vehicle and prep time be compared on one consistent scale, instead of comparing incomparable statistics (e.g. Kruskal–Wallis epsilon-squared vs. Pearson r²) |
| Is a categorical association large? | Cramér's V (chi-square based) | Standard, size-independent effect size for two categorical variables |
| Is a continuous difference large? | Cohen's d, mean/median difference, probability of superiority | Standard effect sizes for a two-group numeric comparison; reported instead of relying on a p-value |
| Which condition dominates breach volume? | Pareto ranking, deterministic tie-break (breach count, then segment name) | Answers "where should effort go" (volume), which is a different question from "which rate is highest" |

**On p-values:** at roughly 43,000 rows, almost every comparison is statistically significant, so no
conclusion in this project rests on a p-value alone (`docs/archive/planning/STATISTICAL_ANALYSIS.md`'s
original test plan already anticipated this). Effect size, its confidence interval, and whether the
pattern survives stratification are what drive every interpretation. See
`notebooks/04_kpi_validation.ipynb` §1 for the full test register, each entry stating why the method was
chosen, what it means practically, and its limitation.

## Validation

- **Data-quality gates** (`src/routeiq/validation/data_quality.py`, `tests/test_data_quality.py`): row
  count, uniqueness, category membership, numeric ranges, SLA-threshold consistency.
- **Cross-layer KPI reconciliation** (`src/routeiq/validation/reconcile.py`,
  `notebooks/04_kpi_validation.ipynb` §2): the same KPIs computed four independent ways — a
  standard-library-only Python recompute, the pandas analysis pipeline, PostgreSQL, and the v1 Power BI
  report's displayed values. 121 of 122 checked metrics agree exactly; the one exception is a documented
  tie-handling difference in the v1 Power BI Pareto label (`docs/limitations.md`).
- This is **reconciliation, not proof of correctness** — it shows independently written code paths reach
  the same numbers from the same file. It does not establish that the underlying data is real
  operational data (see `docs/limitations.md` and `notebooks/01_data_quality.ipynb`).

## Reproducing this project

```bash
pip install -r requirements.txt
python scripts/run_analysis.py     # rebuilds the analytical dataset, tables, figures, results.json
python scripts/run_sql.py          # optional: needs PostgreSQL reachable (PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD)
pytest                             # 46 tests: data quality, features, effect-size helpers, reconciliation
jupyter lab notebooks              # 01-04, already executed with their outputs saved
```
