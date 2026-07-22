from __future__ import annotations

import numpy as np
import pandas as pd


def add_indicators(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy().sort_values("date").reset_index(drop=True)
    close = result["close"].astype(float)
    high = result["high"].astype(float)
    low = result["low"].astype(float)
    volume = result["volume"].astype(float)

    for window in (5, 20, 60, 120):
        result[f"ma{window}"] = close.rolling(window, min_periods=window).mean()
    result["ema12"] = close.ewm(span=12, adjust=False, min_periods=12).mean()
    result["ema26"] = close.ewm(span=26, adjust=False, min_periods=26).mean()
    result["macd"] = result["ema12"] - result["ema26"]
    result["macd_signal"] = result["macd"].ewm(span=9, adjust=False, min_periods=9).mean()
    result["macd_hist"] = (result["macd"] - result["macd_signal"]) * 2

    delta = close.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    average_gain = gains.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    average_loss = losses.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    strength = average_gain / average_loss.replace(0, np.nan)
    result["rsi14"] = (100 - 100 / (1 + strength)).fillna(100).where(average_gain.notna())

    std20 = close.rolling(20, min_periods=20).std(ddof=0)
    result["bollinger_upper"] = result["ma20"] + 2 * std20
    result["bollinger_lower"] = result["ma20"] - 2 * std20

    previous_close = close.shift(1)
    true_range = pd.concat(
        [(high - low), (high - previous_close).abs(), (low - previous_close).abs()],
        axis=1,
    ).max(axis=1)
    result["atr14"] = true_range.rolling(14, min_periods=14).mean()
    result["momentum60"] = close.pct_change(60)
    result["volume_ma20"] = volume.rolling(20, min_periods=20).mean()
    result["volume_ratio"] = volume / result["volume_ma20"].replace(0, np.nan)
    # Shifted ranges are safe to compare against today's close without future leakage.
    result["high55_prev"] = high.shift(1).rolling(55, min_periods=55).max()
    result["low20_prev"] = low.shift(1).rolling(20, min_periods=20).min()
    return result
