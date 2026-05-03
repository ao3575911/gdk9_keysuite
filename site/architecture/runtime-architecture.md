# Runtime Architecture

KeySuite is a small reference runtime with four runtime layers:

- `grammar_loader.py` loads and unwraps `grammar/gdk9-v1.0.0.yaml`.
- `transitions.py` validates and compiles the transition table.
- `ime_runtime.py` executes the finite state machine and owns volatile buffer state.
- `reducer.py` performs pure reduction at commit.

The CLI entry point is `reference/keysuite/src/main.py`. It tokenizes input,
feeds events into the runtime, and prints only committed output.

The architecture keeps the grammar as the runtime control surface. Standards,
tests, and runtime behavior stay synchronized through the versioned grammar
artifact.
