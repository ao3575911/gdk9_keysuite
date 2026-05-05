# Runtime Architecture

KeySuite is a deterministic runtime with a kernel, session manager, event bus, and transport boundary:

- `grammar_loader.py` loads and unwraps `grammar/gdk9-v1.0.0.yaml`.
- `transitions.py` validates and compiles the transition table.
- `runtime.py` owns `SessionManager`, `RuntimeSession`, and `IMEKernel`.
- `events.py` publishes structured runtime events for state changes and commits.
- `api.py` adapts the runtime to REST and WebSocket transport without coupling the reducer.
- `reducer.py` performs pure reduction at commit.

The CLI entry point is `keysuite/cli.py`. It tokenizes input, feeds events into
the runtime, and prints only committed output.

The architecture keeps the grammar as the runtime control surface. Standards,
tests, and runtime behavior stay synchronized through the versioned grammar
artifact.

## Runtime Hardening

- Each session owns its own `IMEKernel`, history stack, and macro context.
- The runtime emits token, transition, commit, macro, undo, redo, and error events.
- WebSocket connections are tracked separately from sessions so they can be closed and rate-limited independently.
- Metrics and health endpoints expose active sessions, connections, token throughput, latency, and error rate.
- Optional persistence keeps session snapshots recoverable without making the reducer stateful.
