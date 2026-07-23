from __future__ import annotations

import json
from datetime import date

import pytest
from pydantic import ValidationError

from api.app.ai.compiler import evaluate_spec
from api.app.ai.deepseek import DeepSeekClient
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


def test_deepseek_normalizes_percentage_risk_values() -> None:
    raw = {
        "version": "1.0",
        "name": "测试策略",
        "entry_conditions": [{"left": {"name": "MA", "period": 20}, "operator": "cross_above", "right": {"name": "MA", "period": 60}}],
        "exit_conditions": [{"left": {"name": "close"}, "operator": "cross_below", "right": {"name": "MA", "period": 20}}],
        "risk": {"stop_loss_pct": 8, "max_position": 10},
    }
    spec = DeepSeekClient._parse_spec(json.dumps(raw, ensure_ascii=False))
    assert spec.risk.stop_loss_pct == 0.08
    assert spec.risk.max_position == 0.1


def test_deepseek_corrects_an_invalid_first_response(monkeypatch) -> None:
    valid = generate_mock_spec("MA20上穿MA60，亏损8%退出，最大仓位10%").model_dump_json()
    responses = iter(
        [
            ('{"strategy_name":"字段错误"}', 10, 3),
            (valid, 20, 15),
        ]
    )
    client = DeepSeekClient()
    monkeypatch.setattr("api.app.ai.deepseek.settings.deepseek_api_key", "test-key")
    monkeypatch.setattr(client, "_request", lambda messages: next(responses))
    spec, input_tokens, output_tokens = client.generate("生成一个测试用A股趋势策略")
    assert spec.name
    assert input_tokens == 30
    assert output_tokens == 18
