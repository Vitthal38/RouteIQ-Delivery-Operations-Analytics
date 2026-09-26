"""Project configuration: filesystem paths for RouteIQ Phase 1.

All paths are derived from this file's location so no path is hardcoded
to a specific machine or working directory. Every module that needs a
file location imports from here rather than constructing its own path.
"""

from __future__ import annotations

from pathlib import Path

# Project root is the parent of the `python/` package directory.
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

# Source data (never modified in place).
SOURCE_RAW_CSV: Path = PROJECT_ROOT / "amazon_delivery.csv"

# Project structure (STEP 8 of the Phase 1 scope).
DATA_DIR: Path = PROJECT_ROOT / "data"
RAW_DATA_DIR: Path = DATA_DIR / "raw"
CLEANED_DATA_DIR: Path = DATA_DIR / "cleaned"
DOCS_DIR: Path = PROJECT_ROOT / "docs"
PYTHON_DIR: Path = PROJECT_ROOT / "python"
ANALYSIS_DIR: Path = PYTHON_DIR / "analysis"
LOGS_DIR: Path = PROJECT_ROOT / "logs"
REPORTS_DIR: Path = PROJECT_ROOT / "reports"
OUTPUT_DIR: Path = PROJECT_ROOT / "output"
FIGURES_DIR: Path = OUTPUT_DIR / "figures"

# Raw data archived under data/raw/ (copied from SOURCE_RAW_CSV, read-only).
RAW_DATA_CSV: Path = RAW_DATA_DIR / "amazon_delivery.csv"

# Phase 1 outputs.
CLEANED_DELIVERY_CSV: Path = CLEANED_DATA_DIR / "cleaned_delivery.csv"
SLA_REFERENCE_CSV: Path = CLEANED_DATA_DIR / "sla_reference.csv"
PROFILING_REPORT_MD: Path = REPORTS_DIR / "profiling_report.md"
CLEANING_LOG_MD: Path = REPORTS_DIR / "cleaning_log.md"
VALIDATION_REPORT_MD: Path = REPORTS_DIR / "validation_report.md"

# Phase 4 (Python EDA + statistical analysis) outputs — structured evidence,
# per PYTHON_ANALYSIS_PLAN.md's Output Files table.
EDA_SUMMARY_JSON: Path = OUTPUT_DIR / "eda_summary.json"
STATISTICAL_TEST_RESULTS_JSON: Path = OUTPUT_DIR / "statistical_test_results.json"
PARETO_RANKING_CSV: Path = OUTPUT_DIR / "pareto_ranking.csv"

# Phase 4 narrative reports.
PYTHON_ANALYSIS_PREFLIGHT_MD: Path = REPORTS_DIR / "python_analysis_preflight.md"
PYTHON_SQL_CROSS_VALIDATION_MD: Path = REPORTS_DIR / "python_sql_cross_validation.md"
STATISTICAL_ANALYSIS_REPORT_MD: Path = REPORTS_DIR / "statistical_analysis_report.md"
PYTHON_EDA_REPORT_MD: Path = REPORTS_DIR / "python_eda_report.md"
VALIDATED_FINDINGS_CANDIDATES_MD: Path = REPORTS_DIR / "validated_findings_candidates.md"
PYTHON_PHASE2_VALIDATION_MD: Path = REPORTS_DIR / "python_phase2_validation.md"

# Log file (timestamped at run time by logging_config.py).
LOG_FILE_PREFIX: str = "phase1_pipeline"
ANALYSIS_LOG_FILE_PREFIX: str = "phase4_analysis"


def ensure_directory_structure() -> None:
    """Create the full project folder skeleton if it does not exist yet.

    Idempotent — safe to call on every run. Never touches file contents,
    only ensures the target directories exist.
    """
    for directory in (
        DATA_DIR,
        RAW_DATA_DIR,
        CLEANED_DATA_DIR,
        DOCS_DIR,
        PYTHON_DIR,
        ANALYSIS_DIR,
        LOGS_DIR,
        REPORTS_DIR,
        OUTPUT_DIR,
        FIGURES_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)
