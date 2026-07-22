from __future__ import annotations

import sys
from datetime import UTC, date, datetime
from types import SimpleNamespace

import pandas as pd
import pytest

from api.app.data_sources.akshare_provider import AkshareProvider
from api.app.data_sources.base import ProviderError, validate_frame
from api.app.data_sources.cache import ParquetCache
from api.app.data_sources.catalog import get_instrument, normalize_symbol
from api.app.data_sources.rate_limit import RateLimiter
from api.app.models.market import DataKind, DataMeta


def test_symbol_normalization() -> None:
    assert normalize_symbol("600519") == "600519.SH"
    assert normalize_symbol("sz000333") == "000333.SZ"
    with pytest.raises(ValueError):
        normalize_symbol("999999")


def test_akshare_chinese_fields_are_normalized(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = pd.DataFrame([{"日期": "2026-01-05", "开盘": 10, "最高": 11, "最低": 9, "收盘": 10.5, "成交量": 1000, "成交额": 10500}])
    monkeypatch.setitem(sys.modules, "akshare", SimpleNamespace(stock_zh_a_hist=lambda **_: raw))
    provider = AkshareProvider()
    provider.limiter.minimum_interval = 0
    result = provider.fetch_daily(get_instrument("600519.SH"), date(2026, 1, 1), date(2026, 1, 6))
    assert list(result.columns) == ["date", "open", "high", "low", "close", "volume", "amount", "suspended", "adjustment"]
    assert result.iloc[0]["close"] == 10.5


def test_integrity_check_rejects_invalid_ohlc() -> None:
    invalid = pd.DataFrame(
        [
            {
                "date": "2026-01-01",
                "open": 10,
                "high": 9,
                "low": 8,
                "close": 10,
                "volume": 1,
                "amount": 1,
                "suspended": False,
                "adjustment": "qfq",
            }
        ]
    )
    with pytest.raises(ProviderError):
        validate_frame(invalid)


def test_parquet_cache_tracks_staleness(tmp_path, demo_frame: pd.DataFrame) -> None:
    cache = ParquetCache(tmp_path, ttl_hours=1)
    meta = DataMeta(provider="test", kind=DataKind.DEMO, updated_at=datetime.now(UTC))
    cache.write("600036.SH", demo_frame, meta)
    loaded = cache.read("600036.SH")
    assert loaded is not None
    assert len(loaded[0]) == len(demo_frame)
    assert loaded[1].is_stale is False


def test_rate_limiter_waits_only_for_remaining_interval(monkeypatch: pytest.MonkeyPatch) -> None:
    timeline = iter([10.0, 10.2])
    sleeps: list[float] = []
    monkeypatch.setattr("api.app.data_sources.rate_limit.time.monotonic", lambda: next(timeline))
    monkeypatch.setattr("api.app.data_sources.rate_limit.time.sleep", sleeps.append)
    limiter = RateLimiter(1.0)
    limiter._last_call = 9.5
    limiter.wait()
    assert sleeps == [0.5]
