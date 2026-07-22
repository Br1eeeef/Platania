from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import pytest

from api.app.data_sources.catalog import get_instrument
from api.app.data_sources.demo import DemoProvider


@pytest.fixture
def demo_frame() -> pd.DataFrame:
    end = date(2026, 7, 22)
    return DemoProvider().fetch_daily(get_instrument("600036.SH"), end - timedelta(days=900), end)


@pytest.fixture
def benchmark_frame() -> pd.DataFrame:
    end = date(2026, 7, 22)
    return DemoProvider().fetch_daily(get_instrument("000300.SH"), end - timedelta(days=900), end)
