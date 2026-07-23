from __future__ import annotations

import pandas as pd
import pytest
from pydantic import ValidationError

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


def test_configurable_request_is_preserved_in_parameter_snapshot() -> None:
    request = BacktestRequest(
        symbol="600036.SH",
        strategy_id="trend_momentum",
        initial_cash=250_000,
        max_position=0.35,
        benchmark_symbol="000300.SH",
        strategy_parameters={"rsi_min": 45, "rsi_max": 68, "atr_stop": 2.5},
    )
    result = BacktestEngine().run(synthetic_frame(), synthetic_frame(), request, provider="test", is_demo=False)
    assert result.parameters["initial_cash"] == 250_000
    assert result.parameters["max_position"] == 0.35
    assert result.parameters["strategy_parameters"]["atr_stop"] == 2.5
    assert result.parameters["benchmark_symbol"] == "000300.SH"


@pytest.mark.parametrize(
    ("strategy_id", "parameters"),
    [
        ("trend_momentum", {"unknown": 1}),
        ("trend_momentum", {"rsi_min": 80, "rsi_max": 60}),
        ("mean_reversion", {"rsi_entry": 60}),
    ],
)
def test_strategy_parameter_whitelist_and_ranges(strategy_id: str, parameters: dict[str, float]) -> None:
    with pytest.raises(ValidationError):
        BacktestRequest(symbol="600036.SH", strategy_id=strategy_id, strategy_parameters=parameters)
