# IME Execution Model

The GDk9 IME kernel maintains a grammar-declared state, a volatile composition
buffer, and optional mode context. For each input event, it reads the event
class, looks up the current transition, applies the transition action, then
moves to the next state.

Only `reduce_and_emit` may emit output. `ABORT` clears volatile state and
returns to `IDLE`; it is also the recovery path from `ERROR`.

`MODE_SHIFT` from `IDLE` enters `ERROR`; mode context must come from an existing
composition. Literal escape is handled before event dispatch.

Normative source: `standards/ime/GDk9-IME-Model-v1.0.0.md`.
