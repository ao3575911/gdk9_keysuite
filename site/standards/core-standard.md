# Core Standard

GDk9 requires deterministic execution, explicit symbol classes, and pure reduction.

An implementation claiming GDk9 v1.0.0 conformance must classify every input
event under explicit symbol jurisdiction, execute through a finite state
machine, keep composition state volatile until commit, emit only at commit, and
produce identical output for identical input sequences and grammar versions.

Normative source: `standards/core/GDk9-Core-Standard-v1.0.0.md`.
