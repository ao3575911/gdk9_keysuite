from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from threading import RLock
from typing import Any, Protocol

from .errors import ConfigurationError


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class SessionRecord:
    session_id: str
    snapshot: dict[str, Any]
    history: list[dict[str, Any]] = field(default_factory=list)
    redo: list[dict[str, Any]] = field(default_factory=list)
    updated_at: str = field(default_factory=_now_iso)


class StateStore(Protocol):
    def save_session(
        self,
        session_id: str,
        snapshot: dict[str, Any],
        *,
        history: list[dict[str, Any]] | None = None,
        redo: list[dict[str, Any]] | None = None,
    ) -> None: ...

    def load_session(self, session_id: str) -> SessionRecord | None: ...

    def delete_session(self, session_id: str) -> None: ...

    def save_job_state(self, job_id: str, state: dict[str, Any]) -> None: ...

    def load_job_state(self, job_id: str) -> dict[str, Any] | None: ...


class InMemoryStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._sessions: dict[str, SessionRecord] = {}
        self._jobs: dict[str, dict[str, Any]] = {}

    def save_session(
        self,
        session_id: str,
        snapshot: dict[str, Any],
        *,
        history: list[dict[str, Any]] | None = None,
        redo: list[dict[str, Any]] | None = None,
    ) -> None:
        with self._lock:
            self._sessions[session_id] = SessionRecord(
                session_id=session_id,
                snapshot=dict(snapshot),
                history=list(history or []),
                redo=list(redo or []),
            )

    def load_session(self, session_id: str) -> SessionRecord | None:
        with self._lock:
            return self._sessions.get(session_id)

    def delete_session(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)

    def save_job_state(self, job_id: str, state: dict[str, Any]) -> None:
        with self._lock:
            self._jobs[job_id] = dict(state)

    def load_job_state(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            state = self._jobs.get(job_id)
            return dict(state) if state is not None else None

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "sessions": {session_id: record.snapshot for session_id, record in self._sessions.items()},
                "job_state": dict(self._jobs),
            }


class RedisStore:
    def __init__(self, url: str | None = None, client: Any | None = None) -> None:
        self._lock = RLock()
        self._client = client
        self._url = url
        if self._client is None and self._url is not None:
            try:
                import redis  # type: ignore
            except ModuleNotFoundError as exc:  # pragma: no cover - optional extra
                raise ConfigurationError("redis extra is not installed") from exc
            self._client = redis.Redis.from_url(self._url)

    def _ensure_client(self) -> Any:
        if self._client is None:
            raise ConfigurationError("RedisStore requires a redis client or connection URL")
        return self._client

    def save_session(
        self,
        session_id: str,
        snapshot: dict[str, Any],
        *,
        history: list[dict[str, Any]] | None = None,
        redo: list[dict[str, Any]] | None = None,
    ) -> None:
        client = self._ensure_client()
        record = SessionRecord(session_id, dict(snapshot), list(history or []), list(redo or []))
        client.set(f"keysuite:session:{session_id}", json.dumps(record.__dict__, separators=(",", ":")))

    def load_session(self, session_id: str) -> SessionRecord | None:
        client = self._ensure_client()
        payload = client.get(f"keysuite:session:{session_id}")
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        if isinstance(payload, str):
            return SessionRecord(**json.loads(payload))
        if isinstance(payload, SessionRecord):  # pragma: no cover - test double convenience
            return payload
        raise ConfigurationError("RedisStore returned an unsupported session payload")

    def delete_session(self, session_id: str) -> None:
        client = self._ensure_client()
        client.delete(f"keysuite:session:{session_id}")

    def save_job_state(self, job_id: str, state: dict[str, Any]) -> None:
        client = self._ensure_client()
        client.set(f"keysuite:job:{job_id}", json.dumps(dict(state), separators=(",", ":")))

    def load_job_state(self, job_id: str) -> dict[str, Any] | None:
        client = self._ensure_client()
        payload = client.get(f"keysuite:job:{job_id}")
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        if isinstance(payload, str):
            return dict(json.loads(payload))
        if isinstance(payload, dict):  # pragma: no cover - test double convenience
            return dict(payload)
        return payload
