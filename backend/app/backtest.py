from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TradingCosts:
    commission_rate: float = 0.0003
    minimum_commission: float = 5.0
    stamp_duty_rate: float = 0.0005
    slippage_rate: float = 0.0005
    lot_size: int = 100


def run_backtest(
    bars: list[dict[str, Any]],
    positions: list[int],
    *,
    initial_cash: float = 100_000.0,
    costs: TradingCosts = TradingCosts(),
) -> dict[str, Any]:
    if len(bars) != len(positions):
        raise ValueError("bars and positions must have equal length")

    cash = initial_cash
    shares = 0
    pending_position = 0
    entry: dict[str, Any] | None = None
    trades: list[dict[str, Any]] = []
    curve: list[dict[str, Any]] = []

    for index, bar in enumerate(bars):
        open_price = float(bar["open"])
        close_price = float(bar["close"])

        if pending_position == 1 and shares == 0:
            fill_price = open_price * (1 + costs.slippage_rate)
            affordable = cash / (fill_price * (1 + costs.commission_rate))
            quantity = math.floor(affordable / costs.lot_size) * costs.lot_size
            if quantity > 0:
                gross = quantity * fill_price
                commission = max(costs.minimum_commission, gross * costs.commission_rate)
                cash -= gross + commission
                shares = quantity
                entry = {
                    "date": bar["date"],
                    "price": fill_price,
                    "quantity": quantity,
                    "cost": commission,
                    "index": index,
                }
        elif pending_position == 0 and shares > 0 and entry is not None and index > entry["index"]:
            fill_price = open_price * (1 - costs.slippage_rate)
            gross = shares * fill_price
            commission = max(costs.minimum_commission, gross * costs.commission_rate)
            stamp_duty = gross * costs.stamp_duty_rate
            cash += gross - commission - stamp_duty
            invested = entry["quantity"] * entry["price"] + entry["cost"]
            proceeds = gross - commission - stamp_duty
            trades.append(
                {
                    "entry_date": entry["date"],
                    "exit_date": bar["date"],
                    "entry_price": round(entry["price"], 3),
                    "exit_price": round(fill_price, 3),
                    "quantity": shares,
                    "return": round(proceeds / invested - 1, 4),
                    "pnl": round(proceeds - invested, 2),
                }
            )
            shares = 0
            entry = None

        equity = cash + shares * close_price
        curve.append({"date": bar["date"], "equity": round(equity, 2)})
        pending_position = positions[index]

    final_equity = curve[-1]["equity"] if curve else initial_cash
    returns = [
        curve[index]["equity"] / curve[index - 1]["equity"] - 1
        for index in range(1, len(curve))
        if curve[index - 1]["equity"]
    ]
    total_return = final_equity / initial_cash - 1
    years = max(len(bars) / 252, 1 / 252)
    annualized = (1 + total_return) ** (1 / years) - 1 if total_return > -1 else -1.0
    maximum_drawdown = _maximum_drawdown([point["equity"] for point in curve])
    sharpe = _sharpe_ratio(returns)
    buy_hold = float(bars[-1]["close"]) / float(bars[0]["close"]) - 1 if bars else 0.0
    wins = sum(1 for trade in trades if trade["pnl"] > 0)

    return {
        "initial_cash": initial_cash,
        "final_equity": final_equity,
        "total_return": round(total_return, 4),
        "annualized_return": round(annualized, 4),
        "benchmark_return": round(buy_hold, 4),
        "max_drawdown": round(maximum_drawdown, 4),
        "sharpe": round(sharpe, 2),
        "trade_count": len(trades),
        "win_rate": round(wins / len(trades), 4) if trades else 0.0,
        "equity_curve": curve,
        "trades": trades[-12:],
        "assumptions": {
            "execution": "次日开盘",
            "commission_rate": costs.commission_rate,
            "minimum_commission": costs.minimum_commission,
            "stamp_duty_rate": costs.stamp_duty_rate,
            "slippage_rate": costs.slippage_rate,
            "lot_size": costs.lot_size,
        },
    }


def _maximum_drawdown(values: list[float]) -> float:
    peak = 0.0
    maximum = 0.0
    for value in values:
        peak = max(peak, value)
        if peak:
            maximum = min(maximum, value / peak - 1)
    return maximum


def _sharpe_ratio(returns: list[float]) -> float:
    if len(returns) < 2:
        return 0.0
    average = sum(returns) / len(returns)
    variance = sum((value - average) ** 2 for value in returns) / (len(returns) - 1)
    standard_deviation = math.sqrt(variance)
    return average / standard_deviation * math.sqrt(252) if standard_deviation else 0.0

