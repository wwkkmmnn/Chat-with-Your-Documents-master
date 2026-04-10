from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SessionService:
    def __init__(self, sessions_path: Path) -> None:
        self.sessions_path = Path(sessions_path)
        self.sessions_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        if not self.sessions_path.exists():
            self._write_store({"sessions": []})

    def list_sessions(self) -> list[dict[str, Any]]:
        with self._lock:
            store = self._read_store()
            sessions = [self.serialize_session(item) for item in store["sessions"]]
            return sorted(sessions, key=lambda item: item["updatedAt"], reverse=True)

    def create_session(self, title: str | None = None, session_id: str | None = None) -> dict[str, Any]:
        with self._lock:
            store = self._read_store()
            new_session = {
                "id": session_id or f"session_{uuid.uuid4().hex[:10]}",
                "title": title or "新对话",
                "createdAt": _utc_now(),
                "updatedAt": _utc_now(),
                "messages": [],
            }
            store["sessions"].append(new_session)
            self._write_store(store)
            return self.serialize_session(new_session)

    def ensure_session(self, session_id: str | None = None) -> dict[str, Any]:
        with self._lock:
            if session_id:
                session = self.get_session(session_id)
                if session:
                    return self.serialize_session(session)
            return self.create_session(session_id=session_id)

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        with self._lock:
            store = self._read_store()
            for session in store["sessions"]:
                if session["id"] == session_id:
                    return session
        return None

    def get_messages(self, session_id: str) -> list[dict[str, Any]]:
        session = self.get_session(session_id)
        if not session:
            return []
        return list(session["messages"])

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        message_type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            store = self._read_store()
            for session in store["sessions"]:
                if session["id"] != session_id:
                    continue

                message = {
                    "id": f"msg_{uuid.uuid4().hex[:12]}",
                    "role": role,
                    "type": message_type or role,
                    "content": content,
                    "metadata": metadata or {},
                    "createdAt": _utc_now(),
                }
                session["messages"].append(message)
                session["updatedAt"] = _utc_now()
                if role == "user" and session["title"] == "新对话":
                    session["title"] = content.strip()[:18] or session["title"]
                self._write_store(store)
                return message

        raise KeyError(f"Session not found: {session_id}")

    def serialize_session(self, session: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": session["id"],
            "title": session["title"],
            "createdAt": session["createdAt"],
            "updatedAt": session["updatedAt"],
            "messageCount": len(session["messages"]),
        }

    def _read_store(self) -> dict[str, Any]:
        with self.sessions_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _write_store(self, store: dict[str, Any]) -> None:
        with self.sessions_path.open("w", encoding="utf-8") as file:
            json.dump(store, file, ensure_ascii=False, indent=2)
