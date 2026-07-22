from __future__ import annotations

import pandas as pd

from api.app.indicators import add_indicators


def test_indicators_have_expected_warmup_and_values(demo_frame: pd.DataFrame) -> None:
    result = add_indicators(demo_frame)
    assert pd.isna(result.iloc[18]["ma20"])
    assert pd.notna(result.iloc[19]["ma20"])
    assert pd.notna(result.iloc[-1]["macd"])
    assert 0 <= result.iloc[-1]["rsi14"] <= 100
    assert result.iloc[-1]["bollinger_lower"] < result.iloc[-1]["bollinger_upper"]
    assert result.iloc[-1]["atr14"] > 0


def test_shifted_breakout_range_does_not_include_current_bar(demo_frame: pd.DataFrame) -> None:
    altered = demo_frame.copy()
    altered.loc[100, "high"] = altered.loc[:99, "high"].max() * 5
    result = add_indicators(altered)
    assert result.loc[100, "high55_prev"] < altered.loc[100, "high"]
