"""Data-quality checks as a table (used by notebook 01; the same rules are enforced by tests/)."""

from __future__ import annotations

import numpy as np
import pandas as pd

VALID = {
    "Traffic": {"Low", "Medium", "High", "Jam"},
    "Weather": {"Sunny", "Cloudy", "Fog", "Windy", "Stormy", "Sandstorms"},
    "Area": {"Metropolitian", "Urban", "Semi-Urban", "Other"},
    "Vehicle": {"motorcycle", "scooter", "van"},
}


def data_quality_checks(cleaned: pd.DataFrame) -> pd.DataFrame:
    """One row per check: name, expected, actual, PASS/FAIL."""
    rows: list[tuple[str, object, object]] = []

    def add(name, expected, actual):
        rows.append((name, expected, actual))

    add("row count", 43_648, len(cleaned))
    add("duplicate Order_ID", 0, int(cleaned["Order_ID"].duplicated().sum()))
    add("fully duplicated records", 0, int(cleaned.duplicated().sum()))
    add("null key columns (Order_ID, date, category, area, traffic, weather, vehicle, delivery time)", 0,
        int(cleaned[["Order_ID", "Order_Date", "Category", "Area", "Traffic", "Weather", "Vehicle",
                     "Delivery_Time"]].isna().sum().sum()))
    for col, ok in VALID.items():
        add(f"{col}: values outside the documented set", 0, int((~cleaned[col].isin(ok)).sum()))
    add("categories", 16, int(cleaned["Category"].nunique()))
    add("delivery time <= 0", 0, int((cleaned["Delivery_Time"] <= 0).sum()))
    add("prep time < 0", 0, int((cleaned["prep_time_minutes"] < 0).sum()))
    add("order hour outside 0-23", 0, int((~cleaned["order_hour"].between(0, 23)).sum()))
    add("rating outside 1-5 (non-null)", 0, int((~cleaned["Agent_Rating"].dropna().between(1, 5)).sum()))
    add("age outside 18-65", 0, int((~cleaned["Agent_Age"].between(18, 65)).sum()))
    add("negative distance", 0, int((cleaned["distance_km"].dropna() < 0).sum()))
    recomputed = cleaned["Delivery_Time"] > cleaned["sla_threshold_minutes"]
    add("breach flag != (delivery time > threshold)", 0, int((recomputed != cleaned["sla_breach_flag"]).sum()))
    add("categories with more than one SLA threshold", 0,
        int((cleaned.groupby("Category")["sla_threshold_minutes"].nunique() > 1).sum()))
    p75 = cleaned.groupby("Category")["Delivery_Time"].apply(lambda s: np.percentile(s, 75))
    stored = cleaned.groupby("Category")["sla_threshold_minutes"].first()
    add("category thresholds != fresh P75", 0, int((~np.isclose(p75.sort_index(), stored.sort_index())).sum()))
    add("deliveries exactly at their threshold that are flagged as breaches", 0,
        int(cleaned.loc[cleaned["Delivery_Time"] == cleaned["sla_threshold_minutes"], "sla_breach_flag"].sum()))
    out = pd.DataFrame(rows, columns=["check", "expected", "actual"])
    out["status"] = np.where(out["expected"] == out["actual"], "PASS", "FAIL")
    return out


def exclusion_summary(cleaned: pd.DataFrame) -> pd.DataFrame:
    """Rows that are kept but excluded from specific analyses (never silently dropped)."""
    n = len(cleaned)
    items = [
        ("No valid agent rating", int((~cleaned["agent_rating_valid_flag"]).sum()), "rating analysis and driver model"),
        ("Invalid coordinates (distance unavailable)", int((~cleaned["coordinates_valid_flag"]).sum()), "distance analysis"),
        ("Area = Other (not a formal tier)", int((cleaned["Area"] == "Other").sum()), "tier comparisons (kept elsewhere)"),
        ("Area = Semi-Urban (n=152, 100% breach)", int((cleaned["Area"] == "Semi-Urban").sum()),
         "driver model (complete separation); reported descriptively"),
    ]
    out = pd.DataFrame(items, columns=["group", "rows", "excluded_from"])
    out["share_of_dataset_pct"] = 100 * out["rows"] / n
    return out
