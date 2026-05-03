# Runtime Conformance

KeySuite v1.0.0 implements GDk9 v1.0.0 by loading
`grammar/gdk9-v1.0.0.yaml`.

Evidence commands:

```bash
pytest
make release-check
keysuite validate
keysuite run --tokens "C C . 3 3 SPACE"
keysuite inspect-grammar --fsm
```

Covered behavior includes basic implication reduction, repeatability, rollback,
abort, mode shift, timeout commit, invalid-event error state, grammar loading,
token classification, required state validation, YAML transition control,
unknown action rejection, undeclared jurisdiction rejection, strict schema
validation, CLI diagnostics, trace and debug output, JSON output, literal escape
behavior, stdin/file input, REPL handling, and no output before commit.
