# GDk9 and KeySuite Documentation

This directory contains release-oriented documentation that complements the standards in `standards/` and the site pages in `site/`.

The hardened runtime release adds focused documentation for:

- session isolation and event-driven execution
- websocket lifecycle and backpressure handling
- API authentication, rate limiting, and validation
- scaling and persistence boundaries
- threat-model updates for the new transport and governance layers

## Documents

- `api.md`: Python import surface and REST API quickstart
- `configuration.md`: TOML and environment variable precedence
- `macros.md`: macro registration and expansion rules
- `websocket.md`: streaming session message and event protocol
- `architecture.md`: session lifecycle, event bus, and websocket flow
- `scaling.md`: stateful vs stateless deployment boundaries and horizontal scaling
- `security.md`: API keys, rate limiting, and input validation
- `GITHUB_READY.md`: final push checklist
- `RUNTIME_CONFORMANCE.md`: runtime and test evidence
- `VERSION_MATRIX.md`: version synchronization table
- `CONFORMANCE_VECTORS.md`: canonical runtime vectors
- `RELEASE_PROVENANCE.md`: checksum, publication, and SBOM guidance
- `THREAT_MODEL.md`: local runtime threat model

Use `site/` for public documentation pages and `standards/` for normative specifications.

Use `requirements.lock` when reproducing release checks exactly.
