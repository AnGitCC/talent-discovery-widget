"""WebSocket connection and session context management."""
import json
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SessionContext:
    """Per-session state that persists across messages."""
    session_id: str
    created_at: float = field(default_factory=time.time)
    history: list[dict] = field(default_factory=list)
    cached_candidates: list[dict] = field(default_factory=list)
    selected_ids: list[str] = field(default_factory=list)
    fullscreen: bool = False
    # Per-session result cache — avoid redundant AI calls
    cached_reports: dict[str, dict] = field(default_factory=dict)
    cached_compares: dict[str, dict] = field(default_factory=dict)
    cached_profiles: dict[str, dict] = field(default_factory=dict)

    def add_message(self, role: str, content: str, msg_type: str = "text"):
        self.history.append({"role": role, "content": content, "type": msg_type})
        if len(self.history) > 20:
            self.history = self.history[-20:]

    def compare_key(self, ids: list[str]) -> str:
        return ",".join(sorted(ids))


class WSManager:
    """Manages WebSocket connections and session contexts."""

    def __init__(self):
        self._sessions: dict[str, SessionContext] = {}

    def get_or_create(self, session_id: str) -> SessionContext:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionContext(session_id=session_id)
        return self._sessions[session_id]

    def get(self, session_id: str) -> SessionContext | None:
        return self._sessions.get(session_id)

    def remove(self, session_id: str):
        self._sessions.pop(session_id, None)

    def cleanup_stale(self, max_age_seconds: int = 3600):
        """Remove sessions older than max_age_seconds."""
        now = time.time()
        stale = [
            sid for sid, ctx in self._sessions.items()
            if now - ctx.created_at > max_age_seconds
        ]
        for sid in stale:
            self._sessions.pop(sid, None)


ws_manager = WSManager()
