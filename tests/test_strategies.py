from __future__ import annotations

from datetime import timedelta

import pandas as pd
import pytest

from api.app.models.strategy import SignalState
from api.app.strategies import MeanReversionStrategy, TrendMomentumStrategy, VolumeBreakoutStrategy


@pytest.mark.parametrize("strategy", [TrendMomentumStrategy(), VolumeBreakoutStrategy(), MeanReversionStrategy()])
def test_strategy_returns_aligned_targets(strategy, demo_frame: pd.DataFrame, benchmark_frame: pd.DataFrame) -> None:
    result = strategy.evaluate(demo_frame, benchmark_frame)
    assert len(result.frame) == len(demo_frame)
    assert result.frame["target_position"].between(0, 1).all()
    assert set(result.frame["signal_event"].unique()).issubset({"", "entry", "exit"})
    assert result.signal.state in set(SignalState)
    assert result.signal.reasons


def test_future_bar_cannot_change_historical_targets(demo_frame: pd.DataFrame, benchmark_frame: pd.DataFrame) -> None:
    strategy = TrendMomentumStrategy()
    baseline = strategy.evaluate(demo_frame, benchmark_frame).frame["target_position"]
    future = demo_frame.iloc[-1].copy()
    future["date"] = demo_frame.iloc[-1]["date"].to_pydatetime() + timedelta(days=1)
    future["open"] = future["high"] = future["low"] = future["close"] = float(future["close"]) * 10
    extended = pd.concat([demo_frame, pd.DataFrame([future])], ignore_index=True)
    rerun = strategy.evaluate(extended, benchmark_frame).frame["target_position"].iloc[:-1]
    pd.testing.assert_series_equal(baseline.reset_index(drop=True), rerun.reset_index(drop=True))


def test_strategy_parameter_override_caps_target_position(
    demo_frame: pd.DataFrame, benchmark_frame: pd.DataFrame
) -> None:
    result = TrendMomentumStrategy().evaluate(
        demo_frame,
        benchmark_frame,
        {"rsi_min": 0, "rsi_max": 100, "atr_stop": 4.0, "max_position": 0.25},
    )
    assert result.frame["target_position"].max() <= 0.25
