from __future__ import annotations

from importlib import metadata


def _discover_version() -> str:
    try:
        return metadata.version("keysuite")
    except metadata.PackageNotFoundError:
        return "1.1.0.dev3"


__version__ = _discover_version()
__grammar_compatibility__ = "1.0.0"
