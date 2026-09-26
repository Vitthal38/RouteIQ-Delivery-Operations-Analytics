"""Shared plotting theme and path setup for the RouteIQ JupyterLab notebooks.

Every notebook in this folder calls `setup_paths()` first (so it can import
the already-approved `python/` and `python/analysis/` modules without any
hardcoded absolute path) and then `apply_theme()` (so all 6 notebooks share
one consistent RouteIQ visual identity). This file contains no analytical
logic of its own — every calculation a notebook needs is imported from the
existing, approved `python/analysis/*.py` modules.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt

# RouteIQ semantic palette (matches the approved Power BI visual system):
#   Navy  = primary analytical series / structure
#   Teal  = positive / on-time / secondary series
#   Coral = SLA breach / risk / delay — never used for anything else
NAVY = "#123B5D"
TEAL = "#00A6A6"
CORAL = "#E45756"
BACKGROUND = "#F5F7F9"
TEXT = "#17212B"
TEXT_SOFT = "#6B7785"
GRID = "#D9E1E8"

# A muted sequential band, used only where more than 3 series must be told
# apart on one chart (e.g. per-category bars) and a single hue would be
# illegible — never used to encode breach/on-time status.
NEUTRAL_SEQUENCE = ["#123B5D", "#2C5678", "#5E84A0", "#8CA9C0", "#B7C9D8", "#D7E0E8"]


def setup_paths() -> Path:
    """Add `python/` and `python/analysis/` to sys.path and return the
    project root. Idempotent and safe to call at the top of every notebook.
    Resolves the project root from this file's own location — no path is
    hardcoded to a specific machine."""
    python_dir = Path(__file__).resolve().parent.parent
    project_root = python_dir.parent
    analysis_dir = python_dir / "analysis"
    for p in (str(python_dir), str(analysis_dir)):
        if p not in sys.path:
            sys.path.insert(0, p)
    return project_root


def apply_theme() -> None:
    """Apply the shared RouteIQ matplotlib theme. Deliberately restrained:
    no 3D, no gradients, no chart types beyond what matplotlib/seaborn offer
    natively for the approved chart list."""
    plt.rcParams.update({
        "figure.facecolor": BACKGROUND,
        "axes.facecolor": "white",
        "axes.edgecolor": GRID,
        "axes.labelcolor": TEXT,
        "axes.titlecolor": TEXT,
        "axes.titleweight": "bold",
        "axes.titlesize": 12,
        "axes.labelsize": 10.5,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": GRID,
        "grid.linewidth": 0.7,
        "text.color": TEXT,
        "xtick.color": TEXT_SOFT,
        "ytick.color": TEXT_SOFT,
        "font.size": 10,
        "font.family": "sans-serif",
        "legend.frameon": False,
        "savefig.facecolor": BACKGROUND,
    })


def annotate_bars(ax, bars, fmt: str = "{:.1f}%", color: str = TEXT, offset: float = 0.6) -> None:
    """Write a value label above each bar in `bars`. Small shared helper to
    avoid repeating the same 4-line loop in every chart cell."""
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2, height + offset,
            fmt.format(height), ha="center", va="bottom", fontsize=9, color=color,
        )


def sample_size_caption(ax, text: str) -> None:
    """Small italic sample-size / scope caption under the axes, consistent
    across every chart that needs one — this project's rule is that a rate
    or mean is never shown without its n being visible somewhere on/near
    the chart."""
    ax.text(
        0.0, -0.22, text, transform=ax.transAxes, fontsize=8.5,
        color=TEXT_SOFT, style="italic", ha="left", va="top",
    )
