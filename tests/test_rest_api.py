from fastapi.testclient import TestClient

from keysuite.api import create_app
from keysuite.config import RuntimeConfig
from keysuite import Runtime


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


def test_rest_api_serves_favicon():
    client = TestClient(create_app())

    response = client.get("/favicon.ico")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert b"<svg" in response.content


def test_docs_and_openapi_describe_api_key_auth_when_configured():
    runtime = Runtime(config=RuntimeConfig(api_keys=["secret"]))
    client = TestClient(create_app(runtime))

    docs = client.get("/docs")
    openapi = client.get("/openapi.json").json()

    assert docs.status_code == 200
    assert openapi["components"]["securitySchemes"]["ApiKeyAuth"] == {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
    }
    assert openapi["paths"]["/v1/health"]["get"]["security"] == [{"ApiKeyAuth": []}]


def test_health_reports_non_secret_api_policy():
    runtime = Runtime(
        config=RuntimeConfig(
            api_keys=["secret"],
            max_requests_per_window=5,
            rate_limit_window_seconds=30,
            max_messages_per_second=7,
            max_payload_size=128,
        )
    )
    client = TestClient(create_app(runtime))

    health = client.get("/v1/health", headers={"X-API-Key": "secret"}).json()

    assert health["api"]["docs_url"] == "/docs"
    assert health["api"]["openapi_url"] == "/openapi.json"
    assert health["api"]["auth_required"] is True
    assert health["api"]["api_key_header"] == "X-API-Key"
    assert "secret" not in str(health["api"])
    assert health["api"]["rate_limits"] == {
        "requests_per_window": 5,
        "window_seconds": 30,
        "messages_per_second": 7,
        "max_payload_size": 128,
    }
