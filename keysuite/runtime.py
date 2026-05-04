from __future__ import annotations

import asyncio
import re
import uuid
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Iterable

from .config import RuntimeConfig
from .errors import (
    HistoryError,
    MacroExpansionError,
    RuntimeLimitError,
    SessionNotFoundError,
    TokenValidationError,
)
from .events import token_to_event
from .grammar import Grammar
from .grammar_loader import load_grammar
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
    kernel: IMEKernel | None = None
    trace: list[dict] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    error: dict | None = None
    escaped: bool = False
    cursor: int = 0
    macros: dict[str, list[str]] = field(default_factory=dict)
    _history: list[SessionSnapshot] = field(default_factory=list, init=False, repr=False)
    _redo: list[SessionSnapshot] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        self.kernel = IMEKernel(self.table, reduce_buffer)
        loaded_macros = {**self.config.macros, **self.macros}
        self.macros = {name: [] for name in loaded_macros}
        for name, tokens in loaded_macros.items():
            self.register_macro(name, list(tokens))
        self._history = [self._snapshot_state()]

    def _kernel(self) -> IMEKernel:
        if self.kernel is None:
            raise HistoryError("runtime kernel not initialized")
        return self.kernel

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
        rule = self.table.get(from_state, {}).get(event["class"])
        before = self.snapshot() if self.debug_level >= 3 else None
        output = kernel.handle(event)
        if output is not None:
            self.outputs.append(output)
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
        self.cursor += 1
        self._push_history()
        if kernel.state == "ERROR":
            self._record_error(
                token,
                event["class"],
                "Token has no GDk9 jurisdiction or no valid transition",
                "TokenValidationError",
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

    def unregister_macro(self, name: str) -> None:
        self.macros.pop(name, None)

    def expand_macro(self, name: str) -> list[str]:
        if name not in self.macros:
            raise MacroExpansionError(f"unknown macro: {name}")
        return self._expand_macro(name, 0, ())

    def process_token(self, token: str, *, literal: bool = False, depth: int = 0, seen: tuple[str, ...] = ()) -> list[dict]:
        try:
            _validate_token_shape(token)
            if literal:
                self._handle_event(token, literal=True)
                return [self.trace[-1]]

            if self.escaped:
                self._handle_event(token, literal=True)
                self.escaped = False
                return [self.trace[-1]]

            if self.cursor >= self.config.max_token_count:
                raise RuntimeLimitError(f"token limit exceeded: {self.config.max_token_count}")

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
                return [entry]

            if token in self.macros:
                expanded = self._expand_macro(token, depth, seen)
                events = [
                    {
                        "type": "macro_expansion",
                        "macro": token,
                        "expanded": list(expanded),
                        "cursor": self.cursor,
                    }
                ]
                self._trace_event(events[0])
                for part in expanded:
                    events.extend(self.process_token(part, literal=False, depth=depth + 1, seen=seen + (token,)))
                    if self._kernel().state == "ERROR":
                        break
                return events

            self._handle_event(token, literal=literal)
            return [self.trace[-1]]
        except (TokenValidationError, MacroExpansionError, RuntimeLimitError) as exc:
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
            self._push_history()
            return [error_event]

    def feed(self, token: str) -> None:
        self.process_token(token)

    def finalize(self) -> None:
        kernel = self._kernel()
        if self.error is None and self.escaped:
            kernel.state = "ERROR"
            self._record_error(
                self.escape_token or "_",
                "ESCAPE",
                "Escape marker must be followed by a literal token",
                "TokenValidationError",
            )
            self.escaped = False
            self._push_history()
            return

        if self.auto_commit and self.error is None and kernel.state in {"COMPOSE", "MODE"}:
            self._handle_event("SPACE")

    def process(self, tokens: list[str], finalize: bool = True) -> dict:
        for token in tokens:
            self.feed(token)
        if finalize:
            self.finalize()
        return self.result()

    def result(self) -> dict:
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
        if len(self._history) <= 1:
            raise HistoryError("no undo history available")
        snapshot = self._history.pop()
        self._redo.append(snapshot)
        self._restore(self._history[-1])
        event = {"type": "undo", "cursor": self.cursor, "state": self._kernel().state}
        self._trace_event(event)
        return self.result()

    def redo(self) -> dict:
        if not self._redo:
            raise HistoryError("no redo history available")
        snapshot = self._redo.pop()
        self._history.append(snapshot)
        self._restore(snapshot)
        event = {"type": "redo", "cursor": self.cursor, "state": self._kernel().state}
        self._trace_event(event)
        return self.result()

    def clear_history(self) -> None:
        self._history = [self._snapshot_state()]
        self._redo.clear()


class Runtime:
    def __init__(
        self,
        grammar: Grammar | dict | None = None,
        *,
        config: RuntimeConfig | None = None,
        grammar_path: str | Path | None = None,
        version_policy: str | None = None,
    ) -> None:
        self.config = config or RuntimeConfig.from_sources()
        if grammar is None:
            grammar_path = grammar_path or self.config.grammar_path
            grammar = load_grammar(grammar_path, version_policy=version_policy or self.config.version_policy)
        elif not isinstance(grammar, Grammar):
            grammar = Grammar(grammar, source_path=grammar_path, version_policy=version_policy or self.config.version_policy)
        self.grammar: Grammar = grammar
        self.table = generate_transition_table(self.grammar)
        self.sessions: dict[str, RuntimeSession] = {}
        self.default_session_id: str | None = None

    def create_session(self, session_id: str | None = None, *, config: RuntimeConfig | None = None) -> RuntimeSession:
        session = RuntimeSession(
            self.grammar,
            self.table,
            config=config or self.config,
            session_id=session_id or uuid.uuid4().hex,
        )
        self.sessions[session.session_id] = session
        if self.default_session_id is None:
            self.default_session_id = session.session_id
        return session

    def get_session(self, session_id: str | None = None) -> RuntimeSession:
        if session_id is None:
            if self.default_session_id is None:
                return self.create_session()
            session_id = self.default_session_id
        if session_id not in self.sessions:
            raise SessionNotFoundError(f"session not found: {session_id}")
        return self.sessions[session_id]

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


class AsyncRuntime:
    def __init__(self, runtime: Runtime | None = None):
        self.runtime = runtime or Runtime()
        self._locks: dict[str, asyncio.Lock] = {}

    def _lock_for(self, session_id: str | None) -> asyncio.Lock:
        key = session_id or "__default__"
        lock = self._locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[key] = lock
        return lock

    async def create_session(self, session_id: str | None = None, *, config: RuntimeConfig | None = None) -> RuntimeSession:
        async with self._lock_for(session_id):
            return self.runtime.create_session(session_id=session_id, config=config)

    async def process(self, tokens: list[str], session_id: str | None = None) -> dict:
        async with self._lock_for(session_id):
            return self.runtime.process(tokens, session_id=session_id)

    async def process_token(self, token: str, session_id: str | None = None) -> list[dict]:
        async with self._lock_for(session_id):
            return self.runtime.process_token(token, session_id=session_id)

    async def process_stream(self, tokens: Iterable[str], session_id: str | None = None) -> dict:
        async with self._lock_for(session_id):
            return self.runtime.process_stream(tokens, session_id=session_id)

    async def undo(self, session_id: str | None = None) -> dict:
        async with self._lock_for(session_id):
            return self.runtime.undo(session_id=session_id)

    async def redo(self, session_id: str | None = None) -> dict:
        async with self._lock_for(session_id):
            return self.runtime.redo(session_id=session_id)
