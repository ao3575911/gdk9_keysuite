from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import time
from collections import deque
from threading import RLock
from typing import Any
import uuid


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ConnectionState:
    websocket: Any
    session_id: str
    api_key: str | None = None
    connection_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    connected_at: str = field(default_factory=_now_iso)
    last_seen: float = field(default_factory=time.monotonic)
    heartbeat_at: float = field(default_factory=time.monotonic)
    message_times: deque[float] = field(default_factory=deque)
    closed: bool = False

    def touch(self) -> None:
        now = time.monotonic()
        self.last_seen = now
        self.heartbeat_at = now

    def allow_message(self, max_messages_per_second: int) -> tuple[bool, float | None]:
        now = time.monotonic()
        cutoff = now - 1.0
        while self.message_times and self.message_times[0] < cutoff:
            self.message_times.popleft()
        if len(self.message_times) >= max_messages_per_second:
            retry_after = 1.0 - (now - self.message_times[0]) if self.message_times else 1.0
            return False, max(retry_after, 0.0)
        self.message_times.append(now)
        self.touch()
        return True, None

    def is_idle(self, timeout_seconds: float) -> bool:
        return (time.monotonic() - self.last_seen) >= timeout_seconds


class ConnectionManager:
    def __init__(self, *, max_messages_per_second: int = 20, max_payload_size: int = 16_384) -> None:
        self.max_messages_per_second = max_messages_per_second
        self.max_payload_size = max_payload_size
        self._lock = RLock()
        self._connections: dict[str, ConnectionState] = {}
        self._by_session: dict[str, set[str]] = {}

    def register(self, websocket: Any, session_id: str, *, api_key: str | None = None) -> ConnectionState:
        state = ConnectionState(websocket=websocket, session_id=session_id, api_key=api_key)
        with self._lock:
            self._connections[state.connection_id] = state
            self._by_session.setdefault(session_id, set()).add(state.connection_id)
        return state

    def unregister(self, connection_id: str) -> ConnectionState | None:
        with self._lock:
            state = self._connections.pop(connection_id, None)
            if state is not None:
                state.closed = True
                session_connections = self._by_session.get(state.session_id)
                if session_connections is not None:
                    session_connections.discard(connection_id)
                    if not session_connections:
                        self._by_session.pop(state.session_id, None)
            return state

    def connection_count(self, session_id: str | None = None) -> int:
        with self._lock:
            if session_id is None:
                return len(self._connections)
            return len(self._by_session.get(session_id, set()))

    def connections_for_session(self, session_id: str) -> list[ConnectionState]:
        with self._lock:
            ids = list(self._by_session.get(session_id, set()))
            return [self._connections[connection_id] for connection_id in ids if connection_id in self._connections]

    def get(self, connection_id: str) -> ConnectionState | None:
        with self._lock:
            return self._connections.get(connection_id)

    def record_message(self, connection_id: str) -> tuple[bool, float | None]:
        state = self.get(connection_id)
        if state is None:
            return False, None
        return state.allow_message(self.max_messages_per_second)

    def close_session(self, session_id: str) -> list[ConnectionState]:
        with self._lock:
            connection_ids = list(self._by_session.pop(session_id, set()))
            states = []
            for connection_id in connection_ids:
                state = self._connections.pop(connection_id, None)
                if state is not None:
                    state.closed = True
                    states.append(state)
            return states

    def active_sessions(self) -> list[str]:
        with self._lock:
            return sorted(self._by_session)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "active_connections": len(self._connections),
                "active_sessions": len(self._by_session),
                "sessions": {session_id: len(connection_ids) for session_id, connection_ids in self._by_session.items()},
                "max_messages_per_second": self.max_messages_per_second,
                "max_payload_size": self.max_payload_size,
            }
