import numpy as np
import pandas as pd
import pytest

from routeiq.config import ANALYTICAL_DATASET_CSV
from routeiq.features.analytical import (
    ANALYTICAL_COLUMNS, FEATURE_DEFINITIONS, PEAK_HOURS, build_analytical_dataset, derive_peak_hours, hour_band,
)


def test_every_column_is_documented():
    assert set(ANALYTICAL_COLUMNS) == set(FEATURE_DEFINITIONS)


def test_peak_hours_rule_matches_constant(analytical):
    assert derive_peak_hours(analytical["order_hour"]) == PEAK_HOURS == tuple(range(17, 24))


@pytest.mark.parametrize("hour,band", [(0, "1_00-07 overnight"), (8, "2_08-10 morning"), (11, "3_11-14 midday"),
                                       (15, "4_15-16 afternoon"), (18, "5_17-18 early evening"),
                                       (19, "6_19-21 evening peak"), (23, "7_22-23 late evening")])
def test_hour_band_edges(hour, band):
    assert hour_band(hour) == band


def test_step_flags(analytical):
    rated = analytical["agent_rating"].notna()
    expected = (analytical.loc[rated, "agent_rating"] < 4.5).astype(int)
    assert (expected == analytical.loc[rated, "rating_lt_4_5"]).all()
    assert ((analytical["agent_age"] >= 30).astype(int) == analytical["age_ge_30"]).all()


def test_minutes_over_sla(analytical):
    assert (analytical["minutes_over_sla"] >= 0).all()
    assert (analytical.loc[analytical["breach_flag"] == 0, "minutes_over_sla"] == 0).all()
    assert (analytical.loc[analytical["breach_flag"] == 1, "minutes_over_sla"] > 0).all()


def test_build_is_deterministic_and_matches_saved_file(cleaned):
    a, b = build_analytical_dataset(cleaned), build_analytical_dataset(cleaned)
    pd.testing.assert_frame_equal(a, b)
    if ANALYTICAL_DATASET_CSV.exists():
        saved = pd.read_csv(ANALYTICAL_DATASET_CSV)
        assert len(saved) == len(a)
        assert (saved["breach_flag"].to_numpy() == a["breach_flag"].to_numpy()).all()
        assert np.allclose(saved["delivery_time_minutes"], a["delivery_time_minutes"])
