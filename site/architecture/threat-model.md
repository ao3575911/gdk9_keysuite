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
