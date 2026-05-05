# KeySuite

KeySuite is the canonical Python runtime for GDk9 v1.0.0.

It loads `grammar/gdk9-v1.0.0.yaml`, validates grammar schema and
grammar-controlled transitions, processes finite-state events, and emits output
only at commit.

## Command Surface

- `keysuite run`
- `keysuite validate`
- `keysuite inspect-grammar`
- `keysuite dump-fsm`
- `keysuite reduce`
- `keysuite conformance`
- `keysuite repl`
- `keysuite completion`

Primary source files:

- `keysuite/cli.py`
- `keysuite/runtime.py`
- `keysuite/reducer.py`
- `keysuite/grammar_loader.py`
- `keysuite/events.py`
- `keysuite/api.py`

Compatibility shims remain available under `reference/keysuite/src/` for
backward-compatible imports, but the authoritative implementation lives in
`keysuite/`.
