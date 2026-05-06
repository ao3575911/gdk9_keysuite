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


def _coerce_list_of_strings(value: Any, name: str) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return list(value)
    if isinstance(value, str):
        tokens = [item.strip() for item in value.split(",") if item.strip()]
        return tokens
    raise ConfigurationError(f"{name} must be a list of strings")


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
    max_sessions: int = 32
    session_idle_ttl_seconds: int = 900
    session_cleanup_interval_seconds: int = 60
    max_messages_per_second: int = 20
    max_payload_size: int = 16_384
    connection_timeout_seconds: int = 30
    heartbeat_interval_seconds: int = 15
    max_requests_per_window: int = 120
    rate_limit_window_seconds: int = 60
    max_queue_size: int = 256
    queue_policy: str = "reject"
    enable_metrics: bool = True
    enable_tracing: bool = False
    json_logging: bool = True
    api_key_header: str = "X-API-Key"
    api_keys: list[str] = field(default_factory=list)
    persistence_backend: str = "memory"
    persistence_url: str | None = None
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
            "max_sessions": toml_data.get("max_sessions", 32),
            "session_idle_ttl_seconds": toml_data.get("session_idle_ttl_seconds", 900),
            "session_cleanup_interval_seconds": toml_data.get("session_cleanup_interval_seconds", 60),
            "max_messages_per_second": toml_data.get("max_messages_per_second", 20),
            "max_payload_size": toml_data.get("max_payload_size", 16_384),
            "connection_timeout_seconds": toml_data.get("connection_timeout_seconds", 30),
            "heartbeat_interval_seconds": toml_data.get("heartbeat_interval_seconds", 15),
            "max_requests_per_window": toml_data.get("max_requests_per_window", 120),
            "rate_limit_window_seconds": toml_data.get("rate_limit_window_seconds", 60),
            "max_queue_size": toml_data.get("max_queue_size", 256),
            "queue_policy": toml_data.get("queue_policy", "reject"),
            "enable_metrics": toml_data.get("enable_metrics", True),
            "enable_tracing": toml_data.get("enable_tracing", False),
            "json_logging": toml_data.get("json_logging", True),
            "api_key_header": toml_data.get("api_key_header", "X-API-Key"),
            "api_keys": _coerce_list_of_strings(toml_data.get("api_keys"), "api_keys"),
            "persistence_backend": toml_data.get("persistence_backend", "memory"),
            "persistence_url": toml_data.get("persistence_url"),
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
            "max_sessions",
            "session_idle_ttl_seconds",
            "session_cleanup_interval_seconds",
            "max_messages_per_second",
            "max_payload_size",
            "connection_timeout_seconds",
            "heartbeat_interval_seconds",
            "max_requests_per_window",
            "rate_limit_window_seconds",
            "max_queue_size",
            "queue_policy",
            "enable_metrics",
            "enable_tracing",
            "json_logging",
            "api_key_header",
            "api_keys",
            "persistence_backend",
            "persistence_url",
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
            "KEYSUITE_MAX_SESSIONS": "max_sessions",
            "KEYSUITE_SESSION_IDLE_TTL_SECONDS": "session_idle_ttl_seconds",
            "KEYSUITE_SESSION_CLEANUP_INTERVAL_SECONDS": "session_cleanup_interval_seconds",
            "KEYSUITE_MAX_MESSAGES_PER_SECOND": "max_messages_per_second",
            "KEYSUITE_MAX_PAYLOAD_SIZE": "max_payload_size",
            "KEYSUITE_CONNECTION_TIMEOUT_SECONDS": "connection_timeout_seconds",
            "KEYSUITE_HEARTBEAT_INTERVAL_SECONDS": "heartbeat_interval_seconds",
            "KEYSUITE_MAX_REQUESTS_PER_WINDOW": "max_requests_per_window",
            "KEYSUITE_RATE_LIMIT_WINDOW_SECONDS": "rate_limit_window_seconds",
            "KEYSUITE_MAX_QUEUE_SIZE": "max_queue_size",
            "KEYSUITE_QUEUE_POLICY": "queue_policy",
            "KEYSUITE_ENABLE_METRICS": "enable_metrics",
            "KEYSUITE_ENABLE_TRACING": "enable_tracing",
            "KEYSUITE_JSON_LOGGING": "json_logging",
            "KEYSUITE_API_KEY_HEADER": "api_key_header",
            "KEYSUITE_API_KEYS": "api_keys",
            "KEYSUITE_PERSISTENCE_BACKEND": "persistence_backend",
            "KEYSUITE_PERSISTENCE_URL": "persistence_url",
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
            if "api_keys" in explicit:
                explicit["api_keys"] = _coerce_list_of_strings(explicit["api_keys"], "api_keys")
            values.update(explicit)

        try:
            values["max_buffer_size"] = _coerce_int(values["max_buffer_size"], "max_buffer_size")
            values["max_token_count"] = _coerce_int(values["max_token_count"], "max_token_count")
            values["max_macro_expansion_depth"] = _coerce_int(
                values["max_macro_expansion_depth"], "max_macro_expansion_depth"
            )
            values["history_limit"] = _coerce_int(values["history_limit"], "history_limit")
            values["debug_level"] = _coerce_int(values["debug_level"], "debug_level")
            values["max_sessions"] = _coerce_int(values["max_sessions"], "max_sessions")
            values["session_idle_ttl_seconds"] = _coerce_int(
                values["session_idle_ttl_seconds"], "session_idle_ttl_seconds"
            )
            values["session_cleanup_interval_seconds"] = _coerce_int(
                values["session_cleanup_interval_seconds"], "session_cleanup_interval_seconds"
            )
            values["max_messages_per_second"] = _coerce_int(
                values["max_messages_per_second"], "max_messages_per_second"
            )
            values["max_payload_size"] = _coerce_int(values["max_payload_size"], "max_payload_size")
            values["connection_timeout_seconds"] = _coerce_int(
                values["connection_timeout_seconds"], "connection_timeout_seconds"
            )
            values["heartbeat_interval_seconds"] = _coerce_int(
                values["heartbeat_interval_seconds"], "heartbeat_interval_seconds"
            )
            values["max_requests_per_window"] = _coerce_int(
                values["max_requests_per_window"], "max_requests_per_window"
            )
            values["rate_limit_window_seconds"] = _coerce_int(
                values["rate_limit_window_seconds"], "rate_limit_window_seconds"
            )
            values["max_queue_size"] = _coerce_int(values["max_queue_size"], "max_queue_size")
        except ConfigurationError:
            raise

        if values["version_policy"] not in {"strict", "latest-compatible"}:
            raise ConfigurationError("version_policy must be 'strict' or 'latest-compatible'")
        if values["queue_policy"] not in {"reject", "drop"}:
            raise ConfigurationError("queue_policy must be 'reject' or 'drop'")
        if values["persistence_backend"] not in {"memory", "redis"}:
            raise ConfigurationError("persistence_backend must be 'memory' or 'redis'")
        values["enable_metrics"] = _coerce_bool(values["enable_metrics"], "enable_metrics")
        values["enable_tracing"] = _coerce_bool(values["enable_tracing"], "enable_tracing")
        values["json_logging"] = _coerce_bool(values["json_logging"], "json_logging")

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
        values["api_keys"] = sorted(set(_coerce_list_of_strings(values["api_keys"], "api_keys")))

        return cls(**values)
