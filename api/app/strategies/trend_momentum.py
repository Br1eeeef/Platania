from __future__ import annotations

import pandas as pd

from api.app.indicators import add_indicators
from api.app.models.strategy import SignalSnapshot, SignalState, StrategyDescriptor, StrategyId

from .base import Strategy, StrategyEvaluation, risk_level, safe_value


class TrendMomentumStrategy(Strategy):
    descriptor = StrategyDescriptor(
        id=StrategyId.TREND_MOMENTUM,
        name="趋势动量",
        summary="多周期均线、60日动量与 RSI 联合过滤，ATR 风险退出",
        parameters={"rsi_min": 42, "rsi_max": 72, "atr_stop": 3.0, "max_position": 0.9},
    )

    def evaluate(self, frame: pd.DataFrame, benchmark: pd.DataFrame | None = None) -> StrategyEvaluation:
        data = add_indicators(frame)
        params = self.descriptor.parameters
        holding = False
        entry_price = 0.0
        targets: list[float] = []
        events: list[str] = []
        for row in data.itertuples():
            ready = all(pd.notna(value) for value in (row.ma20, row.ma60, row.momentum60, row.rsi14, row.atr14))
            entry = (
                ready
                and row.close > row.ma20 > row.ma60
                and row.momentum60 > 0
                and params["rsi_min"] <= row.rsi14 <= params["rsi_max"]
            )
            stop = holding and row.close <= entry_price - params["atr_stop"] * row.atr14
            exit_rule = ready and (row.close < row.ma20 or stop)
            event = ""
            if not holding and entry:
                holding = True
                entry_price = row.close
                event = "entry"
            elif holding and exit_rule:
                holding = False
                event = "exit"
            targets.append(float(params["max_position"]) if holding else 0.0)
            events.append(event)
        data["target_position"] = targets
        data["signal_event"] = events
        latest = data.iloc[-1]
        reasons = [
            f"收盘价 {'高于' if latest.close > latest.ma20 else '不高于'} MA20",
            f"MA20 {'高于' if latest.ma20 > latest.ma60 else '不高于'} MA60",
            f"60日动量 {latest.momentum60:.2%}",
            f"RSI14 {latest.rsi14:.1f}",
        ]
        state = SignalState.HOLD if targets[-1] else (SignalState.CANDIDATE if entry else SignalState.OBSERVE)
        score = (
            sum(
                [
                    latest.close > latest.ma20,
                    latest.ma20 > latest.ma60,
                    latest.momentum60 > 0,
                    params["rsi_min"] <= latest.rsi14 <= params["rsi_max"],
                ]
            )
            * 25
        )
        signal = SignalSnapshot(
            strategy_id=self.descriptor.id,
            state=state,
            generated_at=latest.date.date(),
            reasons=reasons,
            invalidation="跌破 MA20 或从入场价回撤 3 倍 ATR",
            risk_level=risk_level(latest.atr14 / latest.close),
            score=score,
            values={key: safe_value(latest[key]) for key in ("ma20", "ma60", "momentum60", "rsi14", "atr14")},
        )
        return StrategyEvaluation(data, signal)
