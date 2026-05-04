# Configuration

KeySuite configuration is loaded in this order:

1. Explicit arguments passed by the caller
2. Environment variables
3. `keysuite.toml`
4. Built-in defaults

## Environment variables

- `KEYSUITE_GRAMMAR`
- `KEYSUITE_MAX_BUFFER_SIZE`
- `KEYSUITE_MAX_TOKEN_COUNT`
- `KEYSUITE_DEBUG`
- `KEYSUITE_VERSION_POLICY`
- `KEYSUITE_MAX_MACRO_EXPANSION_DEPTH`
- `KEYSUITE_HISTORY_LIMIT`

## `keysuite.toml`

```toml
grammar = "grammar/gdk9-v1.0.0.yaml"
max_buffer_size = 256
max_token_count = 4096
max_macro_expansion_depth = 16
history_limit = 128
version_policy = "latest-compatible"

[macros]
pair = ["C", "C"]
```

Supported `version_policy` values:

- `latest-compatible`
- `strict`

## Notes

- Macro definitions are validated against the loaded grammar.
- Oversized buffers and token streams fail with structured runtime errors.
- History snapshots are bounded by `history_limit`.
