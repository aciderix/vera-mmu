"""Project workspace and runtime resolution for the VERA-MMU Core (M1, C02/C11)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Any, Mapping


class WorkspaceError(ValueError):
    """Raised when a profile resolves a workspace or runtime outside its project."""


@dataclass(frozen=True)
class Workspace:
    """A validated project workspace, independent of any VCS or domain pack."""

    project_root: Path
    profile_path: Path
    roots: tuple[Path, ...]
    runtime_dir: Path
    vcs_roots: tuple[Path, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "project_root": str(self.project_root),
            "profile_path": str(self.profile_path),
            "roots": [str(root) for root in self.roots],
            "runtime_dir": str(self.runtime_dir),
            "vcs_roots": [str(root) for root in self.vcs_roots],
        }


def _mapping(profile: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = profile.get(key)
    if not isinstance(value, Mapping):
        raise WorkspaceError(f"Le profile ne contient pas d’objet {key!r} valide.")
    return value


def _relative_path(value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise WorkspaceError(f"{label} doit être un chemin relatif non vide.")
    path = Path(value.strip())
    if path.is_absolute() or PureWindowsPath(value).drive or ".." in path.parts or "\\" in value or "\x00" in value:
        raise WorkspaceError(f"{label} doit rester relatif, sans traversal ni séparateur non portable.")
    return path


def _inside(root: Path, candidate: Path, label: str) -> Path:
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise WorkspaceError(f"{label} sort de la racine du projet.") from exc
    return resolved


def _profile_anchor(profile_path: Path) -> Path:
    """Infer a project anchor without accepting upward traversal in profile values."""
    source = profile_path.expanduser().resolve()
    if not source.is_file():
        raise WorkspaceError(f"Profil introuvable : {source}")
    parent = source.parent
    if source.name == "project.yaml" and parent.name == ".vera-mmu":
        return parent.parent
    return parent


def _vcs_root(path: Path, project_root: Path) -> Path | None:
    """Return a local Git marker root if present; VCS remains entirely optional."""
    current = path
    while True:
        if (current / ".git").exists():
            return current
        if current == project_root:
            return None
        parent = current.parent
        if parent == current:
            return None
        current = parent


class WorkspaceResolver:
    """Resolve one profile-bound workspace without requiring a VCS executable."""

    def __init__(self, profile: Mapping[str, Any], profile_path: str | Path) -> None:
        self._profile = profile
        self._profile_path = Path(profile_path)

    def resolve(self) -> Workspace:
        """Resolve profile roots and runtime with fail-closed path confinement."""
        source = self._profile_path.expanduser().resolve()
        anchor = _profile_anchor(source)
        workspace = _mapping(self._profile, "workspace")
        storage = _mapping(self._profile, "storage")

        primary = _inside(anchor, anchor / _relative_path(workspace.get("root"), "workspace.root"), "workspace.root")
        if not primary.is_dir():
            raise WorkspaceError("workspace.root doit désigner un répertoire existant.")

        additional = workspace.get("additional_roots", [])
        if not isinstance(additional, list) or not all(isinstance(item, str) for item in additional):
            raise WorkspaceError("workspace.additional_roots doit être une liste de chemins relatifs.")
        roots: list[Path] = [primary]
        for index, value in enumerate(additional):
            candidate = _inside(anchor, anchor / _relative_path(value, f"workspace.additional_roots[{index}]"), "workspace.additional_roots")
            if not candidate.is_dir():
                raise WorkspaceError(f"workspace.additional_roots[{index}] doit désigner un répertoire existant.")
            if candidate in roots:
                raise WorkspaceError("workspace.additional_roots ne peut pas dupliquer une racine.")
            roots.append(candidate)

        runtime = _inside(anchor, anchor / _relative_path(storage.get("memory_dir"), "storage.memory_dir"), "storage.memory_dir")
        if runtime == anchor:
            raise WorkspaceError("storage.memory_dir doit désigner un sous-répertoire du projet.")

        vcs_roots = tuple(sorted({root for candidate in roots if (root := _vcs_root(candidate, anchor)) is not None}, key=str))
        return Workspace(
            project_root=anchor,
            profile_path=source,
            roots=tuple(roots),
            runtime_dir=runtime,
            vcs_roots=vcs_roots,
        )


def resolve_workspace(profile: Mapping[str, Any], profile_path: str | Path) -> Workspace:
    """Resolve a workspace through the explicit M1 resolver primitive."""
    return WorkspaceResolver(profile, profile_path).resolve()
