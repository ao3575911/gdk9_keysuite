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
- `GET /v1/metrics`
- `GET /v1/grammar`
- `GET /v1/session/{session_id}`
- `POST /v1/process`
- `POST /v1/session`
- `POST /v1/session/{session_id}/process`
- `POST /v1/session/{session_id}/undo`
- `POST /v1/session/{session_id}/redo`
- `DELETE /v1/session/{session_id}`

OpenAPI docs are available at `/docs` and `/openapi.json`.

When API keys are configured, include the configured header on every `/v1` request. The default header is `X-API-Key`.
