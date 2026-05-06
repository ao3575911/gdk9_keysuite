from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from .config import RuntimeConfig
from .errors import (
    ConfigurationError,
    HistoryError,
    KeySuiteError,
    MacroExpansionError,
    RuntimeLimitError,
    SessionNotFoundError,
    TokenValidationError,
)
from .events import runtime_event
from .grammar_loader import grammar_summary
from .runtime import AsyncRuntime, Runtime
from .security import AuthenticationError, AuthConfig, RateLimitExceededError, SlidingWindowRateLimiter
from .telemetry import configure_json_logging
from .transport import ConnectionManager
from .version import __version__


FAVICON_SVG = """<svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
<rect width="32" height="32" rx="6" fill="#111111"/>
<rect x="8" y="8" width="3" height="16" fill="#1E90FF"/>
<rect x="14" y="10" width="3" height="12" fill="#1E90FF"/>
<rect x="20" y="12" width="3" height="8" fill="#1E90FF"/>
</svg>
"""


class ProcessRequest(BaseModel):
    tokens: list[str] = Field(default_factory=list)
    session_id: str | None = None


class SessionCreateRequest(BaseModel):
    session_id: str | None = None
    config: dict[str, Any] | None = None


@dataclass
class Governance:
    auth: AuthConfig
    request_limiter: SlidingWindowRateLimiter
    session_limiter: SlidingWindowRateLimiter

    def authenticate(self, request: Request | WebSocket) -> str:
        header_value = request.headers.get(self.auth.header_name)
        return self.auth.authenticate(header_value)

    def check_request(self, api_key: str) -> None:
        allowed, retry_after = self.request_limiter.allow(api_key or "anonymous")
        if not allowed:
            raise RateLimitExceededError(
                f"API key rate limit exceeded; retry after {retry_after:.2f} seconds"
            )

    def check_session(self, session_id: str) -> None:
        allowed, retry_after = self.session_limiter.allow(session_id)
        if not allowed:
            raise RateLimitExceededError(
                f"session rate limit exceeded for {session_id}; retry after {retry_after:.2f} seconds"
            )


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _error_payload(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        }
    }


def _error_response(status_code: int, code: str, message: str, details: dict[str, Any] | None = None) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=_error_payload(code, message, details))


def _result_error_http(result: dict[str, Any]) -> HTTPException:
    error = result.get("error") or {}
    error_type = error.get("type")
    message = error.get("message") or "runtime error"
    details = dict(error)
    if error_type == "RuntimeLimitError":
        status = 429 if any(keyword in message.lower() for keyword in {"queue", "rate", "session"}) else 413
        return HTTPException(status_code=status, detail={"code": "RUNTIME_LIMIT", "message": message, "details": details})
    if error_type in {"TokenValidationError", "MacroExpansionError"}:
        return HTTPException(status_code=422, detail={"code": error_type.upper(), "message": message, "details": details})
    return HTTPException(status_code=400, detail={"code": "RUNTIME_ERROR", "message": message, "details": details})


def _map_exception(exc: Exception) -> HTTPException:
    if isinstance(exc, AuthenticationError):
        return HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "message": str(exc), "details": {}})
    if isinstance(exc, RateLimitExceededError):
        return HTTPException(status_code=429, detail={"code": "RATE_LIMITED", "message": str(exc), "details": {}})
    if isinstance(exc, (TokenValidationError, MacroExpansionError)):
        return HTTPException(status_code=422, detail={"code": exc.__class__.__name__.upper(), "message": str(exc), "details": {}})
    if isinstance(exc, RuntimeLimitError):
        status = 429 if any(keyword in str(exc).lower() for keyword in {"queue", "rate", "session"}) else 413
        return HTTPException(status_code=status, detail={"code": "RUNTIME_LIMIT", "message": str(exc), "details": {}})
    if isinstance(exc, (SessionNotFoundError, HistoryError)):
        code = "SESSION_NOT_FOUND" if isinstance(exc, SessionNotFoundError) else "HISTORY_ERROR"
        return HTTPException(status_code=404 if isinstance(exc, SessionNotFoundError) else 409, detail={"code": code, "message": str(exc), "details": {}})
    if isinstance(exc, ConfigurationError):
        return HTTPException(status_code=400, detail={"code": "CONFIGURATION_ERROR", "message": str(exc), "details": {}})
    if isinstance(exc, KeySuiteError):
        return HTTPException(status_code=400, detail={"code": "KEYSUITE_ERROR", "message": str(exc), "details": {}})
    return HTTPException(status_code=500, detail={"code": "INTERNAL_ERROR", "message": str(exc), "details": {}})


def _normalize_http_exception(exc: HTTPException) -> dict[str, Any]:
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        return detail
    return {"code": "HTTP_ERROR", "message": str(detail), "details": {}}


def _subscription_events(subscription) -> list[dict[str, Any]]:
    return subscription.drain_nowait()


def _api_policy(app: FastAPI, config: RuntimeConfig, governance: Governance) -> dict[str, Any]:
    return {
        "docs_url": app.docs_url,
        "openapi_url": app.openapi_url,
        "auth_required": governance.auth.enabled,
        "api_key_header": governance.auth.header_name,
        "rate_limits": {
            "requests_per_window": config.max_requests_per_window,
            "window_seconds": config.rate_limit_window_seconds,
            "messages_per_second": config.max_messages_per_second,
            "max_payload_size": config.max_payload_size,
        },
        "websocket": {
            "endpoint": "/v1/ws/session/{session_id}",
            "connection_timeout_seconds": config.connection_timeout_seconds,
            "heartbeat_interval_seconds": config.heartbeat_interval_seconds,
        },
    }


def _install_openapi_auth_schema(app: FastAPI, governance: Governance) -> None:
    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema

        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        if governance.auth.enabled:
            components = schema.setdefault("components", {})
            security_schemes = components.setdefault("securitySchemes", {})
            security_schemes["ApiKeyAuth"] = {
                "type": "apiKey",
                "in": "header",
                "name": governance.auth.header_name,
            }
            for path, operations in schema.get("paths", {}).items():
                if not path.startswith("/v1"):
                    continue
                for operation in operations.values():
                    if isinstance(operation, dict):
                        operation.setdefault("security", [{"ApiKeyAuth": []}])

        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = custom_openapi


async def _send_ws_error(
    websocket: WebSocket,
    session_id: str,
    *,
    message: str,
    error_type: str,
    **details: Any,
) -> None:
    payload = {"message": message, "error_type": error_type, **details}
    await websocket.send_json(runtime_event("ERROR", session_id, payload))


def create_app(runtime: Runtime | None = None) -> FastAPI:
    runtime = runtime or Runtime()
    config = runtime.config
    app = FastAPI(
        title="KeySuite API",
        version=__version__,
        description="REST and WebSocket access to the GDk9 KeySuite runtime.",
    )
    app.state.runtime = runtime
    app.state.async_runtime = AsyncRuntime(runtime, max_queue_size=config.max_queue_size)
    app.state.connection_manager = ConnectionManager(
        max_messages_per_second=config.max_messages_per_second,
        max_payload_size=config.max_payload_size,
    )
    app.state.governance = Governance(
        auth=AuthConfig(set(config.api_keys), header_name=config.api_key_header),
        request_limiter=SlidingWindowRateLimiter(
            limit=config.max_requests_per_window,
            window_seconds=float(config.rate_limit_window_seconds),
        ),
        session_limiter=SlidingWindowRateLimiter(
            limit=config.max_requests_per_window,
            window_seconds=float(config.rate_limit_window_seconds),
        ),
    )
    app.state.logger = configure_json_logging(level=logging.INFO if config.json_logging else logging.WARNING)
    _install_openapi_auth_schema(app, app.state.governance)

    @app.middleware("http")
    async def guard_requests(request: Request, call_next):
        if request.url.path.startswith("/v1"):
            content_length = request.headers.get("content-length")
            if content_length is not None and content_length.isdigit() and int(content_length) > config.max_payload_size:
                return _error_response(
                    413,
                    "PAYLOAD_TOO_LARGE",
                    "request body exceeds configured payload size",
                    {"max_payload_size": config.max_payload_size},
                )
            try:
                api_key = app.state.governance.authenticate(request)
                app.state.governance.check_request(api_key)
                request.state.api_key = api_key
            except Exception as exc:
                http_exc = exc if isinstance(exc, HTTPException) else _map_exception(exc)
                return _error_response(http_exc.status_code, _normalize_http_exception(http_exc)["code"], _normalize_http_exception(http_exc)["message"], _normalize_http_exception(http_exc)["details"])
        return await call_next(request)

    @app.get("/favicon.ico", include_in_schema=False)
    def favicon() -> Response:
        return Response(
            content=FAVICON_SVG,
            media_type="image/svg+xml",
            headers={"Cache-Control": "public, max-age=86400"},
        )

    @app.exception_handler(HTTPException)
    async def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
        normalized = _normalize_http_exception(exc)
        return _error_response(exc.status_code, normalized["code"], normalized["message"], normalized["details"])

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return _error_response(422, "VALIDATION_ERROR", "request validation failed", {"errors": exc.errors()})

    @app.exception_handler(KeySuiteError)
    async def handle_keysuite_error(_: Request, exc: KeySuiteError) -> JSONResponse:
        http_exc = _map_exception(exc)
        normalized = _normalize_http_exception(http_exc)
        return _error_response(http_exc.status_code, normalized["code"], normalized["message"], normalized["details"])

    @app.get("/v1/health")
    def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "version": __version__,
            "timestamp": _timestamp(),
            "sessions": len(runtime.sessions),
            "active_connections": app.state.connection_manager.connection_count(),
            "metrics": runtime.metrics.snapshot(),
            "session_manager": runtime.session_manager.snapshot(),
            "connections": app.state.connection_manager.snapshot(),
            "api": _api_policy(app, config, app.state.governance),
        }

    @app.get("/v1/metrics")
    def metrics() -> dict[str, Any]:
        return {
            "timestamp": _timestamp(),
            "metrics": runtime.metrics.snapshot(),
            "session_manager": runtime.session_manager.snapshot(),
            "connections": app.state.connection_manager.snapshot(),
        }

    @app.get("/v1/grammar")
    def get_grammar() -> dict[str, Any]:
        return grammar_summary(runtime.grammar)

    @app.post("/v1/session")
    def create_session(payload: SessionCreateRequest, request: Request) -> dict[str, Any]:
        try:
            session = runtime.create_session(session_id=payload.session_id, config=RuntimeConfig.from_sources(explicit=payload.config or {}))
            return {"session_id": session.session_id, "state": session.snapshot()}
        except Exception as exc:
            raise _map_exception(exc)

    @app.get("/v1/session/{session_id}")
    def get_session(session_id: str, request: Request) -> dict[str, Any]:
        try:
            app.state.governance.check_session(session_id)
            session = runtime.get_session(session_id)
            return {"session_id": session.session_id, "state": session.snapshot(), "result": session.result()}
        except Exception as exc:
            raise _map_exception(exc)

    @app.delete("/v1/session/{session_id}")
    async def destroy_session(session_id: str) -> dict[str, Any]:
        try:
            app.state.governance.check_session(session_id)
            runtime.destroy_session(session_id)
            closed = app.state.connection_manager.close_session(session_id)
            for connection_state in closed:
                try:
                    await connection_state.websocket.close(code=1001)
                except Exception:
                    app.state.logger.warning(
                        "failed to close websocket during session destroy",
                        exc_info=True,
                    )
            app.state.connection_manager.snapshot()
            runtime.metrics.set_active_connections(app.state.connection_manager.connection_count())
            return {"session_id": session_id, "destroyed": True, "closed_connections": len(closed)}
        except Exception as exc:
            raise _map_exception(exc)

    @app.post("/v1/process")
    def process_tokens(payload: ProcessRequest, request: Request) -> dict[str, Any]:
        try:
            session = runtime.get_session(payload.session_id)
            app.state.governance.check_session(session.session_id)
            result = session.process(payload.tokens)
            if result["status"] == "error":
                raise _result_error_http(result)
            return {"session_id": session.session_id, **result}
        except Exception as exc:
            if isinstance(exc, HTTPException):
                raise exc
            raise _map_exception(exc)

    @app.post("/v1/session/{session_id}/process")
    def process_session(session_id: str, payload: ProcessRequest, request: Request) -> dict[str, Any]:
        try:
            session = runtime.get_session(session_id)
            app.state.governance.check_session(session.session_id)
            result = session.process(payload.tokens)
            if result["status"] == "error":
                raise _result_error_http(result)
            return {"session_id": session.session_id, **result}
        except Exception as exc:
            if isinstance(exc, HTTPException):
                raise exc
            raise _map_exception(exc)

    @app.post("/v1/session/{session_id}/undo")
    def undo(session_id: str, request: Request) -> dict[str, Any]:
        try:
            app.state.governance.check_session(session_id)
            session = runtime.get_session(session_id)
            result = session.undo()
            return {"session_id": session.session_id, **result}
        except Exception as exc:
            if isinstance(exc, HTTPException):
                raise exc
            raise _map_exception(exc)

    @app.post("/v1/session/{session_id}/redo")
    def redo(session_id: str, request: Request) -> dict[str, Any]:
        try:
            app.state.governance.check_session(session_id)
            session = runtime.get_session(session_id)
            result = session.redo()
            return {"session_id": session.session_id, **result}
        except Exception as exc:
            if isinstance(exc, HTTPException):
                raise exc
            raise _map_exception(exc)

    @app.websocket("/v1/ws/session/{session_id}")
    async def websocket_session(websocket: WebSocket, session_id: str) -> None:
        connection = None
        subscription = None
        try:
            api_key = app.state.governance.authenticate(websocket)
            app.state.governance.check_request(api_key)
        except Exception:
            await websocket.close(code=4401)
            return

        try:
            session = runtime.get_session(session_id)
            app.state.governance.check_session(session.session_id)
        except Exception:
            await websocket.close(code=4404)
            return

        await websocket.accept()
        connection = app.state.connection_manager.register(websocket, session.session_id, api_key=api_key)
        runtime.metrics.set_active_connections(app.state.connection_manager.connection_count())
        subscription = runtime.event_bus.subscribe(session_id=session.session_id)

        try:
            while True:
                try:
                    raw_message = await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=float(config.connection_timeout_seconds),
                    )
                except asyncio.TimeoutError:
                    await websocket.send_json(
                        runtime_event(
                            "PING",
                            session.session_id,
                            {"message": "heartbeat", "timestamp": _timestamp()},
                        )
                    )
                    try:
                        raw_message = await asyncio.wait_for(
                            websocket.receive_text(),
                            timeout=float(config.heartbeat_interval_seconds),
                        )
                    except asyncio.TimeoutError:
                        await websocket.send_json(
                            runtime_event(
                                "ERROR",
                                session.session_id,
                                {
                                    "message": "connection timed out",
                                    "error_type": "TimeoutError",
                                },
                            )
                        )
                        break

                if len(raw_message.encode("utf-8")) > app.state.connection_manager.max_payload_size:
                    await websocket.send_json(
                        runtime_event(
                            "ERROR",
                            session.session_id,
                            {
                                "message": "websocket payload exceeds configured limit",
                                "error_type": "PayloadTooLarge",
                                "max_payload_size": app.state.connection_manager.max_payload_size,
                            },
                        )
                    )
                    break

                allowed, retry_after = app.state.connection_manager.record_message(connection.connection_id)
                if not allowed:
                    await websocket.send_json(
                        runtime_event(
                            "ERROR",
                            session.session_id,
                            {
                                "message": "message rate limit exceeded",
                                "error_type": "RateLimitExceeded",
                                "retry_after_seconds": retry_after,
                            },
                        )
                    )
                    break

                try:
                    app.state.governance.check_request(api_key)
                    session = runtime.get_session(session.session_id)
                    app.state.governance.check_session(session.session_id)
                except RateLimitExceededError as exc:
                    await _send_ws_error(
                        websocket,
                        session.session_id,
                        message=str(exc),
                        error_type="RateLimitExceeded",
                    )
                    await websocket.close(code=4408)
                    break
                except SessionNotFoundError as exc:
                    await _send_ws_error(
                        websocket,
                        session.session_id,
                        message=str(exc),
                        error_type="SessionNotFound",
                    )
                    await websocket.close(code=4404)
                    break

                try:
                    message = json.loads(raw_message)
                except json.JSONDecodeError:
                    await websocket.send_json(
                        runtime_event(
                            "ERROR",
                            session.session_id,
                            {
                                "message": "invalid JSON payload",
                                "error_type": "ValidationError",
                            },
                        )
                    )
                    continue

                kind = message.get("type", "token")
                if kind == "pong":
                    connection.touch()
                    session.touch()
                    await websocket.send_json(runtime_event("HEARTBEAT", session.session_id, {"status": "ok"}))
                    continue

                if kind == "token":
                    await app.state.async_runtime.process_token(message["value"], session_id=session.session_id)
                    for event in _subscription_events(subscription):
                        await websocket.send_json(event)
                    continue

                if kind == "tokens":
                    result = await app.state.async_runtime.process(message["values"], session_id=session.session_id)
                    for event in _subscription_events(subscription):
                        await websocket.send_json(event)
                    await websocket.send_json(runtime_event("RESULT", session.session_id, result))
                    continue

                if kind == "undo":
                    result = await app.state.async_runtime.undo(session.session_id)
                    for event in _subscription_events(subscription):
                        await websocket.send_json(event)
                    await websocket.send_json(runtime_event("RESULT", session.session_id, result))
                    continue

                if kind == "redo":
                    result = await app.state.async_runtime.redo(session.session_id)
                    for event in _subscription_events(subscription):
                        await websocket.send_json(event)
                    await websocket.send_json(runtime_event("RESULT", session.session_id, result))
                    continue

                if kind == "register_macro":
                    await app.state.async_runtime.register_macro(
                        message["name"],
                        message["tokens"],
                        session_id=session.session_id,
                    )
                    for event in _subscription_events(subscription):
                        await websocket.send_json(event)
                    await websocket.send_json(
                        runtime_event(
                            "RESULT",
                            session.session_id,
                            {"operation": "register_macro", "name": message["name"]},
                        )
                    )
                    continue

                if kind == "unregister_macro":
                    await app.state.async_runtime.unregister_macro(message["name"], session_id=session.session_id)
                    for event in _subscription_events(subscription):
                        await websocket.send_json(event)
                    await websocket.send_json(
                        runtime_event(
                            "RESULT",
                            session.session_id,
                            {"operation": "unregister_macro", "name": message["name"]},
                        )
                    )
                    continue

                await websocket.send_json(
                    runtime_event(
                        "ERROR",
                        session.session_id,
                        {
                            "message": f"unsupported message type: {kind}",
                            "error_type": "ValidationError",
                        },
                    )
                )
        except WebSocketDisconnect:
            return
        except Exception as exc:
            await websocket.send_json(
                runtime_event(
                    "ERROR",
                    session.session_id,
                    {
                        "message": str(exc),
                        "error_type": exc.__class__.__name__,
                    },
                )
            )
            await websocket.close(code=1011)
        finally:
            if subscription is not None:
                runtime.event_bus.unsubscribe(subscription)
            if connection is not None:
                app.state.connection_manager.unregister(connection.connection_id)
            runtime.metrics.set_active_connections(app.state.connection_manager.connection_count())

    return app
