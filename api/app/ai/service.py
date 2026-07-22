from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date

from api.app.core.config import settings

from .compiler import compile_readable_code
from .deepseek import DeepSeekClient
from .mock import generate_mock_spec
from .spec import StrategyGenerationResponse

DISCLAIMER = "AI 输出仅供量化研究与历史回测，不构成投资建议；保存前请核对全部规则与风险参数。"


class QuotaExceeded(RuntimeError):
    pass


class AiStrategyService:
    def __init__(self) -> None:
        self.usage: dict[tuple[str, date], int] = defaultdict(int)
        self.history: dict[str, list[StrategyGenerationResponse]] = defaultdict(list)
        self.client = DeepSeekClient()

    def generate(self, user_id: str, prompt: str, daily_limit: int | None = None) -> StrategyGenerationResponse:
        limit = daily_limit or settings.deepseek_daily_free_limit
        key = (user_id, date.today())
        if self.usage[key] >= limit:
            raise QuotaExceeded("今日 AI 策略生成额度已用完")
        if settings.deepseek_enabled:
            spec, input_tokens, output_tokens = self.client.generate(prompt)
            mode = "deepseek"
        else:
            spec = generate_mock_spec(prompt)
            input_tokens = len(prompt)
            output_tokens = len(spec.model_dump_json())
            mode = "mock"
        # Usage is committed only after a fully validated spec is produced.
        self.usage[key] += 1
        result = StrategyGenerationResponse(
            id=uuid.uuid4().hex,
            mode=mode,
            spec=spec,
            readable_code=compile_readable_code(spec),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            daily_used=self.usage[key],
            daily_limit=limit,
            disclaimer=DISCLAIMER,
        )
        self.history[user_id].append(result)
        return result

    def refund(self, user_id: str, generation_id: str) -> None:
        """Compensate local usage when persistent usage recording fails."""
        key = (user_id, date.today())
        before = len(self.history[user_id])
        self.history[user_id] = [item for item in self.history[user_id] if item.id != generation_id]
        if len(self.history[user_id]) < before:
            self.usage[key] = max(0, self.usage[key] - 1)


ai_strategy_service = AiStrategyService()
