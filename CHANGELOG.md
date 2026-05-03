# Changelog

## Unreleased

- Added GitHub Actions CI, CodeQL, dependency audit, and static security scanning workflows.
- Added a security policy and Dependabot configuration.
- Hardened the CLI with positional token arrays, `--tokens`, `--grammar`, `--trace`, `--json`, `--version`, `validate`, `inspect-grammar`, and `reduce`.
- Added non-zero CLI exit behavior for unrecovered `ERROR` state.
- Added strict grammar schema validation for required keys, supported versions, unknown fields, exact-token uniqueness, transitions, actions, and reachability.
- Implemented the grammar-declared literal escape marker `_`.
- Added grammar hash reporting for validation and machine-readable CLI output.

## v1.0.0 - 2026-05-03

- Published the initial GDk9 v1.0.0 standards stack.
- Published the KeySuite v1.0.0 reference runtime.
- Added grammar-controlled finite-state execution, pure reduction, conformance tests, release docs, and documentation site content.
