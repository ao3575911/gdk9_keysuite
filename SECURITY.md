# Security Policy

## Supported Versions

| Version | Supported |
| --- | --- |
| 1.0.x | Yes |

## Reporting a Vulnerability

Report suspected vulnerabilities privately through GitHub private vulnerability reporting for this repository. If that is unavailable, contact the maintainer listed on the repository profile and request a private disclosure channel.

Include:

- affected version
- reproduction steps
- expected and actual behavior
- security impact
- suggested remediation, if known

Do not publicly disclose the issue until a fix or advisory has been prepared.

## Security Posture

KeySuite is a local deterministic runtime. It does not intentionally perform network calls, shell execution, credential handling, dynamic imports, or filesystem writes during normal runtime execution.

Security-sensitive changes include grammar loading, transition validation, CLI parsing, packaging, release workflows, and any future integration that accepts untrusted input from another process.
