# Changelog

## Unreleased

- No unreleased changes.

## v1.1.0.dev3 - 2026-05-06

- Added `DONE` as a grammar-declared commit token in the canonical grammar, packaged grammar data, and compatibility grammar aliases.
- Added conformance vectors for `DONE` commits, implication commits, and mode commits while preserving the existing `SPACE` commit vectors.
- Removed the root CLI help brace-list from command output without changing subcommand behavior.
- Added a local `/favicon.ico` response so browser access to `/docs` no longer emits a favicon 404.
- Hardened websocket handling with heartbeat-driven session refresh, per-frame API-key limiting, structured rate-limit errors, and missing-session close behavior.
- Added OpenAPI API-key metadata and non-secret API policy data in `/v1/health`.
- Replaced the Bandit `try/except/pass` and runtime `assert` findings with explicit error handling.
- Expanded REST, websocket, grammar-alias, CLI, and conformance regression coverage.
- Synchronized README, release docs, version metadata, changelog, and provenance guidance for the `1.1.0.dev3` release line.

## v1.1.0.dev2 - 2026-05-05

- Refreshed the release documentation set for the hardened runtime additions.
- Reworked the public and reference documentation to describe the canonical `keysuite/` layout.
- Bumped the release metadata to `1.1.0.dev2` across package, manifest, and version files.
- Updated release provenance guidance to include the canonical runtime package in release evidence.
- Re-stamped the public release pages and version matrix for the development release.

## v1.1.0.dev1 - 2026-05-05

- Hardened the runtime around explicit session isolation, event publication, websocket connection tracking, API governance, and observability.
- Added session lifecycle, scaling, and security documentation for the new runtime boundaries.
- Updated every repository README to reflect the hardened API, websocket, and release surfaces.
- Bumped the development release metadata to `1.1.0.dev1` across package, manifest, and version files.
- Added compatibility grammar aliases `grammar/gdk9-v1.0.0-2.yaml` and `grammar/gdk9-v1.0.0-3.yaml` without changing GDk9 v1.0.0 semantics.
- Added `examples/README.md` with annotated production-grade outcomes for the shipped token fixtures.
- Fixed the CLI grammar-loader import path so the runtime resolves the bundled default grammar consistently.
- Updated the reduction contract to reference canonical `keysuite/reducer.py` instead of the legacy reference-path implementation.
- Added loader coverage for the grammar alias files and packaged all three grammar YAML artifacts.
- Replaced stale `reference/keysuite/src/*` pointers in the README with canonical `keysuite/*` paths.
- Added `httpx` to the development dependency set so FastAPI TestClient collection succeeds in CI and local Python.

## v1.0.0 - 2026-05-03

- Published the initial GDk9 v1.0.0 standards stack.
- Published the KeySuite v1.0.0 reference runtime.
- Added grammar-controlled finite-state execution, pure reduction, conformance tests, release docs, and documentation site content.
