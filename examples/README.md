# KeySuite Examples

These fixtures are production-grade because each token stream maps directly to a
normative GDk9 behavior and has a single expected outcome.

The `.tokens` files are intentionally unannotated so they remain valid runtime
inputs. The annotations live here instead.

| File | Tokens | Expected result | Annotation |
| --- | --- | --- | --- |
| `basic.tokens` | `C C . 3 3 SPACE` | `CC→33` | Basic implication reduction. `.` is the bind marker, and `SPACE` commits the buffer. |
| `rollback.tokens` | `A B BACKSPACE SPACE` | `A` | Rollback removes the last buffered symbol before commit, leaving the first symbol intact. |
| `abort.tokens` | `A ESC` | no output | Abort clears volatile state and suppresses emission. This is a negative completion path, not a failure. |
| `mode_shift.tokens` | `X : A B SPACE` | `X(AB)` | Mode shift scopes reduction inside the active mode and preserves the outer symbol as the mode label. |
| `invalid.tokens` | `@` | error: `Token has no GDk9 jurisdiction or no valid transition` | Invalid input transitions into `ERROR` deterministically and does not emit output. |

## Completion Evidence

These are the commands that establish the examples directory is complete and
behaviorally aligned with the runtime:

```bash
keysuite run --file examples/basic.tokens
keysuite run --file examples/rollback.tokens
keysuite run --file examples/abort.tokens
keysuite run --file examples/mode_shift.tokens
keysuite run --file examples/invalid.tokens
keysuite conformance conformance/vectors
```

## Production Criteria

- The token fixtures are minimal and exact.
- The annotations match the normative conformance vectors.
- The examples cover success, rollback, abort, mode shift, and invalid-input paths.
- The examples do not introduce new syntax or behavior beyond GDk9 v1.0.0.
