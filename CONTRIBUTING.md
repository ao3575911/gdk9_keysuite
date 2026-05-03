<img src="branding/logos/gdk9-logo.svg" width="180"/>

# Contributing to GDk9 and KeySuite

GDk9 is standards infrastructure. KeySuite is the reference runtime. Contributions must preserve determinism, explicit symbol jurisdiction, commit-only output, and pure reduction.

## Contribution Types

## Standards

Changes to the Core Standard, Grammar Specification, IME Model, Reduction Contract, or Conformance Specification require a GDk9 Enhancement Proposal in `proposals/`.

Standards changes must update:

- the affected document in `standards/`
- `grammar/gdk9-v1.0.0.yaml` when behavior changes
- site documentation in `site/`
- release documentation in `docs/`
- conformance tests in `tests/`

## Runtime

Runtime changes belong under `reference/keysuite/src/`.

Allowed runtime work:

- bug fixes
- conformance improvements
- portability improvements
- clearer validation
- performance improvements that do not change semantics

Runtime changes must include tests when behavior changes.

## Tests

Tests live in `tests/` and use `pytest`.

Run:

```bash
pytest
make release-check
```

## Forbidden Changes

- probabilistic output
- hidden state
- implicit symbol reinterpretation
- output before commit
- standards behavior changes without a GDk9-EP

## Commit Messages

Use focused commits. For release commits, prefer the Lore trailer style documented in `AGENTS.md`.
