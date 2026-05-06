# Release Provenance

This repository treats `grammar/gdk9-v1.0.0.yaml`, `standards/`, `keysuite/`, `reference/`, and `tests/` as the release-critical artifact set.

## Local Evidence

Run before tagging or publishing:

```bash
pip install -r requirements.lock
make test
make conformance
make release-check
keysuite validate
python -m compileall -q keysuite reference tests
```

For the `1.1.0.dev3` line, retain release-check output that shows the canonical
`CC→33` smoke result, `32/32` conformance vectors, and the expected invalid-token
failure from `scripts/release_acceptance.sh`.

## Artifact Hashes

Generate release checksums with:

```bash
sha256sum grammar/gdk9-v1.0.0.yaml VERSION version/current.txt
```

This command prints checksum records to stdout. Attach that output to release
notes or a separate checksum artifact; do not write checksum output into
`version/current.txt`, which is the release version manifest.

## Registry and Signing

For published package artifacts:

- build from a clean checkout
- publish through a CI workflow, not a local workstation
- retain workflow logs for provenance
- attach SHA-256 checksums for source and wheel artifacts
- prefer Sigstore/GitHub artifact attestations when publishing to PyPI or GitHub Releases
- refresh `requirements.lock` from a trusted environment when dependency versions change

## SBOM

Generate an SBOM during release once a package registry target is selected. CycloneDX and SPDX are acceptable formats. The SBOM should include runtime dependencies and build tooling used to produce release artifacts.
