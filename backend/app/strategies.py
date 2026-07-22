from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .indicators import atr, rolling_max, rolling_std, rsi, sma


StrategyName = Literal["trend", "breakout", "mean_reversion"]


STRATEGIES: dict[StrategyName, dict[str, str]] = {
    "trend": {"name": "均线趋势", "description": "20/60 日均线多头排列并用 120 日趋势过滤"},
    "breakout": {"name": "放量突破", "description": "突破 20 日高点、成交量确认，跌破 20 日线离场"},
    "mean_reversion": {"name": "趋势内回归", "description": "长期趋势向上时捕捉 RSI 与布林带的短期超卖"},
}


@dataclass(frozen=True)
class StrategyResult:
    positions: list[int]
    entries: list[bool]
    exits: list[bool]
    indicators: dict[str, list[float | None]]


def evaluate_strategy(bars: list[dict[str, Any]], strategy: StrategyName) -> StrategyResult:
    if strategy not in STRATEGIES:
        raise ValueError(f"unknown strategy: {strategy}")
    closes = [float(bar["close"]) for bar in bars]
    highs = [float(bar["high"]) for bar in bars]
    lows = [float(bar["low"]) for bar in bars]
    volumes = [float(bar["volume"]) for bar in bars]

    ma20 = sma(closes, 20)
    ma60 = sma(closes, 60)
    ma120 = sma(closes, 120)
    rsi14 = rsi(closes, 14)
    atr14 = atr(highs, lows, closes, 14)
    volume_ma20 = sma(volumes, 20)
    std20 = rolling_std(closes, 20)
    high20 = rolling_max(highs, 20)
    upper = [None if mean is None or deviation is None else mean + 2 * deviation for mean, deviation in zip(ma20, std20)]
    lower = [None if mean is None or deviation is None else mean - 2 * deviation for mean, deviation in zip(ma20, std20)]
    volume_ratio = [
        None if average in {None, 0} else volume / float(average)
        for volume, average in zip(volumes, volume_ma20)
    ]

    positions = [0] * len(bars)
    entries = [False] * len(bars)
    exits = [False] * len(bars)
    holding = False
    entry_price = 0.0

    for index, close in enumerate(closes):
        ready = ma120[index] is not None
        enter = False
        leave = False
        if ready and strategy == "trend":
            assert ma20[index] is not None and ma60[index] is not None and ma120[index] is not None
            slope_up = index >= 65 and ma60[index - 5] is not None and ma60[index] > ma60[index - 5]
            enter = close > ma20[index] > ma60[index] > ma120[index] and slope_up
            leave = close < ma20[index] or ma20[index] < ma60[index]
        elif ready and strategy == "breakout":
            previous_high = high20[index - 1] if index else None
            enter = previous_high is not None and close > previous_high and (volume_ratio[index] or 0) >= 1.25
            leave = ma20[index] is not None and (close < ma20[index] or (holding and close < entry_price * 0.91))
        elif ready and strategy == "mean_reversion":
            assert ma120[index] is not None
            trend_filter = close > ma120[index]
            oversold = (rsi14[index] or 100) < 34 or (lower[index] is not None and close < lower[index])
            enter = trend_filter and oversold
            leave = (rsi14[index] or 0) > 56 or (ma20[index] is not None and close > ma20[index])

        if not holding and enter:
            holding = True
            entry_price = close
            entries[index] = True
        elif holding and leave:
            holding = False
            exits[index] = True
        positions[index] = int(holding)

    return StrategyResult(
        positions=positions,
        entries=entries,
        exits=exits,
        indicators={
            "ma20": ma20,
            "ma60": ma60,
            "ma120": ma120,
            "rsi14": rsi14,
            "atr14": atr14,
            "bollinger_upper": upper,
            "bollinger_lower": lower,
            "volume_ratio": volume_ratio,
        },
    )


def score_latest(bars: list[dict[str, Any]], result: StrategyResult) -> dict[str, Any]:
    closes = [float(bar["close"]) for bar in bars]
    latest = len(bars) - 1
    ma20 = result.indicators["ma20"][latest]
    ma60 = result.indicators["ma60"][latest]
    ma120 = result.indicators["ma120"][latest]
    rsi14 = result.indicators["rsi14"][latest]
    volume_ratio = result.indicators["volume_ratio"][latest]
    atr14 = result.indicators["atr14"][latest]
    close = closes[latest]

    trend_points = 0
    trend_points += 12 if ma20 and close > ma20 else 0
    trend_points += 12 if ma20 and ma60 and ma20 > ma60 else 0
    trend_points += 11 if ma60 and ma120 and ma60 > ma120 else 0

    momentum_60 = close / closes[-61] - 1 if len(closes) > 60 else 0.0
    momentum_points = max(0.0, min(25.0, 12.5 + momentum_60 * 80))
    volume_points = max(0.0, min(15.0, ((volume_ratio or 0.6) - 0.6) * 15))
    volatility = (atr14 / close) if atr14 else 0.05
    risk_points = max(0.0, min(15.0, 15 - volatility * 260))
    mean_reversion_points = 10.0 if rsi14 and 38 <= rsi14 <= 68 else 5.0
    score = round(min(100.0, trend_points + momentum_points + volume_points + risk_points + mean_reversion_points), 1)

    if score >= 72:
        rating = "强势"
    elif score >= 58:
        rating = "关注"
    elif score >= 42:
        rating = "中性"
    else:
        rating = "弱势"
    return {
        "score": score,
        "rating": rating,
        "position": "持有" if result.positions[latest] else "空仓",
        "momentum_60d": round(momentum_60, 4),
        "rsi14": round(rsi14, 2) if rsi14 is not None else None,
        "volume_ratio": round(volume_ratio, 2) if volume_ratio is not None else None,
        "atr_ratio": round(volatility, 4),
    }

