<img src="../../branding/logos/gdk9-logo.svg" width="180"/>

# GDk9 Reduction Contract v1.0.0

## Status

Normative for GDk9 v1.0.0.

## Function

Reduction is a pure function:

```text
kappa(buffer, mode) -> output
```

For KeySuite v1.0.0, `kappa` is implemented by `reference/keysuite/src/reducer.py`.

## Purity Requirements

The reducer MUST:

- depend only on `buffer` and `mode`
- produce the same output for the same inputs
- avoid external I/O
- avoid hidden mutable state
- avoid probabilistic or model-derived rewriting

## Bind Semantics

The canonical bind marker is `.`. If the buffer contains a bind marker, the first marker is the implication boundary:

```text
left . right -> left→right
```

Additional bind markers after the first are treated as content inside the right side by KeySuite v1.0.0.

## Mode Semantics

When `mode` is present, the reduced result is wrapped as:

```text
mode(result)
```

Mode context is captured before the mode-scoped buffer starts.
