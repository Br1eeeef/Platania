from __future__ import annotations

import os
from datetime import date, timedelta

import pandas as pd
import pytest

# Tests must remain deterministic even when the developer has configured real services in .env.
os.environ.update(
    {
        "PLATANIA_ENV": "development",
        "SUPABASE_URL": "",
        "SUPABASE_SECRET_KEY": "",
        "SUPABASE_SERVICE_ROLE_KEY": "",
        "SUPABASE_JWT_SECRET": "",
        "DEEPSEEK_API_KEY": "",
    }
)

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
