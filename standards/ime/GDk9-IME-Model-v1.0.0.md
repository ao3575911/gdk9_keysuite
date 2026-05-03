<img src="../../branding/logos/gdk9-logo.svg" width="180"/>

# GDk9 IME Execution Model v1.0.0

## Status

Normative for GDk9 v1.0.0.

## Runtime State

An IME kernel maintains:

- `state`: one of the grammar-declared states
- `buffer`: volatile composition symbols
- `mode`: optional mode context captured by `MODE_SHIFT`

The buffer and mode are volatile. They MUST NOT be treated as committed output.

## Event Handling

For each input event:

1. Read the event class and value.
2. Look up the transition for the current state and event class.
3. If no transition exists, enter `ERROR` and emit nothing.
4. Apply the transition action.
5. Move to the transition next state.

## Commit Boundary

Only `reduce_and_emit` MAY emit output. In v1.0.0, `reduce_and_emit` is reachable from `COMPOSE` and `MODE` through `COMMIT`.

`COMMIT` while `IDLE` is a no-op.

## Abort and Rollback

`ROLLBACK` removes the most recent buffered symbol where the transition table permits it. `ABORT` clears volatile state and returns to `IDLE`. `ABORT` is also the recovery path from `ERROR`.

## Error State

Invalid or out-of-jurisdiction events MUST NOT be coerced into content. They move the kernel to `ERROR` unless the grammar explicitly defines another transition for that state and event class.

`MODE_SHIFT` from `IDLE` has no v1.0.0 transition and therefore enters `ERROR`. Mode context must be captured from an existing composition.

## Literal Escape

The literal escape marker is handled before event dispatch. When `_` precedes a token, the following token enters the runtime as literal `CONTENT`. Escaped bind markers do not form implication boundaries.
