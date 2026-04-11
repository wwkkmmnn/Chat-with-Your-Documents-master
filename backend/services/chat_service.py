from __future__ import annotations

from typing import Any, Iterable

from backend.utils.sse import sse_event


class ChatService:
    def __init__(
        self,
        router_service,
        skill_registry,
        llm_service,
        session_service,
        rag_service,
    ) -> None:
        self.router_service = router_service
        self.skill_registry = skill_registry
        self.llm_service = llm_service
        self.session_service = session_service
        self.rag_service = rag_service

    def stream_chat(self, session_id: str | None, message: str, file_ids: list[str] | None = None):
        normalized_file_ids = [file_id for file_id in (file_ids or []) if file_id]
        session = self.session_service.ensure_session(session_id=session_id)
        session_identifier = session["id"]
        #文件参数标准化，创建或获取会话
        try:
            previous_messages = self.session_service.get_messages(session_identifier)
            # 将用户消息添加到会话历史中，包含文件ID的元信息
            self.session_service.add_message(
                session_identifier,
                role="user",
                content=message,
                message_type="user",
                metadata={"fileIds": normalized_file_ids},
            )

            # 决策路由，基于用户消息、文件上下文和可用工具，选择回答策略
            route = self.router_service.decide(
                message=message,
                file_ids=normalized_file_ids,
                available_file_count=len(self.rag_service.list_files()),
            )

            # 路由结果包含选择的模式（如直接回答、文档检索、网页搜索或混合）和原因，这里先将路由决策发送给前端
            yield sse_event(
                "route",
                {
                    "mode": route.mode,
                    "label": route.label,
                    "reason": route.reason,
                },
            )

            # 根据路由决策执行相应的工具，收集工具输出，并在每步都通过 SSE 发送更新给前端
            tool_outputs: list[dict[str, Any]] = []
            for tool_name in self._tool_plan(route.mode):
                yield sse_event(
                    "tool_start",
                    {
                        "tool": tool_name,
                        "label": self._tool_label(tool_name),
                        "status": "running",
                    },
                )
                result = self._run_tool(tool_name, message, normalized_file_ids, tool_outputs)
                tool_outputs.append({"tool": tool_name, **result})

                tool_payload = {
                    "tool": tool_name,
                    "label": self._tool_label(tool_name),
                    "status": "success" if result.get("summary") or result.get("results") else "empty",
                    "summary": result.get("summary", ""),
                    "items": result.get("results", []),
                }
                yield sse_event("tool_result", tool_payload)

                # 将工具结果也添加到会话历史中，作为后续回答的上下文
                self.session_service.add_message(
                    session_identifier,
                    role="tool",
                    content=tool_payload["summary"] or f"{self._tool_label(tool_name)} 已完成。",
                    message_type="tool",
                    metadata={
                        "tool": tool_name,
                        "items": tool_payload["items"][:3],
                    },
                )

            #将工具结果格式化为结构化文本
            tool_context = "\n\n".join(
                section for section in (self._format_tool_context(item) for item in tool_outputs) if section
            )
            #格式化历史消息（最近 6 条）
            history_context = self._format_history(previous_messages)

            #准备降级方案：如果 LLM API 出错，用这个内容替代,通常是工具结果的摘要
            fallback_answer = self._fallback_answer(route.mode, tool_outputs)
            assistant_chunks: list[str] = []
            
            #调用 LLM 服务的流式接口，边生成边发送给前端，同时收集完整回答以便后续存储
            for token in self.llm_service.stream(
                system_prompt=self._system_prompt(route.mode),
                user_prompt=self._user_prompt(message, history_context, tool_context),
                fallback_answer=fallback_answer,
            ):
                assistant_chunks.append(token)
                yield sse_event("token", {"text": token})

            #将完整回答添加到会话历史中，标记为助手消息，并附上使用的路由模式和工具信息
            assistant_text = "".join(assistant_chunks).strip() or fallback_answer
            self.session_service.add_message(
                session_identifier,
                role="assistant",
                content=assistant_text,
                message_type="assistant",
                metadata={"route": route.mode, "fileIds": normalized_file_ids},
            )

            yield sse_event(
                "done",
                {
                    "sessionId": session_identifier,
                    "route": route.mode,
                },
            )
        except Exception as exc:  # pragma: no cover - runtime safety path
            error_message = f"当前请求处理失败：{exc}"
            self.session_service.add_message(
                session_identifier,
                role="assistant",
                content=error_message,
                message_type="assistant",
                metadata={"route": "error"},
            )
            yield sse_event("token", {"text": error_message})
            yield sse_event("done", {"sessionId": session_identifier, "route": "error"})

    # 根据路由模式规划需要执行的工具列表，简单示例中直接映射，实际可更复杂
    def _tool_plan(self, route_mode: str) -> list[str]:
        if route_mode == "doc_search":
            return ["doc_search"]
        if route_mode == "web_search":
            return ["web_search"]
        if route_mode == "hybrid":
            return ["web_search", "doc_search", "summarize"]
        return []

    # 根据工具名称执行对应的技能，并返回结果，技能内部封装了具体的调用逻辑
    def _run_tool(
        self,
        tool_name: str,
        message: str,
        file_ids: list[str],
        tool_outputs: list[dict[str, Any]],
    ) -> dict[str, Any]:
        skill = self.skill_registry.get(tool_name)

        if tool_name == "doc_search":
            return skill.run(query=message, file_ids=file_ids, top_k=self.rag_service.max_search_results)
        if tool_name == "web_search":
            return skill.run(query=message, max_results=self.rag_service.max_search_results)
        if tool_name == "summarize":
            content = "\n\n".join(
                section for section in (self._format_tool_context(item) for item in tool_outputs) if section
            )
            return skill.run(query=message, content=content)
        return skill.run(query=message)

    def _system_prompt(self, route_mode: str) -> str:
        return (
            "你是一个多工具智能助手。"
            f"当前模式是 {route_mode}。"
            "优先依据提供的历史消息与工具上下文回答，不要编造不存在的搜索结果或文档结论。"
            "如果信息不足，要明确说明缺口。"
            "回答尽量简洁、结构清晰，并在合适时引用来源。"
        )

    def _user_prompt(self, message: str, history_context: str, tool_context: str) -> str:
        sections = [
            f"用户问题：{message}",
            f"历史对话：\n{history_context or '无'}",
            f"工具上下文：\n{tool_context or '无'}",
        ]
        return "\n\n".join(sections)

    def _format_history(self, messages: Iterable[dict[str, Any]]) -> str:
        history_lines: list[str] = []
        for item in list(messages)[-6:]:
            if item["role"] not in {"user", "assistant"}:
                continue
            prefix = "用户" if item["role"] == "user" else "助手"
            history_lines.append(f"{prefix}: {item['content']}")
        return "\n".join(history_lines)

    def _format_tool_context(self, item: dict[str, Any]) -> str:
        tool_name = item.get("tool", "")
        summary = item.get("summary", "").strip()
        results = item.get("results", [])

        if tool_name == "doc_search":
            details = [
                f"- {row['fileName']} 第{row['page'] or '?'}页：{row['snippet']}"
                for row in results
            ]
            return "\n".join(["[文档检索]", summary, *details]).strip()

        if tool_name == "web_search":
            details = [
                f"- {row['title']} | {row['url']} | {row['snippet']}"
                for row in results
            ]
            return "\n".join(["[网页搜索]", summary, *details]).strip()

        if tool_name == "summarize":
            return "\n".join(["[中间总结]", summary]).strip()

        return summary

    def _fallback_answer(self, route_mode: str, tool_outputs: list[dict[str, Any]]) -> str:
        if not tool_outputs:
            return (
                "当前未配置 DEEPSEEK_API_KEY，或模型服务暂不可用。"
                "请在 .env 中补充配置后再试。"
            )

        lines = ["当前返回的是工具检索摘要："]
        for item in tool_outputs:
            label = self._tool_label(item["tool"])
            summary = item.get("summary", "").strip() or "未获取到有效结果。"
            lines.append(f"{label}：{summary}")

        sources = []
        for item in tool_outputs:
            for result in item.get("results", []):
                source = result.get("fileName") or result.get("url")
                if source and source not in sources:
                    sources.append(source)

        if sources:
            lines.append(f"参考来源：{', '.join(sources[:4])}")
        elif route_mode == "direct_answer":
            lines.append("该问题属于直接问答场景，因此暂时没有工具来源可引用。")

        return "\n".join(lines)

    def _tool_label(self, tool_name: str) -> str:
        labels = {
            "doc_search": "文档检索",
            "web_search": "网页搜索",
            "summarize": "总结工具",
        }
        return labels.get(tool_name, tool_name)
