"""Raw data loading for the cleaning pipeline (read-only)."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from routeiq.config import RAW_DATA_CSV, SOURCE_RAW_CSV
from routeiq.cleaning.constants import EXPECTED_RAW_COLUMN_COUNT, EXPECTED_RAW_ROW_COUNT, RAW_COLUMNS

logger = logging.getLogger("routeiq_phase1")


def resolve_raw_path() -> "Path":
    """Return the raw CSV location: data/raw/ first, then the legacy project root.

    The raw file is never modified. It is not redistributed with this repo, so
    a clear error explains where to get it if it is missing.
    """
    for candidate in (RAW_DATA_CSV, SOURCE_RAW_CSV):
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"Raw dataset not found at {RAW_DATA_CSV}. Download amazon_delivery.csv from "
        "https://www.kaggle.com/datasets/sujalsuthar/amazon-delivery-dataset and place it "
        "in data/raw/ (see data/README.md)."
    )


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
    raw_path = resolve_raw_path()
    df = pd.read_csv(raw_path, dtype={"Order_ID": str})
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
