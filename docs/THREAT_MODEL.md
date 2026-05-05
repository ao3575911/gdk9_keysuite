# Threat Model

## Scope

KeySuite is a local reference runtime for GDk9 v1.0.0. The primary trust boundary is untrusted input entering the CLI or a host integration that calls the runtime.

## Assets

- grammar control file integrity
- deterministic runtime behavior
- commit-only output guarantee
- release artifact integrity
- repository and package metadata

## Non-Goals

KeySuite does not provide credential storage beyond configured API keys, transport encryption, or public remote-service exposure. The API and websocket surfaces are intentionally local-first and rely on deployment controls for TLS and external network policy.

## Threats

| Threat | Control |
| --- | --- |
| Malformed grammar changes runtime semantics | Strict schema validation and transition compiler rejection |
| Invalid user tokens fail silently | CLI diagnostics and non-zero unrecovered error exits |
| Syntax/control tokens need literal input | `_` literal escape handling |
| Dependency compromise | Dependabot, bounded dependency ranges, `pip-audit` workflow |
| Static security regression | CodeQL and Bandit workflows |
| Release artifact tampering | Release checksum and provenance procedure |
| API key abuse or missing authorization | Header-based API key gate with optional configured keys |
| Session or websocket overload | Per-session and per-connection rate limiting, bounded payloads, cleanup worker |
| Silent state leakage across clients | Per-session `IMEKernel`, history, macro context, and connection isolation |

## Review Triggers

Run a security review when changing grammar loading, CLI parsing, transition actions, packaging, release workflows, or any integration that processes untrusted input outside the local CLI.
