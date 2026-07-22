from __future__ import annotations

import json
import math
import random
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from .catalog import get_stock
from .config import settings


Bar = dict[str, Any]


class MarketDataError(RuntimeError):
    pass


class MarketDataRepository:
    def __init__(self, cache_dir: Path | None = None) -> None:
        self.cache_dir = cache_dir or settings.cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def load(self, symbol: str, *, minimum_bars: int = 260) -> tuple[list[Bar], dict[str, Any]]:
        get_stock(symbol)
        cached = self._read_cache(symbol)
        if cached and len(cached["bars"]) >= minimum_bars:
            return cached["bars"], cached["meta"]

        bars = generate_demo_bars(symbol)
        meta = {
            "source": "demo",
            "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "is_demo": True,
        }
        self._write_cache(symbol, bars, meta)
        return bars, meta

    def refresh(self, symbol: str, source: str = "auto") -> tuple[list[Bar], dict[str, Any]]:
        get_stock(symbol)
        requested_source = source if source != "auto" else settings.data_source
        if requested_source in {"auto", "akshare"}:
            try:
                bars = fetch_akshare_daily(symbol)
                meta = {
                    "source": "akshare",
                    "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                    "is_demo": False,
                }
                self._write_cache(symbol, bars, meta)
                return bars, meta
            except (ImportError, MarketDataError) as exc:
                if requested_source == "akshare":
                    raise MarketDataError(str(exc)) from exc

        bars = generate_demo_bars(symbol)
        meta = {
            "source": "demo",
            "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "is_demo": True,
        }
        self._write_cache(symbol, bars, meta)
        return bars, meta

    def _cache_path(self, symbol: str) -> Path:
        return self.cache_dir / f"{symbol}.json"

    def _read_cache(self, symbol: str) -> dict[str, Any] | None:
        path = self._cache_path(symbol)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload.get("bars"), list) or not payload["bars"]:
                return None
            return payload
        except (OSError, json.JSONDecodeError, TypeError):
            return None

    def _write_cache(self, symbol: str, bars: list[Bar], meta: dict[str, Any]) -> None:
        path = self._cache_path(symbol)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps({"meta": meta, "bars": bars}, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        temporary.replace(path)


def fetch_akshare_daily(symbol: str, days: int = 520) -> list[Bar]:
    try:
        import akshare as ak
    except ImportError as exc:
        raise ImportError("AKShare 未安装；运行 pip install akshare 后再刷新真实行情") from exc

    end = date.today()
    start = end - timedelta(days=int(days * 1.7))
    try:
        frame = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start.strftime("%Y%m%d"),
            end_date=end.strftime("%Y%m%d"),
            adjust="qfq",
        )
    except Exception as exc:  # Provider errors vary across AKShare releases.
        raise MarketDataError(f"AKShare 请求失败：{exc}") from exc

    if frame is None or frame.empty:
        raise MarketDataError("AKShare 未返回行情数据")

    required = {"日期", "开盘", "收盘", "最高", "最低", "成交量", "成交额"}
    if not required.issubset(frame.columns):
        raise MarketDataError("AKShare 返回字段与预期不一致")

    bars: list[Bar] = []
    for row in frame.to_dict(orient="records"):
        bars.append(
            {
                "date": str(row["日期"])[:10],
                "open": round(float(row["开盘"]), 3),
                "high": round(float(row["最高"]), 3),
                "low": round(float(row["最低"]), 3),
                "close": round(float(row["收盘"]), 3),
                "volume": int(float(row["成交量"])),
                "amount": round(float(row["成交额"]), 2),
            }
        )
    if len(bars) < 130:
        raise MarketDataError("有效交易日不足 130 天，无法运行策略")
    return bars


def generate_demo_bars(symbol: str, count: int = 520) -> list[Bar]:
    """Generate reproducible OHLCV data with realistic trend regimes."""
    seed = int(symbol) * 97 + 20260722
    rng = random.Random(seed)
    start_prices = {
        "600519": 1480.0,
        "600036": 31.0,
        "601318": 43.0,
        "000333": 54.0,
        "300750": 188.0,
        "000001": 10.5,
    }
    price = start_prices.get(symbol, 25.0)
    calendar_days = _business_days(date.today(), count)
    bars: list[Bar] = []

    for index, day in enumerate(calendar_days):
        regime = math.sin(index / 58 + (seed % 13)) * 0.0009
        drift = 0.00028 + regime
        shock = rng.gauss(0, 0.014 if symbol != "300750" else 0.021)
        overnight = rng.gauss(0, 0.0045)
        open_price = max(1.0, price * (1 + overnight))
        close_price = max(1.0, price * (1 + drift + shock))
        spread = abs(rng.gauss(0.012, 0.005))
        high = max(open_price, close_price) * (1 + spread * rng.uniform(0.25, 0.85))
        low = min(open_price, close_price) * (1 - spread * rng.uniform(0.25, 0.85))
        base_volume = 480_000 + (seed % 17) * 35_000
        volume_multiplier = 1 + min(2.8, abs(shock) * 30) + rng.uniform(-0.22, 0.28)
        volume = max(60_000, int(base_volume * volume_multiplier))
        bars.append(
            {
                "date": day.isoformat(),
                "open": round(open_price, 3),
                "high": round(high, 3),
                "low": round(low, 3),
                "close": round(close_price, 3),
                "volume": volume,
                "amount": round(volume * close_price * 100, 2),
            }
        )
        price = close_price
    return bars


def _business_days(end: date, count: int) -> list[date]:
    days: list[date] = []
    current = end
    while len(days) < count:
        if current.weekday() < 5:
            days.append(current)
        current -= timedelta(days=1)
    return list(reversed(days))

