# KeySuite API

KeySuite now ships as an importable Python package and an API server.

## Python imports

```python
from keysuite import Runtime, Grammar, load_grammar

grammar = load_grammar()
runtime = Runtime(grammar)
session = runtime.create_session()
result = session.process(["C", "C", ".", "3", "3", "SPACE"])
print(result["outputs"])  # ["CC→33"]
```

## FastAPI app

```python
from keysuite.api import create_app

app = create_app()
```

The app exposes:

- `GET /v1/health`
- `GET /favicon.ico`
- `GET /v1/metrics`
- `GET /v1/grammar`
- `GET /v1/session/{session_id}`
- `POST /v1/process`
- `POST /v1/session`
- `POST /v1/session/{session_id}/process`
- `POST /v1/session/{session_id}/undo`
- `POST /v1/session/{session_id}/redo`
- `DELETE /v1/session/{session_id}`

OpenAPI docs are available at `/docs` and `/openapi.json`. The local API also
serves `/favicon.ico` so browser exploration does not create a favicon 404. When
API keys are configured, `/openapi.json` marks `/v1` operations with the
configured API-key header so generated clients and browser users see the
authentication contract.

When API keys are configured, include the configured header on every `/v1` request. The default header is `X-API-Key`.

## Health and Policy Metadata

`GET /v1/health` returns runtime status, session and connection counts, metrics snapshots, and non-secret API policy metadata:

```json
{
  "status": "ok",
  "api": {
    "docs_url": "/docs",
    "openapi_url": "/openapi.json",
    "auth_required": true,
    "api_key_header": "X-API-Key",
    "rate_limits": {
      "requests_per_window": 120,
      "window_seconds": 60,
      "messages_per_second": 20,
      "max_payload_size": 16384
    },
    "websocket": {
      "endpoint": "/v1/ws/session/{session_id}",
      "connection_timeout_seconds": 30,
      "heartbeat_interval_seconds": 15
    }
  }
}
```

The health payload reports header names and limits, never configured API key values.
