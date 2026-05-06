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
- `SECURITY.md`, `CHANGELOG.md`, and `.github/workflows/` are present.
- `VERSION` and `version/current.txt` identify GDk9, KeySuite, and grammar versions.
- `grammar/gdk9-v1.0.0.yaml` contains version metadata and transition rules.
- `requirements.txt` has bounded ranges and `requirements.lock` records the tested dependency set.
- `standards/`, `site/`, `reference/`, `scripts/`, and `docs/` contain current documentation.
- `tests/` includes conformance coverage for grammar-controlled transitions, schema validation, CLI diagnostics, tracing and debug levels, stdin/file input, REPL behavior, literal escape behavior, REST docs/health behavior, and websocket auth/rate-limit behavior.
- GitHub repository security settings enable Dependabot alerts, secret scanning, and push protection where available.
- Release notes include artifact checksums or a link to generated provenance evidence.
- generated caches, virtual environments, egg-info, and archives are not staged.
