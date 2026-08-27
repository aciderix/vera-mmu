"""Local, transport-neutral VCS observation with no command or network operations."""
from __future__ import annotations

from dataclasses import dataclass

from .store import MemoryStore, StoreError


class VcsError(StoreError):
    """Raised when project-local version-control state is ambiguous or invalid."""


@dataclass(frozen=True)
class VcsStatus:
    """Minimal local VCS observation; it intentionally contains no path, remote or revision."""

    provider: str
    status: str

    def as_dict(self) -> dict[str, str]:
        return {"provider": self.provider, "status": self.status}


def inspect_vcs(store: MemoryStore) -> VcsStatus:
    """Observe only the project-root marker without executing any VCS command."""
    if not isinstance(store, MemoryStore):
        raise VcsError("Store invalide pour le diagnostic VCS VERA.")
    marker = store.workspace.project_root / ".git"
    if marker.is_symlink():
        raise VcsError("Marqueur VCS symlinké : état ambigu refusé.")
    if not marker.exists():
        return VcsStatus("NONE", "NO_VCS")
    if not marker.is_dir():
        raise VcsError("Marqueur VCS non répertoire : état ambigu refusé.")
    return VcsStatus("GIT", "OBSERVED")
