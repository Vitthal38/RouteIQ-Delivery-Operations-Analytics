"""Rebuild the analytical dataset and every table, figure and results.json.

Usage:  python scripts/run_analysis.py
Reads   data/processed/cleaned_delivery.csv (frozen cleaned data)
Writes  data/processed/analytical_deliveries.csv, outputs/tables/*.csv,
        outputs/figures/*.png, outputs/results.json
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from routeiq.analysis.run import run_all  # noqa: E402

if __name__ == "__main__":
    run_all()
