from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.analysis.prompts import SYSTEM_PROMPT, build_user_prompt
from app.analysis.schema import AnalysisResult
from app.config import Settings

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def analyze_news(self, *, source_name: str, title: str, summary: str) -> AnalysisResult:
        if not self.settings.llm_api_key.strip():
            logger.warning('LLM_API_KEY missing; returning neutral analysis')
            return AnalysisResult.neutral_fallback('تحلیل LLM غیرفعال است.')

        payload = {
            'model': self.settings.llm_model,
            'temperature': 0.2,
            'response_format': {'type': 'json_object'},
            'messages': [
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {
                    'role': 'user',
                    'content': build_user_prompt(source_name=source_name, title=title, summary=summary),
                },
            ],
        }

        last_error: Exception | None = None
        for attempt in range(2):
            try:
                raw = await self._chat(payload)
                return self._parse_json(raw)
            except Exception as error:  # noqa: BLE001
                last_error = error
                logger.warning('LLM attempt %s failed: %s', attempt + 1, error)
        logger.error('LLM failed after retries: %s', last_error)
        return AnalysisResult.neutral_fallback('تحلیل خودکار موقتاً در دسترس نیست.')

    async def _chat(self, payload: dict[str, Any]) -> str:
        headers = {
            'Authorization': f'Bearer {self.settings.llm_api_key}',
            'Content-Type': 'application/json',
        }
        url = f"{self.settings.llm_base_url.rstrip('/')}/chat/completions"
        timeout = httpx.Timeout(self.settings.llm_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content')
        if not isinstance(content, str) or not content.strip():
            raise ValueError('empty LLM content')
        return content

    def _parse_json(self, content: str) -> AnalysisResult:
        try:
            parsed = json.loads(content)
            return AnalysisResult.model_validate(parsed)
        except Exception as error:  # noqa: BLE001
            raise ValueError(f'invalid analysis JSON: {error}') from error
