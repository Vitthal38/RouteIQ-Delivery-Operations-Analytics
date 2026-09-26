"""Can the frozen cleaned dataset be reproduced from the raw file? (Skipped when raw data is absent.)"""
import numpy as np
import pandas as pd
import pytest

from routeiq.config import CLEANED_DELIVERY_CSV, RAW_DATA_CSV, SOURCE_RAW_CSV, SLA_REFERENCE_CSV

pytestmark = pytest.mark.raw_data


@pytest.mark.skipif(not (RAW_DATA_CSV.exists() or SOURCE_RAW_CSV.exists()),
                    reason="raw Kaggle file not present (see data/README.md)")
def test_raw_to_cleaned_reproduces_frozen_dataset():
    from routeiq.cleaning.pipeline import rebuild_cleaned_dataframe
    rebuilt, sla_ref = rebuild_cleaned_dataframe()
    stored = pd.read_csv(CLEANED_DELIVERY_CSV)
    assert len(rebuilt) == len(stored) == 43_648
    assert list(rebuilt.columns) == list(stored.columns)
    for col in stored.columns:
        a, b = rebuilt[col].reset_index(drop=True), stored[col].reset_index(drop=True)
        if pd.api.types.is_float_dtype(b) or pd.api.types.is_float_dtype(a):
            assert np.allclose(a.astype(float), b.astype(float), equal_nan=True, atol=1e-9), col
        else:
            assert (a.astype(str) == b.astype(str)).all(), col
    ref_stored = pd.read_csv(SLA_REFERENCE_CSV)
    assert len(sla_ref) == len(ref_stored) == 16
