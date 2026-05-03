<img src="../../branding/logos/gdk9-logo.svg" width="180"/>

# GDk9 Core Standard v1.0.0

## Status

Normative for GDk9 v1.0.0.

## Purpose

GDk9 defines deterministic symbolic implication infrastructure. It specifies how symbolic input is classified, buffered, committed, and reduced without prediction, hidden reinterpretation, or probabilistic mutation.

## Core Requirements

An implementation claiming GDk9 v1.0.0 conformance MUST:

- classify every input event under explicit symbol jurisdiction
- execute through a finite state machine
- keep composition state volatile until commit
- emit output only at a commit boundary
- reduce buffered symbols through a pure function
- recover from abort without emitting output
- produce identical output for identical input sequences and grammar versions

## Non-Goals

GDk9 is not an autocorrect engine, macro system, editor plugin, predictive text model, or keyboard layout. Implementations MAY expose GDk9 through those environments, but they MUST NOT change GDk9 semantics to fit those environments.

## Versioned Artifacts

The v1.0.0 standard stack consists of:

- `standards/core/GDk9-Core-Standard-v1.0.0.md`
- `standards/grammar/GDk9-Grammar-Spec-v1.0.0.md`
- `standards/ime/GDk9-IME-Model-v1.0.0.md`
- `standards/reduction/GDk9-Reduction-Contract-v1.0.0.md`
- `standards/conformance/GDk9-Conformance-Spec-v1.0.0.md`
- `grammar/gdk9-v1.0.0.yaml`

## Canonical Runtime Rule

The machine-readable grammar controls runtime transition behavior. A runtime MAY optimize loading and execution, but the observable transition behavior MUST match the versioned grammar artifact it claims to implement.
