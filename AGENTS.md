# Repository Guidelines

## Project Structure & Module Organization

This repository contains the GDk9 standards stack and the KeySuite reference runtime. Runtime source lives in `reference/keysuite/src/`, with the CLI entry point in `main.py`, reducer logic in `reducer.py`, grammar loading in `grammar_loader.py`, and state handling in `ime_runtime.py`. Tests live in `tests/` and cover basic implication, repeatability, and reducer behavior. Versioned normative documents are under `standards/`; machine-readable grammar is in `grammar/gdk9-v1.0.0.yaml`; generated documentation pages are in `site/`; logos are in `branding/logos/`; proposals are in `proposals/`.

## Build, Test, and Development Commands

- `python3 -m venv .venv && source .venv/bin/activate`: create and enter a local virtual environment.
- `pip install -e .`: install KeySuite in editable mode from `pyproject.toml`.
- `pip install -r requirements.txt`: install runtime and test dependencies, including `pyyaml` and `pytest`.
- `pytest` or `make test`: run the test suite.
- `keysuite "C C . 3 3"` or `make run`: run the CLI example.
- `make clean`: remove build, distribution, egg-info, and Python cache artifacts.

## Coding Style & Naming Conventions

Use Python 3 with 4-space indentation, type hints where they clarify public function contracts, and small deterministic functions. Module and function names use `snake_case`; classes use `PascalCase`. Keep imports explicit and local to the existing package layout. Do not introduce probabilistic behavior, hidden mutable state, or output before commit boundaries.

## Testing Guidelines

Tests use `pytest` and follow `tests/test_*.py` naming. Add regression coverage for every runtime behavior change, especially reducer output, state transitions, rollback/abort handling, and determinism. Standards or grammar changes should include conformance-oriented tests that prove the reference runtime still enforces explicit symbol jurisdiction and pure reduction.

## Commit & Pull Request Guidelines

The current history uses short, direct subjects such as `Add documentation site` and release-oriented subjects such as `GDk9 v1.0.0 + KeySuite reference implementation`. Keep commits focused and describe why the change exists. Pull requests should summarize affected areas, list verification commands run, and call out any standards, grammar, or conformance impact. Standards changes should reference or include a GDk9 Enhancement Proposal.

## Security & Configuration Tips

Do not commit virtual environments, caches, build outputs, or generated archives. Treat `standards/` and `grammar/` as versioned source-of-truth inputs; update them deliberately and keep runtime behavior synchronized with tests.
