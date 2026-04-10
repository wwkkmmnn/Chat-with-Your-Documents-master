from __future__ import annotations

from backend.skills.base import BaseSkill


class DocSearchSkill(BaseSkill):
    name = "doc_search"
    description = "Search uploaded documents and return the most relevant snippets."

    def __init__(self, rag_service) -> None:
        self.rag_service = rag_service

    def input_schema(self) -> dict:
        return {
            "query": "str",
            "file_ids": "list[str]",
            "top_k": "int",
        }

    def run(self, **kwargs) -> dict:
        query = kwargs.get("query", "")
        file_ids = kwargs.get("file_ids")
        top_k = kwargs.get("top_k", self.rag_service.max_search_results)
        results = self.rag_service.search(query=query, file_ids=file_ids, top_k=top_k)

        if not results:
            return {
                "summary": "没有命中文档片段，请先上传文件或调整提问方式。",
                "results": [],
            }

        source_names = []
        for item in results:
            if item["fileName"] not in source_names:
                source_names.append(item["fileName"])

        return {
            "summary": f"命中 {len(results)} 个文档片段，主要来源：{'、'.join(source_names[:3])}。",
            "results": results,
        }
