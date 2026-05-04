from fastapi.testclient import TestClient

from keysuite.api import create_app


def test_websocket_api_emits_macro_undo_and_error_events():
    client = TestClient(create_app())
    session_id = client.post("/v1/session", json={}).json()["session_id"]

    with client.websocket_connect(f"/v1/ws/session/{session_id}") as websocket:
        websocket.send_json({"type": "register_macro", "name": "pair", "tokens": ["C", "C"]})
        registered = websocket.receive_json()
        assert registered["type"] == "macro_registered"

        websocket.send_json({"type": "token", "value": "pair"})
        macro_event = websocket.receive_json()
        transition_one = websocket.receive_json()
        transition_two = websocket.receive_json()
        assert macro_event["type"] == "macro_expansion"
        assert transition_one["type"] == "transition"
        assert transition_two["type"] == "transition"

        websocket.send_json({"type": "token", "value": "SPACE"})
        commit_event = websocket.receive_json()
        assert commit_event["output"] == "CC"

        websocket.send_json({"type": "undo"})
        undo_event = websocket.receive_json()
        assert undo_event["type"] == "undo"

        websocket.send_json({"type": "token", "value": "@"})
        error_event = websocket.receive_json()
        assert error_event["type"] == "error"
        assert error_event["error_type"] == "TokenValidationError"
