from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION_MANIFEST = ROOT / "version" / "current.txt"
HASHLIB_COMMAND = [
    sys.executable,
    "-m",
    "hashlib",
    "sha256",
    "grammar/gdk9-v1.0.0.yaml",
    "VERSION",
    "version/current.txt",
]


def test_version_manifest_is_not_a_checksum_artifact() -> None:
    manifest = VERSION_MANIFEST.read_text(encoding="utf-8")

    assert "sha256" not in manifest.lower()
    assert not re.search(r"\b[0-9a-fA-F]{64}\b", manifest)


def test_hashlib_module_command_does_not_mutate_version_manifest() -> None:
    before = VERSION_MANIFEST.read_bytes()

    subprocess.run(HASHLIB_COMMAND, cwd=ROOT, check=True, capture_output=True, text=True)

    assert VERSION_MANIFEST.read_bytes() == before


def test_release_provenance_documents_stdout_checksum_command() -> None:
    provenance = (ROOT / "docs" / "RELEASE_PROVENANCE.md").read_text(encoding="utf-8")

    assert "sha256sum grammar/gdk9-v1.0.0.yaml VERSION version/current.txt" in provenance
    assert "python -m hashlib sha256" not in provenance
