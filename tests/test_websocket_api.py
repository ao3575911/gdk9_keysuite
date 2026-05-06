import time

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from keysuite.api import create_app
from keysuite.config import RuntimeConfig
from keysuite import Runtime


def test_websocket_api_emits_macro_undo_and_error_events():
    client = TestClient(create_app())
    session_id = client.post("/v1/session", json={}).json()["session_id"]

    with client.websocket_connect(f"/v1/ws/session/{session_id}") as websocket:
        websocket.send_json({"type": "register_macro", "name": "pair", "tokens": ["C", "C"]})
        registered = websocket.receive_json()
        assert registered["type"] == "RESULT"
        assert registered["session_id"] == session_id
        assert registered["payload"]["operation"] == "register_macro"

        websocket.send_json({"type": "token", "value": "pair"})
        macro_events = [websocket.receive_json() for _ in range(8)]
        assert macro_events[0]["type"] == "TOKEN_ACCEPTED"
        assert macro_events[1]["type"] == "MACRO_EXPANDED"
        assert macro_events[2]["type"] == "TOKEN_ACCEPTED"
        assert macro_events[3]["type"] == "STATE_TRANSITION"
        assert macro_events[4]["type"] == "BUFFER_UPDATED"
        assert macro_events[5]["type"] == "TOKEN_ACCEPTED"
        assert macro_events[6]["type"] == "STATE_TRANSITION"
        assert macro_events[7]["type"] == "BUFFER_UPDATED"

        websocket.send_json({"type": "token", "value": "SPACE"})
        commit_events = [websocket.receive_json() for _ in range(4)]
        assert commit_events[-1]["type"] == "COMMIT"
        assert commit_events[-1]["payload"]["output"] == "CC"

        websocket.send_json({"type": "undo"})
        undo_event = websocket.receive_json()
        undo_result = websocket.receive_json()
        assert undo_event["type"] == "UNDO"
        assert undo_result["type"] == "RESULT"
        assert undo_result["payload"]["state"] == "COMPOSE"

        websocket.send_json({"type": "token", "value": "@"})
        error_events = [websocket.receive_json() for _ in range(2)]
        assert [event["type"] for event in error_events] == ["TOKEN_ACCEPTED", "ERROR"]
        assert error_events[-1]["payload"]["error_type"] == "TokenValidationError"


def test_websocket_heartbeat_keeps_session_alive_for_cleanup():
    runtime = Runtime(
        config=RuntimeConfig(
            session_idle_ttl_seconds=1,
            session_cleanup_interval_seconds=0,
        )
    )
    client = TestClient(create_app(runtime))
    session = runtime.create_session("live")

    with client.websocket_connect("/v1/ws/session/live") as websocket:
        session.last_accessed_at = time.monotonic() - 10
        websocket.send_json({"type": "pong"})

        heartbeat = websocket.receive_json()
        expired = runtime.cleanup_idle_sessions()

        assert heartbeat["type"] == "HEARTBEAT"
        assert expired == []
        assert runtime.get_session("live") is session


def test_websocket_frames_share_api_key_request_rate_limit():
    runtime = Runtime(
        config=RuntimeConfig(
            api_keys=["secret"],
            max_requests_per_window=2,
            rate_limit_window_seconds=60,
        )
    )
    runtime.create_session("limited")
    client = TestClient(create_app(runtime))

    with client.websocket_connect("/v1/ws/session/limited", headers={"X-API-Key": "secret"}) as websocket:
        websocket.send_json({"type": "pong"})
        assert websocket.receive_json()["type"] == "HEARTBEAT"

        websocket.send_json({"type": "pong"})
        limited = websocket.receive_json()

        assert limited["type"] == "ERROR"
        assert limited["payload"]["error_type"] == "RateLimitExceeded"
        assert "API key rate limit exceeded" in limited["payload"]["message"]

        try:
            websocket.receive_json()
        except WebSocketDisconnect:
            pass
