from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from threading import RLock
import time
from typing import Any

from .errors import KeySuiteError


class AuthenticationError(KeySuiteError):
    """Raised when an API key is missing or invalid."""


class RateLimitExceededError(KeySuiteError):
    """Raised when a request or connection exceeds the configured limit."""


@dataclass(frozen=True)
class AuthConfig:
    api_keys: set[str]
    header_name: str = "X-API-Key"

    @property
    def enabled(self) -> bool:
        return bool(self.api_keys)

    def authenticate(self, value: str | None) -> str:
        if not self.enabled:
            return value or ""
        if value is None or value not in self.api_keys:
            raise AuthenticationError("invalid or missing API key")
        return value


class SlidingWindowRateLimiter:
    def __init__(self, *, limit: int, window_seconds: float) -> None:
        if limit <= 0:
            raise ValueError("limit must be positive")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        self.limit = limit
        self.window_seconds = window_seconds
        self._lock = RLock()
        self._events: dict[str, deque[float]] = {}

    def allow(self, key: str, cost: int = 1) -> tuple[bool, float | None]:
        now = time.monotonic()
        with self._lock:
            queue = self._events.setdefault(key, deque())
            cutoff = now - self.window_seconds
            while queue and queue[0] < cutoff:
                queue.popleft()
            if len(queue) + cost > self.limit:
                retry_after = self.window_seconds - (now - queue[0]) if queue else self.window_seconds
                return False, max(retry_after, 0.0)
            for _ in range(cost):
                queue.append(now)
            return True, None

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "limit": self.limit,
                "window_seconds": self.window_seconds,
                "keys": {key: len(queue) for key, queue in self._events.items()},
            }
