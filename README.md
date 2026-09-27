<div align="center">

# RouteIQ
### Delivery Operations Analytics

A delivery operations analytics case study uncovering SLA breaches, operational bottlenecks, and
performance patterns across traffic, weather, time of day, and delivery segments.

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-0B172A?style=flat-square&logo=postgresql&logoColor=19B5C5)
![SQL](https://img.shields.io/badge/SQL-29%20queries-19B5C5?style=flat-square)
![Python](https://img.shields.io/badge/Python-pandas%20%2B%20SciPy-0B172A?style=flat-square&logo=python&logoColor=19B5C5)
![Power BI](https://img.shields.io/badge/Power%20BI-DAX-13263D?style=flat-square&logo=powerbi&logoColor=E85D5D)
![Tests](https://img.shields.io/badge/pytest-46%20tests-7BC67B?style=flat-square)

[View Dashboard](powerbi/RouteIQ_v1.pbix) · [Explore the Analysis](docs/analytical_findings.md) · [Documentation Index](#documentation-index)

<br>

<img src="powerbi/screenshots/v1_page1_executive_overview.png" alt="RouteIQ Executive Overview dashboard page" width="900">

</div>

<br>

## Executive Snapshot

| 43,648 | 76.34% | 23.66% | 195 min |
|:---:|:---:|:---:|:---:|
| **Deliveries analyzed** | **On-time rate** | **SLA breach rate** | **P90 delivery time** |

## Business problem

A last-mile delivery operation wants to know: how much of its delivery volume misses its expected
delivery-time benchmark, where that risk concentrates, and which operational conditions are associated
with it — using only the data actually available (no cost data, no agent identifiers, no company-set
SLA).

## Key questions

1. What is the overall delivery performance (volume, on-time rate, breach rate, P90)?
2. Where are breaches concentrated — by area, traffic, weather, and their combination?
3. When do breaches happen — is there a time-of-day pattern?
4. What operational factors are associated with longer deliveries or higher breach rates?
5. How does agent rating relate to delivery performance, and does a simple correlation capture it?
6. How sensitive are the conclusions to the SLA definition itself?
7. Which segments should operations investigate first, and what can't be concluded from this data?

## Key findings

*Associations observed in this dataset — never causal claims. Full detail with every figure sourced:
[`docs/analytical_findings.md`](docs/analytical_findings.md).*

#### 01 — Evening operations concentrate the risk
**72%** of delivery volume occurs in the 17:00–23:59 window, but it carries **89%** of all SLA breaches.

#### 02 — Agent rating is a step, not a slope
**63.2%** breach rate at rating 4.4 vs. **10.5%** at rating 4.5 — a 52.7-point jump that survives
controlling for traffic and area (risk ratio **3.69**). A simple correlation coefficient misses this
entirely; the same round-number step also shows up at agent age 30.

#### 03 — Breach rate and breach volume tell different stories
**Metropolitan** holds 74.8% of volume and 83.7% of breach volume — a volume story, not an unusually
high rate (26.5%, close to the dataset average). **Semi-Urban** shows the highest rate (**100%**), but
on only **n = 152** deliveries — too small to act on alone.

#### 04 — Two factors show no association at all
Preparation time (Cramér's V = 0.006) and weekend-vs-weekday timing show clean null results — neither
is a lever worth pursuing based on this data.

#### 05 — The data itself looks synthetic-style
95% of delivery times are multiples of 5 minutes, and several exact round-number steps appear — disclosed
plainly, not hidden ([`docs/limitations.md`](docs/limitations.md)).

## Dashboard

<table>
  <tr>
    <td width="50%">
      <b>01 — Executive Overview</b><br>
      <sub>Volume, on-time rate, breach rate, P90, and the weekly trend at a glance.</sub><br>
      <img src="powerbi/screenshots/v1_page1_executive_overview.png" width="100%">
    </td>
    <td width="50%">
      <b>02 — Area &amp; Category Performance</b><br>
      <sub>Where breach rate concentrates across area and delivery category.</sub><br>
      <img src="powerbi/screenshots/v1_page2_area_category.png" width="100%">
    </td>
  </tr>
  <tr>
    <td width="50%">
      <b>03 — Agent Performance</b><br>
      <sub>The rating/age step effect, at attribute level only — no individual agent identifier exists.</sub><br>
      <img src="powerbi/screenshots/v1_page3_agent_performance.png" width="100%">
    </td>
    <td width="50%">
      <b>04 — Delay Root Cause</b><br>
      <sub>Traffic and weather effects on one comparable scale, with the statistical evidence shown.</sub><br>
      <img src="powerbi/screenshots/v1_page4_delay_root_cause.png" width="100%">
    </td>
  </tr>
</table>

These are screenshots of the actual report, not design mockups. It's a 4-page report today; a 5-page
structure with a live SLA-sensitivity parameter and drillthrough is specified but not yet built — see
[`powerbi/README.md`](powerbi/README.md) for the exact, current gap list.

## Recommendations

*Full Finding → Evidence → Action → KPI → Limitation detail for every item:
[`docs/recommendations.md`](docs/recommendations.md).*

| Finding | Action | Monitor |
|---|---|---|
| Rating below 4.5 carries 50.2% of all breaches, in a genuine step | Confirm what the rating field represents and when it's recorded, before treating it as a coaching lever | Breach rate by rating band |
| Evening peak (17:00–23:59) is 72% of volume, 89% of breaches | Review dispatch capacity for that window, especially 19:00–21:00 | Breach rate and volume by hour band |
| Jam traffic + adverse weather is the highest-risk combination | Prioritize dispatch/routing review for Jam-traffic periods in Metropolitan | Breach rate by area × traffic |
| Metropolitan's high breach volume reflects volume, not an unusually bad rate | Frame it as "largest volume to address," not "worst-performing area" | Breach rate *and* volume by area, read together |
| Semi-Urban's 100% breach rate rests on n = 152 | A bounded, low-cost review — not a resourcing commitment | Semi-Urban rate and n, tracked together |
| Preparation time shows no association with breach or delivery time | Do not prioritize prep-time changes as a delay lever | None — re-check only if the process changes |
| Weekend/weekday breach rates are practically identical | Do not adjust weekend staffing based on this dataset | None while the null result holds |

## Technical workflow

```
Raw data (Kaggle, 43,739 rows)
    -> Python cleaning + feature engineering
    -> Cleaned dataset (43,648 rows)
    -> PostgreSQL star schema
    -> Controlled analytical view (Python + SQL, one definition each)
    -> SQL analysis (29 queries) + Python descriptive/diagnostic analysis
    -> Cross-layer KPI reconciliation (4 independent recomputations)
    -> Power BI report + DAX
    -> Business recommendations
```

Data model: one fact table (`FactDelivery`) and six dimensions
(`sql/schema/`, [`docs/data_dictionary.md`](docs/data_dictionary.md)). Included to demonstrate
dimensional modelling and BI-model discipline — a single flat table would work equally well for this
dataset's size; see [`docs/methodology.md`](docs/methodology.md) for the honest framing.

**Stack:** PostgreSQL 18 · SQL (CTEs, window functions, `PERCENTILE_CONT`, `LAG`, conditional
aggregation) · Python (pandas, NumPy, SciPy, Matplotlib) · Power BI (DAX) · pytest · Git/GitHub.

## Repository structure

```
.
├── README.md, requirements.txt, pytest.ini
├── data/
│   ├── raw/            amazon_delivery.csv (not redistributed — see data/README.md)
│   └── processed/      cleaned_delivery.csv (43,648 rows), sla_reference.csv, analytical_deliveries.csv
├── sql/
│   ├── schema/          01-09: star schema + the controlled analytical view
│   ├── analysis/         Q01-Q29 business-question queries
│   └── validation/       Cross-cutting test suite
├── src/routeiq/
│   ├── cleaning/         Raw -> cleaned pipeline
│   ├── features/         The controlled analytical dataset (one definition per feature)
│   ├── analysis/         Segments, time-of-day, prep-time, thresholds, SLA sensitivity, scenarios, figures
│   ├── statistics/       Effect-size helpers (Wilson CI, risk/odds ratio, Cramér's V, Mantel-Haenszel, Cohen's d)
│   └── validation/       Data-quality checks, independent recompute, cross-layer reconciliation
├── notebooks/            01_data_quality, 02_eda, 03_operational_analysis, 04_kpi_validation
├── tests/                46 pytest tests
├── scripts/              run_analysis.py, run_sql.py, run_all.py
├── powerbi/              RouteIQ_v1.pbix, screenshots/, README.md (measures + page spec)
└── docs/
    ├── methodology.md, data_dictionary.md, analytical_findings.md
    ├── limitations.md, recommendations.md, dashboard_guide.md
    └── archive/          Prior-phase planning docs, validation reports, and the earlier analysis version
```

## Validation and reproducibility

- **Cross-layer KPI reconciliation:** the same KPIs computed four independent ways (plain Python, the
  pandas pipeline, PostgreSQL, and the deployed Power BI report). **121 of 122 checked metrics agree
  exactly** — the one exception is a documented Power BI tie-handling issue
  ([`docs/limitations.md`](docs/limitations.md)). This is reconciliation, not proof of correctness.
- **46 automated tests** — data quality, feature definitions, effect-size calculations against known
  answers, and the reconciliation itself.

```bash
pip install -r requirements.txt
python scripts/run_analysis.py     # rebuilds the analytical dataset, tables, figures, results.json
jupyter lab notebooks              # 01-04, already executed with their outputs saved
```

To also run the SQL layer, connect a PostgreSQL 18 instance (`sql/schema/01`–`09` in order), set the
standard `PG*` environment variables, and run `python scripts/run_sql.py`. Full steps, including the raw
data source: [`docs/methodology.md`](docs/methodology.md).

## Limitations

Full detail in [`docs/limitations.md`](docs/limitations.md). In short: treat this as a realistic
synthetic-style dataset, not verified real operations; no agent identifier exists (attribute-level only);
`bicycle` has 0 rows after cleaning; the SLA is an analyst-defined benchmark, not a company target; no
cost/revenue data exists, so no financial impact is estimated anywhere.

## Documentation index

| Where | What |
|---|---|
| [`docs/methodology.md`](docs/methodology.md) | Pipeline, SLA definition, descriptive methods used and why, reproduction steps |
| [`docs/data_dictionary.md`](docs/data_dictionary.md) | Every column, every derived feature, the star schema |
| [`docs/analytical_findings.md`](docs/analytical_findings.md) | Every finding, with its source query/notebook |
| [`docs/limitations.md`](docs/limitations.md) | Data realism, agent-attribute caveats, statistical scope, known discrepancy |
| [`docs/recommendations.md`](docs/recommendations.md) | Finding → Evidence → Action → KPI → Limitation, for every recommendation |
| [`docs/dashboard_guide.md`](docs/dashboard_guide.md), [`powerbi/README.md`](powerbi/README.md) | The dashboard page-by-page, DAX measures, current gaps |
| [`docs/archive/`](docs/archive) | Prior-phase planning docs, validation reports, and the earlier (v1) analysis code |

## Data source

Built on the public [Amazon Delivery Dataset](https://www.kaggle.com/datasets/sujalsuthar/amazon-delivery-dataset)
by sujalsuthar on Kaggle. The raw file is not redistributed in this repo; see the dataset page for its
licence terms and `data/README.md` for how to obtain it.

<br>

<div align="center">

## Explore RouteIQ

[View Dashboard](powerbi/RouteIQ_v1.pbix) · [View Analysis](docs/analytical_findings.md) · [Connect on GitHub](https://github.com/Vitthal38)

**Vitthal Misal** · Data Analyst

</div>
