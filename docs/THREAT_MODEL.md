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

KeySuite does not provide authentication, authorization, networking, credential storage, encryption, or remote service access.

## Threats

| Threat | Control |
| --- | --- |
| Malformed grammar changes runtime semantics | Strict schema validation and transition compiler rejection |
| Invalid user tokens fail silently | CLI diagnostics and non-zero unrecovered error exits |
| Syntax/control tokens need literal input | `_` literal escape handling |
| Dependency compromise | Dependabot, bounded dependency ranges, `pip-audit` workflow |
| Static security regression | CodeQL and Bandit workflows |
| Release artifact tampering | Release checksum and provenance procedure |

## Review Triggers

Run a security review when changing grammar loading, CLI parsing, transition actions, packaging, release workflows, or any integration that processes untrusted input outside the local CLI.
