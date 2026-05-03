# Contributing

GDk9 is standards infrastructure. KeySuite is the reference runtime.
Contributions must preserve determinism, explicit symbol jurisdiction,
commit-only output, and pure reduction.

Runtime changes belong under `reference/keysuite/src/` and must include tests
when behavior changes. Documentation changes should keep `site/`, `docs/`,
`standards/`, and `grammar/` synchronized when they affect public behavior or
release claims.

Before submitting a release-affecting change, run:

```bash
pytest
make release-check
```

See `CONTRIBUTING.md` and `CONTRIBUTORS.md` for the repository-level governance
and contributor records.
