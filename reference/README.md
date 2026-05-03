# KeySuite Reference Runtime

This directory contains the KeySuite reference runtime for GDk9 v1.0.0.

## Source

- `keysuite/src/main.py`
- `keysuite/src/grammar_loader.py`
- `keysuite/src/transitions.py`
- `keysuite/src/ime_runtime.py`
- `keysuite/src/reducer.py`

## Runtime Contract

The runtime loads `grammar/gdk9-v1.0.0.yaml`, validates transitions, processes
finite-state events, and emits output only at commit.

## Common Commands

```bash
keysuite run --tokens "C C . 3 3 SPACE"
keysuite run --file examples/basic.tokens
keysuite validate
keysuite inspect-grammar --fsm
keysuite conformance conformance/vectors
keysuite repl
```

Run from the repository root:

```bash
pytest
make release-check
```

