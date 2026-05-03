# GDk9 - Symbolic Implication Infrastructure

<p align="center">
  <img width="240" height="64" alt="GDk9 Logo" src="https://github.com/user-attachments/assets/c8ac739a-e058-45f4-afcc-763d16ff3cc9" />
</p>

<p align="center">
  <a href="https://gdk-9-key-suite-runtime-gui--ao3575911.replit.app/">
    <img alt="Live Demo" src="https://img.shields.io/badge/Live%20Demo-Open%20GUI-brightgreen?style=for-the-badge&logo=rocket" />
  </a>
  <a href="https://github.com/ao3575911/gdk9_keysuite/releases">
    <img alt="Version 1.0.0" src="https://img.shields.io/badge/Version-1.0.0-blue?style=for-the-badge" />
  </a>
  <a href="LICENSE">
    <img alt="License MIT" src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" />
  </a>
</p>

**GDk9** is a deterministic symbolic implication architecture.  
**KeySuite** is the official reference runtime for GDk9 v1.0.0.

Symbols enter explicit jurisdiction, flow through a finite state machine, and produce output **only at commit boundaries** after pure reduction.

## Current Release

- **GDk9 Standard**: 1.0.0
- **KeySuite Runtime**: 1.0.0
- **Grammar**: `grammar/gdk9-v1.0.0.yaml`
- **Python Package**: `keysuite` 1.0.0

## Quick Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

**Verify:**

```bash
keysuite --help
keysuite validate
keysuite run --tokens "C C . 3 3 SPACE"
```

**Expected output:** `CC→33`

## CLI Overview

| Command              | Purpose                              | Example |
|----------------------|--------------------------------------|--------|
| `keysuite run`       | Process token stream                 | `keysuite run C C . 3 3 SPACE` |
| `keysuite validate`  | Validate grammar                     | `keysuite validate` |
| `keysuite inspect-grammar` | Inspect grammar / FSM          | `keysuite inspect-grammar --fsm` |
| `keysuite reduce`    | Pure reducer (no state machine)      | `keysuite reduce A . B` |
| `keysuite conformance` | Run test vectors                   | `keysuite conformance conformance/vectors` |
| `keysuite repl`      | Interactive session                  | `keysuite repl` |
| `keysuite completion`| Shell completions                    | `keysuite completion bash` |

### Common Usage Patterns

- **Positional**: `keysuite run C C . 3 3 SPACE`
- **Quoted string**: `keysuite run --tokens "C C . 3 3 SPACE"`
- **Stdin**: `echo "C C . 3 3 SPACE" \| keysuite run --stdin`
- **File**: `keysuite run --file examples/basic.tokens`

**Literal content** (escape token `_`):

```bash
keysuite run A _ . B          # → A.B
```

## Features & Behaviors

- **Mode shifts**: `X : A B SPACE`
- **Rollback**: `A B BACKSPACE SPACE`
- **Abort**: `A ESC`
- **Debug levels**: `--debug 0..3` (or `--trace`)
- **Strict exit codes** for scripting/CI

See full [CLI Reference](site/reference/cli.md) and [Runtime Reference](reference/README.md).

## Cookbook

### Basic Implication
```bash
keysuite run --tokens "C C . 3 3 SPACE"
```

### Mode Shift + Commit
```bash
keysuite run --tokens "X : A B SPACE"
```

### Rollback
```bash
keysuite run --tokens "A B BACKSPACE SPACE"
```

### Interactive REPL
```bash
keysuite repl
```
Inside REPL: `:state`, `:reset`, `:quit`

## Development & Testing

```bash
pytest                    # unit tests
make conformance          # full conformance suite
make release-check        # pre-release validation
```

## Project Structure

- `grammar/gdk9-v1.0.0.yaml` — Canonical grammar definition
- `reference/keysuite/` — Core runtime (loader, FSM compiler, reducer, IME)
- `conformance/vectors/` — Official test vectors
- `docs/` & `site/` — Documentation

## Documentation

- [Runtime Architecture](reference/README.md)
- [CLI Reference](site/reference/cli.md)
- [Conformance Specification](docs/RUNTIME_CONFORMANCE.md)
- [Test Vectors](docs/CONFORMANCE_VECTORS.md)

---

**GDk9** is intentionally narrow by design — focused on correctness, determinism, and explicit symbolic jurisdiction.
