# GDk9 v1.0.0 Conformance Vectors

These vectors are canonical examples for the KeySuite reference runtime.

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

The CLI appends `SPACE` as an automatic commit unless `--no-auto-commit` is used.

Run the full vector suite with:

```bash
keysuite conformance conformance/vectors
make conformance
```
