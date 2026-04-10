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
    event_stream = services.chat_service.stream_chat(
        session_id=request.sessionId,
        message=request.message,
        file_ids=request.fileIds,
    )
    return StreamingResponse(
        event_stream,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
