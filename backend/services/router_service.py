from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RouteDecision:
    mode: str
    label: str
    reason: str


class RouterService:
    _labels = {
        "direct_answer": "直接回答",
        "doc_search": "文档问答",
        "web_search": "网页搜索",
        "hybrid": "混合模式",
    }

    _web_keywords = (
        "搜索",
        "搜一下",
        "查一下",
        "查一查",
        "最新",
        "联网",
        "网页",
        "web",
        "search",
        "news",
        "google",
        "bing",
        "duckduckgo",
    )
    _doc_keywords = (
        "文档",
        "pdf",
        "文件",
        "资料",
        "这份",
        "这篇",
        "上传",
        "论文",
        "根据文档",
        "基于文档",
    )
    _hybrid_keywords = (
        "结合",
        "综合",
        "对比",
        "同时",
        "再结合",
        "简历",
        "融合",
    )

    def decide(
        self,
        message: str,
        file_ids: list[str] | None = None,
        available_file_count: int = 0,
    ) -> RouteDecision:
        normalized = message.lower()
        selected_files = bool(file_ids)
        has_any_files = selected_files or available_file_count > 0
        wants_web = any(keyword in normalized for keyword in self._web_keywords)
        wants_doc = any(keyword in normalized for keyword in self._doc_keywords)
        wants_hybrid = any(keyword in normalized for keyword in self._hybrid_keywords)

        if wants_web and (wants_doc or (selected_files and wants_hybrid)):
            return self._decision("hybrid", "问题同时涉及上传文档和外部信息检索。")

        if wants_web and selected_files and ("文档" in message or "文件" in message):
            return self._decision("hybrid", "已选择文档且问题显式要求联网补充。")

        if wants_web:
            return self._decision("web_search", "问题包含明显的搜索或最新信息意图。")

        if selected_files:
            return self._decision("doc_search", "当前已选择文档，优先走文档问答。")

        if wants_doc and has_any_files:
            return self._decision("doc_search", "问题提到了文档内容，且存在可检索文件。")

        return self._decision("direct_answer", "问题可直接由模型回答。")

    def _decision(self, mode: str, reason: str) -> RouteDecision:
        return RouteDecision(mode=mode, label=self._labels[mode], reason=reason)
