from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from .config import RuntimeConfig
from .errors import (
    HistoryError,
    KeySuiteError,
    MacroExpansionError,
    RuntimeLimitError,
    SessionNotFoundError,
    TokenValidationError,
)
from .grammar_loader import grammar_summary
from .runtime import AsyncRuntime, Runtime
from .version import __version__


class ProcessRequest(BaseModel):
    tokens: list[str] = Field(default_factory=list)
    session_id: str | None = None


class SessionCreateRequest(BaseModel):
    session_id: str | None = None
    config: dict[str, Any] | None = None


def _map_error(exc: Exception) -> HTTPException:
    if isinstance(exc, (TokenValidationError, MacroExpansionError)):
        return HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, RuntimeLimitError):
        return HTTPException(status_code=413, detail=str(exc))
    if isinstance(exc, (SessionNotFoundError, HistoryError)):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, KeySuiteError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail=str(exc))


def _result_error_http(result: dict[str, Any]) -> HTTPException:
    error = result.get("error") or {}
    error_type = error.get("type")
    message = error.get("message") or "runtime error"
    if error_type == "RuntimeLimitError":
        return HTTPException(status_code=413, detail=message)
    if error_type in {"TokenValidationError", "MacroExpansionError"}:
        return HTTPException(status_code=422, detail=message)
    return HTTPException(status_code=400, detail=message)


def create_app(runtime: Runtime | None = None) -> FastAPI:
    runtime = runtime or Runtime()
    app = FastAPI(
        title="KeySuite API",
        version=__version__,
        description="REST and WebSocket access to the GDk9 KeySuite runtime.",
    )
    app.state.runtime = runtime
    app.state.async_runtime = AsyncRuntime(runtime)

    @app.get("/v1/health")
    def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "version": __version__,
            "sessions": len(runtime.sessions),
        }

    @app.get("/v1/grammar")
    def get_grammar() -> dict[str, Any]:
        return grammar_summary(runtime.grammar)

    @app.post("/v1/session")
    def create_session(payload: SessionCreateRequest) -> dict[str, Any]:
        try:
            config = RuntimeConfig.from_sources(explicit=payload.config or {})
            session = runtime.create_session(session_id=payload.session_id, config=config)
            if payload.config:
                session.macros.update(config.macros)
            return {"session_id": session.session_id, "state": session.snapshot()}
        except HTTPException:
            raise
        except Exception as exc:  # pragma: no cover - FastAPI converts to JSON
            raise _map_error(exc)

    @app.post("/v1/process")
    def process_tokens(payload: ProcessRequest) -> dict[str, Any]:
        try:
            session = runtime.get_session(payload.session_id)
            result = session.process(payload.tokens)
            if result["status"] == "error":
                raise _result_error_http(result)
            return {"session_id": session.session_id, **result}
        except HTTPException:
            raise
        except Exception as exc:
            raise _map_error(exc)

    @app.post("/v1/session/{session_id}/process")
    def process_session(session_id: str, payload: ProcessRequest) -> dict[str, Any]:
        try:
            session = runtime.get_session(session_id)
            result = session.process(payload.tokens)
            if result["status"] == "error":
                raise _result_error_http(result)
            return {"session_id": session.session_id, **result}
        except HTTPException:
            raise
        except Exception as exc:
            raise _map_error(exc)

    @app.post("/v1/session/{session_id}/undo")
    def undo(session_id: str) -> dict[str, Any]:
        try:
            session = runtime.get_session(session_id)
            result = session.undo()
            return {"session_id": session.session_id, **result}
        except HTTPException:
            raise
        except Exception as exc:
            raise _map_error(exc)

    @app.post("/v1/session/{session_id}/redo")
    def redo(session_id: str) -> dict[str, Any]:
        try:
            session = runtime.get_session(session_id)
            result = session.redo()
            return {"session_id": session.session_id, **result}
        except HTTPException:
            raise
        except Exception as exc:
            raise _map_error(exc)

    @app.websocket("/v1/ws/session/{session_id}")
    async def websocket_session(websocket: WebSocket, session_id: str) -> None:
        await websocket.accept()
        async_runtime = app.state.async_runtime
        try:
            session = runtime.get_session(session_id)
        except Exception as exc:
            await websocket.send_json({"type": "error", "error": str(exc)})
            await websocket.close(code=1008)
            return

        try:
            while True:
                message = await websocket.receive_json()
                kind = message.get("type", "token")
                if kind == "token":
                    token = message["value"]
                    events = await async_runtime.process_token(token, session_id=session.session_id)
                    for event in events:
                        await websocket.send_json(event)
                    continue
                if kind == "tokens":
                    events = await async_runtime.process(message["values"], session_id=session.session_id)
                    await websocket.send_json({"type": "result", **events})
                    continue
                if kind == "undo":
                    result = await async_runtime.undo(session.session_id)
                    await websocket.send_json({"type": "undo", **result})
                    continue
                if kind == "redo":
                    result = await async_runtime.redo(session.session_id)
                    await websocket.send_json({"type": "redo", **result})
                    continue
                if kind == "register_macro":
                    session.register_macro(message["name"], message["tokens"])
                    await websocket.send_json({"type": "macro_registered", "name": message["name"]})
                    continue
                if kind == "unregister_macro":
                    session.unregister_macro(message["name"])
                    await websocket.send_json({"type": "macro_unregistered", "name": message["name"]})
                    continue
                await websocket.send_json({"type": "error", "error": f"unsupported message type: {kind}"})
        except WebSocketDisconnect:
            return
        except Exception as exc:
            await websocket.send_json({"type": "error", "error": str(exc)})
            await websocket.close(code=1011)

    return app
