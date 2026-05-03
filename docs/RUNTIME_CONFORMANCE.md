# Runtime Conformance

KeySuite v1.0.0 implements GDk9 v1.0.0 by loading `grammar/gdk9-v1.0.0.yaml`.

## Evidence Commands

```bash
pytest
make release-check
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
