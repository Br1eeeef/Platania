from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta

import pandas as pd

from api.app.core.config import settings
from api.app.models.market import DataKind, DataMeta, Instrument

from .akshare_provider import AkshareProvider
from .baostock_provider import BaostockProvider
from .base import MarketDataProvider, ProviderError
from .cache import ParquetCache
from .catalog import get_instrument
from .demo import DemoProvider

logger = logging.getLogger(__name__)


class MarketDataService:
    def __init__(
        self,
        cache: ParquetCache | None = None,
        live_providers: list[MarketDataProvider] | None = None,
        demo_provider: MarketDataProvider | None = None,
    ) -> None:
        self.cache = cache or ParquetCache(settings.cache_dir, settings.cache_ttl_hours)
        self.live_providers = live_providers or [AkshareProvider(), BaostockProvider()]
        self.demo_provider = demo_provider or DemoProvider()

    def load(self, symbol: str, lookback_days: int = 900, timeframe: str = "1d") -> tuple[Instrument, pd.DataFrame, DataMeta]:
        instrument = get_instrument(symbol)
        cached = self.cache.read(instrument.symbol, timeframe)
        if cached:
            frame, meta = cached
            if timeframe != "1d":
                meta.is_stale = datetime.now(UTC) - meta.updated_at.astimezone(UTC) > timedelta(
                    seconds=settings.realtime_cache_ttl_seconds
                )
                if meta.is_stale and not settings.demo_mode:
                    try:
                        return self.refresh(symbol, timeframe=timeframe)
                    except ProviderError:
                        pass
            if meta.is_stale:
                meta.warnings.append("缓存已过期，仍返回最后可用数据；等待定时任务或手动刷新")
            return instrument, frame, meta
        if not settings.demo_mode and settings.on_demand_live_refresh:
            return self.refresh(symbol, timeframe=timeframe)
        end = date.today()
        frame = self.demo_provider.fetch_daily(instrument, end - timedelta(days=lookback_days), end)
        meta = DataMeta(
            provider=self.demo_provider.name,
            kind=DataKind.DEMO,
            updated_at=datetime.now(UTC),
            timeframe=timeframe,
            warnings=["演示数据由固定随机种子生成，不是真实行情"],
        )
        self.cache.write(instrument.symbol, frame, meta, timeframe)
        return instrument, frame, meta

    def refresh(self, symbol: str, force_demo: bool = False, timeframe: str = "1d") -> tuple[Instrument, pd.DataFrame, DataMeta]:
        instrument = get_instrument(symbol)
        end = date.today()
        existing = self.cache.read(instrument.symbol, timeframe)
        start = end - timedelta(days=900 if timeframe == "1d" else 10)
        existing_is_live = bool(existing and not existing[0].empty and existing[1].kind == DataKind.LIVE)
        if existing_is_live and existing:
            start = existing[0]["date"].max().date() - timedelta(days=5 if timeframe == "1d" else 2)

        providers = [] if force_demo or settings.demo_mode else self.live_providers
        warnings: list[str] = []
        for provider in providers:
            try:
                frame = (
                    provider.fetch_daily(instrument, start, end)
                    if timeframe == "1d"
                    else provider.fetch_intraday(instrument, timeframe, start, end)
                )
                meta = DataMeta(
                    provider=provider.name,
                    kind=DataKind.LIVE,
                    updated_at=datetime.now(UTC),
                    timeframe=timeframe,
                    warnings=warnings,
                )
                if existing_is_live:
                    frame = self.cache.merge(instrument.symbol, frame, meta, timeframe)
                else:
                    self.cache.write(instrument.symbol, frame, meta, timeframe)
                return instrument, frame, meta
            except ProviderError as exc:
                logger.warning(
                    "provider_failed provider=%s symbol=%s error=%s", provider.name, instrument.symbol, type(exc).__name__
                )
                warnings.append(f"{provider.name} 不可用，已尝试下一数据源")

        if existing and not existing[0].empty:
            cached_frame, cached_meta = existing
            cached_meta.is_stale = True
            cached_meta.warnings.extend(warnings)
            cached_meta.warnings.append("实时数据源暂不可用，继续展示最后一次成功同步的数据。")
            return instrument, cached_frame, cached_meta

        frame = (
            self.demo_provider.fetch_daily(instrument, end - timedelta(days=900), end)
            if timeframe == "1d"
            else self.demo_provider.fetch_intraday(instrument, timeframe, end - timedelta(days=10), end)
        )
        warnings.append("真实数据源不可用，已明确回退到确定性演示数据")
        meta = DataMeta(
            provider=self.demo_provider.name,
            kind=DataKind.DEMO,
            updated_at=datetime.now(UTC),
            timeframe=timeframe,
            warnings=warnings,
        )
        self.cache.write(instrument.symbol, frame, meta, timeframe)
        return instrument, frame, meta

    @staticmethod
    def resample(frame: pd.DataFrame, period: str) -> pd.DataFrame:
        if period == "1d":
            return frame.copy()
        if period != "1w":
            raise ValueError("period must be 1d or 1w")
        weekly = (
            frame.set_index("date")
            .resample("W-FRI")
            .agg(
                {
                    "open": "first",
                    "high": "max",
                    "low": "min",
                    "close": "last",
                    "volume": "sum",
                    "amount": "sum",
                    "suspended": "all",
                    "adjustment": "last",
                }
            )
            .dropna(subset=["open", "close"])
            .reset_index()
        )
        return weekly


market_data_service = MarketDataService()
