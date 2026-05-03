# KeySuite

KeySuite is the reference runtime implementing GDk9.

It loads `grammar/gdk9-v1.0.0.yaml`, validates grammar schema and
grammar-controlled transitions, processes finite-state events, and emits output
only at commit.

Primary source files:

- `reference/keysuite/src/grammar_loader.py`
- `reference/keysuite/src/transitions.py`
- `reference/keysuite/src/ime_runtime.py`
- `reference/keysuite/src/reducer.py`
- `reference/keysuite/src/main.py`
