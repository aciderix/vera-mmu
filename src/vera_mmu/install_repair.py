"""Guided, preview-then-confirm repair of a project's VERA installation.

The Definition of Done asks for a repairable installation. The Doctor names what is broken, and
this module acts on the one class of failure a repair can honestly fix: a declarative file that
`init-project` owns and that has gone missing.

The boundary is deliberate. Repair restores only files whose content the initialization derives
from the profile itself, never overwrites a file that is present, and never rewrites a profile,
a memory or a catalog the project authored. Anything else is reported as a blocker: guessing a
project's own rules would be exactly the fabrication the product exists to prevent.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile
import os

from .identity import ProfileError, load_profile
from .project_bootstrap import ProjectBootstrapError, preview_project_initialization
from .store import StoreError
from .workspace import WorkspaceError, resolve_workspace


REPAIR_FORMAT = "vera-install-repair/v1"
# Files the initialization derives from the profile, and may therefore restore verbatim.
REPAIRABLE_FILES = ("agent-profiles.yaml", "capabilities.yaml", "gates.yaml", "playbook.md", "policies.yaml", "sync-policy.json")


class InstallRepairError(StoreError):
    """Raised when a repair cannot be planned or applied exactly as reviewed."""


@dataclass(frozen=True)
class RepairAction:
    """One file the repair would restore, and the content it would write."""

    operation: str
    target: str
    sha256: str

    def as_dict(self) -> dict[str, str]:
        return {"operation": self.operation, "target": self.target, "sha256": self.sha256}


@dataclass(frozen=True)
class InstallRepairPreview:
    """What a repair would do, reviewed before anything is written."""

    format: str
    project_id: str
    status: str
    actions: tuple[RepairAction, ...]
    blockers: tuple[str, ...]
    preview_hash: str
    _contents: dict[str, str]

    def as_dict(self) -> dict[str, object]:
        return {
            "format": self.format,
            "project_id": self.project_id,
            "status": self.status,
            "actions": [action.as_dict() for action in self.actions],
            "blockers": list(self.blockers),
            "preview_hash": self.preview_hash,
            "mutation": "NONE",
        }


@dataclass(frozen=True)
class InstallRepairResult:
    """What a confirmed repair actually restored."""

    format: str
    project_id: str
    status: str
    repaired: tuple[str, ...]
    preview_hash: str

    def as_dict(self) -> dict[str, object]:
        return {
            "format": self.format,
            "project_id": self.project_id,
            "status": self.status,
            "repaired": list(self.repaired),
            "preview_hash": self.preview_hash,
        }


def preview_install_repair(profile_path: str | Path) -> InstallRepairPreview:
    """Plan the repair of every derivable file that is missing, writing nothing."""
    source = Path(profile_path)
    try:
        profile = load_profile(source)
        workspace = resolve_workspace(profile, source)
    except (ProfileError, WorkspaceError, OSError, ValueError) as exc:
        raise InstallRepairError(
            f"Installation non réparable : le Project Profile doit être corrigé à la main ({exc})."
        ) from exc
    project = profile.get("project", {})
    project_id = str(project.get("id", ""))
    project_name = str(project.get("name", "")) or project_id
    template = str(project.get("domain", ""))
    try:
        reference = preview_project_initialization(
            workspace.project_root, template=template, project_id=project_id, project_name=project_name,
        )
    except ProjectBootstrapError as exc:
        raise InstallRepairError(f"Contenu de référence indisponible pour la réparation : {exc}") from exc

    actions: list[RepairAction] = []
    blockers: list[str] = []
    contents: dict[str, str] = {}
    for item in reference.files:
        name = Path(item.path).name
        if name not in REPAIRABLE_FILES:
            continue
        candidate = workspace.runtime_dir / name
        if candidate.is_symlink():
            blockers.append(f"`{name}` est un lien symbolique : à retirer à la main avant toute réparation.")
            continue
        if candidate.exists():
            continue
        actions.append(RepairAction("RESTORE_DECLARATIVE_FILE", name, item.sha256))
        contents[name] = item.content

    ordered = tuple(sorted(actions, key=lambda action: action.target))
    status = "NOT_REPAIRABLE" if blockers else ("REPAIRABLE" if ordered else "NOTHING_TO_REPAIR")
    digest = sha256(
        "\0".join((REPAIR_FORMAT, project_id, status, *(f"{a.target}:{a.sha256}" for a in ordered), *sorted(blockers))).encode("utf-8")
    ).hexdigest()
    return InstallRepairPreview(
        format=REPAIR_FORMAT,
        project_id=project_id,
        status=status,
        actions=ordered,
        blockers=tuple(sorted(blockers)),
        preview_hash=digest,
        _contents=contents,
    )


def apply_install_repair(
    profile_path: str | Path, preview: InstallRepairPreview, *, confirm: bool,
) -> InstallRepairResult:
    """Restore exactly the files the reviewed preview named, atomically."""
    if confirm is not True:
        raise InstallRepairError("Réparation refusée sans confirmation explicite.")
    if not isinstance(preview, InstallRepairPreview):
        raise InstallRepairError("Preview de réparation invalide.")
    if preview.status == "NOT_REPAIRABLE":
        raise InstallRepairError("Réparation impossible : " + " ".join(preview.blockers))
    current = preview_install_repair(profile_path)
    if current.preview_hash != preview.preview_hash:
        raise InstallRepairError("Preview de réparation périmé : l’état du projet a changé depuis sa relecture.")
    if not preview.actions:
        return InstallRepairResult(REPAIR_FORMAT, preview.project_id, "NOTHING_TO_REPAIR", (), preview.preview_hash)

    source = Path(profile_path)
    workspace = resolve_workspace(load_profile(source), source)
    repaired: list[str] = []
    for action in preview.actions:
        target = workspace.runtime_dir / action.target
        if target.is_symlink() or target.exists():
            raise InstallRepairError(f"Cible de réparation devenue ambiguë : {action.target}.")
        _write_atomic(target, preview._contents[action.target])
        repaired.append(action.target)
    return InstallRepairResult(REPAIR_FORMAT, preview.project_id, "REPAIRED", tuple(repaired), preview.preview_hash)


def _write_atomic(target: Path, content: str) -> None:
    """Write one restored file atomically, never through a symlink."""
    target.parent.mkdir(parents=True, exist_ok=True)
    handle = NamedTemporaryFile("w", encoding="utf-8", dir=target.parent, prefix=f".{target.name}.", delete=False)
    try:
        with handle as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(handle.name, target)
    except OSError as exc:
        Path(handle.name).unlink(missing_ok=True)
        raise InstallRepairError(f"Écriture atomique impossible pour {target.name}.") from exc
