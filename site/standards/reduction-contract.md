# Reduction Contract

Reduction is a pure function:

```text
kappa(buffer, mode) -> output
```

For KeySuite v1.0.0, the reducer is implemented by
`keysuite/reducer.py`. The canonical bind marker is `.`, and the
first bind marker is the implication boundary:

```text
left . right -> left→right
```

Additional bind markers after the first are right-side content. Escaped literal
bind characters are content and do not form implication boundaries.

Normative source: `standards/reduction/GDk9-Reduction-Contract-v1.0.0.md`.
