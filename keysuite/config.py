from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Mapping

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib  # type: ignore[no-redef]

from .errors import ConfigurationError

DEFAULT_GRAMMAR_FILE = "grammar/gdk9-v1.0.0.yaml"


def _coerce_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or value is None:
        raise ConfigurationError(f"{name} must be an integer")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return int(value)
        except ValueError as exc:
            raise ConfigurationError(f"{name} must be an integer") from exc
    raise ConfigurationError(f"{name} must be an integer")


def _coerce_bool(value: Any, name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in {0, 1}:
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    raise ConfigurationError(f"{name} must be a boolean-like value")


def _load_toml(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:  # type: ignore[attr-defined]
        raise ConfigurationError(f"Unable to load configuration file {path}: {exc}") from exc


def _flatten_toml(data: Mapping[str, Any]) -> dict[str, Any]:
    runtime = data.get("runtime")
    if isinstance(runtime, Mapping):
        merged = dict(data)
        merged.update(runtime)
        merged.pop("runtime", None)
        return merged
    return dict(data)


@dataclass(frozen=True)
class RuntimeConfig:
    grammar_path: str | None = None
    version_policy: str = "latest-compatible"
    max_buffer_size: int = 256
    max_token_count: int = 4096
    max_macro_expansion_depth: int = 16
    history_limit: int = 128
    debug_level: int = 0
    macros: dict[str, list[str]] = field(default_factory=dict)

    def replace(self, **changes: Any) -> "RuntimeConfig":
        return replace(self, **changes)

    @classmethod
    def from_sources(
        cls,
        explicit: Mapping[str, Any] | None = None,
        *,
        env: Mapping[str, str] | None = None,
        toml_path: str | Path | None = None,
    ) -> "RuntimeConfig":
        env = env or {}
        path = Path(toml_path) if toml_path is not None else Path.cwd() / "keysuite.toml"
        toml_data = _flatten_toml(_load_toml(path))

        values: dict[str, Any] = {
            "grammar_path": toml_data.get("grammar_path") or toml_data.get("grammar") or DEFAULT_GRAMMAR_FILE,
            "version_policy": toml_data.get("version_policy", "latest-compatible"),
            "max_buffer_size": toml_data.get("max_buffer_size", 256),
            "max_token_count": toml_data.get("max_token_count", 4096),
            "max_macro_expansion_depth": toml_data.get(
                "max_macro_expansion_depth", 16
            ),
            "history_limit": toml_data.get("history_limit", 128),
            "debug_level": toml_data.get("debug_level", toml_data.get("debug", 0)),
            "macros": dict(toml_data.get("macros", {})),
        }

        allowed_keys = {
            "grammar_path",
            "grammar",
            "version_policy",
            "max_buffer_size",
            "max_token_count",
            "max_macro_expansion_depth",
            "history_limit",
            "debug_level",
            "debug",
            "macros",
        }
        if explicit:
            unknown_explicit = set(explicit) - allowed_keys
            if unknown_explicit:
                raise ConfigurationError(
                    f"Unknown configuration keys: {', '.join(sorted(unknown_explicit))}"
                )

        env_map = {
            "KEYSUITE_GRAMMAR": "grammar_path",
            "KEYSUITE_MAX_BUFFER_SIZE": "max_buffer_size",
            "KEYSUITE_MAX_TOKEN_COUNT": "max_token_count",
            "KEYSUITE_DEBUG": "debug_level",
            "KEYSUITE_VERSION_POLICY": "version_policy",
            "KEYSUITE_MAX_MACRO_EXPANSION_DEPTH": "max_macro_expansion_depth",
            "KEYSUITE_HISTORY_LIMIT": "history_limit",
        }
        for env_key, field_name in env_map.items():
            if env_key in env:
                values[field_name] = env[env_key]

        if explicit:
            explicit = dict(explicit)
            if "grammar" in explicit and "grammar_path" not in explicit:
                explicit["grammar_path"] = explicit.pop("grammar")
            if "debug" in explicit and "debug_level" not in explicit:
                explicit["debug_level"] = explicit.pop("debug")
            values.update(explicit)

        try:
            values["max_buffer_size"] = _coerce_int(values["max_buffer_size"], "max_buffer_size")
            values["max_token_count"] = _coerce_int(values["max_token_count"], "max_token_count")
            values["max_macro_expansion_depth"] = _coerce_int(
                values["max_macro_expansion_depth"], "max_macro_expansion_depth"
            )
            values["history_limit"] = _coerce_int(values["history_limit"], "history_limit")
            values["debug_level"] = _coerce_int(values["debug_level"], "debug_level")
        except ConfigurationError:
            raise

        if values["version_policy"] not in {"strict", "latest-compatible"}:
            raise ConfigurationError("version_policy must be 'strict' or 'latest-compatible'")

        macros = values.get("macros") or {}
        if not isinstance(macros, Mapping):
            raise ConfigurationError("macros must be a mapping of name -> token list")
        normalized_macros: dict[str, list[str]] = {}
        for name, token_list in macros.items():
            if not isinstance(name, str) or not name:
                raise ConfigurationError("macro names must be non-empty strings")
            if not isinstance(token_list, list) or not all(isinstance(token, str) for token in token_list):
                raise ConfigurationError(f"macro {name!r} must be a list of strings")
            normalized_macros[name] = list(token_list)
        values["macros"] = normalized_macros

        return cls(**values)
