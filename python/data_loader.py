"""Raw data loading and archival for the Phase 1 pipeline.

Per DATA_CLEANING_PLAN.md's rollback strategy, the raw CSV is never
modified in place. This module reads it read-only and archives an
identical copy under `data/raw/` so the pipeline has a stable,
project-local source it can always re-run from.
"""

from __future__ import annotations

import logging
import shutil

import pandas as pd

from config import RAW_DATA_CSV, SOURCE_RAW_CSV
from constants import EXPECTED_RAW_COLUMN_COUNT, EXPECTED_RAW_ROW_COUNT, RAW_COLUMNS

logger = logging.getLogger("routeiq_phase1")


def archive_raw_csv() -> None:
    """Copy the source CSV into `data/raw/` if not already archived there.

    The source file at the project root is the single source of truth
    and is never written to. This copy exists only so the project
    structure required by STEP 8 is self-contained.
    """
    RAW_DATA_CSV.parent.mkdir(parents=True, exist_ok=True)
    if not RAW_DATA_CSV.exists() or RAW_DATA_CSV.stat().st_size != SOURCE_RAW_CSV.stat().st_size:
        shutil.copy2(SOURCE_RAW_CSV, RAW_DATA_CSV)
        logger.info("Archived raw CSV to %s", RAW_DATA_CSV)
    else:
        logger.info("Raw CSV already archived at %s (skipping copy)", RAW_DATA_CSV)


def load_raw_data() -> pd.DataFrame:
    """Load the raw delivery dataset read-only and validate its shape.

    Returns:
        A DataFrame with the exact raw column set and dtypes as
        observed during profiling (see DATA_PROFILING_PLAN.md > Data
        Type Validation). No transformation is applied here.

    Raises:
        ValueError: If the loaded shape or column set does not match
            what `DATASET_OVERVIEW.md` documents — a documentation
            conflict must be surfaced, not silently absorbed.
    """
    archive_raw_csv()

    df = pd.read_csv(SOURCE_RAW_CSV, dtype={"Order_ID": str})
    logger.info("Loaded raw dataset: %d rows, %d columns", *df.shape)

    if list(df.columns) != RAW_COLUMNS:
        raise ValueError(
            "Raw CSV column set/order does not match DATASET_OVERVIEW.md's "
            f"documented columns. Expected {RAW_COLUMNS}, got {list(df.columns)}."
        )

    if df.shape[0] != EXPECTED_RAW_ROW_COUNT or df.shape[1] != EXPECTED_RAW_COLUMN_COUNT:
        raise ValueError(
            "Raw CSV shape does not match DATASET_OVERVIEW.md's documented "
            f"structure. Expected ({EXPECTED_RAW_ROW_COUNT}, {EXPECTED_RAW_COLUMN_COUNT}), "
            f"got {df.shape}."
        )

    return df
