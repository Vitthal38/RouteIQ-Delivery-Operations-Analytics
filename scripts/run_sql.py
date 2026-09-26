"""Create the analytical view and run the new SQL analysis (Q23-Q30) against PostgreSQL.

Connection comes from the standard libpq environment variables (never stored in the repo):
    PGHOST (default localhost)  PGPORT (5432)  PGDATABASE (postgres)  PGUSER (postgres)  PGPASSWORD

Usage:  python scripts/run_sql.py [--skip-view]
Writes: outputs/sql_results/Qxx_*.csv   (Q29 is summarised, not dumped: 43k rows)
"""
import argparse
import os
import sys
from decimal import Decimal
from pathlib import Path

import pandas as pd
import psycopg2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from routeiq.config import SQL_RESULTS_DIR  # noqa: E402

QUERIES = sorted((ROOT / "sql" / "analysis").glob("Q2[3-9]_*.sql")) + sorted((ROOT / "sql" / "analysis").glob("Q30_*.sql"))


def connect():
    return psycopg2.connect(host=os.environ.get("PGHOST", "localhost"), port=os.environ.get("PGPORT", "5432"),
                            dbname=os.environ.get("PGDATABASE", "postgres"), user=os.environ.get("PGUSER", "postgres"),
                            password=os.environ.get("PGPASSWORD"))


def to_frame(cur) -> pd.DataFrame:
    cols = [d.name for d in cur.description]
    rows = [[float(v) if isinstance(v, Decimal) else v for v in r] for r in cur.fetchall()]
    return pd.DataFrame(rows, columns=cols)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-view", action="store_true", help="do not (re)create vw_analytical_deliveries")
    args = ap.parse_args()
    SQL_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.autocommit = True
        cur = conn.cursor()
        if not args.skip_view:
            cur.execute((ROOT / "sql" / "schema" / "09_create_analytical_view.sql").read_text(encoding="utf-8"))
            print("created view routeiq.vw_analytical_deliveries")
        for path in QUERIES:
            cur.execute(path.read_text(encoding="utf-8"))
            df = to_frame(cur)
            out = SQL_RESULTS_DIR / f"{path.stem}.csv"
            if path.stem.startswith("Q29"):
                summary = {"rows": len(df), "events": int(df["y"].sum())}
                for c in df.columns:
                    if c not in ("order_id", "order_date", "hour_band"):
                        summary[f"sum_{c}"] = float(df[c].sum())
                pd.DataFrame([summary]).to_csv(out, index=False)
            else:
                df.to_csv(out, index=False)
            print(f"{path.stem}: {len(df)} rows -> {out.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
