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

- state transitions
- commit emissions
- macro expansion
- undo / redo
- errors

Limit and validation failures are reported as error events and respect the configured runtime limits.
