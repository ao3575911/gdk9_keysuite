# Conformance Vectors

| Tokens | Expected Output | Notes |
| --- | --- | --- |
| `C C . 3 3` | `CC→33` | basic implication |
| `A B` | `AB` | plain composition |
| `A B BACKSPACE` | `A` | rollback before commit |
| `A ESC` | none | abort clears volatile state |
| `X : A B` | `X(AB)` | mode-scoped reduction |
| `A . B . C` | `A→B.C` | first bind marker is the implication boundary |
| `A _ . B` | `A.B` | escaped bind marker is literal content |
| `@` | error | invalid token enters unrecovered `ERROR` |

Reference source: `docs/CONFORMANCE_VECTORS.md`.
