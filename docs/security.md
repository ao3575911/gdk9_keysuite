# Security

KeySuite hardens the local runtime with explicit access control and traffic governance while preserving deterministic reduction.

## API Key Model

- API keys are optional.
- When `api_keys` is configured, requests under `/v1` and websocket connections under `/v1/ws/...` must include the configured header.
- Missing or invalid keys are rejected before runtime execution.
- `/docs` remains available for local API exploration. `/openapi.json` marks `/v1` operations with the configured API-key header when authentication is enabled.

## Rate Limiting

Two levels of rate limiting are enforced:

- per API key, to cap overall request volume
- per session, to cap session-specific activity

WebSocket connections also apply per-connection message-rate checks, per-frame API-key request limiting, per-session rate limiting, and bounded payload sizes.

## Input Validation

- Tokens must be non-empty strings without whitespace or control characters.
- Macro definitions must only reference valid grammar or macro tokens.
- WebSocket payloads are size-limited before parsing.
- Request bodies above the configured maximum are rejected early.

## Error Shape

All API errors are normalized to:

```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "session rate limit exceeded",
    "details": {}
  }
}
```

This keeps failure handling machine-readable without leaking implementation internals.

## Operational Notes

- JSON logging is preferred for production deployment.
- Metrics expose active sessions, active connections, token throughput, average latency, and error rate.
- `GET /v1/health` exposes non-secret policy metadata such as route URLs, header names, and rate-limit values. It does not expose configured API keys.
- The persistence layer is intentionally pluggable so a deployment can move from in-memory state to a shared backend without rewriting runtime logic.
