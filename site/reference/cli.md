# CLI Usage

Run the reference runtime after installing the package:

```bash
keysuite "C C . 3 3"
```

Expected output:

```text
CC→33
```

The same example is available through `make run`.

Additional commands:

```bash
keysuite C C . 3 3
keysuite --tokens "C C . 3 3"
keysuite --trace C C . 3 3
keysuite --json @
keysuite validate
keysuite inspect-grammar
keysuite reduce A . B
```

Invalid unrecovered input exits non-zero. `_` escapes the next token as literal
content, so `keysuite A _ . B` emits `A.B`.
