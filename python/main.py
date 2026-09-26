"""RouteIQ — Python Phase 1 pipeline orchestrator.

Runs, in order (mirroring PYTHON_ANALYSIS_PLAN.md Phase 1 and this
task's STEP 1-8 scope):

  1. Load the raw dataset (read-only).
  2. Profile it and write `reports/profiling_report.md`.
  3. Apply DATA_CLEANING_PLAN.md Steps 1-9.
  4. Apply FEATURE_ENGINEERING.md fields 1-8.
  5. Write `data/cleaned/cleaned_delivery.csv`.
  6. Write `data/cleaned/sla_reference.csv` (frozen SLA reference table).
  7. Run VALIDATION_CHECKLIST.md-derived checks and write
     `reports/validation_report.md`.
  8. Write `reports/cleaning_log.md`.

Phase 1 stops here — no EDA, no statistical testing, no SQL, no DAX,
no Power BI, per this task's explicit scope boundary.
"""

from __future__ import annotations

import sys

from cleaning import apply_cleaning_steps
from config import (
    CLEANED_DELIVERY_CSV,
    CLEANING_LOG_MD,
    PROFILING_REPORT_MD,
    SLA_REFERENCE_CSV,
    VALIDATION_REPORT_MD,
    ensure_directory_structure,
)
from data_loader import load_raw_data
from feature_engineering import engineer_features
from logging_config import setup_logger
from profiling import run_full_profile
from report_writer import write_cleaning_log, write_profiling_report, write_validation_report
from validation import run_all_validations


def run_phase1() -> int:
    """Execute the full Phase 1 pipeline. Returns a process exit code."""
    ensure_directory_structure()
    logger = setup_logger()

    logger.info("=== RouteIQ Python Phase 1 — pipeline start ===")

    # STEP 1 — Load raw dataset.
    df_raw = load_raw_data()

    # STEP 2 — Profile raw dataset, generate profiling_report.md. Dataset is
    # never modified by this step.
    raw_profile = run_full_profile(df_raw)
    write_profiling_report(raw_profile, PROFILING_REPORT_MD)
    logger.info("Wrote %s", PROFILING_REPORT_MD)

    # STEP 3 — Apply every DATA_CLEANING_PLAN.md cleaning rule, nothing more.
    df_cleaned, cleaning_summary = apply_cleaning_steps(df_raw)

    # STEP 4 — Generate every FEATURE_ENGINEERING.md field.
    df_engineered, sla_reference, feature_summary = engineer_features(df_cleaned)

    # STEP 5 — Write cleaned_delivery.csv.
    CLEANED_DELIVERY_CSV.parent.mkdir(parents=True, exist_ok=True)
    df_engineered.to_csv(CLEANED_DELIVERY_CSV, index=False)
    logger.info("Wrote %s (%d rows, %d columns)", CLEANED_DELIVERY_CSV, *df_engineered.shape)

    # STEP 6 — Write sla_reference.csv (frozen).
    sla_reference.to_csv(SLA_REFERENCE_CSV, index=False)
    logger.info("Wrote %s (%d categories)", SLA_REFERENCE_CSV, len(sla_reference))

    # STEP 7 — Run every VALIDATION_CHECKLIST.md check applicable to Phase 1
    # scope, generate validation_report.md.
    validation_results = run_all_validations(
        df_raw=df_raw,
        df_cleaned=df_cleaned,
        df_engineered=df_engineered,
        sla_reference=sla_reference,
        cleaning_summary=cleaning_summary,
    )
    write_validation_report(validation_results, VALIDATION_REPORT_MD)
    logger.info("Wrote %s", VALIDATION_REPORT_MD)

    # cleaning_log.md written last so it can include the feature-engineering
    # summary alongside the cleaning-step summary.
    write_cleaning_log(cleaning_summary, feature_summary, CLEANING_LOG_MD)
    logger.info("Wrote %s", CLEANING_LOG_MD)

    if validation_results["all_passed"]:
        logger.info(
            "=== Phase 1 complete: ALL %d validation checks passed ===",
            validation_results["total_checks"],
        )
        return 0

    logger.error(
        "=== Phase 1 complete WITH FAILURES: %d/%d validation checks passed — see %s ===",
        validation_results["passed_checks"],
        validation_results["total_checks"],
        VALIDATION_REPORT_MD,
    )
    return 1


if __name__ == "__main__":
    sys.exit(run_phase1())
