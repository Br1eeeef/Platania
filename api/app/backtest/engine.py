from __future__ import annotations

import math
import uuid
from dataclasses import dataclass

import numpy as np
import pandas as pd

from api.app.models.backtest import BacktestMetrics, BacktestRequest, BacktestResult, Trade


@dataclass
class OpenPosition:
    entry_index: int
    entry_date: pd.Timestamp
    price: float
    quantity: int
    costs: float


class BacktestEngine:
    lot_size = 100

    def run(
        self,
        frame: pd.DataFrame,
        benchmark: pd.DataFrame,
        request: BacktestRequest,
        *,
        provider: str,
        is_demo: bool,
    ) -> BacktestResult:
        required = {"date", "open", "high", "low", "close", "volume", "suspended", "target_position"}
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f"backtest fields missing: {sorted(missing)}")
        if len(frame) < 130:
            raise ValueError("at least 130 daily bars are required")

        data = frame.sort_values("date").reset_index(drop=True).copy()
        cash = request.initial_cash
        shares = 0
        position: OpenPosition | None = None
        pending_target = 0.0
        trades: list[Trade] = []
        equity: list[dict[str, float | str]] = []

        for index, row in data.iterrows():
            previous_close = float(data.iloc[index - 1]["close"]) if index else float(row["open"])
            can_buy = not bool(row["suspended"]) and float(row["open"]) < previous_close * 1.098
            can_sell = not bool(row["suspended"]) and float(row["open"]) > previous_close * 0.902

            if pending_target > 0 and shares == 0 and can_buy:
                fill = float(row["open"]) * (1 + request.slippage_rate)
                budget = cash * min(pending_target, request.max_position)
                quantity = math.floor((budget / (fill * (1 + request.commission_rate))) / self.lot_size) * self.lot_size
                if quantity > 0:
                    gross = quantity * fill
                    commission = max(request.minimum_commission, gross * request.commission_rate)
                    cash -= gross + commission
                    shares = quantity
                    position = OpenPosition(index, row["date"], fill, quantity, commission)
            elif pending_target == 0 and shares > 0 and position and index > position.entry_index and can_sell:
                fill = float(row["open"]) * (1 - request.slippage_rate)
                gross = shares * fill
                commission = max(request.minimum_commission, gross * request.commission_rate)
                stamp_duty = gross * request.stamp_duty_rate
                cash += gross - commission - stamp_duty
                invested = position.quantity * position.price + position.costs
                proceeds = gross - commission - stamp_duty
                total_costs = position.costs + commission + stamp_duty
                trades.append(
                    Trade(
                        entry_date=position.entry_date.date(),
                        exit_date=row["date"].date(),
                        entry_price=round(position.price, 3),
                        exit_price=round(fill, 3),
                        quantity=shares,
                        holding_days=index - position.entry_index,
                        pnl=round(proceeds - invested, 2),
                        return_rate=round(proceeds / invested - 1, 6),
                        costs=round(total_costs, 2),
                    )
                )
                shares = 0
                position = None

            account_value = cash + shares * float(row["close"])
            equity.append({"date": row["date"].date().isoformat(), "value": round(account_value, 2)})
            # Today's close signal can only affect the next trading bar.
            pending_target = float(row["target_position"])

        values = pd.Series([point["value"] for point in equity], dtype=float)
        returns = values.pct_change().dropna()
        total_return = values.iloc[-1] / request.initial_cash - 1
        years = max(len(values) / 252, 1 / 252)
        annualized = (1 + total_return) ** (1 / years) - 1 if total_return > -1 else -1.0
        peaks = values.cummax()
        drawdowns = values / peaks - 1
        benchmark_return = self._benchmark_return(benchmark, data)
        sharpe = float(returns.mean() / returns.std(ddof=1) * np.sqrt(252)) if len(returns) > 1 and returns.std(ddof=1) else 0.0
        wins = [trade.pnl for trade in trades if trade.pnl > 0]
        losses = [-trade.pnl for trade in trades if trade.pnl < 0]
        profit_factor = sum(wins) / sum(losses) if losses else (None if not wins else float("inf"))
        if profit_factor == float("inf"):
            profit_factor = None

        metrics = BacktestMetrics(
            total_return=round(total_return, 6),
            annualized_return=round(annualized, 6),
            benchmark_return=round(benchmark_return, 6),
            max_drawdown=round(float(drawdowns.min()), 6),
            sharpe_ratio=round(sharpe, 3),
            win_rate=round(len(wins) / len(trades), 6) if trades else 0.0,
            profit_factor=round(profit_factor, 3) if profit_factor is not None else None,
            trade_count=len(trades),
            average_holding_days=round(sum(trade.holding_days for trade in trades) / len(trades), 2) if trades else 0.0,
        )
        return BacktestResult(
            id=uuid.uuid4().hex,
            symbol=request.symbol,
            strategy_id=request.strategy_id,
            metrics=metrics,
            equity_curve=equity,
            drawdown_curve=[
                {"date": point["date"], "value": round(float(drawdowns.iloc[index]), 6)} for index, point in enumerate(equity)
            ],
            trades=trades,
            parameters={**request.model_dump(), "execution": "next_open", "lot_size": self.lot_size},
            data_range={"start": data.iloc[0]["date"].date().isoformat(), "end": data.iloc[-1]["date"].date().isoformat()},
            data_source=provider,
            is_demo=is_demo,
        )

    @staticmethod
    def _benchmark_return(benchmark: pd.DataFrame, data: pd.DataFrame) -> float:
        subset = benchmark[(benchmark["date"] >= data.iloc[0]["date"]) & (benchmark["date"] <= data.iloc[-1]["date"])]
        if len(subset) < 2:
            return 0.0
        return float(subset.iloc[-1]["close"] / subset.iloc[0]["close"] - 1)
