#!/usr/bin/env bash
set -e

mkdir -p site/{getting-started,standards,architecture,reference,governance,assets}

cp branding/logos/gdk9-logo.svg site/assets/gdk9-logo.svg
cp branding/logos/keysuite-logo.svg site/assets/keysuite-logo.svg

cat > site/index.md <<'EOF'
# GDk9 Documentation

GDk9 is deterministic symbolic implication infrastructure.

## Start Here

- [Overview](getting-started/overview.md)
- [Quickstart](getting-started/quickstart.md)
- [Concepts](getting-started/concepts.md)

## Standards

- [Core Standard](standards/core-standard.md)
- [Grammar Specification](standards/grammar-specification.md)
- [IME Execution Model](standards/ime-execution-model.md)
- [Reduction Contract](standards/reduction-contract.md)
- [Conformance Specification](standards/conformance-specification.md)

## Architecture

- [Runtime Architecture](architecture/runtime-architecture.md)
- [Release Artifacts](architecture/release-artifacts.md)
- [Threat Model](architecture/threat-model.md)

## Reference

- [KeySuite](reference/keysuite.md)
- [CLI Usage](reference/cli.md)
- [Runtime Conformance](reference/runtime-conformance.md)
- [Conformance Vectors](reference/conformance-vectors.md)

## Governance

- [Standards Process](governance/standards-process.md)
- [Contributing](governance/contributing.md)
EOF

cat > site/getting-started/overview.md <<'EOF'
# Overview

GDk9 defines deterministic symbolic input and implication. Symbols enter an
explicit jurisdiction, move through a finite state machine, and emit output only
at an atomic commit boundary after pure reduction.

KeySuite is the reference runtime for GDk9 v1.0.0. It loads the versioned
grammar, validates transitions, executes the IME state machine, and uses a pure
reducer to produce committed output.
EOF

cat > site/getting-started/quickstart.md <<'EOF'
# Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
keysuite "C C . 3 3"
```

Expected:

```text
CC→33
```
EOF

cat > site/getting-started/concepts.md <<'EOF'
# Concepts

GDk9 uses:

- symbol jurisdiction
- finite-state execution
- atomic commit
- pure reduction

## Symbol Jurisdiction

Every input event is classified before it enters the runtime. Runtime event
classes map to declared grammar symbols such as `CONTENT`, `BIND`,
`MODE_SHIFT`, `COMMIT`, `ROLLBACK`, and `ABORT`.

## Finite-State Execution

The IME kernel moves through grammar-declared states: `IDLE`, `COMPOSE`,
`MODE`, and `ERROR`. Invalid or out-of-jurisdiction events must not be coerced
into content.

## Atomic Commit

The buffer and mode are volatile until commit. Only the `reduce_and_emit`
transition action may emit output.

## Pure Reduction

Reduction depends only on the buffered symbols and optional mode context. It
must not use external I/O, hidden mutable state, or probabilistic rewriting.
EOF

cat > site/standards/core-standard.md <<'EOF'
# Core Standard

GDk9 requires deterministic execution, explicit symbol classes, and pure reduction.

An implementation claiming GDk9 v1.0.0 conformance must classify every input
event under explicit symbol jurisdiction, execute through a finite state
machine, keep composition state volatile until commit, emit only at commit, and
produce identical output for identical input sequences and grammar versions.

Normative source: `standards/core/GDk9-Core-Standard-v1.0.0.md`.
EOF

cat > site/standards/grammar-specification.md <<'EOF'
# Grammar Specification

Symbols are classified as CONTENT, SYNTAX, CONTROL, COMMIT, or ESCAPE.

The canonical machine-readable grammar is `grammar/gdk9-v1.0.0.yaml`. It
declares artifact metadata, symbol jurisdiction, states, event classes, actions,
transitions, and conformance flags.

The transition compiler must reject unknown states, unknown actions, malformed
entries, and event classes without declared symbol jurisdiction.

The grammar loader also performs strict schema validation for required keys,
supported versions, unknown fields, duplicate exact tokens, transition shape,
and state reachability.

`symbols.escape.literal` declares the literal escape marker. KeySuite v1.0.0
consumes `_` before event dispatch and treats the following token as literal
`CONTENT`.

Normative source: `standards/grammar/GDk9-Grammar-Spec-v1.0.0.md`.
EOF

cat > site/standards/ime-execution-model.md <<'EOF'
# IME Execution Model

The GDk9 IME kernel maintains a grammar-declared state, a volatile composition
buffer, and optional mode context. For each input event, it reads the event
class, looks up the current transition, applies the transition action, then
moves to the next state.

Only `reduce_and_emit` may emit output. `ABORT` clears volatile state and
returns to `IDLE`; it is also the recovery path from `ERROR`.

`MODE_SHIFT` from `IDLE` enters `ERROR`; mode context must come from an existing
composition. Literal escape is handled before event dispatch.

Normative source: `standards/ime/GDk9-IME-Model-v1.0.0.md`.
EOF

cat > site/standards/reduction-contract.md <<'EOF'
# Reduction Contract

Reduction is a pure function:

```text
kappa(buffer, mode) -> output
```

For KeySuite v1.0.0, the reducer is implemented by
`reference/keysuite/src/reducer.py`. The canonical bind marker is `.`, and the
first bind marker is the implication boundary:

```text
left . right -> left→right
```

Additional bind markers after the first are right-side content. Escaped literal
bind characters are content and do not form implication boundaries.

Normative source: `standards/reduction/GDk9-Reduction-Contract-v1.0.0.md`.
EOF

cat > site/standards/conformance-specification.md <<'EOF'
# Conformance Specification

GDk9 v1.0.0 conformance requires tests that prove grammar version identity,
explicit symbol jurisdiction, deterministic output, commit-only emission,
rollback behavior, abort recovery, invalid-event error behavior, pure reduction,
transition-table validation, strict grammar schema validation, CLI diagnostics,
trace output, JSON output, and literal escape behavior.

Repository evidence commands:

```bash
pytest
make release-check
keysuite validate
```

Normative source: `standards/conformance/GDk9-Conformance-Spec-v1.0.0.md`.
EOF

cat > site/architecture/runtime-architecture.md <<'EOF'
# Runtime Architecture

KeySuite is a small reference runtime with four runtime layers:

- `grammar_loader.py` loads and unwraps `grammar/gdk9-v1.0.0.yaml`.
- `transitions.py` validates and compiles the transition table.
- `ime_runtime.py` executes the finite state machine and owns volatile buffer state.
- `reducer.py` performs pure reduction at commit.

The CLI entry point is `reference/keysuite/src/main.py`. It tokenizes input,
feeds events into the runtime, and prints only committed output.

The architecture keeps the grammar as the runtime control surface. Standards,
tests, and runtime behavior stay synchronized through the versioned grammar
artifact.
EOF

cat > site/architecture/release-artifacts.md <<'EOF'
# Release Artifacts

GDk9 v1.0.0 and KeySuite v1.0.0 publish a synchronized release tree:

- `standards/` contains the normative standard documents.
- `grammar/gdk9-v1.0.0.yaml` is the machine-readable control artifact.
- `reference/` contains the KeySuite runtime.
- `tests/` contains conformance and regression coverage.
- `docs/` contains release evidence and version metadata.
- `SECURITY.md` defines vulnerability reporting policy.
- `CHANGELOG.md` records release history.
- `site/` contains public documentation pages.
- `version/current.txt` records the current artifact set.

Version changes must update the standards, grammar metadata, tests, public docs,
release docs, `VERSION`, and `version/current.txt` together.
EOF

cat > site/architecture/threat-model.md <<'EOF'
# Threat Model

KeySuite is a local deterministic runtime. The primary trust boundary is
untrusted input entering the CLI or a host integration.

Primary controls:

- strict grammar schema validation
- explicit transition compiler checks
- non-zero CLI exit on unrecovered `ERROR`
- literal escape handling for syntax/control input
- CI, CodeQL, dependency audit, and static security scanning workflows
- release checksum and provenance procedure

Reference source: `docs/THREAT_MODEL.md`.
EOF

cat > site/reference/keysuite.md <<'EOF'
# KeySuite

KeySuite is the reference runtime implementing GDk9.

It loads `grammar/gdk9-v1.0.0.yaml`, validates grammar schema and
grammar-controlled transitions, processes finite-state events, and emits output
only at commit.

Primary source files:

- `reference/keysuite/src/grammar_loader.py`
- `reference/keysuite/src/transitions.py`
- `reference/keysuite/src/ime_runtime.py`
- `reference/keysuite/src/reducer.py`
- `reference/keysuite/src/main.py`
EOF

cat > site/reference/cli.md <<'EOF'
# CLI Usage

Run the reference runtime after installing the package:

```bash
keysuite "C C . 3 3"
```

Expected output:

```text
CC→33
```

The same example is available through `make run`.

Additional commands:

```bash
keysuite C C . 3 3
keysuite --tokens "C C . 3 3"
keysuite --trace C C . 3 3
keysuite --json @
keysuite validate
keysuite inspect-grammar
keysuite reduce A . B
```

Invalid unrecovered input exits non-zero. `_` escapes the next token as literal
content, so `keysuite A _ . B` emits `A.B`.
EOF

cat > site/reference/runtime-conformance.md <<'EOF'
# Runtime Conformance

KeySuite v1.0.0 implements GDk9 v1.0.0 by loading
`grammar/gdk9-v1.0.0.yaml`.

Evidence commands:

```bash
pytest
make release-check
keysuite validate
```

Covered behavior includes basic implication reduction, repeatability, rollback,
abort, mode shift, timeout commit, invalid-event error state, grammar loading,
token classification, required state validation, YAML transition control,
unknown action rejection, undeclared jurisdiction rejection, strict schema
validation, CLI diagnostics, trace output, JSON output, literal escape behavior,
and no output before commit.
EOF

cat > site/reference/conformance-vectors.md <<'EOF'
# Conformance Vectors

| Tokens | Expected Output | Notes |
| --- | --- | --- |
| `C C . 3 3` | `CC→33` | basic implication |
| `A B` | `AB` | plain composition |
| `A B BACKSPACE` | `A` | rollback before commit |
| `A ESC` | none | abort clears volatile state |
| `X : A B` | `X(AB)` | mode-scoped reduction |
| `A . B . C` | `A→B.C` | first bind marker is the implication boundary |
| `A _ . B` | `A.B` | escaped bind marker is literal content |
| `@` | error | invalid token enters unrecovered `ERROR` |

Reference source: `docs/CONFORMANCE_VECTORS.md`.
EOF

cat > site/governance/standards-process.md <<'EOF'
# Standards Process

The GDk9 Core Standard, Grammar Specification, IME Model, Reduction Contract,
and Conformance Specification are governed as versioned standards artifacts.

Standards behavior changes require a GDk9 Enhancement Proposal in `proposals/`.
A conforming change must update the affected standards document, the grammar
when behavior changes, site documentation, release documentation, and
conformance tests.

Implementations must not represent altered behavior or altered standards as
GDk9-compliant unless the change follows the standards governance path.
EOF

cat > site/governance/contributing.md <<'EOF'
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
EOF

echo "Docs created."
