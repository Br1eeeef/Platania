from __future__ import annotations

import json
from typing import Any

import httpx
from pydantic import ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from api.app.core.config import settings

from .spec import StrategySpec

SCHEMA_JSON = json.dumps(StrategySpec.model_json_schema(), ensure_ascii=False, separators=(",", ":"))
SYSTEM_PROMPT = f"""You convert Chinese A-share strategy requests into one JSON StrategySpec 1.0 object.
Return JSON only. Do not wrap it in markdown and do not add explanations.
Follow this JSON Schema exactly; use the exact property names, enum values, and nested left/right indicator shapes:
{SCHEMA_JSON}

Rules:
- Percentages must be decimal fractions: 8% is 0.08 and 10% is 0.10.
- Put ST and suspension exclusions in `exclusions`, never invent filter operators.
- Every entry and exit condition must use `left`, `operator`, and `right` exactly as defined by the schema.
- Express "MA20 crosses above MA60" with left={{"name":"MA","period":20}}, operator="cross_above", right={{"name":"MA","period":60}}.
- Express "close falls below MA20" with left={{"name":"close"}}, operator="cross_below", right={{"name":"MA","period":20}}.
- Allowed indicators and operators are limited by the schema. Never output Python, imports, shell, URLs, or prose.
- Risk must include stop_loss_pct and max_position. max_position cannot exceed 0.5.
"""


class DeepSeekError(RuntimeError):
    """A safe, user-facing DeepSeek integration error."""


class RetryableDeepSeekError(DeepSeekError):
    """A temporary upstream failure that can be retried safely."""


class DeepSeekClient:
    def generate(self, prompt: str) -> tuple[StrategySpec, int, int]:
        if not settings.deepseek_enabled:
            raise DeepSeekError("DeepSeek 尚未配置")

        messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
        content, input_tokens, output_tokens = self._request(messages)
        try:
            return self._parse_spec(content), input_tokens, output_tokens
        except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as first_error:
            correction = self._correction_message(first_error)
            corrected_content, corrected_input, corrected_output = self._request(
                [
                    *messages,
                    {"role": "assistant", "content": content[:12_000]},
                    {"role": "user", "content": correction},
                ]
            )
            try:
                spec = self._parse_spec(corrected_content)
            except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as exc:
                raise DeepSeekError("AI 返回的策略格式仍未通过安全校验，请简化策略描述后重试") from exc
            return spec, input_tokens + corrected_input, output_tokens + corrected_output

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, RetryableDeepSeekError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=6),
        reraise=True,
    )
    def _request(self, messages: list[dict[str, str]]) -> tuple[str, int, int]:
        payload = {
            "model": settings.deepseek_model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0,
            "max_tokens": 1800,
        }
        headers = {"Authorization": f"Bearer {settings.deepseek_api_key}", "Content-Type": "application/json"}
        try:
            with httpx.Client(timeout=httpx.Timeout(40, connect=8)) as client:
                response = client.post(
                    f"{settings.deepseek_api_base.rstrip('/')}/chat/completions", json=payload, headers=headers
                )
        except (httpx.TimeoutException, httpx.NetworkError):
            raise

        if response.status_code in {401, 403}:
            raise DeepSeekError("DeepSeek API Key 无效或没有模型访问权限")
        if response.status_code == 402:
            raise DeepSeekError("DeepSeek 账户余额不足，请充值后重试")
        if response.status_code == 429:
            raise RetryableDeepSeekError("DeepSeek 请求过于频繁，请稍后重试")
        if response.status_code >= 500:
            raise RetryableDeepSeekError("DeepSeek 服务暂时不可用，请稍后重试")
        try:
            response.raise_for_status()
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            usage = body.get("usage", {})
            if not isinstance(content, str) or not content.strip():
                raise TypeError("empty model content")
            return (
                content.strip(),
                int(usage.get("prompt_tokens", 0)),
                int(usage.get("completion_tokens", 0)),
            )
        except (httpx.HTTPStatusError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise DeepSeekError("DeepSeek 返回了无法识别的响应") from exc

    @staticmethod
    def _parse_spec(content: str) -> StrategySpec:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        raw = json.loads(cleaned)
        if not isinstance(raw, dict):
            raise TypeError("StrategySpec must be a JSON object")
        DeepSeekClient._normalize_percentages(raw)
        return StrategySpec.model_validate(raw)

    @staticmethod
    def _normalize_percentages(raw: dict[str, Any]) -> None:
        risk = raw.get("risk")
        if not isinstance(risk, dict):
            return
        limits = {"stop_loss_pct": 20, "take_profit_pct": 100, "max_position": 50}
        for field, upper_percent in limits.items():
            value = risk.get(field)
            if isinstance(value, (int, float)) and not isinstance(value, bool) and 1 <= value <= upper_percent:
                risk[field] = value / 100

    @staticmethod
    def _correction_message(error: Exception) -> str:
        if isinstance(error, ValidationError):
            details = error.errors(include_url=False, include_input=False)
        else:
            details = [{"type": "invalid_json", "message": str(error)[:300]}]
        return (
            "Your previous JSON did not match StrategySpec. Correct it using the exact JSON Schema in the system "
            "message. Do not rename fields or invent operators. Return the complete corrected JSON object only. "
            f"Validation errors: {json.dumps(details, ensure_ascii=False)}"
        )
