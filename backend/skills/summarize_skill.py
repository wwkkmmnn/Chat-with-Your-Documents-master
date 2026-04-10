from __future__ import annotations

import re

from backend.skills.base import BaseSkill


class SummarizeSkill(BaseSkill):
    name = "summarize"
    description = "Summarize intermediate tool outputs into a concise brief."

    def __init__(self, llm_service) -> None:
        self.llm_service = llm_service

    def input_schema(self) -> dict:
        return {
            "query": "str",
            "content": "str",
        }

    def run(self, **kwargs) -> dict:
        query = kwargs.get("query", "")
        content = kwargs.get("content", "").strip()
        if not content:
            return {"summary": "没有可总结的工具上下文。", "results": []}

        fallback_answer = self._fallback_summary(content)
        summary = self.llm_service.complete(
            system_prompt="你是一个总结工具，请把提供的检索上下文压缩成简短摘要。",
            user_prompt=(
                f"用户目标：{query}\n"
                "请将下面的工具结果整理成 3 到 5 句中文摘要，保留关键结论与来源线索：\n\n"
                f"{content}"
            ),
            fallback_answer=fallback_answer,
        )
        return {"summary": summary.strip(), "results": []}

    def _fallback_summary(self, content: str) -> str:
        cleaned = re.sub(r"\s+", " ", content).strip()
        return cleaned[:240] or "暂无摘要。"
