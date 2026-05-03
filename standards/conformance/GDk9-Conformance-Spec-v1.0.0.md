<img src="../../branding/logos/gdk9-logo.svg" width="180"/>

# GDk9 Conformance Specification v1.0.0

## Status

Normative for GDk9 v1.0.0.

## Conformance Claim

An implementation MAY claim GDk9 v1.0.0 conformance only if it passes tests proving:

- grammar version identity
- explicit symbol jurisdiction
- deterministic output
- commit-only emission
- rollback behavior
- abort recovery
- invalid-event error behavior
- pure reduction behavior
- transition-table validation

## Required Evidence

A release MUST publish the following evidence:

- grammar file path and version
- runtime version
- test command
- test result
- any known non-conformance

For this repository, the release evidence command is:

```bash
pytest
```

The stricter local release gate is:

```bash
make release-check
```

## Failure Rules

An implementation is non-conformant if any of the following are true:

- emits output before commit
- treats undeclared symbols as valid content
- rewrites symbols probabilistically
- mutates committed output after emission
- accepts transition table entries with unknown actions or states
- claims a grammar version it does not load
