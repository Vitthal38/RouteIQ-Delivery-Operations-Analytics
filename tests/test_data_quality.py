"""Data-quality gates on the frozen cleaned dataset and the analytical table."""
import numpy as np
import pandas as pd

TRAFFIC = {"Low", "Medium", "High", "Jam"}
WEATHER = {"Sunny", "Cloudy", "Fog", "Windy", "Stormy", "Sandstorms"}
AREA = {"Metropolitian", "Urban", "Semi-Urban", "Other"}  # 'Metropolitian' is the source spelling
VEHICLE = {"motorcycle", "scooter", "van"}                 # no bicycle rows survive cleaning


def test_expected_row_count(cleaned):
    assert len(cleaned) == 43_648


def test_order_id_unique_and_no_null_keys(cleaned):
    assert cleaned["Order_ID"].is_unique
    key_cols = ["Order_ID", "Order_Date", "Category", "Area", "Traffic", "Weather", "Vehicle", "Delivery_Time"]
    assert cleaned[key_cols].notna().all().all()


def test_no_duplicate_records(cleaned):
    assert not cleaned.duplicated().any()


def test_valid_categorical_values(cleaned):
    assert set(cleaned["Traffic"]) == TRAFFIC
    assert set(cleaned["Weather"]) == WEATHER
    assert set(cleaned["Area"]) == AREA
    assert set(cleaned["Vehicle"]) == VEHICLE
    assert cleaned["Category"].nunique() == 16


def test_numeric_ranges(cleaned):
    assert (cleaned["Delivery_Time"] > 0).all()
    assert (cleaned["prep_time_minutes"] >= 0).all()
    assert cleaned["order_hour"].between(0, 23).all()
    assert cleaned["Agent_Rating"].dropna().between(1, 5).all()
    assert cleaned["Agent_Age"].between(18, 65).all()
    assert (cleaned["distance_km"].dropna() >= 0).all()


def test_sla_threshold_is_single_valued_per_category_and_equals_p75(cleaned, sla_reference):
    per_cat = cleaned.groupby("Category")["sla_threshold_minutes"].nunique()
    assert (per_cat == 1).all()
    p75 = cleaned.groupby("Category")["Delivery_Time"].apply(lambda s: np.percentile(s, 75))
    stored = cleaned.groupby("Category")["sla_threshold_minutes"].first()
    assert np.allclose(p75.sort_index().to_numpy(), stored.sort_index().to_numpy())
    ref = sla_reference.set_index("Category")["sla_threshold_minutes"]
    assert np.allclose(ref.sort_index().to_numpy(float), stored.sort_index().to_numpy(float))
    assert sla_reference["row_count"].sum() == 43_648


def test_breach_flag_consistent_with_threshold_strictly_greater(cleaned):
    recomputed = cleaned["Delivery_Time"] > cleaned["sla_threshold_minutes"]
    assert (recomputed == cleaned["sla_breach_flag"]).all()
    equal = cleaned["Delivery_Time"] == cleaned["sla_threshold_minutes"]
    assert equal.sum() > 0 and not cleaned.loc[equal, "sla_breach_flag"].any()  # equality is on time


def test_denominators_add_up(analytical):
    n = len(analytical)
    for col in ("traffic", "weather", "area", "vehicle", "category", "hour_band"):
        assert analytical.groupby(col).size().sum() == n
    on_time = (analytical["breach_flag"] == 0).sum()
    assert on_time + analytical["breach_flag"].sum() == n


def test_analytical_table_shape_and_missingness(analytical):
    assert len(analytical) == 43_648
    assert analytical["agent_rating"].isna().sum() == 54
    assert analytical["rating_lt_4_5"].isna().sum() == 54
    assert analytical["distance_km"].isna().sum() == 3_651
    assert analytical["order_id"].is_unique
