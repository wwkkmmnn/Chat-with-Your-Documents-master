from __future__ import annotations

import re

from openai import OpenAI


class LLMService:
    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self._client: OpenAI | None = None

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def complete(self, system_prompt: str, user_prompt: str, fallback_answer: str = "") -> str:
        if not self.is_configured():
            return fallback_answer or self._basic_summary(user_prompt)

        try:
            response = self._get_client().chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                stream=False,
            )
            content = response.choices[0].message.content or ""
            return content.strip() or fallback_answer
        except Exception:
            return fallback_answer or self._basic_summary(user_prompt)

    def stream(self, system_prompt: str, user_prompt: str, fallback_answer: str = ""):
        if not self.is_configured():
            yield fallback_answer or self._basic_summary(user_prompt)
            return

        try:
            stream = self._get_client().chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                stream=True,
            )
            emitted = False
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    emitted = True
                    yield delta
            if not emitted and fallback_answer:
                yield fallback_answer
        except Exception:
            yield fallback_answer or self._basic_summary(user_prompt)

    def _get_client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._client

    def _basic_summary(self, text: str) -> str:
        cleaned = re.sub(r"\s+", " ", text).strip()
        if not cleaned:
            return "当前没有可总结的内容。"
        return cleaned[:300]
