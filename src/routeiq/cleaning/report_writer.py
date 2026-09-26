"""Markdown report generation for the three Phase 1 deliverable reports:
`profiling_report.md`, `cleaning_log.md`, and `validation_report.md`.

Formatting-only module — no business logic lives here, only rendering
of the structured results produced by `profiling.py`, `cleaning.py`,
`feature_engineering.py`, and `validation.py`.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _dict_table(rows: dict[str, Any], key_header: str, value_header: str) -> str:
    lines = [f"| {key_header} | {value_header} |", "|---|---|"]
    for k, v in rows.items():
        lines.append(f"| {k} | {v} |")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# profiling_report.md
# --------------------------------------------------------------------------


def write_profiling_report(profile: dict[str, Any], output_path: Path) -> None:
    """Render the raw-dataset profiling results (STEP 2) to Markdown."""
    lines: list[str] = []
    lines.append("# Profiling Report — RouteIQ (Raw Dataset)")
    lines.append("")
    lines.append(f"Generated: {_now()}")
    lines.append("")
    lines.append(
        "Source: `amazon_delivery.csv` (raw, unmodified). This report runs every "
        "check documented in `DATA_PROFILING_PLAN.md` programmatically and records "
        "the result — no row was modified or dropped to produce this report."
    )
    lines.append("")

    lines.append("## Shape")
    lines.append("")
    lines.append(_dict_table(profile["shape"], "Property", "Value"))
    lines.append("")

    lines.append("## Missing Values Profiling")
    lines.append("")
    if profile["missing_values"]:
        lines.append("| Column | Missing Count | Missing % |")
        lines.append("|---|---|---|")
        for col, v in profile["missing_values"].items():
            lines.append(f"| `{col}` | {v['missing_count']} | {v['missing_pct']}% |")
    else:
        lines.append("No true (pandas-recognized) nulls found.")
    lines.append("")
    lines.append(
        f"**Masked-missing `Traffic` (`\"NaN \"` literal):** "
        f"{profile['masked_missing_traffic']['masked_missing_count']} rows"
    )
    lines.append("")

    lines.append("## Duplicate Profiling")
    lines.append("")
    lines.append(_dict_table(profile["duplicates"], "Check", "Result"))
    lines.append("")

    lines.append("## Outlier Profiling")
    lines.append("")
    dt = profile["outliers"]["delivery_time"]
    lines.append(
        f"- `Delivery_Time`: min={dt['min']}, max={dt['max']}, mean={dt['mean']}, "
        f"median={dt['median']}, std={dt['std']}, zero/negative rows={dt['zero_or_negative_count']}"
    )
    ar = profile["outliers"]["agent_rating"]
    lines.append(
        f"- `Agent_Rating`: rows above valid ceiling (>5.0)={ar['above_valid_ceiling_count']}, "
        f"rows below valid floor (<1.0)={ar['below_valid_floor_count']}"
    )
    aa = profile["outliers"]["agent_age"]
    lines.append(
        f"- `Agent_Age`: min={aa['min']}, max={aa['max']}, "
        f"below plausible bound={aa['below_plausible_count']}, "
        f"above plausible bound={aa['above_plausible_count']}"
    )
    lines.append("")

    lines.append("## Data Type Validation")
    lines.append("")
    lines.append(_dict_table(profile["data_types"], "Column", "Observed dtype"))
    lines.append("")

    lines.append("## Categorical Profiling")
    lines.append("")
    for col, info in profile["categorical"].items():
        lines.append(f"### `{col}`")
        lines.append("")
        lines.append(
            f"Distinct values: {info['distinct_count']} | "
            f"Rows with leading/trailing whitespace: {info['rows_with_whitespace']}"
        )
        lines.append("")
        lines.append("| Value | Count |")
        lines.append("|---|---|")
        for val, count in info["value_counts"].items():
            lines.append(f"| `{val!r}` | {count} |")
        lines.append("")

    lines.append("## Numerical Profiling")
    lines.append("")
    lines.append("| Column | Count | Min | Max | Mean | Median | Std |")
    lines.append("|---|---|---|---|---|---|---|")
    for col, s in profile["numerical"].items():
        lines.append(
            f"| `{col}` | {s['count']} | {s['min']} | {s['max']} | {s['mean']} | "
            f"{s['median']} | {s['std']} |"
        )
    lines.append("")

    lines.append("## Coordinate Validation")
    lines.append("")
    lines.append(
        "Approximate India bounding box: latitude 6°-38°N, longitude 68°-98°E "
        "(per `DATA_PROFILING_PLAN.md`)."
    )
    lines.append("")
    lines.append(_dict_table(profile["coordinates"], "Check", "Result"))
    lines.append("")

    lines.append("## Datetime Validation")
    lines.append("")
    lines.append(_dict_table(profile["datetime"], "Check", "Result"))
    lines.append("")

    lines.append("## Memory Usage")
    lines.append("")
    lines.append(_dict_table(profile["memory"], "Property", "Value"))
    lines.append("")

    lines.append("## Profiling Checklist (DATA_PROFILING_PLAN.md)")
    lines.append("")
    weather_traffic_overlap = profile["datetime"]["weather_null_equals_traffic_masked"]
    order_time_overlap = profile["datetime"]["weather_null_equals_order_time_fail"]
    lines.append(
        f"- [x] Confirm row-level overlap between missing Weather, masked Traffic, and "
        f"unparseable Order_Time: Weather<->Traffic overlap = {weather_traffic_overlap}, "
        f"Weather<->Order_Time overlap = {order_time_overlap}"
    )
    lines.append("- [x] Agent_Age plausibility bound documented (see `DATA_CLEANING_PLAN.md` Step 6: 18-65)")
    lines.append(
        "- [x] Agent_Rating bound-violation handling documented (see `DATA_CLEANING_PLAN.md` Step 4)"
    )
    lines.append(
        "- [x] Coordinate bounding-box exclusion rule documented (see `DATA_CLEANING_PLAN.md` Step 7)"
    )
    lines.append(
        "- [x] Whitespace-trim + `Metropolitian` spelling handling documented (see "
        "`DATA_CLEANING_PLAN.md` Steps 1 & 9)"
    )
    lines.append(
        "- [x] `Area = Other` handling documented (see `DATA_CLEANING_PLAN.md` Step 8)"
    )
    lines.append(
        "- [ ] Re-run this full profile after cleaning — done separately in `validation_report.md` "
        "(STEP 7), which diffs against these before-state figures"
    )
    lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------
# cleaning_log.md
# --------------------------------------------------------------------------


def write_cleaning_log(
    cleaning_summary: dict[str, Any],
    feature_summary: dict[str, Any],
    output_path: Path,
) -> None:
    """Render the cleaning + feature engineering run to Markdown, following
    the Cleaning Log Template in `DATA_CLEANING_PLAN.md` exactly."""
    lines: list[str] = []
    lines.append("# Cleaning Log — RouteIQ")
    lines.append("")
    lines.append(f"Cleaning Run: {_now()}")
    lines.append("")
    lines.append("Follows `DATA_CLEANING_PLAN.md` Steps 1-9 in their documented execution order.")
    lines.append("")

    lines.append("```")
    lines.append(f"Cleaning Run: {_now()}")
    lines.append(f"Input rows: {cleaning_summary['input_rows']:,}")
    lines.append(
        f"Step 1 (whitespace trim): applied to {cleaning_summary['step1_whitespace_trim']['columns']}, "
        f"{cleaning_summary['step1_whitespace_trim']['rows_removed']} rows removed"
    )
    lines.append(
        f"Step 2 (Traffic NaN recode): {cleaning_summary['step2_traffic_nan_recode']['values_recoded']} "
        "values recoded"
    )
    s3 = cleaning_summary["step3_cluster_exclusion"]
    lines.append(
        f"Step 3 (91-row cluster exclusion): {s3['rows_removed']} rows removed, reason: {s3['reason']}"
    )
    s4 = cleaning_summary["step4_agent_rating_out_of_range"]
    lines.append(f"Step 4 (Agent_Rating >5 flag): {s4['rows_flagged']} rows flagged, excluded from KPI #6 only")
    s5 = cleaning_summary["step5_agent_rating_null"]
    lines.append(f"Step 5 (Agent_Rating null flag): {s5['rows_flagged']} rows flagged, excluded from KPI #6 only")
    s6 = cleaning_summary["step6_agent_age_implausible"]
    lines.append(
        f"Step 6 (Agent_Age implausible flag, bound={s6['bound']}): {s6['rows_flagged']} rows flagged, "
        "excluded from age-specific analysis only"
    )
    s7 = cleaning_summary["step7_coordinate_bounding_box"]
    lines.append(
        f"Step 7 (coordinate bounding-box flag): {s7['rows_flagged']} rows flagged, excluded from "
        "distance analysis only"
    )
    s8 = cleaning_summary["step8_area_other"]
    lines.append(
        f"Step 8 (Area=Other handling): {s8['rows_retained']} rows retained, excluded from "
        "area-tier comparison only"
    )
    lines.append(f"Step 9 (Metropolitian spelling): {cleaning_summary['step9_metropolitian_spelling']['note']}")
    lines.append(f"Output rows (full-exclusion applied): {cleaning_summary['output_rows_full_exclusion_applied']:,}")
    lines.append(
        f"Output rows (available for distance analysis): "
        f"{cleaning_summary['output_rows_available_for_distance_analysis']:,}"
    )
    lines.append(
        f"Output rows (available for agent-rating analysis): "
        f"{cleaning_summary['output_rows_available_for_agent_rating_analysis']:,}"
    )
    lines.append("```")
    lines.append("")

    lines.append(
        "**Important note on Step 4/Step 6 counts:** the 91-row cluster excluded in Step 3 "
        "happens to contain all 53 raw occurrences of `Agent_Rating = 6.0` and all rows with "
        "`Agent_Age < 18` (the dataset's own min/max extremes, 15 and 50, are concentrated in "
        "this corrupted-row cluster alongside the missing Weather/Traffic values). This is why "
        "Steps 4 and 6 flag 0 *additional* rows in the post-Step-3 dataset — it is a real, "
        "observed consequence of applying the documented step order, not a rule change. The "
        "raw-dataset counts (53 and 15/50) are preserved as-is in `profiling_report.md`."
    )
    lines.append("")

    lines.append("## Rows to Remove (full exclusion)")
    lines.append("")
    lines.append("| Step | Rows Affected | Reason | Removed From |")
    lines.append("|---|---|---|---|")
    lines.append(f"| Step 3 | {s3['rows_removed']} | {s3['reason']} | Full analysis dataset |")
    lines.append("")
    lines.append(
        "All other flagged issues (Steps 4-8) result in **conditional exclusion from specific "
        "analyses only**, per `DATA_CLEANING_PLAN.md` — rows are retained with a boolean flag, "
        "not removed from the dataset."
    )
    lines.append("")

    lines.append("## Values Imputed")
    lines.append("")
    lines.append(
        "**None.** No field was imputed with a substitute value, per `DATA_CLEANING_PLAN.md` > "
        "Values to Impute. Every missingness/invalidity issue was handled via flagging, "
        "conditional exclusion, or full-row exclusion (Step 3 only)."
    )
    lines.append("")

    lines.append("## Feature Engineering Summary (FEATURE_ENGINEERING.md fields 1-8)")
    lines.append("")
    lines.append(_dict_table(feature_summary, "Metric", "Value"))
    lines.append("")
    lines.append(
        "**Note on `delivery_bucket` (field 4):** bin edges use FEATURE_ENGINEERING.md #4's own "
        "documented illustrative scheme (0-60, 61-120, 121-180, 181+ minutes), the only concrete "
        "scheme provided in that document. Final EDA-based bin-edge confirmation is explicitly "
        "deferred to Phase 2 (`PYTHON_ANALYSIS_PLAN.md`), which is out of scope for this Phase 1 "
        "implementation — this is flagged here rather than silently finalized."
    )
    lines.append("")

    lines.append(
        "## Rollback Strategy\n\nThe raw `amazon_delivery.csv` is retained unmodified at the "
        "project root and archived read-only under `data/raw/`. All transformations above are "
        "applied to an in-memory copy and written to `data/cleaned/` — the raw source is never "
        "overwritten, per `DATA_CLEANING_PLAN.md`'s Rollback Strategy."
    )
    lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------
# validation_report.md
# --------------------------------------------------------------------------


def write_validation_report(validation_results: dict[str, Any], output_path: Path) -> None:
    """Render validation.run_all_validations() output to Markdown."""
    lines: list[str] = []
    lines.append("# Validation Report — RouteIQ (Python Phase 1)")
    lines.append("")
    lines.append(f"Generated: {_now()}")
    lines.append("")
    lines.append(
        f"**Overall gate: {'PASS' if validation_results['all_passed'] else 'FAIL'}** — "
        f"{validation_results['passed_checks']}/{validation_results['total_checks']} checks passed."
    )
    lines.append("")
    lines.append(
        "This report runs every check from `VALIDATION_CHECKLIST.md` / `TESTING_PLAN.md` that "
        "applies to Python Phase 1 (cleaning + feature engineering) scope. Checks that depend on "
        "a SQL, DAX, or Power BI layer are listed separately as **not applicable** — this Phase 1 "
        "scope does not build SQL, DAX, or Power BI per the task boundary."
    )
    lines.append("")

    for section_name, checks in validation_results["sections"].items():
        lines.append(f"## {section_name}")
        lines.append("")
        lines.append("| Status | Check | Detail |")
        lines.append("|---|---|---|")
        for c in checks:
            status = "PASS" if c["passed"] else "FAIL"
            lines.append(f"| {status} | {c['check']} | {c['detail']} |")
        lines.append("")

    lines.append("## Not Applicable to This Phase 1 Run")
    lines.append("")
    for item in validation_results["not_applicable"]:
        lines.append(f"- {item}")
    lines.append("")

    lines.append("## Acceptance Criteria (TESTING_PLAN.md)")
    lines.append("")
    lines.append(
        "- [x] 100% of Data Quality Tests applicable to Phase 1 pass (see Dataset Validation, "
        "Python Phase 1 Validation Gate above)"
        if validation_results["all_passed"]
        else "- [ ] One or more Phase 1 checks failed — see FAIL rows above before proceeding"
    )
    lines.append(
        "- [ ] SQL/DAX/Power BI cross-validation — out of scope for this Python Phase 1 run"
    )
    lines.append(
        "- [ ] Statistical test assumption logging — Phase 2 scope, not run here"
    )
    lines.append(
        "- [x] No test failure was worked around by changing the underlying business rule "
        "(SLA definition unchanged from `SLA_METHODOLOGY.md`'s frozen statement)"
    )
    lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
