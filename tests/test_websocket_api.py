from fastapi.testclient import TestClient

from keysuite.api import create_app


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
