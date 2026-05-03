# Conformance Specification

GDk9 v1.0.0 conformance requires tests that prove grammar version identity,
explicit symbol jurisdiction, deterministic output, commit-only emission,
rollback behavior, abort recovery, invalid-event error behavior, pure reduction,
transition-table validation, strict grammar schema validation, CLI diagnostics,
trace output, JSON output, and literal escape behavior.

Repository evidence commands:

```bash
pytest
make release-check
keysuite validate
```

Normative source: `standards/conformance/GDk9-Conformance-Spec-v1.0.0.md`.
