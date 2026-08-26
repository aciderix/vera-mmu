"""Declarative description of the historical ARET V1 runtime layout."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AretLegacyRuntimeLayout:
    """Legacy names only; resolving paths and environment remains outside this pack contract."""

    environment_override: str
    default_runtime_dir: str
    sqlite_filename: str
    artifacts_dirname: str
    exports_dirname: str

    @property
    def relative_members(self) -> tuple[str, str, str]:
        return (
            f"{self.default_runtime_dir}/{self.sqlite_filename}",
            f"{self.default_runtime_dir}/{self.artifacts_dirname}",
            f"{self.default_runtime_dir}/{self.exports_dirname}",
        )


def legacy_runtime_layout() -> AretLegacyRuntimeLayout:
    """Return the immutable ARET V1 layout manifest without resolving or creating anything."""
    return AretLegacyRuntimeLayout(
        environment_override="ARET_MEMORY_DIR",
        default_runtime_dir=".aret-memory",
        sqlite_filename="aret_memory.sqlite",
        artifacts_dirname="artifacts",
        exports_dirname="exports",
    )
