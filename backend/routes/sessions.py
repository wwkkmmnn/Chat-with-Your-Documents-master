from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel

from backend.app.dependencies import get_app_services

router = APIRouter()


class CreateSessionRequest(BaseModel):
    title: Optional[str] = None


@router.get("/sessions")
def list_sessions() -> dict:
    services = get_app_services()
    return {"sessions": services.session_service.list_sessions()}


@router.post("/sessions")
def create_session(payload: Optional[CreateSessionRequest] = Body(default=None)) -> dict:
    services = get_app_services()
    session = services.session_service.create_session(title=payload.title if payload else None)
    return {"session": session}


@router.get("/sessions/{session_id}/messages")
def get_session_messages(session_id: str) -> dict:
    services = get_app_services()
    session = services.session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {
        "session": services.session_service.serialize_session(session),
        "messages": session["messages"],
    }
