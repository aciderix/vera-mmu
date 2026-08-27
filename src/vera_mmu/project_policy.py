"""Small fail-closed project policy checks shared by project-local writes."""

from __future__ import annotations

from pathlib import Path

from .project_catalogs import ProjectCatalogError, load_project_catalogs
from .store import MemoryStore, StoreError


class ProjectPolicyError(StoreError):
    """Raised when an operation is not admitted by the declared project policy."""


def require_project_write(store: MemoryStore, *, confirm: bool) -> None:
    """Require the closed filesystem.write policy before a project-state mutation."""
    if not isinstance(store, MemoryStore):
        raise ProjectPolicyError("Écriture projet refusée sans MemoryStore VERA actif.")
    require_project_write_for_profile(store.workspace.profile_path, confirm=confirm)


def require_project_write_for_profile(profile_path: str | Path, *, confirm: bool) -> None:
    """Check a profile-bound filesystem.write decision before opening a target store."""
    if confirm is not True:
        raise ProjectPolicyError("Écriture projet refusée sans confirmation explicite.")
    try:
        policies = load_project_catalogs(profile_path).policies
        filesystem = policies["filesystem"]
        decision = filesystem["write"]
    except (ProjectCatalogError, KeyError, TypeError) as exc:
        raise ProjectPolicyError("Policy filesystem.write absente ou invalide.") from exc
    if decision == "deny":
        raise ProjectPolicyError("Écriture projet refusée par filesystem.write=deny.")
    if decision in {"confirm", "allow"}:
        return
    raise ProjectPolicyError("Decision filesystem.write hors contrat fermé.")
