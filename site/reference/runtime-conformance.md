# Runtime Conformance

KeySuite v1.0.0 implements GDk9 v1.0.0 by loading
`grammar/gdk9-v1.0.0.yaml`.

Evidence commands:

```bash
pytest
make release-check
keysuite validate
```

Covered behavior includes basic implication reduction, repeatability, rollback,
abort, mode shift, timeout commit, invalid-event error state, grammar loading,
token classification, required state validation, YAML transition control,
unknown action rejection, undeclared jurisdiction rejection, strict schema
validation, CLI diagnostics, trace output, JSON output, literal escape behavior,
and no output before commit.
