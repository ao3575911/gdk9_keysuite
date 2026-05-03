# KeySuite Reference Runtime

This directory contains the KeySuite reference runtime for GDk9 v1.0.0.

## Source

- `keysuite/src/grammar_loader.py`
- `keysuite/src/transitions.py`
- `keysuite/src/ime_runtime.py`
- `keysuite/src/reducer.py`
- `keysuite/src/main.py`

## Contract

The runtime loads `grammar/gdk9-v1.0.0.yaml`, validates transitions, processes finite-state events, and emits output only at commit.

Run from the repository root:

```bash
pytest
keysuite "C C . 3 3"
```
