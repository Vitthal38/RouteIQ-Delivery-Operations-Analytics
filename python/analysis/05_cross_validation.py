"""Phase 4, Module 5 — Independent Python reproduction of core SQL KPIs.

Every figure below is computed fresh from data/cleaned/cleaned_delivery.csv
with pandas — none of it is copied from any SQL report text. This is what
reports/python_sql_cross_validation.md's comparison table is built from.
"""

from __future__ import annotations

from typing import Any

from _common import load_cleaned_data, logger, save_json
from config import EDA_SUMMARY_JSON


def main() -> dict[str, Any]:
    df = load_cleaned_data()

    results: dict[str, Any] = {
        "total_deliveries": int(len(df)),
        "distinct_order_ids": int(df["Order_ID"].nunique()),
        "total_breaches": int(df["sla_breach_flag"].sum()),
        "overall_breach_rate_pct": round(float(df["sla_breach_flag"].mean() * 100), 4),
        "breach_rate_by_area_pct": {
            k: round(float(v), 4)
            for k, v in (df.groupby("Area")["sla_breach_flag"].mean() * 100).to_dict().items()
        },
        "category_counts": df["Category"].value_counts().to_dict(),
        "vehicle_counts": df["Vehicle"].value_counts().to_dict(),
        "area_counts": df["Area"].value_counts().to_dict(),
        "weather_counts": df["Weather"].value_counts().to_dict(),
        "traffic_counts": df["Traffic"].value_counts().to_dict(),
        "weekday_avg_delivery_time": round(
            float(df.loc[~df["is_weekend"], "Delivery_Time"].mean()), 4
        ),
        "weekend_avg_delivery_time": round(
            float(df.loc[df["is_weekend"], "Delivery_Time"].mean()), 4
        ),
        "weekday_count": int((~df["is_weekend"]).sum()),
        "weekend_count": int(df["is_weekend"].sum()),
        "breach_count_by_weather": df.groupby("Weather")["sla_breach_flag"].sum().to_dict(),
        "sla_threshold_by_category": (
            df.groupby("Category")["sla_threshold_minutes"].agg(lambda s: s.unique()[0]).to_dict()
        ),
        "sla_threshold_category_has_single_value": bool(
            (df.groupby("Category")["sla_threshold_minutes"].nunique() == 1).all()
        ),
        "distance_valid_row_count": int(df["coordinates_valid_flag"].sum()),
        "agent_rating_valid_row_count": int(df["agent_rating_valid_flag"].sum()),
    }

    save_json({"05_cross_validation": results}, EDA_SUMMARY_JSON)
    logger.info("Module 5 (cross-validation figures) complete: %d top-level keys", len(results))
    return results


if __name__ == "__main__":
    main()
