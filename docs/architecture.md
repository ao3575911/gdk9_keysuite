# Architecture

KeySuite remains a deterministic GDk9 runtime. The hardening pass adds lifecycle and transport control around the kernel without changing reducer purity or FSM transition semantics.

## Session Lifecycle

- `Runtime` owns a `SessionManager`.
- `SessionManager.create_session()` builds an isolated `RuntimeSession` with its own `IMEKernel`, history stack, macro context, and store handle.
- `SessionManager.get_session()` refreshes last-access time for idle cleanup.
- `SessionManager.destroy_session()` removes session state and updates runtime metrics.
- A cleanup worker prunes idle sessions after `session_idle_ttl_seconds`.

## Event System

Runtime events are emitted in-process through `EventBus`.

Observed event types include:

- `TOKEN_ACCEPTED`
- `STATE_TRANSITION`
- `BUFFER_UPDATED`
- `COMMIT`
- `ERROR`
- `MACRO_EXPANDED`
- `UNDO`
- `REDO`

The event payload is transport-agnostic. WebSocket clients subscribe to the bus and receive JSON envelopes in the form:

```json
{
  "type": "STATE_TRANSITION",
  "session_id": "abc123",
  "payload": {
    "from_state": "IDLE",
    "to_state": "COMPOSE"
  },
  "timestamp": "2026-05-05T12:00:00Z"
}
```

## WebSocket Flow

1. The client authenticates with an API key when configured.
2. The server resolves the target session and registers the socket with `ConnectionManager`.
3. Incoming messages are bounded by payload size and per-connection message rate.
4. Runtime calls publish structured events to the `EventBus`.
5. The websocket handler drains the subscription queue and forwards those events to the client.
6. Heartbeat timeouts trigger a ping frame and a graceful close if the peer does not respond.

## Persistence Boundary

Persistence is optional and pluggable.

- `InMemoryStore` is the default.
- `RedisStore` is a scaffold for external state backends.

Only runtime state that benefits from replay or recovery should be persisted. The reducer remains pure and stateless.
