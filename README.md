# GDk9 - Symbolic Implication Infrastructure

GDk9 is a deterministic symbolic implication architecture. KeySuite is the reference runtime implementing the GDk9 IME model.

The goal is narrow and auditable: symbols enter an explicit jurisdiction, move through a finite state machine, and emit output only at an atomic commit boundary after pure reduction.

## Current Release

- GDk9 Standard: 1.0.0
- KeySuite Runtime: 1.0.0
- Grammar: `grammar/gdk9-v1.0.0.yaml` version 1.0.0
- Package: `keysuite` version 1.0.0

## Repository Structure

```text
standards/      Normative GDk9 specifications
grammar/        Machine-readable runtime grammar and transition control
reference/      KeySuite reference runtime
tests/          Conformance, determinism, and runtime regression tests
site/           Human-readable documentation site content
docs/           Release, implementation, and GitHub readiness docs
proposals/      GDk9 Enhancement Proposals
branding/       Logos and identity assets
scripts/        Release and repository helper scripts
version/        Machine-readable current version manifest
```

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
keysuite "C C . 3 3"
```

For release reproduction, install the locked dependency set with `pip install -r requirements.lock`.

Expected output:

```text
CC→33
```

The CLI also accepts token arrays and runtime inspection commands:

```bash
keysuite C C . 3 3
keysuite --tokens "C C . 3 3"
keysuite --trace C C . 3 3
keysuite --json @
keysuite --grammar grammar/gdk9-v1.0.0.yaml validate
keysuite inspect-grammar
```

Invalid unrecovered input exits non-zero and reports a diagnostic. The grammar-declared literal escape marker `_` treats the following token as literal content, so `keysuite A _ . B` emits `A.B`.

## Test and Release Check

```bash
pytest
make release-check
```

The conformance suite verifies deterministic repeatability, commit-only output, rollback, abort recovery, mode shift behavior, grammar loading, token classification, and YAML-controlled transition validation.

## Grammar as Control Surface

`grammar/gdk9-v1.0.0.yaml` is the canonical machine-readable control file for GDk9 v1.0.0 behavior. It defines:

- version and artifact metadata
- symbol classes and symbol jurisdiction
- event classes
- allowed runtime actions
- state list
- transition table
- conformance flags

KeySuite reads this file to generate the runtime transition table. The runtime rejects transition entries that reference unknown states, unknown actions, or undeclared symbol jurisdiction.

## Runtime Contract

KeySuite contains four small runtime layers:

- `grammar_loader.py` loads, unwraps, and schema-validates the GDk9 grammar.
- `transitions.py` validates and compiles the transition table.
- `ime_runtime.py` executes the finite state machine and owns volatile buffer state.
- `reducer.py` performs pure reduction at commit.

`keysuite validate` reports the loaded grammar version and SHA-256 hash for release provenance and debugging.

No output is emitted before commit. Invalid events move the kernel to `ERROR`; `ABORT` clears volatile state and returns to `IDLE`.

## Documentation

- Security policy: `SECURITY.md`
- Changelog: `CHANGELOG.md`
- Site index: `site/index.md`
- Architecture docs: `site/architecture/`
- Governance docs: `site/governance/`
- Standards docs: `standards/`
- Release docs: `docs/`
- Threat model: `docs/THREAT_MODEL.md`
- Release provenance: `docs/RELEASE_PROVENANCE.md`
- Runtime reference: `reference/README.md`
- Script reference: `scripts/README.md`

## Standards

GDk9 v1.0.0 is split into five normative documents:

- Core Standard
- Grammar Specification
- IME Execution Model
- Reduction Contract
- Conformance Specification

Standards changes require a GDk9 Enhancement Proposal in `proposals/`.

## GitHub Push Preparation

Run the release gate first:

```bash
make release-check
make clean
git status --short
```

Then push manually or use:

```bash
./scripts/push_github.sh git@github.com:USER/gdk9_keysuite.git
```

The script runs compile and test checks before committing and pushing.

## License

The KeySuite software is MIT licensed. GDk9 standards governance is documented in `LICENSE`, `CONTRIBUTING.md`, `CONTRIBUTORS.md`, and `site/governance/`.
