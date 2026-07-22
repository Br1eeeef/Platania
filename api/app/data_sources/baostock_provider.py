from __future__ import annotations

from datetime import date

import pandas as pd
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from api.app.core.config import settings
from api.app.models.market import Instrument

from .base import MarketDataProvider, ProviderError, ProviderUnavailable, validate_frame
from .rate_limit import RateLimiter


class BaostockProvider(MarketDataProvider):
    name = "baostock"

    def __init__(self) -> None:
        self.limiter = RateLimiter(settings.provider_min_interval_seconds)

    @retry(
        retry=retry_if_exception_type(ProviderUnavailable),
        stop=stop_after_attempt(settings.provider_max_retries),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    def fetch_daily(self, instrument: Instrument, start: date, end: date, adjustment: str = "qfq") -> pd.DataFrame:
        try:
            import baostock as bs
        except ImportError as exc:
            raise ProviderUnavailable("BaoStock is not installed") from exc
        self.limiter.wait()
        login = bs.login()
        if login.error_code != "0":
            raise ProviderUnavailable("BaoStock login failed")
        try:
            query = bs.query_history_k_data_plus(
                f"{instrument.exchange.lower()}.{instrument.code}",
                "date,open,high,low,close,volume,amount,tradestatus",
                start_date=start.isoformat(),
                end_date=end.isoformat(),
                frequency="d",
                adjustflag={"hfq": "1", "qfq": "2", "none": "3"}.get(adjustment, "2"),
            )
            if query.error_code != "0":
                raise ProviderUnavailable("BaoStock query failed")
            rows: list[list[str]] = []
            while query.next():
                rows.append(query.get_row_data())
        finally:
            bs.logout()
        if not rows:
            raise ProviderUnavailable("BaoStock returned no rows")
        raw = pd.DataFrame(rows, columns=query.fields)
        raw["suspended"] = raw["tradestatus"].ne("1") | pd.to_numeric(raw["volume"], errors="coerce").fillna(0).eq(0)
        raw["adjustment"] = adjustment
        try:
            return validate_frame(raw.drop(columns=["tradestatus"]))
        except (ValueError, TypeError) as exc:
            raise ProviderError("BaoStock returned invalid data") from exc
