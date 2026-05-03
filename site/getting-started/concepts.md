# Concepts

GDk9 uses:

- symbol jurisdiction
- finite-state execution
- atomic commit
- pure reduction

## Symbol Jurisdiction

Every input event is classified before it enters the runtime. Runtime event
classes map to declared grammar symbols such as `CONTENT`, `BIND`,
`MODE_SHIFT`, `COMMIT`, `ROLLBACK`, and `ABORT`.

## Finite-State Execution

The IME kernel moves through grammar-declared states: `IDLE`, `COMPOSE`,
`MODE`, and `ERROR`. Invalid or out-of-jurisdiction events must not be coerced
into content.

## Atomic Commit

The buffer and mode are volatile until commit. Only the `reduce_and_emit`
transition action may emit output.

## Pure Reduction

Reduction depends only on the buffered symbols and optional mode context. It
must not use external I/O, hidden mutable state, or probabilistic rewriting.
