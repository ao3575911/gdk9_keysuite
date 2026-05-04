from fastapi.testclient import TestClient

from keysuite.api import create_app


def test_rest_api_round_trip_and_history():
    client = TestClient(create_app())

    health = client.get("/v1/health").json()
    assert health["status"] == "ok"
    assert health["version"].startswith("1.1.0")

    grammar = client.get("/v1/grammar").json()
    assert grammar["version"] == "1.0.0"

    session = client.post("/v1/session", json={}).json()
    session_id = session["session_id"]

    result = client.post(
        f"/v1/session/{session_id}/process",
        json={"tokens": ["C", "C", "SPACE"]},
    ).json()
    assert result["outputs"] == ["CC"]

    undo = client.post(f"/v1/session/{session_id}/undo").json()
    assert undo["outputs"] == []
    assert undo["state"] == "COMPOSE"

    redo = client.post(f"/v1/session/{session_id}/redo").json()
    assert redo["outputs"] == ["CC"]
    assert redo["state"] == "IDLE"
