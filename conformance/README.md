# GDk9 Conformance Vectors

This directory contains canonical GDk9 conformance vectors.

The vectors are implementation-independent. Any GDk9 runtime, regardless of language, should be able to process these JSONL files and compare its behavior against the expected result.

## Format

Each line is a standalone JSON object.

```json
{
  "id": "implication.basic.001",
  "tokens": ["C", "C", ".", "3", "3", "SPACE"],
  "output": "CC→33",
  "final_state": "IDLE",
  "exit_code": 0
}
