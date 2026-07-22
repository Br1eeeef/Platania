from __future__ import annotations

from typing import Any

from .backtest import run_backtest
from .catalog import STOCKS, get_stock
from .data import MarketDataRepository
from .strategies import STRATEGIES, StrategyName, evaluate_strategy, score_latest


repository = MarketDataRepository()


def stock_analysis(symbol: str, strategy: StrategyName, *, chart_bars: int = 260) -> dict[str, Any]:
    bars, meta = repository.load(symbol)
    result = evaluate_strategy(bars, strategy)
    score = score_latest(bars, result)
    backtest = run_backtest(bars, result.positions)
    start = max(0, len(bars) - chart_bars)

    chart: list[dict[str, Any]] = []
    for index in range(start, len(bars)):
        item = dict(bars[index])
        for name, series in result.indicators.items():
            value = series[index]
            item[name] = round(value, 3) if value is not None else None
        item["entry"] = result.entries[index]
        item["exit"] = result.exits[index]
        item["position"] = result.positions[index]
        chart.append(item)

    previous = bars[-2]
    latest = bars[-1]
    change = float(latest["close"]) / float(previous["close"]) - 1
    stock = get_stock(symbol)
    return {
        "stock": stock,
        "strategy": {"id": strategy, **STRATEGIES[strategy]},
        "quote": {
            "date": latest["date"],
            "close": latest["close"],
            "change": round(change, 4),
            "volume": latest["volume"],
        },
        "signal": score,
        "backtest": backtest,
        "bars": chart,
        "data_meta": meta,
    }


def market_overview() -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    positive = 0
    for symbol in STOCKS:
        bars, meta = repository.load(symbol)
        result = evaluate_strategy(bars, "trend")
        score = score_latest(bars, result)
        daily_change = float(bars[-1]["close"]) / float(bars[-2]["close"]) - 1
        if daily_change > 0:
            positive += 1
        candidates.append(
            {
                **get_stock(symbol),
                "close": bars[-1]["close"],
                "change": round(daily_change, 4),
                "score": score["score"],
                "rating": score["rating"],
                "position": score["position"],
                "source": meta["source"],
            }
        )
    candidates.sort(key=lambda item: item["score"], reverse=True)
    average_change = sum(item["change"] for item in candidates) / len(candidates)
    return {
        "market": "A股研究池",
        "stock_count": len(candidates),
        "advancers": positive,
        "decliners": len(candidates) - positive,
        "average_change": round(average_change, 4),
        "candidates": candidates,
    }

