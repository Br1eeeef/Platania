from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from api.app.ai.compiler import evaluate_spec
from api.app.ai.mock import generate_mock_spec
from api.app.ai.service import ai_strategy_service
from api.app.ai.spec import Condition, IndicatorName, IndicatorRef, Operator, RiskRules, StrategySpec


def test_mock_strategy_extracts_risk_parameters() -> None:
    spec = generate_mock_spec("生成A股趋势策略，MA20上穿MA60，亏损8%退出，最大仓位10%，排除ST")
    assert spec.risk.stop_loss_pct == 0.08
    assert spec.risk.max_position == 0.1
    assert spec.entry_conditions[0].operator == Operator.CROSS_ABOVE


def test_spec_rejects_unsafe_or_excessive_values() -> None:
    with pytest.raises(ValidationError):
        StrategySpec(
            name="不安全策略",
            entry_conditions=[Condition(left=IndicatorRef(name=IndicatorName.CLOSE), operator=Operator.GT, right=1)],
            exit_conditions=[Condition(left=IndicatorRef(name=IndicatorName.CLOSE), operator=Operator.LT, right=1)],
            risk=RiskRules(stop_loss_pct=0.5, max_position=0.9),
        )
    with pytest.raises(ValidationError):
        IndicatorRef(name=IndicatorName.MA)


def test_validated_spec_compiles_without_executing_code(demo_frame) -> None:
    spec = generate_mock_spec("MA20上穿MA60，亏损8%退出，最大仓位10%")
    result = evaluate_spec(demo_frame, spec)
    assert "target_position" in result
    assert result["target_position"].max() <= 0.1


def test_failed_persistent_usage_can_be_compensated() -> None:
    user_id = "quota-compensation-test"
    key = (user_id, date.today())
    before = ai_strategy_service.usage[key]
    result = ai_strategy_service.generate(user_id, "生成A股趋势策略，MA20上穿MA60，亏损8%退出", daily_limit=10)
    assert ai_strategy_service.usage[key] == before + 1
    ai_strategy_service.refund(user_id, result.id)
    assert ai_strategy_service.usage[key] == before
    assert all(item.id != result.id for item in ai_strategy_service.history[user_id])
