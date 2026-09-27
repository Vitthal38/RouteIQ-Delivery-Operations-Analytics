"""Cross-layer reconciliation: independent CSV recompute vs pandas outputs vs SQL vs Power BI v1.

This is reconciliation, not proof of correctness: every layer reads the same cleaned CSV.
The one known, documented disagreement is the v1 Power BI Pareto label at rank 7 (tie handling).
"""
import os

import pytest

from routeiq.config import SQL_RESULTS_DIR
from routeiq.validation.independent import compute, percentile_linear
from routeiq.validation.reconcile import run_reconciliation

KNOWN_V1_DIFFERENCES = {"pareto_cumulative_pct_rank_7"}


def test_percentile_implementation_matches_numpy():
    import numpy as np
    data = [3, 9, 27, 1, 14, 20, 5, 8, 8, 31]
    for p in (0.1, 0.5, 0.7, 0.75, 0.9):
        assert percentile_linear(data, p) == pytest.approx(np.percentile(data, 100 * p))


def test_independent_recompute_reproduces_frozen_kpis():
    from routeiq.config import CLEANED_DELIVERY_CSV
    ind = compute(CLEANED_DELIVERY_CSV)
    assert ind["total_deliveries"] == 43_648
    assert ind["breached_deliveries"] == 10_328 == ind["stored_flag_breaches"]
    assert ind["stored_flag_mismatches_vs_recomputed"] == 0
    assert ind["rating_best_cut"][0] == 4.5 and ind["age_best_cut"][0] == 30


def test_all_layers_agree():
    rec = run_reconciliation(write=False)
    assert len(rec) > 100
    failures = rec[rec["status"] == "FAIL"]
    assert failures.empty, failures[["metric", "independent_csv", "pandas_outputs", "sql", "notes"]].to_string()
    differs = set(rec.loc[rec["status"] == "PBI_v1_DIFFERS", "metric"])
    assert differs <= KNOWN_V1_DIFFERENCES, f"unexpected v1 Power BI differences: {differs - KNOWN_V1_DIFFERENCES}"


def test_sql_snapshots_present_and_all_q29_checks_pass():
    q29 = SQL_RESULTS_DIR / "Q29_cross_validation_reconciliation.csv"
    if not q29.exists():
        pytest.skip("run scripts/run_sql.py to create SQL result snapshots")
    import pandas as pd
    df = pd.read_csv(q29)
    assert len(df) == 14 and (df["status"] == "PASS").all()


@pytest.mark.live_sql
@pytest.mark.skipif(os.environ.get("ROUTEIQ_LIVE_SQL") != "1", reason="set ROUTEIQ_LIVE_SQL=1 and PG* variables")
def test_live_database_q29_passes():
    import psycopg2
    from pathlib import Path
    conn = psycopg2.connect(host=os.environ.get("PGHOST", "localhost"), port=os.environ.get("PGPORT", "5432"),
                            dbname=os.environ.get("PGDATABASE", "postgres"), user=os.environ.get("PGUSER", "postgres"),
                            password=os.environ.get("PGPASSWORD"))
    try:
        cur = conn.cursor()
        cur.execute(Path(__file__).resolve().parents[1].joinpath("sql", "analysis",
                    "Q29_cross_validation_reconciliation.sql").read_text(encoding="utf-8"))
        rows = cur.fetchall()
    finally:
        conn.close()
    assert len(rows) == 14 and all(r[-1] == "PASS" for r in rows)
