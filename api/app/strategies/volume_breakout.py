from __future__ import annotations

import pandas as pd

from api.app.indicators import add_indicators
from api.app.models.strategy import SignalSnapshot, SignalState, StrategyDescriptor, StrategyId

from .base import Strategy, StrategyEvaluation, risk_level, safe_value


class VolumeBreakoutStrategy(Strategy):
    descriptor = StrategyDescriptor(
        id=StrategyId.VOLUME_BREAKOUT,
        name="放量突破",
        summary="突破过去 55 日高点并由成交量和大盘趋势确认",
        parameters={"volume_ratio": 1.5, "atr_stop": 2.8, "max_position": 0.8},
    )

    def evaluate(
        self,
        frame: pd.DataFrame,
        benchmark: pd.DataFrame | None = None,
        parameters: dict[str, float | int] | None = None,
    ) -> StrategyEvaluation:
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
        params = {**self.descriptor.parameters, **(parameters or {})}
        holding = False
        entry_price = 0.0
        targets: list[float] = []
        events: list[str] = []
        for row in data.itertuples():
            ready = all(
                pd.notna(value) for value in (row.high55_prev, row.low20_prev, row.volume_ratio, row.atr14, row.market_ma120)
            )
            entry = (
                ready
                and row.close > row.high55_prev
                and row.volume_ratio >= params["volume_ratio"]
                and row.market_close >= row.market_ma120
            )
            stop = holding and row.close <= entry_price - params["atr_stop"] * row.atr14
            exit_rule = ready and (row.close < row.low20_prev or stop)
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
        market_ok = latest.market_close >= latest.market_ma120
        reasons = [
            f"收盘价 {'突破' if latest.close > latest.high55_prev else '未突破'} 55日高点",
            f"量比 {latest.volume_ratio:.2f}，阈值 {params['volume_ratio']:.2f}",
            f"大盘趋势过滤 {'通过' if market_ok else '未通过'}",
        ]
        setup = latest.close >= latest.high55_prev * 0.98 and latest.volume_ratio >= 1.1 and market_ok
        state = SignalState.HOLD if targets[-1] else (SignalState.CANDIDATE if setup else SignalState.OBSERVE)
        score = min(
            100,
            35 * float(latest.close > latest.high55_prev)
            + 35 * min(latest.volume_ratio / params["volume_ratio"], 1)
            + 30 * float(market_ok),
        )
        signal = SignalSnapshot(
            strategy_id=self.descriptor.id,
            state=state,
            generated_at=latest.date.date(),
            reasons=reasons,
            invalidation="跌破过去 20 日低点或从入场价回撤 2.8 倍 ATR",
            risk_level=risk_level(latest.atr14 / latest.close),
            score=round(score, 1),
            values={key: safe_value(latest[key]) for key in ("high55_prev", "low20_prev", "volume_ratio", "atr14")},
        )
        return StrategyEvaluation(data, signal)
