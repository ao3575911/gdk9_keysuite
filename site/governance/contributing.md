# Contributing

GDk9 is standards infrastructure. KeySuite is the canonical runtime.
Contributions must preserve determinism, explicit symbol jurisdiction,
commit-only output, and pure reduction.

Runtime changes belong under `keysuite/` and must include tests when behavior
changes. The legacy `reference/keysuite/src/` tree remains as compatibility
shims only. Documentation changes should keep `site/`, `docs/`, `standards/`,
and `grammar/` synchronized when they affect public behavior or release claims.

Before submitting a release-affecting change, run:

```bash
pytest
make release-check
```

See `CONTRIBUTING.md` and `CONTRIBUTORS.md` for the repository-level governance
and contributor records.
