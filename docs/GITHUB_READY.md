# GitHub Readiness Checklist

Run:

```bash
make release-check
make clean
git status --short
```

Check:

- `README.md` explains install, test, runtime, docs, and release flow.
- `LICENSE`, `CONTRIBUTING.md`, and `CONTRIBUTORS.md` are present.
- `VERSION` and `version/current.txt` identify GDk9, KeySuite, and grammar versions.
- `grammar/gdk9-v1.0.0.yaml` contains version metadata and transition rules.
- `standards/`, `site/`, `reference/`, `scripts/`, and `docs/` contain current documentation.
- `tests/` includes conformance coverage for grammar-controlled transitions.
- generated caches, virtual environments, egg-info, and archives are not staged.
