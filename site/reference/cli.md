# CLI Usage

KeySuite exposes a small command surface:

```bash
keysuite run --tokens "C C . 3 3 SPACE"
keysuite validate
keysuite validate grammar/gdk9-v1.0.0.yaml
keysuite inspect-grammar --fsm
keysuite dump-fsm
keysuite reduce A . B
keysuite conformance conformance/vectors
keysuite repl
keysuite completion bash
```

## Input Forms

```bash
keysuite run C C . 3 3 SPACE
keysuite run --tokens "C C . 3 3 SPACE"
echo "C C . 3 3 SPACE" | keysuite run --stdin
keysuite run --file examples/basic.tokens
```

## Debug Levels

- `--debug 0`: no extra debug output
- `--debug 1`: emitted output plus final state
- `--debug 2`: transition trace
- `--debug 3`: full runtime detail

`--trace` is kept as an alias for `--debug 2`.

## Exit Codes

- `0`: success
- `1`: runtime or conformance failure
- `2`: CLI usage error
- `3`: grammar or schema validation error
- `4`: stdin or file input error
- `5`: internal runtime exception

## Shell Completions

Generate a script:

```bash
keysuite completion bash
keysuite completion zsh
keysuite completion fish
```

Install it by copying the generated file into the shell's completion directory.

## Notes

The grammar escape token `_` makes the next token literal content, so
`keysuite run A _ . B` emits `A.B`.
