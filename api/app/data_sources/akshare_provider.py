from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from datetime import date

import pandas as pd
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from api.app.core.config import settings
from api.app.models.market import Instrument

from .base import MarketDataProvider, ProviderError, ProviderUnavailable, validate_frame
from .rate_limit import RateLimiter

FIELD_MAP = {
    "日期": "date",
    "开盘": "open",
    "最高": "high",
    "最低": "low",
    "收盘": "close",
    "成交量": "volume",
    "成交额": "amount",
}


class AkshareProvider(MarketDataProvider):
    name = "akshare"

    def __init__(self) -> None:
        self.limiter = RateLimiter(settings.provider_min_interval_seconds)

    @retry(
        retry=retry_if_exception_type((ProviderUnavailable, ProviderError)),
        stop=stop_after_attempt(settings.provider_max_retries),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    def fetch_daily(self, instrument: Instrument, start: date, end: date, adjustment: str = "qfq") -> pd.DataFrame:
        try:
            import akshare as ak
        except ImportError as exc:
            raise ProviderUnavailable("AKShare is not installed") from exc
        self.limiter.wait()

        def request() -> pd.DataFrame:
            return ak.stock_zh_a_hist(
                symbol=instrument.code,
                period="daily",
                start_date=start.strftime("%Y%m%d"),
                end_date=end.strftime("%Y%m%d"),
                adjust=adjustment,
            )

        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(request)
        try:
            raw = future.result(timeout=settings.provider_timeout_seconds)
        except FutureTimeoutError as exc:
            future.cancel()
            raise ProviderUnavailable(f"AKShare timed out after {settings.provider_timeout_seconds}s") from exc
        except Exception as exc:
            raise ProviderUnavailable(f"AKShare request failed: {type(exc).__name__}") from exc
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
        if raw is None or raw.empty:
            raise ProviderUnavailable("AKShare returned no rows")
        missing = set(FIELD_MAP) - set(raw.columns)
        if missing:
            raise ProviderError(f"AKShare fields changed: {sorted(missing)}")
        frame = raw.rename(columns=FIELD_MAP)[list(FIELD_MAP.values())].copy()
        frame["suspended"] = frame["volume"].fillna(0).eq(0)
        frame["adjustment"] = adjustment
        return validate_frame(frame)
