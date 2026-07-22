from __future__ import annotations

import re

from .spec import Condition, IndicatorName, IndicatorRef, Operator, RiskRules, StrategySpec


def generate_mock_spec(prompt: str) -> StrategySpec:
    periods = [int(value) for value in re.findall(r"MA\s*(\d{1,3})", prompt, flags=re.IGNORECASE)]
    fast, slow = (periods + [20, 60])[:2]
    loss_match = re.search(r"(?:亏损|止损)\s*(\d+(?:\.\d+)?)%", prompt)
    position_match = re.search(r"(?:仓位|最大仓位)\s*(\d+(?:\.\d+)?)%", prompt)
    stop_loss = min(float(loss_match.group(1)) / 100, 0.2) if loss_match else 0.08
    max_position = min(float(position_match.group(1)) / 100, 0.5) if position_match else 0.1
    return StrategySpec(
        name="AI 趋势交叉策略（Mock）",
        universe=["沪深A股"],
        exclusions=["ST", "停牌", "上市不足120日"],
        filters=[
            Condition(
                left=IndicatorRef(name=IndicatorName.CLOSE),
                operator=Operator.GT,
                right=IndicatorRef(name=IndicatorName.MA, period=120),
            )
        ],
        entry_conditions=[
            Condition(
                left=IndicatorRef(name=IndicatorName.MA, period=fast),
                operator=Operator.CROSS_ABOVE,
                right=IndicatorRef(name=IndicatorName.MA, period=slow),
            )
        ],
        exit_conditions=[
            Condition(
                left=IndicatorRef(name=IndicatorName.CLOSE),
                operator=Operator.LT,
                right=IndicatorRef(name=IndicatorName.MA, period=fast),
            )
        ],
        risk=RiskRules(stop_loss_pct=stop_loss, max_position=max_position),
        parameter_notes={"mock": "未配置 DeepSeek API Key；当前结果由确定性规则模板生成"},
    )
