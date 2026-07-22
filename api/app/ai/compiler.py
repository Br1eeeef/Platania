from __future__ import annotations

import pandas as pd

from api.app.indicators import add_indicators

from .spec import Condition, IndicatorName, IndicatorRef, Operator, StrategySpec


def evaluate_spec(frame: pd.DataFrame, spec: StrategySpec) -> pd.DataFrame:
    data = add_indicators(frame)
    entry = _combine(data, spec.entry_conditions)
    exit_rule = _combine(data, spec.exit_conditions)
    filters = _combine(data, spec.filters) if spec.filters else pd.Series(True, index=data.index)
    holding = False
    entry_price = 0.0
    targets: list[float] = []
    events: list[str] = []
    for index, row in data.iterrows():
        event = ""
        stop = holding and float(row["close"]) <= entry_price * (1 - spec.risk.stop_loss_pct)
        take_profit = (
            holding
            and spec.risk.take_profit_pct is not None
            and float(row["close"]) >= entry_price * (1 + spec.risk.take_profit_pct)
        )
        if not holding and bool(filters.iloc[index]) and bool(entry.iloc[index]):
            holding = True
            entry_price = float(row["close"])
            event = "entry"
        elif holding and (bool(exit_rule.iloc[index]) or stop or take_profit):
            holding = False
            event = "exit"
        targets.append(spec.risk.max_position if holding else 0.0)
        events.append(event)
    data["target_position"] = targets
    data["signal_event"] = events
    return data


def compile_readable_code(spec: StrategySpec) -> str:
    lines = [
        f"# {spec.name}",
        "# 由受约束 StrategySpec 生成，仅用于阅读；平台不会执行此文本。",
        "def strategy(data):",
        f"    universe = {spec.universe!r}",
        f"    filters = {_describe_conditions(spec.filters)!r}",
        f"    entry = {_describe_conditions(spec.entry_conditions)!r}",
        f"    exit = {_describe_conditions(spec.exit_conditions)!r}",
        f"    stop_loss = {spec.risk.stop_loss_pct!r}",
        f"    take_profit = {spec.risk.take_profit_pct!r}",
        f"    max_position = {spec.risk.max_position!r}",
        "    return build_platform_strategy(data, filters, entry, exit, stop_loss, take_profit, max_position)",
    ]
    return "\n".join(lines)


def _combine(data: pd.DataFrame, conditions: list[Condition]) -> pd.Series:
    output = pd.Series(True, index=data.index)
    for condition in conditions:
        left = _series(data, condition.left)
        right = _series(data, condition.right) if isinstance(condition.right, IndicatorRef) else float(condition.right)
        previous_right = right.shift(1) if isinstance(right, pd.Series) else right
        if condition.operator == Operator.GT:
            result = left > right
        elif condition.operator == Operator.LT:
            result = left < right
        elif condition.operator == Operator.CROSS_ABOVE:
            result = (left > right) & (left.shift(1) <= previous_right)
        else:
            result = (left < right) & (left.shift(1) >= previous_right)
        output &= result.fillna(False)
    return output


def _series(data: pd.DataFrame, ref: IndicatorRef) -> pd.Series:
    if ref.name == IndicatorName.CLOSE:
        return data["close"]
    if ref.name == IndicatorName.MA:
        column = f"ma{ref.period}"
        return data[column] if column in data else data["close"].rolling(ref.period or 20).mean()
    if ref.name == IndicatorName.EMA:
        return data["close"].ewm(span=ref.period, adjust=False, min_periods=ref.period).mean()
    if ref.name == IndicatorName.MACD:
        return data["macd"]
    if ref.name == IndicatorName.RSI:
        return data["rsi14"] if ref.period == 14 else _rsi(data["close"], ref.period or 14)
    if ref.name == IndicatorName.BOLLINGER_UPPER:
        mean = data["close"].rolling(ref.period or 20).mean()
        return mean + 2 * data["close"].rolling(ref.period or 20).std(ddof=0)
    if ref.name == IndicatorName.BOLLINGER_LOWER:
        mean = data["close"].rolling(ref.period or 20).mean()
        return mean - 2 * data["close"].rolling(ref.period or 20).std(ddof=0)
    if ref.name == IndicatorName.ATR:
        return data["atr14"]
    if ref.name == IndicatorName.MOMENTUM:
        return data["close"].pct_change(ref.period or 60)
    if ref.name == IndicatorName.VOLUME_RATIO:
        return data["volume"] / data["volume"].rolling(ref.period or 20).mean()
    raise ValueError(f"unsupported indicator: {ref.name}")


def _rsi(close: pd.Series, period: int) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    return 100 - 100 / (1 + gain / loss.replace(0, pd.NA))


def _describe_conditions(conditions: list[Condition]) -> list[str]:
    return [
        f"{condition.left.model_dump()} {condition.operator} {condition.right.model_dump() if isinstance(condition.right, IndicatorRef) else condition.right}"
        for condition in conditions
    ]
