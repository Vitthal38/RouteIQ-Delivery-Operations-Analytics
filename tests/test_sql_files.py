"""Static checks on the SQL deliverables (they are executed by scripts/run_sql.py and tests/test_reconciliation.py)."""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "sql" / "analysis"
NEW_QUERIES = [f"Q{n}" for n in range(23, 30)]


def test_twentynine_numbered_queries_exist():
    numbered = sorted(p.name[:3] for p in ANALYSIS.glob("Q[0-9][0-9]_*.sql"))
    assert numbered == [f"Q{n:02d}" for n in range(1, 30)]


@pytest.mark.parametrize("q", NEW_QUERIES)
def test_new_queries_state_their_business_question(q):
    path = next(ANALYSIS.glob(f"{q}_*.sql"))
    head = path.read_text(encoding="utf-8")[:1500]
    assert "Business question" in head, f"{path.name} must state the business question it answers"
    assert "vw_analytical_deliveries" in path.read_text(encoding="utf-8")


def test_view_and_validation_files_exist():
    assert (ROOT / "sql" / "schema" / "09_create_analytical_view.sql").exists()
    assert (ROOT / "sql" / "validation" / "final_test_suite.sql").exists()


def test_frozen_sla_rule_not_redefined_in_view():
    text = (ROOT / "sql" / "schema" / "09_create_analytical_view.sql").read_text(encoding="utf-8")
    assert "delivery_time_minutes > f.sla_threshold_minutes" in text  # strict greater-than
    assert "PERCENTILE" not in text.upper()                             # the view never recomputes the threshold
