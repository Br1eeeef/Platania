from __future__ import annotations

import hashlib
import math
import random
from datetime import date, datetime, timedelta

import pandas as pd

from api.app.models.market import Instrument

from .base import MarketDataProvider, validate_frame


class DemoProvider(MarketDataProvider):
    name = "deterministic-demo"
    live = False

    def fetch_daily(self, instrument: Instrument, start: date, end: date, adjustment: str = "qfq") -> pd.DataFrame:
        dates = pd.bdate_range(start=start, end=end)
        seed = int(hashlib.sha256(f"platania:{instrument.symbol}".encode()).hexdigest()[:12], 16)
        rng = random.Random(seed)
        start_price = {
            "600519.SH": 1480.0,
            "600036.SH": 31.0,
            "601318.SH": 43.0,
            "000333.SZ": 54.0,
            "300750.SZ": 188.0,
            "000001.SZ": 10.5,
            "000300.SH": 3700.0,
        }.get(instrument.symbol, 30.0)
        price = start_price
        rows: list[dict[str, object]] = []
        volatility = 0.010 if instrument.symbol == "000300.SH" else 0.016
        for index, day in enumerate(dates):
            regime = math.sin(index / 62 + seed % 19) * 0.0010
            shock = rng.gauss(0, volatility)
            overnight = rng.gauss(0, volatility * 0.25)
            suspended = instrument.symbol != "000300.SH" and index > 30 and index % 173 == seed % 173
            if suspended:
                rows.append(
                    {
                        "date": day,
                        "open": price,
                        "high": price,
                        "low": price,
                        "close": price,
                        "volume": 0,
                        "amount": 0,
                        "suspended": True,
                        "adjustment": adjustment,
                    }
                )
                continue
            open_price = max(0.5, price * (1 + overnight))
            close_price = max(0.5, price * (1 + 0.00025 + regime + shock))
            spread = abs(rng.gauss(volatility * 0.75, volatility * 0.3))
            high = max(open_price, close_price) * (1 + spread * rng.uniform(0.25, 0.8))
            low = min(open_price, close_price) * (1 - spread * rng.uniform(0.25, 0.8))
            base_volume = 520_000 + (seed % 23) * 31_000
            volume = max(50_000, int(base_volume * (1 + min(2.5, abs(shock) * 30) + rng.uniform(-0.2, 0.25))))
            rows.append(
                {
                    "date": day,
                    "open": round(open_price, 3),
                    "high": round(high, 3),
                    "low": round(low, 3),
                    "close": round(close_price, 3),
                    "volume": volume,
                    "amount": round(volume * close_price * 100, 2),
                    "suspended": False,
                    "adjustment": adjustment,
                }
            )
            price = close_price
        return validate_frame(pd.DataFrame(rows))

    def fetch_intraday(self, instrument: Instrument, interval: str, start: date, end: date) -> pd.DataFrame:
        minutes = int(interval)
        daily = self.fetch_daily(instrument, start - timedelta(days=5), end, adjustment="none").tail(8)
        rows: list[dict[str, object]] = []
        for daily_row in daily.itertuples():
            price = float(daily_row.open)
            target = float(daily_row.close)
            slots = list(range(0, 240, minutes))
            for slot_index, slot in enumerate(slots):
                hour = 9 + (30 + slot) // 60
                minute = (30 + slot) % 60
                if hour >= 12:
                    hour += 1
                timestamp = datetime.combine(daily_row.date.date(), datetime.min.time()).replace(hour=hour, minute=minute)
                progress = (slot_index + 1) / len(slots)
                close = price + (target - price) * progress
                rows.append(
                    {
                        "date": timestamp,
                        "open": price,
                        "high": max(price, close),
                        "low": min(price, close),
                        "close": close,
                        "volume": daily_row.volume / len(slots),
                        "amount": daily_row.amount / len(slots),
                        "suspended": daily_row.suspended,
                        "adjustment": "none",
                    }
                )
                price = close
        return validate_frame(pd.DataFrame(rows))
