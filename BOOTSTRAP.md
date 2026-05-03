<img src="branding/logos/gdk9-logo.svg" width="180"/>

# GDk9 Bootstrap Context

GDk9 is deterministic symbolic implication infrastructure. KeySuite is the reference runtime implementing the GDk9 IME model.

---

## System State

- GDk9 Standard: 1.0.0
- KeySuite Runtime: 1.0.0
- Grammar: `grammar/gdk9-v1.0.0.yaml` version 1.0.0
- Runtime source: `reference/keysuite/src/`
- Normative standards: `standards/`
- Human documentation: `site/` and `docs/`
- Conformance tests: `tests/`

---

## Core Principles

- Deterministic execution
- Finite state machine (IME model)
- Explicit symbol jurisdiction
- Atomic commit only
- Pure reduction (κ)

---

## Example

Input:

```text
C C . 3 3
```

Output:

```text
CC→33
```

---

## Bootstrap Commands

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
pytest
keysuite "C C . 3 3"
```

## Release Gate

Before pushing to GitHub, run:

```bash
make release-check
make clean
git status --short
```

Expected runtime output for the release example is `CC→33`.
