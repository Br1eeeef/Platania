from __future__ import annotations

import json

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from api.app.core.config import settings

from .spec import StrategySpec

SYSTEM_PROMPT = """You convert A-share strategy requests into JSON only. Return a StrategySpec 1.0 object.
Allowed indicators: close, MA, EMA, MACD, RSI, BollingerUpper, BollingerLower, ATR, momentum, volume_ratio.
Allowed operators: gt, lt, cross_above, cross_below. Never output Python, imports, shell, URLs, or prose.
Risk must include stop_loss_pct and max_position no greater than 0.5."""


class DeepSeekError(RuntimeError):
    pass


class DeepSeekClient:
    @retry(
        retry=retry_if_exception_type((httpx.HTTPError, DeepSeekError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=6),
        reraise=True,
    )
    def generate(self, prompt: str) -> tuple[StrategySpec, int, int]:
        if not settings.deepseek_enabled:
            raise DeepSeekError("DeepSeek is not configured")
        payload = {
            "model": settings.deepseek_model,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
            "max_tokens": 1800,
        }
        headers = {"Authorization": f"Bearer {settings.deepseek_api_key}", "Content-Type": "application/json"}
        with httpx.Client(timeout=httpx.Timeout(35, connect=8)) as client:
            response = client.post(f"{settings.deepseek_api_base.rstrip('/')}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
        body = response.json()
        try:
            content = body["choices"][0]["message"]["content"].strip().removeprefix("```json").removesuffix("```").strip()
            spec = StrategySpec.model_validate(json.loads(content))
            usage = body.get("usage", {})
            return spec, int(usage.get("prompt_tokens", 0)), int(usage.get("completion_tokens", 0))
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise DeepSeekError("DeepSeek returned an invalid StrategySpec") from exc
