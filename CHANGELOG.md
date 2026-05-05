# Changelog

## v1.1.0.dev0 - 2026-05-05

- Added compatibility grammar aliases `grammar/gdk9-v1.0.0-2.yaml` and `grammar/gdk9-v1.0.0-3.yaml` without changing GDk9 v1.0.0 semantics.
- Added `examples/README.md` with annotated production-grade outcomes for the shipped token fixtures.
- Fixed the CLI grammar-loader import path so the runtime resolves the bundled default grammar consistently.
- Updated the reduction contract to reference canonical `keysuite/reducer.py` instead of the legacy reference-path implementation.
- Added loader coverage for the grammar alias files and packaged all three grammar YAML artifacts.

## Unreleased

- Future maintenance and release notes will appear here.

## v1.0.0 - 2026-05-03

- Published the initial GDk9 v1.0.0 standards stack.
- Published the KeySuite v1.0.0 reference runtime.
- Added grammar-controlled finite-state execution, pure reduction, conformance tests, release docs, and documentation site content.
