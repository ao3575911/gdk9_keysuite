from __future__ import annotations

import asyncio
import re
import uuid
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .config import RuntimeConfig
from .errors import (
    ConfigurationError,
    HistoryError,
    MacroExpansionError,
    RuntimeLimitError,
    SessionNotFoundError,
    TokenValidationError,
)
from .events import EventBus, runtime_event, token_to_event
from .grammar import Grammar
from .grammar_loader import load_grammar
from .persistence import InMemoryStore, RedisStore, StateStore
from .telemetry import RuntimeMetrics
from .reducer import reduce_buffer
from .symbols import BufferedSymbol, LiteralSymbol, symbol_text
from .transitions import generate_transition_table

TOKEN_PATTERN = re.compile(r"^[^\s\x00]+$")
MACRO_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")


def _stringify_value(value) -> str:
    if isinstance(value, LiteralSymbol):
        return value.value
    return str(value)


def _stringify_buffer(buffer: list[BufferedSymbol]) -> list[str]:
    return [_stringify_value(symbol) for symbol in buffer]


@dataclass(frozen=True)
class SessionSnapshot:
    state: str
    buffer: tuple[tuple[str, str], ...]
    mode: str | None
    outputs: tuple[str, ...]
    cursor: int
    escaped: bool
    error: dict | None
    trace_size: int


def _snapshot_to_dict(snapshot: SessionSnapshot) -> dict[str, Any]:
    return {
        "state": snapshot.state,
        "buffer": list(snapshot.buffer),
        "mode": snapshot.mode,
        "outputs": list(snapshot.outputs),
        "cursor": snapshot.cursor,
        "escaped": snapshot.escaped,
        "error": dict(snapshot.error) if snapshot.error else None,
        "trace_size": snapshot.trace_size,
    }


class IMEKernel:
    def __init__(self, transitions: dict, reducer=reduce_buffer):
        self.transitions = transitions
        self.reducer = reducer
        self.reset()

    def reset(self):
        self.state = "IDLE"
        self.buffer: list[BufferedSymbol] = []
        self.mode: str | None = None

    def handle(self, event: dict):
        event_class = event["class"]
        value = event.get("value")
        rule = self.transitions.get(self.state, {}).get(event_class)

        if rule is None:
            self.state = "ERROR"
            return None

        next_state, action = rule
        output = self.apply(action, value)
        self.state = next_state
        return output

    def apply(self, action: str, value):
        if action == "append":
            self.buffer.append(value)
        elif action == "mark_bind":
            self.buffer.append(".")
        elif action == "set_mode":
            self.mode = "".join(symbol_text(symbol) for symbol in self.buffer) if self.buffer else None
            self.buffer.clear()
        elif action == "pop":
            if self.buffer:
                self.buffer.pop()
        elif action == "clear":
            self.reset()
        elif action == "reduce_and_emit":
            output = self.reducer(self.buffer, self.mode)
            self.reset()
            return output
        return None


def _validate_token_shape(token: str) -> None:
    if not isinstance(token, str) or not token:
        raise TokenValidationError("token must be a non-empty string")
    if not TOKEN_PATTERN.match(token):
        raise TokenValidationError(f"token contains whitespace or control characters: {token!r}")


def _token_is_valid_for_macro(token: str, grammar: Grammar | dict) -> bool:
    event = token_to_event(token, grammar)
    escape_token = grammar.get("symbols", {}).get("escape", {}).get("literal")
    return event["class"] != "INVALID" or token == escape_token


@dataclass
class RuntimeSession:
    grammar: Grammar | dict
    table: dict
    config: RuntimeConfig = field(default_factory=RuntimeConfig)
    auto_commit: bool = True
    debug_level: int = 0
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    event_bus: EventBus | None = None
    metrics: RuntimeMetrics | None = None
    store: StateStore | None = None
    kernel: IMEKernel | None = None
    trace: list[dict] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    error: dict | None = None
    escaped: bool = False
    cursor: int = 0
    macros: dict[str, list[str]] = field(default_factory=dict)
    last_accessed_at: float = field(default_factory=time.monotonic)
    _history: list[SessionSnapshot] = field(default_factory=list, init=False, repr=False)
    _redo: list[SessionSnapshot] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        self.kernel = IMEKernel(self.table, reduce_buffer)
        loaded_macros = {**self.config.macros, **self.macros}
        self.macros = {name: [] for name in loaded_macros}
        for name, tokens in loaded_macros.items():
            self.register_macro(name, list(tokens))
        self._history = [self._snapshot_state()]
        self.touch()
        self._persist_state()

    def _kernel(self) -> IMEKernel:
        if self.kernel is None:
            raise HistoryError("runtime kernel not initialized")
        return self.kernel

    def touch(self) -> None:
        self.last_accessed_at = time.monotonic()

    def _publish(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        event = runtime_event(event_type, self.session_id, payload)
        if self.event_bus is not None:
            self.event_bus.publish(event)
        return event

    def _persist_state(self) -> None:
        if self.store is None:
            return
        self.store.save_session(
            self.session_id,
            self.result(),
            history=[_snapshot_to_dict(snapshot) for snapshot in self._history],
            redo=[_snapshot_to_dict(snapshot) for snapshot in self._redo],
        )

    @property
    def escape_token(self) -> str | None:
        return self.grammar.get("symbols", {}).get("escape", {}).get("literal")

    def _snapshot_state(self) -> SessionSnapshot:
        kernel = self._kernel()
        return SessionSnapshot(
            state=kernel.state,
            buffer=tuple(
                ("literal", symbol.value) if isinstance(symbol, LiteralSymbol) else ("symbol", str(symbol))
                for symbol in kernel.buffer
            ),
            mode=kernel.mode,
            outputs=tuple(self.outputs),
            cursor=self.cursor,
            escaped=self.escaped,
            error=self.error.copy() if self.error else None,
            trace_size=len(self.trace),
        )

    def snapshot(self) -> dict:
        self.touch()
        kernel = self._kernel()
        return {
            "session_id": self.session_id,
            "state": kernel.state,
            "buffer": _stringify_buffer(kernel.buffer),
            "mode": kernel.mode,
            "debug_level": self.debug_level,
            "escaped": self.escaped,
            "cursor": self.cursor,
            "history_size": len(self._history),
            "redo_size": len(self._redo),
            "macros": sorted(self.macros),
        }

    def _record_error(self, token: str, event_class: str, message: str, error_type: str) -> None:
        self.error = {
            "token": token,
            "event_class": event_class,
            "message": message,
            "type": error_type,
        }

    def _push_history(self) -> None:
        self._history.append(self._snapshot_state())
        if len(self._history) > self.config.history_limit:
            self._history.pop(0)
        self._redo.clear()

    def _restore(self, snapshot: SessionSnapshot) -> None:
        kernel = self._kernel()
        kernel.state = snapshot.state
        kernel.buffer = [
            LiteralSymbol(value) if kind == "literal" else value for kind, value in snapshot.buffer
        ]
        kernel.mode = snapshot.mode
        self.outputs = list(snapshot.outputs)
        self.cursor = snapshot.cursor
        self.escaped = snapshot.escaped
        self.error = snapshot.error.copy() if snapshot.error else None
        self.trace = self.trace[: snapshot.trace_size]

    def _validate_limits_before_event(self, event_class: str) -> None:
        kernel = self._kernel()
        if event_class in {"CONTENT", "BIND"} and len(kernel.buffer) >= self.config.max_buffer_size:
            raise RuntimeLimitError(f"buffer limit exceeded: {self.config.max_buffer_size}")

    def _trace_event(self, entry: dict) -> None:
        self.trace.append(entry)

    def _handle_event(self, token: str, literal: bool = False) -> None:
        kernel = self._kernel()
        _validate_token_shape(token)
        event = token_to_event(token, self.grammar, literal=literal)
        if event["class"] == "INVALID":
            raise TokenValidationError("Token has no GDk9 jurisdiction or no valid transition")

        self._validate_limits_before_event(event["class"])
        from_state = kernel.state
        before_buffer = _stringify_buffer(kernel.buffer)
        rule = self.table.get(from_state, {}).get(event["class"])
        before = self.snapshot() if self.debug_level >= 3 else None
        output = kernel.handle(event)
        if output is not None:
            self.outputs.append(output)
        after_buffer = _stringify_buffer(kernel.buffer)
        after = self.snapshot() if self.debug_level >= 3 else None
        step = {
            "type": "transition",
            "token": token,
            "from_state": from_state,
            "event_class": event["class"],
            "value": _stringify_value(event["value"]),
            "to_state": kernel.state,
            "action": rule[1] if rule else "error",
            "output": output,
            "literal": literal,
            "cursor": self.cursor,
        }
        if before is not None:
            step["before"] = before
        if after is not None:
            step["after"] = after
        self._trace_event(step)
        self._publish(
            "STATE_TRANSITION",
            {
                "token": token,
                "literal": literal,
                "from_state": from_state,
                "to_state": kernel.state,
                "event_class": event["class"],
                "action": rule[1] if rule else "error",
                "cursor": self.cursor,
            },
        )
        if after_buffer != before_buffer:
            self._publish(
                "BUFFER_UPDATED",
                {
                    "token": token,
                    "literal": literal,
                    "buffer": after_buffer,
                    "mode": kernel.mode,
                    "cursor": self.cursor,
                },
            )
        if output is not None:
            self._publish(
                "COMMIT",
                {
                    "token": token,
                    "output": output,
                    "buffer": after_buffer,
                    "mode": kernel.mode,
                    "cursor": self.cursor,
                },
            )
        self.cursor += 1
        self._push_history()
        if kernel.state == "ERROR":
            self._record_error(
                token,
                event["class"],
                "Token has no GDk9 jurisdiction or no valid transition",
                "TokenValidationError",
            )
            self._publish(
                "ERROR",
                {
                    "token": token,
                    "event_class": event["class"],
                    "message": "Token has no GDk9 jurisdiction or no valid transition",
                    "error_type": "TokenValidationError",
                    "cursor": self.cursor,
                },
            )
        else:
            self.error = None

    def _expand_macro(self, token: str, depth: int, seen: tuple[str, ...]) -> list[str]:
        if token not in self.macros:
            return [token]
        if token in seen:
            raise MacroExpansionError(f"recursive macro expansion detected: {' -> '.join((*seen, token))}")
        if depth >= self.config.max_macro_expansion_depth:
            raise MacroExpansionError(
                f"macro expansion depth exceeded: {self.config.max_macro_expansion_depth}"
            )
        expanded: list[str] = []
        for part in self.macros[token]:
            if part in self.macros:
                expanded.extend(self._expand_macro(part, depth + 1, seen + (token,)))
            else:
                expanded.append(part)
        return expanded

    def register_macro(self, name: str, tokens: list[str]) -> None:
        self.touch()
        if not isinstance(name, str) or not MACRO_NAME_PATTERN.match(name):
            raise MacroExpansionError(f"invalid macro name: {name!r}")
        if _token_is_valid_for_macro(name, self.grammar):
            raise MacroExpansionError(f"macro name conflicts with grammar token: {name}")
        if not isinstance(tokens, list) or not all(isinstance(token, str) for token in tokens):
            raise MacroExpansionError("macro tokens must be a list of strings")
        if len(tokens) > self.config.max_token_count:
            raise RuntimeLimitError("macro token count exceeds configured limit")
        for token in tokens:
            _validate_token_shape(token)
            if token not in self.macros and not _token_is_valid_for_macro(token, self.grammar):
                raise MacroExpansionError(f"macro token is not valid for grammar: {token!r}")
        self.macros[name] = list(tokens)
        self._persist_state()

    def unregister_macro(self, name: str) -> None:
        self.touch()
        self.macros.pop(name, None)
        self._persist_state()

    def expand_macro(self, name: str) -> list[str]:
        self.touch()
        if name not in self.macros:
            raise MacroExpansionError(f"unknown macro: {name}")
        return self._expand_macro(name, 0, ())

    def process_token(self, token: str, *, literal: bool = False, depth: int = 0, seen: tuple[str, ...] = ()) -> list[dict]:
        start = time.perf_counter()
        had_error = False
        self.touch()
        try:
            _validate_token_shape(token)
            if self.cursor >= self.config.max_token_count:
                raise RuntimeLimitError(f"token limit exceeded: {self.config.max_token_count}")

            self._publish(
                "TOKEN_ACCEPTED",
                {
                    "token": token,
                    "literal": literal,
                    "cursor": self.cursor,
                    "state": self._kernel().state,
                },
            )

            if literal:
                self._handle_event(token, literal=True)
                if self._kernel().state == "ERROR":
                    had_error = True
                return [self.trace[-1]]

            if self.escaped:
                self._handle_event(token, literal=True)
                self.escaped = False
                if self._kernel().state == "ERROR":
                    had_error = True
                return [self.trace[-1]]

            escape_token = self.escape_token
            if escape_token and token == escape_token:
                entry = {
                    "type": "escape",
                    "from_state": self.kernel.state if self.kernel else "IDLE",
                    "event_class": "ESCAPE",
                    "value": token,
                    "to_state": self.kernel.state if self.kernel else "IDLE",
                    "action": "escape_next",
                    "output": None,
                    "literal": False,
                    "cursor": self.cursor,
                }
                self.trace.append(entry)
                self.escaped = True
                self._publish(
                    "STATE_TRANSITION",
                    {
                        "token": token,
                        "literal": False,
                        "from_state": entry["from_state"],
                        "to_state": entry["to_state"],
                        "event_class": "ESCAPE",
                        "action": "escape_next",
                        "cursor": self.cursor,
                    },
                )
                self._persist_state()
                return [entry]

            if token in self.macros:
                expanded = self._expand_macro(token, depth, seen)
                expansion_event = {
                    "type": "macro_expansion",
                    "macro": token,
                    "expanded": list(expanded),
                    "cursor": self.cursor,
                }
                self._trace_event(expansion_event)
                self._publish(
                    "MACRO_EXPANDED",
                    {
                        "macro": token,
                        "expanded": list(expanded),
                        "cursor": self.cursor,
                    },
                )
                events = [expansion_event]
                for part in expanded:
                    events.extend(self.process_token(part, literal=False, depth=depth + 1, seen=seen + (token,)))
                    if self._kernel().state == "ERROR":
                        had_error = True
                        break
                return events

            self._handle_event(token, literal=literal)
            if self._kernel().state == "ERROR":
                had_error = True
            return [self.trace[-1]]
        except (TokenValidationError, MacroExpansionError, RuntimeLimitError) as exc:
            had_error = True
            kernel = self._kernel()
            kernel.state = "ERROR"
            self._record_error(token, "INVALID", str(exc), exc.__class__.__name__)
            error_event = {
                "type": "error",
                "token": token,
                "state": kernel.state,
                "message": str(exc),
                "error_type": exc.__class__.__name__,
                "cursor": self.cursor,
            }
            self._trace_event(error_event)
            self._publish(
                "ERROR",
                {
                    "token": token,
                    "message": str(exc),
                    "error_type": exc.__class__.__name__,
                    "cursor": self.cursor,
                },
            )
            self._push_history()
            return [error_event]
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            if self.metrics is not None:
                self.metrics.record_request(elapsed_ms, tokens=1, error=had_error)
            self._persist_state()

    def feed(self, token: str) -> None:
        self.process_token(token)

    def finalize(self) -> None:
        self.touch()
        kernel = self._kernel()
        if self.error is None and self.escaped:
            kernel.state = "ERROR"
            self._record_error(
                self.escape_token or "_",
                "ESCAPE",
                "Escape marker must be followed by a literal token",
                "TokenValidationError",
            )
            self._publish(
                "ERROR",
                {
                    "token": self.escape_token or "_",
                    "message": "Escape marker must be followed by a literal token",
                    "error_type": "TokenValidationError",
                    "cursor": self.cursor,
                },
            )
            self.escaped = False
            self._push_history()
            self._persist_state()
            return

        if self.auto_commit and self.error is None and kernel.state in {"COMPOSE", "MODE"}:
            self._handle_event("SPACE")
        self._persist_state()

    def process(self, tokens: list[str], finalize: bool = True) -> dict:
        self.touch()
        for token in tokens:
            self.feed(token)
        if finalize:
            self.finalize()
        return self.result()

    def result(self) -> dict:
        self.touch()
        kernel = self._kernel()
        return {
            "status": "error" if kernel.state == "ERROR" else "ok",
            "state": kernel.state,
            "buffer": _stringify_buffer(kernel.buffer),
            "mode": kernel.mode,
            "outputs": list(self.outputs),
            "trace": list(self.trace),
            "error": self.error,
            "cursor": self.cursor,
            "session_id": self.session_id,
            "macros": {name: list(tokens) for name, tokens in self.macros.items()},
        }

    def undo(self) -> dict:
        self.touch()
        start = time.perf_counter()
        if len(self._history) <= 1:
            raise HistoryError("no undo history available")
        snapshot = self._history.pop()
        self._redo.append(snapshot)
        self._restore(self._history[-1])
        event = {"type": "undo", "cursor": self.cursor, "state": self._kernel().state}
        self._trace_event(event)
        self._publish(
            "UNDO",
            {
                "cursor": self.cursor,
                "state": self._kernel().state,
                "outputs": list(self.outputs),
            },
        )
        result = self.result()
        if self.metrics is not None:
            self.metrics.record_request((time.perf_counter() - start) * 1000.0, error=False)
        self._persist_state()
        return result

    def redo(self) -> dict:
        self.touch()
        start = time.perf_counter()
        if not self._redo:
            raise HistoryError("no redo history available")
        snapshot = self._redo.pop()
        self._history.append(snapshot)
        self._restore(snapshot)
        event = {"type": "redo", "cursor": self.cursor, "state": self._kernel().state}
        self._trace_event(event)
        self._publish(
            "REDO",
            {
                "cursor": self.cursor,
                "state": self._kernel().state,
                "outputs": list(self.outputs),
            },
        )
        result = self.result()
        if self.metrics is not None:
            self.metrics.record_request((time.perf_counter() - start) * 1000.0, error=False)
        self._persist_state()
        return result

    def clear_history(self) -> None:
        self.touch()
        self._history = [self._snapshot_state()]
        self._redo.clear()
        self._persist_state()


class SessionManager:
    def __init__(
        self,
        grammar: Grammar | dict,
        table: dict,
        config: RuntimeConfig,
        *,
        metrics: RuntimeMetrics | None = None,
        event_bus: EventBus | None = None,
        store: StateStore | None = None,
        max_sessions: int | None = None,
        idle_ttl_seconds: int | None = None,
        cleanup_interval_seconds: int | None = None,
        auto_start_cleanup: bool = True,
    ) -> None:
        self.grammar = grammar
        self.table = table
        self.config = config
        self.metrics = metrics or RuntimeMetrics()
        self.event_bus = event_bus or EventBus()
        self.store = store or InMemoryStore()
        self.max_sessions = max_sessions if max_sessions is not None else config.max_sessions
        self.idle_ttl_seconds = (
            idle_ttl_seconds if idle_ttl_seconds is not None else config.session_idle_ttl_seconds
        )
        self.cleanup_interval_seconds = (
            cleanup_interval_seconds
            if cleanup_interval_seconds is not None
            else config.session_cleanup_interval_seconds
        )
        self.sessions: dict[str, RuntimeSession] = {}
        self.default_session_id: str | None = None
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._cleanup_thread: threading.Thread | None = None
        if auto_start_cleanup and self.idle_ttl_seconds > 0 and self.cleanup_interval_seconds > 0:
            self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
            self._cleanup_thread.start()

    def _cleanup_loop(self) -> None:
        while not self._stop.wait(self.cleanup_interval_seconds):
            self.cleanup_idle_sessions()

    def _build_session(
        self,
        session_id: str | None = None,
        *,
        config: RuntimeConfig | None = None,
    ) -> RuntimeSession:
        return RuntimeSession(
            self.grammar,
            self.table,
            config=config or self.config,
            session_id=session_id or uuid.uuid4().hex,
            event_bus=self.event_bus,
            metrics=self.metrics,
            store=self.store,
        )

    def create_session(self, session_id: str | None = None, *, config: RuntimeConfig | None = None) -> RuntimeSession:
        with self._lock:
            if session_id is not None and session_id in self.sessions:
                raise ValueError(f"session already exists: {session_id}")
            if session_id is None and len(self.sessions) >= self.max_sessions:
                raise RuntimeLimitError(f"maximum sessions exceeded: {self.max_sessions}")
            if session_id is not None and len(self.sessions) >= self.max_sessions:
                raise RuntimeLimitError(f"maximum sessions exceeded: {self.max_sessions}")
            session = self._build_session(session_id, config=config)
            self.sessions[session.session_id] = session
            if self.default_session_id is None:
                self.default_session_id = session.session_id
            self.metrics.set_active_sessions(len(self.sessions))
            return session

    def destroy_session(self, session_id: str) -> None:
        with self._lock:
            session = self.sessions.pop(session_id, None)
            if session is None:
                raise SessionNotFoundError(f"session not found: {session_id}")
            if self.default_session_id == session_id:
                self.default_session_id = next(iter(self.sessions), None)
            self.metrics.set_active_sessions(len(self.sessions))
            self.store.delete_session(session_id)

    def get_session(self, session_id: str | None = None) -> RuntimeSession:
        with self._lock:
            if session_id is None:
                if self.default_session_id is None:
                    return self.create_session()
                session_id = self.default_session_id
            session = self.sessions.get(session_id)
            if session is None:
                raise SessionNotFoundError(f"session not found: {session_id}")
            session.touch()
            return session

    def cleanup_idle_sessions(self) -> list[str]:
        expired: list[str] = []
        if self.idle_ttl_seconds <= 0:
            return expired
        now = time.monotonic()
        with self._lock:
            for session_id, session in list(self.sessions.items()):
                if now - session.last_accessed_at >= self.idle_ttl_seconds:
                    expired.append(session_id)
                    self.sessions.pop(session_id, None)
                    self.store.delete_session(session_id)
            if expired:
                if self.default_session_id in expired:
                    self.default_session_id = next(iter(self.sessions), None)
                self.metrics.set_active_sessions(len(self.sessions))
        return expired

    def active_session_ids(self) -> list[str]:
        with self._lock:
            return sorted(self.sessions)

    def close(self) -> None:
        self._stop.set()
        if self._cleanup_thread is not None and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=0.1)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "active_sessions": len(self.sessions),
                "default_session_id": self.default_session_id,
                "session_ids": sorted(self.sessions),
                "max_sessions": self.max_sessions,
                "idle_ttl_seconds": self.idle_ttl_seconds,
            }


class Runtime:
    def __init__(
        self,
        grammar: Grammar | dict | None = None,
        *,
        config: RuntimeConfig | None = None,
        grammar_path: str | Path | None = None,
        version_policy: str | None = None,
        store: StateStore | None = None,
        event_bus: EventBus | None = None,
        metrics: RuntimeMetrics | None = None,
        max_sessions: int | None = None,
        session_idle_ttl_seconds: int | None = None,
        session_cleanup_interval_seconds: int | None = None,
    ) -> None:
        self.config = config or RuntimeConfig.from_sources()
        if grammar is None:
            grammar_path = grammar_path or self.config.grammar_path
            grammar = load_grammar(grammar_path, version_policy=version_policy or self.config.version_policy)
        elif not isinstance(grammar, Grammar):
            grammar = Grammar(
                grammar,
                source_path=grammar_path,
                version_policy=version_policy or self.config.version_policy,
            )
        self.grammar: Grammar = grammar
        self.table = generate_transition_table(self.grammar)
        self.event_bus = event_bus or EventBus()
        self.metrics = metrics or RuntimeMetrics()
        if store is None:
            if self.config.persistence_backend == "redis":
                if not self.config.persistence_url:
                    raise ConfigurationError(
                        "persistence_backend='redis' requires persistence_url or an explicit store"
                    )
                store = RedisStore(self.config.persistence_url)
            else:
                store = InMemoryStore()
        self.store = store
        self.session_manager = SessionManager(
            self.grammar,
            self.table,
            self.config,
            metrics=self.metrics,
            event_bus=self.event_bus,
            store=self.store,
            max_sessions=max_sessions,
            idle_ttl_seconds=session_idle_ttl_seconds,
            cleanup_interval_seconds=session_cleanup_interval_seconds,
        )
        self.sessions = self.session_manager.sessions
        self.default_session_id: str | None = self.session_manager.default_session_id

    def create_session(self, session_id: str | None = None, *, config: RuntimeConfig | None = None) -> RuntimeSession:
        session = self.session_manager.create_session(session_id=session_id, config=config)
        self.default_session_id = self.session_manager.default_session_id
        return session

    def destroy_session(self, session_id: str) -> None:
        self.session_manager.destroy_session(session_id)
        self.default_session_id = self.session_manager.default_session_id

    def get_session(self, session_id: str | None = None) -> RuntimeSession:
        session = self.session_manager.get_session(session_id)
        self.default_session_id = self.session_manager.default_session_id
        return session

    def cleanup_idle_sessions(self) -> list[str]:
        expired = self.session_manager.cleanup_idle_sessions()
        self.default_session_id = self.session_manager.default_session_id
        return expired

    def process(self, tokens: list[str], session_id: str | None = None) -> dict:
        return self.get_session(session_id).process(tokens)

    def process_token(self, token: str, session_id: str | None = None) -> list[dict]:
        return self.get_session(session_id).process_token(token)

    def process_stream(self, tokens: Iterable[str], session_id: str | None = None) -> dict:
        return self.get_session(session_id).process(list(tokens))

    def undo(self, session_id: str | None = None) -> dict:
        return self.get_session(session_id).undo()

    def redo(self, session_id: str | None = None) -> dict:
        return self.get_session(session_id).redo()

    def clear_history(self, session_id: str | None = None) -> None:
        self.get_session(session_id).clear_history()

    def register_macro(self, name: str, tokens: list[str], session_id: str | None = None) -> None:
        self.get_session(session_id).register_macro(name, tokens)

    def unregister_macro(self, name: str, session_id: str | None = None) -> None:
        self.get_session(session_id).unregister_macro(name)

    def expand_macro(self, name: str, session_id: str | None = None) -> list[str]:
        return self.get_session(session_id).expand_macro(name)

    def close(self) -> None:
        self.session_manager.close()


class AsyncRuntime:
    def __init__(self, runtime: Runtime | None = None, *, max_queue_size: int | None = None) -> None:
        self.runtime = runtime or Runtime()
        self._locks: dict[str, asyncio.Lock] = {}
        self.max_queue_size = max_queue_size if max_queue_size is not None else self.runtime.config.max_queue_size
        self.queue_policy = self.runtime.config.queue_policy
        self._queue: asyncio.Queue[dict[str, Any]] | None = None
        self._worker_task: asyncio.Task[None] | None = None

    def _lock_for(self, session_id: str | None) -> asyncio.Lock:
        key = session_id or "__default__"
        lock = self._locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[key] = lock
        return lock

    async def _ensure_queue(self) -> asyncio.Queue[dict[str, Any]]:
        if self.max_queue_size <= 0:
            raise RuntimeLimitError("async queue is disabled")
        if self._queue is None:
            self._queue = asyncio.Queue(maxsize=self.max_queue_size)
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._queue_worker())
        return self._queue

    async def _queue_worker(self) -> None:
        queue = self._queue
        if queue is None:
            raise RuntimeLimitError("async queue is not initialized")
        while True:
            job = await queue.get()
            future: asyncio.Future[Any] = job["future"]
            try:
                result = await asyncio.to_thread(job["runner"])
                if asyncio.iscoroutine(result):
                    result = await result
                if not future.done():
                    future.set_result(result)
            except Exception as exc:  # pragma: no cover - worker error path
                if not future.done():
                    future.set_exception(exc)
            finally:
                queue.task_done()
                self.runtime.metrics.set_queue_depth(queue.qsize())

    async def _submit(self, operation: str, runner):
        if self.max_queue_size > 0:
            queue = await self._ensure_queue()
            loop = asyncio.get_running_loop()
            future: asyncio.Future[Any] = loop.create_future()
            job = {"operation": operation, "future": future, "runner": runner}
            try:
                queue.put_nowait(job)
            except asyncio.QueueFull as exc:
                raise RuntimeLimitError("async processing queue is overloaded") from exc
            self.runtime.metrics.set_queue_depth(queue.qsize())
            return await future
        return await asyncio.to_thread(runner)

    async def create_session(self, session_id: str | None = None, *, config: RuntimeConfig | None = None) -> RuntimeSession:
        async with self._lock_for(session_id):
            return await self._submit(
                "create_session",
                lambda: self.runtime.create_session(session_id=session_id, config=config),
            )

    async def destroy_session(self, session_id: str) -> None:
        async with self._lock_for(session_id):
            await self._submit("destroy_session", lambda: self.runtime.destroy_session(session_id))

    async def process(self, tokens: list[str], session_id: str | None = None) -> dict:
        async with self._lock_for(session_id):
            return await self._submit("process", lambda: self.runtime.process(tokens, session_id=session_id))

    async def process_token(self, token: str, session_id: str | None = None) -> list[dict]:
        async with self._lock_for(session_id):
            return await self._submit("process_token", lambda: self.runtime.process_token(token, session_id=session_id))

    async def process_stream(self, tokens: Iterable[str], session_id: str | None = None) -> dict:
        token_list = list(tokens)
        async with self._lock_for(session_id):
            return await self._submit(
                "process_stream",
                lambda: self.runtime.process_stream(token_list, session_id=session_id),
            )

    async def undo(self, session_id: str | None = None) -> dict:
        async with self._lock_for(session_id):
            return await self._submit("undo", lambda: self.runtime.undo(session_id=session_id))

    async def redo(self, session_id: str | None = None) -> dict:
        async with self._lock_for(session_id):
            return await self._submit("redo", lambda: self.runtime.redo(session_id=session_id))

    async def clear_history(self, session_id: str | None = None) -> None:
        async with self._lock_for(session_id):
            await self._submit("clear_history", lambda: self.runtime.clear_history(session_id=session_id))

    async def register_macro(self, name: str, tokens: list[str], session_id: str | None = None) -> None:
        async with self._lock_for(session_id):
            await self._submit("register_macro", lambda: self.runtime.register_macro(name, tokens, session_id=session_id))

    async def unregister_macro(self, name: str, session_id: str | None = None) -> None:
        async with self._lock_for(session_id):
            await self._submit("unregister_macro", lambda: self.runtime.unregister_macro(name, session_id=session_id))

    async def expand_macro(self, name: str, session_id: str | None = None) -> list[str]:
        async with self._lock_for(session_id):
            return await self._submit("expand_macro", lambda: self.runtime.expand_macro(name, session_id=session_id))
