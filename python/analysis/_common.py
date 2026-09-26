"""Shared utilities for Phase 4 (Python EDA + statistical analysis) scripts.

Every `python/analysis/*.py` module imports from here rather than
duplicating path setup, data loading, or JSON serialization logic.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# Make the flat `python/` package (config.py, constants.py, logging_config.py)
# importable from this subdirectory, matching the existing project convention.
_PYTHON_DIR = Path(__file__).resolve().parent.parent
if str(_PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(_PYTHON_DIR))

from config import CLEANED_DELIVERY_CSV  # noqa: E402
from logging_config import setup_logger  # noqa: E402

logger = setup_logger("routeiq_phase4")


def load_cleaned_data() -> pd.DataFrame:
    """Load the frozen, approved Phase 1 output — read-only, never regenerated.

    Raises:
        FileNotFoundError: if the approved artifact is missing.
        ValueError: if the row count does not match the frozen 43,648 figure
            (a Phase 4 preflight-level integrity check, not a cleaning step).
    """
    if not CLEANED_DELIVERY_CSV.exists():
        raise FileNotFoundError(
            f"Approved artifact not found: {CLEANED_DELIVERY_CSV}. This phase "
            "reads the frozen Phase 1 output only and never regenerates it."
        )
    df = pd.read_csv(CLEANED_DELIVERY_CSV)
    if len(df) != 43_648:
        raise ValueError(
            f"Expected 43,648 rows in the approved cleaned dataset, got {len(df)}. "
            "This indicates the artifact was regenerated or modified — STOP, do "
            "not proceed with analysis on an unexpected row count."
        )
    logger.info("Loaded approved cleaned dataset: %d rows, %d columns", *df.shape)
    return df


class _NumpyJSONEncoder(json.JSONEncoder):
    """Encoder that handles numpy/pandas scalar types JSON can't serialize natively."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, (pd.Timestamp,)):
            return obj.isoformat()
        return super().default(obj)


def save_json(data: dict[str, Any], path: Path) -> None:
    """Write a results dict to disk as pretty-printed JSON, merging with any
    existing content at that path (each analysis module owns its own keys)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    existing: dict[str, Any] = {}
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = {}
    existing.update(data)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, cls=_NumpyJSONEncoder)
    logger.info("Wrote %s", path)


def eta_squared_from_anova(groups: list[np.ndarray]) -> float:
    """Eta-squared effect size for a one-way ANOVA: SS_between / SS_total."""
    all_values = np.concatenate(groups)
    grand_mean = all_values.mean()
    ss_total = float(np.sum((all_values - grand_mean) ** 2))
    ss_between = float(sum(len(g) * (g.mean() - grand_mean) ** 2 for g in groups))
    return ss_between / ss_total if ss_total > 0 else float("nan")


def epsilon_squared_from_kruskal(h_statistic: float, n_total: int, k_groups: int) -> float:
    """Epsilon-squared effect size for Kruskal-Wallis: (H - k + 1) / (n - k)."""
    denom = n_total - k_groups
    return (h_statistic - k_groups + 1) / denom if denom > 0 else float("nan")


def cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    """Cohen's d for two independent samples, pooled standard deviation."""
    n1, n2 = len(a), len(b)
    var1, var2 = a.var(ddof=1), b.var(ddof=1)
    pooled_sd = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    return (a.mean() - b.mean()) / pooled_sd if pooled_sd > 0 else float("nan")


def classify_effect_size_eta_epsilon(value: float) -> str:
    """Cohen's conventional bands for eta-squared / epsilon-squared."""
    if np.isnan(value):
        return "undefined"
    if value < 0.01:
        return "negligible"
    if value < 0.06:
        return "small"
    if value < 0.14:
        return "medium"
    return "large"


def classify_effect_size_d(value: float) -> str:
    """Cohen's conventional bands for Cohen's d."""
    v = abs(value)
    if np.isnan(v):
        return "undefined"
    if v < 0.2:
        return "negligible"
    if v < 0.5:
        return "small"
    if v < 0.8:
        return "medium"
    return "large"


def classify_correlation_r(value: float) -> str:
    """Conventional bands for a Pearson/Spearman correlation coefficient magnitude."""
    v = abs(value)
    if np.isnan(v):
        return "undefined"
    if v < 0.1:
        return "negligible"
    if v < 0.3:
        return "weak"
    if v < 0.5:
        return "moderate"
    if v < 0.7:
        return "strong"
    return "very strong"
