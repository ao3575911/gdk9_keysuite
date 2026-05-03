# Overview

GDk9 defines deterministic symbolic input and implication. Symbols enter an
explicit jurisdiction, move through a finite state machine, and emit output only
at an atomic commit boundary after pure reduction.

KeySuite is the reference runtime for GDk9 v1.0.0. It loads the versioned
grammar, validates transitions, executes the IME state machine, and uses a pure
reducer to produce committed output.
