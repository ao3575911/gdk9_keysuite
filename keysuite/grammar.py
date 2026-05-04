from __future__ import annotations

from pathlib import Path

from .version import __version__


class Grammar(dict):
    def __init__(
        self,
        mapping: dict | None = None,
        *,
        source_path: str | Path | None = None,
        version_policy: str = "latest-compatible",
    ) -> None:
        super().__init__(mapping or {})
        self.source_path = str(source_path) if source_path is not None else None
        self.version_policy = version_policy

    @property
    def metadata(self) -> dict:
        return {
            "artifact": self.get("artifact"),
            "version": self.get("version"),
            "standard_version": self.get("standard_version"),
            "keysuite_runtime_version": self.get("keysuite_runtime_version"),
            "source_path": self.source_path,
            "version_policy": self.version_policy,
            "runtime_version": __version__,
        }

    def describe(self) -> dict:
        return dict(self.metadata)
