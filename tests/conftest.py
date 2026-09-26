import pandas as pd
import pytest

from routeiq.config import CLEANED_DELIVERY_CSV, SLA_REFERENCE_CSV
from routeiq.features.analytical import build_analytical_dataset


@pytest.fixture(scope="session")
def cleaned() -> pd.DataFrame:
    return pd.read_csv(CLEANED_DELIVERY_CSV)


@pytest.fixture(scope="session")
def sla_reference() -> pd.DataFrame:
    return pd.read_csv(SLA_REFERENCE_CSV)


@pytest.fixture(scope="session")
def analytical(cleaned) -> pd.DataFrame:
    return build_analytical_dataset(cleaned)
