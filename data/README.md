# Data

## `raw/` — not redistributed

Download `amazon_delivery.csv` from the
[Amazon Delivery Dataset](https://www.kaggle.com/datasets/sujalsuthar/amazon-delivery-dataset) (Kaggle,
author sujalsuthar) and place it here as `data/raw/amazon_delivery.csv`. Check the dataset page's own
licence terms before redistributing it further. 43,739 rows, 16 columns.

`src/routeiq/cleaning/pipeline.py` reads this file (or a legacy copy at the project root) and never
writes to it.

## `processed/` — the frozen, derived data this project analyses

| File | Rows | Built by |
|---|---|---|
| `cleaned_delivery.csv` | 43,648 | `python -m routeiq.cleaning.pipeline` (raw → cleaned + feature engineering) |
| `sla_reference.csv` | 16 (one per category) | Same pipeline — the frozen per-category P75 threshold |
| `analytical_deliveries.csv` | 43,648 | `python scripts/run_analysis.py` (adds `breach_flag`, `hour_band`, `rating_lt_4_5`, etc. — see `docs/data_dictionary.md`) |

These are committed to the repository because they are the frozen inputs every notebook, SQL query and
test in this project reads — reproducing them from the raw file is optional, not required, to explore
the analysis. See `docs/methodology.md` for the full pipeline and `tests/test_pipeline_reproducibility.py`
for the check that the raw file, if present, reproduces `cleaned_delivery.csv` exactly.
