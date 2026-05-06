# GDk9 Conformance Vectors

This directory contains canonical GDk9 conformance vectors.

The vectors are implementation-independent. Any GDk9 runtime, regardless of language, should be able to process these JSONL files and compare its behavior against the expected result.

The hardened KeySuite runtime still uses these vectors as the canonical behavior
check. Session isolation, event publication, and websocket transport do not
change the vector outputs. The suite covers both `SPACE` and `DONE` as
grammar-declared commit events.

## Format

Each line is a standalone JSON object.

## Release Notes

- Keep the vectors in sync with `standards/` and `grammar/`.
- Do not encode transport-specific metadata in the vectors.
- Re-run the conformance suite after version bumps and runtime hardening changes.

```json
{
  "id": "implication.basic.001",
  "tokens": ["C", "C", ".", "3", "3", "SPACE"],
  "output": "CC→33",
  "final_state": "IDLE",
  "exit_code": 0
}
