from __future__ import annotations

import math
from collections.abc import Sequence


Number = int | float


def sma(values: Sequence[Number], window: int) -> list[float | None]:
    if window <= 0:
        raise ValueError("window must be positive")
    output: list[float | None] = [None] * len(values)
    running = 0.0
    for index, value in enumerate(values):
        running += float(value)
        if index >= window:
            running -= float(values[index - window])
        if index >= window - 1:
            output[index] = running / window
    return output


def rolling_max(values: Sequence[Number], window: int) -> list[float | None]:
    output: list[float | None] = [None] * len(values)
    for index in range(window - 1, len(values)):
        output[index] = max(float(value) for value in values[index - window + 1 : index + 1])
    return output


def rolling_std(values: Sequence[Number], window: int) -> list[float | None]:
    averages = sma(values, window)
    output: list[float | None] = [None] * len(values)
    for index in range(window - 1, len(values)):
        mean = averages[index]
        assert mean is not None
        variance = sum((float(value) - mean) ** 2 for value in values[index - window + 1 : index + 1]) / window
        output[index] = math.sqrt(variance)
    return output


def rsi(values: Sequence[Number], window: int = 14) -> list[float | None]:
    output: list[float | None] = [None] * len(values)
    if len(values) <= window:
        return output
    gains = [0.0]
    losses = [0.0]
    for previous, current in zip(values, values[1:]):
        change = float(current) - float(previous)
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))

    average_gain = sum(gains[1 : window + 1]) / window
    average_loss = sum(losses[1 : window + 1]) / window
    output[window] = _rsi_value(average_gain, average_loss)
    for index in range(window + 1, len(values)):
        average_gain = (average_gain * (window - 1) + gains[index]) / window
        average_loss = (average_loss * (window - 1) + losses[index]) / window
        output[index] = _rsi_value(average_gain, average_loss)
    return output


def atr(highs: Sequence[Number], lows: Sequence[Number], closes: Sequence[Number], window: int = 14) -> list[float | None]:
    true_ranges: list[float] = []
    for index, (high, low) in enumerate(zip(highs, lows)):
        previous_close = float(closes[index - 1]) if index else float(closes[0])
        true_ranges.append(max(float(high) - float(low), abs(float(high) - previous_close), abs(float(low) - previous_close)))
    return sma(true_ranges, window)


def _rsi_value(average_gain: float, average_loss: float) -> float:
    if average_loss == 0:
        return 100.0
    relative_strength = average_gain / average_loss
    return 100 - 100 / (1 + relative_strength)

