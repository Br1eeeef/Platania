from __future__ import annotations

import pandas as pd

from api.app.indicators import add_indicators
from api.app.models.strategy import SignalSnapshot, SignalState, StrategyDescriptor, StrategyId

from .base import Strategy, StrategyEvaluation, risk_level, safe_value


class MeanReversionStrategy(Strategy):
    descriptor = StrategyDescriptor(
        id=StrategyId.MEAN_REVERSION,
        name="趋势内均值回归",
        summary="长期趋势非空头时捕捉 RSI 与布林带共同确认的超卖",
        parameters={"rsi_entry": 32, "rsi_exit": 55, "max_holding_days": 15, "max_position": 0.6},
    )

    def evaluate(self, frame: pd.DataFrame, benchmark: pd.DataFrame | None = None) -> StrategyEvaluation:
        data = add_indicators(frame)
        if benchmark is not None:
            market = add_indicators(benchmark)[["date", "close", "ma120"]].rename(
                columns={"close": "market_close", "ma120": "market_ma120"}
            )
            data = data.merge(market, on="date", how="left")
            data[["market_close", "market_ma120"]] = data[["market_close", "market_ma120"]].ffill()
        else:
            data["market_close"] = data["close"]
            data["market_ma120"] = data["ma120"]
        params = self.descriptor.parameters
        holding = False
        held_days = 0
        targets: list[float] = []
        events: list[str] = []
        for row in data.itertuples():
            ready = all(pd.notna(value) for value in (row.rsi14, row.bollinger_lower, row.ma20, row.market_ma120))
            market_ok = ready and row.market_close >= row.market_ma120 * 0.97
            entry = ready and market_ok and row.rsi14 < params["rsi_entry"] and row.close < row.bollinger_lower
            exit_rule = holding and (
                row.close >= row.ma20 or row.rsi14 >= params["rsi_exit"] or held_days >= params["max_holding_days"]
            )
            event = ""
            if not holding and entry:
                holding = True
                held_days = 0
                event = "entry"
            elif holding and exit_rule:
                holding = False
                event = "exit"
            if holding:
                held_days += 1
            targets.append(float(params["max_position"]) if holding else 0.0)
            events.append(event)
        data["target_position"] = targets
        data["signal_event"] = events
        latest = data.iloc[-1]
        market_ok = latest.market_close >= latest.market_ma120 * 0.97
        setup = latest.rsi14 < 38 and latest.close < latest.bollinger_lower * 1.02 and market_ok
        reasons = [
            f"RSI14 {latest.rsi14:.1f}，入场阈值 {params['rsi_entry']:.0f}",
            f"收盘价 {'低于' if latest.close < latest.bollinger_lower else '未低于'} 布林带下轨",
            f"大盘长期趋势 {'允许' if market_ok else '禁止'}均值回归",
        ]
        state = SignalState.HOLD if targets[-1] else (SignalState.CANDIDATE if setup else SignalState.OBSERVE)
        score = min(
            100, 40 * max(0, (45 - latest.rsi14) / 20) + 35 * float(latest.close < latest.bollinger_lower) + 25 * float(market_ok)
        )
        signal = SignalSnapshot(
            strategy_id=self.descriptor.id,
            state=state,
            generated_at=latest.date.date(),
            reasons=reasons,
            invalidation="回到 MA20、RSI 恢复至 55 或持仓达到 15 个交易日",
            risk_level=risk_level(latest.atr14 / latest.close),
            score=round(score, 1),
            values={key: safe_value(latest[key]) for key in ("rsi14", "bollinger_lower", "ma20", "atr14")},
        )
        return StrategyEvaluation(data, signal)
