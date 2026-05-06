from __future__ import annotations

from importlib import resources
from pathlib import Path

import yaml

from .grammar import Grammar
from .schema import validate_grammar
from .version import __version__

DEFAULT_GRAMMAR_FILE = "gdk9-v1.0.0.yaml"


def _unwrap_grammar(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError("GDk9 grammar must be a mapping")
    return data.get("gdk9_grammar", data)


def _default_resource_path() -> tuple[str, str]:
    return ("keysuite.data", DEFAULT_GRAMMAR_FILE)


def _load_from_resource() -> tuple[dict, str]:
    package, filename = _default_resource_path()
    data = resources.files(package).joinpath(filename).read_text(encoding="utf-8")
    return yaml.safe_load(data), f"{package}/{filename}"


def _load_from_path(path: Path) -> tuple[dict, str]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle), str(path)


def load_grammar(
    path: str | Path | None = None,
    *,
    version_policy: str = "latest-compatible",
    runtime_version: str = __version__,
) -> Grammar:
    if path is None:
        raw, source = _load_from_resource()
    else:
        candidate = Path(path)
        if candidate.exists():
            raw, source = _load_from_path(candidate)
        else:
            raise FileNotFoundError(f"Grammar file not found: {candidate}")

    grammar = validate_grammar(_unwrap_grammar(raw), runtime_version=runtime_version, version_policy=version_policy)
    return Grammar(grammar, source_path=source, version_policy=version_policy)


def grammar_summary(grammar: Grammar | dict) -> dict:
    return {
        "artifact": grammar.get("artifact"),
        "version": grammar.get("version"),
        "standard_version": grammar.get("standard_version"),
        "keysuite_runtime_version": grammar.get("keysuite_runtime_version"),
        "states": list(grammar.get("states", [])),
        "source_path": getattr(grammar, "source_path", None),
        "version_policy": getattr(grammar, "version_policy", None),
    }
