from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import asyncio
import threading
from typing import Any, Iterable

from .symbols import LiteralSymbol


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class RuntimeEvent:
    type: str
    session_id: str
    payload: dict[str, Any]
    timestamp: str = field(default_factory=_now_iso)

    def as_message(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "session_id": self.session_id,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }


def runtime_event(event_type: str, session_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return RuntimeEvent(event_type, session_id, payload or {}).as_message()


@dataclass
class EventSubscription:
    session_id: str | None = None
    event_types: set[str] | None = None
    queue: asyncio.Queue[dict[str, Any]] = field(default_factory=asyncio.Queue)
    closed: bool = False

    def __hash__(self) -> int:
        return id(self)

    def matches(self, event: dict[str, Any]) -> bool:
        if self.closed:
            return False
        if self.session_id is not None and event.get("session_id") != self.session_id:
            return False
        if self.event_types is not None and event.get("type") not in self.event_types:
            return False
        return True

    def push(self, event: dict[str, Any]) -> None:
        if self.matches(event):
            self.queue.put_nowait(event)

    def drain_nowait(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        while True:
            try:
                items.append(self.queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        return items

    async def receive(self) -> dict[str, Any]:
        return await self.queue.get()

    def close(self) -> None:
        self.closed = True
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except asyncio.QueueEmpty:  # pragma: no cover - race-safe cleanup
                break


class EventBus:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._subscriptions: set[EventSubscription] = set()

    def subscribe(
        self,
        *,
        session_id: str | None = None,
        event_types: Iterable[str] | None = None,
    ) -> EventSubscription:
        subscription = EventSubscription(
            session_id=session_id,
            event_types=set(event_types) if event_types is not None else None,
        )
        with self._lock:
            self._subscriptions.add(subscription)
        return subscription

    def unsubscribe(self, subscription: EventSubscription) -> None:
        with self._lock:
            self._subscriptions.discard(subscription)
        subscription.close()

    def publish(self, event: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            subscriptions = tuple(self._subscriptions)
        for subscription in subscriptions:
            subscription.push(event)
        return event

    def subscriber_count(self) -> int:
        with self._lock:
            return len(self._subscriptions)


def _in_range(token: str, range_spec: str) -> bool:
    return (
        len(token) == 1
        and len(range_spec) == 3
        and range_spec[1] == "-"
        and ord(range_spec[0]) <= ord(token) <= ord(range_spec[2])
    )


def token_to_event(token: str, grammar: dict, literal: bool = False) -> dict:
    if literal:
        return {"class": "CONTENT", "value": LiteralSymbol(token)}

    symbols = grammar.get("symbols", {})
    syntax = symbols.get("syntax", {})
    control = symbols.get("control", {})

    exact = {
        syntax.get("bind"): "BIND",
        syntax.get("mode_shift"): "MODE_SHIFT",
        control.get("rollback"): "ROLLBACK",
        control.get("abort"): "ABORT",
    }
    exact.update({commit: "COMMIT" for commit in symbols.get("commit", [])})

    event_class = exact.get(token)
    if event_class is None and any(_in_range(token, spec) for spec in symbols.get("content", [])):
        event_class = "CONTENT"

    return {"class": event_class or "INVALID", "value": token}
