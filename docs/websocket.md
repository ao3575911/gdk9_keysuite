# WebSocket API

The streaming session endpoint is:

```text
/v1/ws/session/{session_id}
```

## Message types

### Token

```json
{"type": "token", "value": "C"}
```

### Token batch

```json
{"type": "tokens", "values": ["C", "C", "SPACE"]}
```

### Heartbeat response

```json
{"type": "pong"}
```

### Undo / redo

```json
{"type": "undo"}
{"type": "redo"}
```

### Macro registration

```json
{"type": "register_macro", "name": "pair", "tokens": ["C", "C"]}
```

## Event types

The server emits JSON events for:

- token acceptance
- state transitions
- buffer updates
- commit emissions
- macro expansion
- undo / redo
- errors

Limit and validation failures are reported as error events and respect the configured runtime limits.

## Message Envelope

All runtime events are delivered as:

```json
{
  "type": "STATE_TRANSITION",
  "session_id": "abc123",
  "payload": {},
  "timestamp": "2026-05-05T12:00:00Z"
}
```

## Heartbeats and Limits

- Connections close after the configured idle timeout if no frames arrive.
- The server sends a `PING` event before closing on timeout.
- Client `pong` frames refresh both connection liveness and the owning session idle TTL.
- Message payloads are size-limited.
- Per-connection message rate limits are enforced.
- When API keys are configured, the websocket handshake and each received frame also consume the API-key request limit.
- Session-specific websocket activity consumes the session rate limit.
- Rate-limit failures are returned as `ERROR` events before the socket closes.
