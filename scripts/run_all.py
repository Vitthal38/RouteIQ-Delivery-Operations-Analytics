"""One command to rebuild every analytical output and run the validation suite.

Usage:  python scripts/run_all.py            # analysis + tests
        python scripts/run_all.py --sql      # also (re)create the SQL view and run Q23-Q29 (needs PGPASSWORD etc.)

Steps: (1) analytical dataset, tables, figures, results.json  (2) optional SQL run
       (3) four-layer reconciliation  (4) pytest
The frozen cleaned dataset (data/processed/cleaned_delivery.csv) is read, never rewritten.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sql", action="store_true", help="run the SQL layer against PostgreSQL first")
    args = ap.parse_args()

    from routeiq.analysis.run import run_all
    run_all()

    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    if args.sql:
        subprocess.run([sys.executable, str(ROOT / "scripts" / "run_sql.py")], check=True, env=env)

    from routeiq.validation.reconcile import run_reconciliation
    rec = run_reconciliation()
    print(f"reconciliation: {rec['status'].value_counts().to_dict()}")

    code = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT, env=env).returncode
    return code


if __name__ == "__main__":
    sys.exit(main())
