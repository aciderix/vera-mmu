"""Constrained local runtime location for the VERA-MMU Core (M1, C02)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Any, Mapping

from .workspace import Workspace, WorkspaceError, resolve_workspace


class RuntimeLocatorError(WorkspaceError):
    """Raised when a runtime child escapes the configured local runtime directory."""


@dataclass(frozen=True)
class RuntimeLocator:
    """Validated local locations for future memory, SQLite, and artifact layers."""

    project_root: Path
    runtime_dir: Path
    sqlite_path: Path
    artifacts_dir: Path

    def as_dict(self) -> dict[str, str]:
        return {
            "project_root": str(self.project_root),
            "runtime_dir": str(self.runtime_dir),
            "sqlite_path": str(self.sqlite_path),
            "artifacts_dir": str(self.artifacts_dir),
        }

    @classmethod
    def from_profile(cls, profile: Mapping[str, Any], profile_path: str | Path) -> "RuntimeLocator":
        """Resolve and confine all runtime paths using one validated Project Profile."""
        return cls.from_workspace(profile, resolve_workspace(profile, profile_path))

    @classmethod
    def from_workspace(cls, profile: Mapping[str, Any], workspace: Workspace) -> "RuntimeLocator":
        """Derive runtime children without creating them or opening a storage backend."""
        storage = profile.get("storage")
        if not isinstance(storage, Mapping):
            raise RuntimeLocatorError("Le profile ne contient pas de storage valide.")
        sqlite = cls._inside_runtime(workspace.runtime_dir, storage.get("sqlite_file"), "storage.sqlite_file")
        artifacts = cls._inside_runtime(workspace.runtime_dir, storage.get("artifacts_dir"), "storage.artifacts_dir")
        if sqlite == workspace.runtime_dir or artifacts == workspace.runtime_dir:
            raise RuntimeLocatorError("Les chemins de runtime doivent désigner des enfants du runtime.")
        return cls(
            project_root=workspace.project_root,
            runtime_dir=workspace.runtime_dir,
            sqlite_path=sqlite,
            artifacts_dir=artifacts,
        )

    @staticmethod
    def _inside_runtime(runtime_dir: Path, value: Any, label: str) -> Path:
        if not isinstance(value, str) or not value.strip():
            raise RuntimeLocatorError(f"{label} doit être un chemin relatif non vide.")
        candidate_value = Path(value)
        if candidate_value.is_absolute() or PureWindowsPath(value).drive or ".." in candidate_value.parts or "\\" in value or "\x00" in value:
            raise RuntimeLocatorError(f"{label} doit rester relatif, sans traversal.")
        candidate = (runtime_dir / candidate_value).resolve(strict=False)
        try:
            candidate.relative_to(runtime_dir)
        except ValueError as exc:
            raise RuntimeLocatorError(f"{label} sort du runtime configuré.") from exc
        return candidate
