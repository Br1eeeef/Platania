from __future__ import annotations

import pandas as pd

from api.app.backtest import BacktestEngine
from api.app.models.backtest import BacktestRequest


def synthetic_frame() -> pd.DataFrame:
    dates = pd.bdate_range("2025-01-01", periods=150)
    close = [10.0 + index * 0.03 for index in range(150)]
    frame = pd.DataFrame(
        {
            "date": dates,
            "open": close,
            "high": [value * 1.01 for value in close],
            "low": [value * 0.99 for value in close],
            "close": close,
            "volume": 1_000_000,
            "amount": 10_000_000,
            "suspended": False,
            "target_position": 0.0,
        }
    )
    frame.loc[120:129, "target_position"] = 0.5
    return frame


def test_next_bar_execution_t1_costs_and_metrics() -> None:
    frame = synthetic_frame()
    request = BacktestRequest(symbol="600036.SH", strategy_id="trend_momentum", initial_cash=100_000)
    result = BacktestEngine().run(frame, frame, request, provider="test", is_demo=True)
    assert result.trades[0].entry_date == frame.iloc[121]["date"].date()
    assert result.trades[0].exit_date == frame.iloc[131]["date"].date()
    assert result.trades[0].quantity % 100 == 0
    assert result.trades[0].costs > 0
    assert result.metrics.trade_count == 1
    assert result.metrics.max_drawdown <= 0
    assert len(result.equity_curve) == len(frame)
    assert len(result.drawdown_curve) == len(frame)


def test_suspension_defers_entry() -> None:
    frame = synthetic_frame()
    frame.loc[121, "suspended"] = True
    result = BacktestEngine().run(
        frame, frame, BacktestRequest(symbol="600036.SH", strategy_id="trend_momentum"), provider="test", is_demo=True
    )
    assert result.trades[0].entry_date == frame.iloc[122]["date"].date()
