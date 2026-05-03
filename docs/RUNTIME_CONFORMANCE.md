# Runtime Conformance

KeySuite v1.0.0 implements GDk9 v1.0.0 by loading `grammar/gdk9-v1.0.0.yaml`.

## Evidence Commands

```bash
pytest
make release-check
keysuite validate
keysuite run --tokens "C C . 3 3 SPACE"
keysuite inspect-grammar --fsm
```

## Covered Behaviors

- basic implication reduction
- repeatability
- rollback
- abort
- mode shift
- timeout commit
- invalid event error state
- grammar loading
- token classification
- required state validation
- YAML transition control
- unknown action rejection
- undeclared jurisdiction rejection
- no output before commit
- strict grammar schema validation
- non-zero CLI exit on unrecovered error
- trace, debug, and JSON CLI output
- literal escape behavior for syntax tokens
- stdin and file input
- REPL command handling
