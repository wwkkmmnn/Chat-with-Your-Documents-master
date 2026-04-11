from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.app.dependencies import get_app_services

router = APIRouter()


class ChatStreamRequest(BaseModel):
    sessionId: Optional[str] = None
    message: str
    fileIds: List[str] = Field(default_factory=list)


@router.post("/chat/stream")
async def stream_chat(request: ChatStreamRequest) -> StreamingResponse:
    services = get_app_services()
    #请求方 (client): 发送单个 POST 请求，响应方 (server): 用 生成器 yield 多个 SSE 事件
    #每个SSE事件由 event: 和 data: 两行组成，事件之间用 两个换行符 分隔（\n\n）
    event_stream = services.chat_service.stream_chat(
        session_id=request.sessionId,
        message=request.message,
        file_ids=request.fileIds,
    )
    #FastAPI: 用 StreamingResponse 将生成器转成 HTTP 流，设置正确的 Content-Type 和 SSE 相关的 headers，确保前端能正确处理流式响应
    #Step 1: 发送响应头;Step 2: 迭代生成器(从生成器获得一个SSE事件)，逐个发送数据块;Step 3: 生成器完成，发送最后一个空块
    return StreamingResponse(
        event_stream,
        media_type="text/event-stream", #告诉客户端这是一个 SSE 流
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive", #保持连接不断开，允许持续发送事件
            "X-Accel-Buffering": "no",
        },
    )

"""
客户端与后端的交互流程示例：

客户端                              后端                          HTTP连接
  │                                  │                               │
  ├─ POST /api/chat/stream ────────→ │                               │
  │ { message, fileIds }             │                               │
  │                                  ├─ stream_chat() 返回生成器     │
  │                                  │                               │
  │                                  ├─ StreamingResponse 包装       │
  │                                  │                      ↓ 发送响应头
  │ ← 200 OK (Content-Type: SSE) ────────────────────────────────────┤
  │ Connection: keep-alive           │                      保持连接   │
  │                                  │                               │
  │                                  ├─ 执行 yield sse_event("route")
  │ ← event: route                   │                      ↓ 发送body
  │   data: {...}                    │         <─────────────────────┤
  │   (空行)                          │                               │
  │                                  ├─ 执行 yield sse_event("tool_start")
  │ ← event: tool_start              │                      ↓ 发送body
  │   data: {...}                    │         <─────────────────────┤
  │   (空行)                          │                               │
  │                                  ├─ [执行工具代码，耗时1秒]       │
  │                                  │                               │
  │                                  ├─ 执行 yield sse_event("tool_result")
  │ ← event: tool_result             │                      ↓ 发送body
  │   data: {...}                    │         <─────────────────────┤
  │   (空行)                          │                               │
  │                                  ├─ [调用 LLM 生成 token]        │
  │                                  │                               │
  │ ← event: token                   │─ for token in stream:        │
  │   data: {"text":"根"}             │  yield sse_event("token")    │
  │   (空行)                          │                      ↓ 发送body
  │ ← event: token                   │         <─────────────────────┤
  │   data: {"text":"据"}             │                               │
  │   (空行)                          │                      ↓ 发送body
  │ ← event: token                   │         <─────────────────────┤
  │   data: {"text":"文"}             │                               │
  │   (空行)                          │                      ↓ 发送body
  │ ← event: token                   │         <─────────────────────┤
  │   data: {"text":"档"}             │                               │
  │   (空行)                          │                      ↓ 发送body
  │ ← ... 更多 token ...              │         <─────────────────────┤
  │                                  │                               │
  │                                  ├─ 执行 yield sse_event("done")
  │ ← event: done                    │                      ↓ 发送body
  │   data: {...}                    │         <─────────────────────┤
  │   (空行)                          │                               │
  │                                  ├─ 生成器完成，关闭连接
  │ ← EOF                            │                      关闭       │
  │ (连接关闭)                        │                               │
  │                                  │                               │


"""