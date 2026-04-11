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

    # 完成接口，适合一次性获取完整回答的场景
    def complete(self, system_prompt: str, user_prompt: str, fallback_answer: str = "") -> str:
        if not self.is_configured():
            return fallback_answer or self._basic_summary(user_prompt)

        try:
            #调用 API（同步方式），传入系统提示和用户提示，获取完整回答
            response = self._get_client().chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2, #降低温度参数以获得更确定性的回答，减少随机性
                stream=False, #一次性获取完整回答，适合 complete 方法，stream 方法会分块获取
            )
            content = response.choices[0].message.content or ""
            return content.strip() or fallback_answer
        except Exception:
            return fallback_answer or self._basic_summary(user_prompt)

    # 流式接口，适合边生成边展示的场景，使用生成器 yield 逐步返回内容
    def stream(self, system_prompt: str, user_prompt: str, fallback_answer: str = ""):
        if not self.is_configured():
            yield fallback_answer or self._basic_summary(user_prompt)
            return

        try:
            #调用 API 的流式接口，获取一个生成器对象，迭代它可以逐步获得生成的内容块
            stream = self._get_client().chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                stream=True, #开启流式模式，允许逐步获取生成内容，适合 stream 方法，complete 方法会一次性获取完整回答
            )
            emitted = False
            for chunk in stream:
                if not chunk.choices:
                    continue
                #从每个返回的块中提取增量内容（delta），如果有内容则 yield 给调用方，允许边生成边展示；如果没有内容但有 fallback_answer，则在流结束后 yield 降级方案
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

    # 简单的文本清理和截断，作为没有 API 配置时的降级方案，确保至少返回一些有用的信息而不是完全空白
    def _basic_summary(self, text: str) -> str:
        cleaned = re.sub(r"\s+", " ", text).strip()
        if not cleaned:
            return "当前没有可总结的内容。"
        return cleaned[:300]
