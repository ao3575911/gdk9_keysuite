# Macros

KeySuite macro support allows reusable token sequences to be registered per session.

## Registering macros

```python
session.register_macro("pair", ["C", "C"])
session.process(["pair", "SPACE"])
```

## Validation rules

- Macro names must be safe identifiers.
- Macro tokens must be valid grammar tokens, registered macro names, or escape-aware literal sequences.
- Recursive expansion is rejected.
- Expansion depth is limited by `max_macro_expansion_depth`.

## TOML macros

Macros can be declared in `keysuite.toml`:

```toml
[macros]
pair = ["C", "C"]
```

## Expansion events

The REST and WebSocket APIs emit macro expansion events before the expanded token stream is processed.
