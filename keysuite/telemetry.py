from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import logging
import threading
import time
import uuid
from collections import deque
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # pragma: no cover - logging shim
        payload: dict[str, Any] = {
            "timestamp": _now_iso(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def configure_json_logging(name: str = "keysuite", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    logger.propagate = False
    return logger


def trace_event(name: str, *, attributes: dict[str, Any] | None = None) -> dict[str, Any]:
    trace_id = uuid.uuid4().hex
    span_id = uuid.uuid4().hex[:16]
    payload = {
        "trace_id": trace_id,
        "span_id": span_id,
        "name": name,
        "timestamp": _now_iso(),
        "attributes": attributes or {},
    }
    return payload


@dataclass
class RuntimeMetrics:
    active_sessions: int = 0
    active_connections: int = 0
    tokens_processed: int = 0
    requests_total: int = 0
    errors_total: int = 0
    total_latency_ms: float = 0.0
    queue_depth: int = 0
    _token_timestamps: deque[float] = field(default_factory=lambda: deque(maxlen=8192), repr=False)
    _lock: threading.RLock = field(default_factory=threading.RLock, init=False, repr=False)

    def set_active_sessions(self, count: int) -> None:
        with self._lock:
            self.active_sessions = count

    def set_active_connections(self, count: int) -> None:
        with self._lock:
            self.active_connections = count

    def set_queue_depth(self, depth: int) -> None:
        with self._lock:
            self.queue_depth = depth

    def record_tokens(self, count: int = 1) -> None:
        now = time.monotonic()
        with self._lock:
            self.tokens_processed += count
            for _ in range(count):
                self._token_timestamps.append(now)

    def record_request(self, latency_ms: float, *, tokens: int = 0, error: bool = False) -> None:
        with self._lock:
            self.requests_total += 1
            self.total_latency_ms += latency_ms
            if error:
                self.errors_total += 1
        if tokens:
            self.record_tokens(tokens)

    def record_error(self) -> None:
        with self._lock:
            self.errors_total += 1

    def tokens_per_second(self, window_seconds: float = 1.0) -> float:
        cutoff = time.monotonic() - window_seconds
        with self._lock:
            while self._token_timestamps and self._token_timestamps[0] < cutoff:
                self._token_timestamps.popleft()
            return len(self._token_timestamps) / max(window_seconds, 1e-9)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            avg_latency = self.total_latency_ms / self.requests_total if self.requests_total else 0.0
            error_rate = self.errors_total / self.requests_total if self.requests_total else 0.0
            return {
                "active_sessions": self.active_sessions,
                "active_connections": self.active_connections,
                "tokens_processed": self.tokens_processed,
                "tokens_per_second": self.tokens_per_second(),
                "avg_latency_ms": round(avg_latency, 3),
                "error_rate": round(error_rate, 4),
                "requests_total": self.requests_total,
                "errors_total": self.errors_total,
                "queue_depth": self.queue_depth,
            }
