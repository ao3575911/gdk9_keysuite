# Release Artifacts

GDk9 v1.0.0 and KeySuite v1.1.0.dev3 publish a synchronized release tree:

- `standards/` contains the normative standard documents.
- `grammar/gdk9-v1.0.0.yaml` is the machine-readable control artifact.
- `keysuite/` contains the canonical runtime package.
- `reference/` contains compatibility shims for legacy import paths.
- `tests/` contains conformance and regression coverage.
- `docs/` contains release evidence and version metadata.
- `SECURITY.md` defines vulnerability reporting policy.
- `CHANGELOG.md` records release history.
- `site/` contains public documentation pages.
- `version/current.txt` records the current artifact set.

Version changes must update the standards, grammar metadata, tests, public docs,
release docs, `VERSION`, `pyproject.toml`, and `version/current.txt` together.
