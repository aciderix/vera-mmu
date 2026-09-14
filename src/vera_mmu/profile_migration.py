"""Read-only planning for physical Project Profile/runtime migrations.

This module intentionally performs no filesystem mutation.  It establishes the
preflight/preview contract required before a future atomic migration executor.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path, PureWindowsPath
import shutil
import sqlite3
from tempfile import NamedTemporaryFile
from typing import Any, Callable, Mapping

import yaml

from .identity import canonical_json, load_profile, project_identity, validate_profile
from .runtime import RuntimeLocator
from .workspace import WorkspaceError, resolve_workspace


class ProfileMigrationError(ValueError):
    """Raised when a physical migration preview cannot be safely constructed."""


_MIGRATION_STATES = {
    "PLANNED",
    "COPYING",
    "VERIFIED",
    "SWITCHING",
    "COMMITTED",
    "DIVERGED",
    "RECOVERY_REQUIRED",
    "ROLLED_BACK",
    "EXECUTING",  # legacy same-filesystem state retained for recovery compatibility
}

_MIGRATION_TRANSITIONS: dict[str, frozenset[str]] = {
    "PLANNED": frozenset({"COPYING", "EXECUTING", "RECOVERY_REQUIRED"}),
    "COPYING": frozenset({"VERIFIED", "COPYING", "DIVERGED", "RECOVERY_REQUIRED"}),
    "VERIFIED": frozenset({"SWITCHING", "DIVERGED", "RECOVERY_REQUIRED"}),
    "SWITCHING": frozenset({"PLANNED", "COMMITTED", "ROLLED_BACK", "DIVERGED", "RECOVERY_REQUIRED"}),
    "EXECUTING": frozenset({"PLANNED", "SWITCHING", "COMMITTED", "ROLLED_BACK", "DIVERGED", "RECOVERY_REQUIRED"}),
    "DIVERGED": frozenset({"RECOVERY_REQUIRED", "ROLLED_BACK"}),
    "RECOVERY_REQUIRED": frozenset({"PLANNED", "ROLLED_BACK", "COMMITTED"}),
    "COMMITTED": frozenset(),
    "ROLLED_BACK": frozenset(),
}


@dataclass(frozen=True)
class MigrationInventoryEntry:
    source: str
    target: str
    kind: str
    exists: bool
    size: int
    sha256: str | None

    def as_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "target": self.target,
            "kind": self.kind,
            "exists": self.exists,
            "size": self.size,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class ProfileMigrationPreview:
    profile_path: str
    old_profile_hash: str
    new_profile_hash: str
    old_identity: dict[str, str]
    new_identity: dict[str, str]
    old_runtime: str
    new_runtime: str
    inventory: tuple[MigrationInventoryEntry, ...]
    workspace_moves: tuple[dict[str, str], ...]
    workspace_inventory: tuple[MigrationInventoryEntry, ...]
    migration_strategy: str
    preview_hash: str

    def as_dict(self) -> dict[str, object]:
        return {
            "format": "vera-profile-physical-migration/v1",
            "status": "PREVIEW",
            "profile_path": self.profile_path,
            "old_profile_hash": self.old_profile_hash,
            "new_profile_hash": self.new_profile_hash,
            "old_identity": self.old_identity,
            "new_identity": self.new_identity,
            "old_runtime": self.old_runtime,
            "new_runtime": self.new_runtime,
            "inventory": [item.as_dict() for item in self.inventory],
            "workspace_moves": [dict(item) for item in self.workspace_moves],
            "workspace_inventory": [item.as_dict() for item in self.workspace_inventory],
            "migration_strategy": self.migration_strategy,
            "preview_hash": self.preview_hash,
            "mutation": "NONE",
        }


def _profile_file(path: str | Path) -> Path:
    source = Path(path).expanduser()
    if source.is_symlink() or not source.is_file() or source.parent.is_symlink():
        raise ProfileMigrationError("Project Profile ou son répertoire ambigu.")
    return source.resolve(strict=True)


def _journal_dir(profile_path: Path) -> Path:
    """Keep migration control files outside the runtime being moved."""
    directory = profile_path.parent.parent if profile_path.parent.name == ".vera-mmu" else profile_path.parent
    if directory.is_symlink() or not directory.is_dir():
        raise ProfileMigrationError("Répertoire de journal de migration ambigu.")
    return directory


def _relative(value: Any, label: str, *, allow_dot: bool = False) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ProfileMigrationError(f"{label} doit être un chemin relatif non vide.")
    path = Path(value.strip())
    if path.is_absolute() or PureWindowsPath(value).drive or ".." in path.parts or "\\" in value or "\x00" in value:
        raise ProfileMigrationError(f"{label} doit rester relatif, sans traversal ni séparateur non portable.")
    if not allow_dot and path == Path("."):
        raise ProfileMigrationError(f"{label} doit désigner un sous-répertoire ou fichier relatif.")
    return path


def _candidate(anchor: Path, value: Any, label: str, *, allow_dot: bool = False) -> Path:
    relative = _relative(value, label, allow_dot=allow_dot)
    candidate = (anchor / relative).resolve(strict=False)
    try:
        candidate.relative_to(anchor)
    except ValueError as exc:
        raise ProfileMigrationError(f"{label} sort de la racine du projet.") from exc
    current = anchor
    for part in candidate.relative_to(anchor).parts:
        current = current / part
        if current.is_symlink():
            raise ProfileMigrationError(f"{label} traverse un symlink ambigu : {current}.")
    return candidate


def _assert_non_overlapping(paths: Mapping[str, Path], anchor: Path) -> None:
    items = sorted(paths.items(), key=lambda item: len(item[1].parts))
    for index, (name, path) in enumerate(items):
        try:
            path.relative_to(anchor)
        except ValueError as exc:
            raise ProfileMigrationError(f"{name} sort de l’ancre du projet.") from exc
        for other_name, other in items[index + 1 :]:
            if path == other or path in other.parents or other in path.parents:
                raise ProfileMigrationError(f"Chevauchement interdit entre {name} et {other_name}.")


def _file_entry(source: Path, target: Path, kind: str) -> MigrationInventoryEntry:
    if source.is_symlink():
        raise ProfileMigrationError(f"Source symlinkée refusée : {source}.")
    if not source.exists():
        return MigrationInventoryEntry(str(source), str(target), kind, False, 0, None)
    if not source.is_file():
        raise ProfileMigrationError(f"Source persistante non régulière : {source}.")
    data = source.read_bytes()
    return MigrationInventoryEntry(str(source), str(target), kind, True, len(data), sha256(data).hexdigest())


def _runtime_entries(old_runtime: Path, new_runtime: Path) -> list[MigrationInventoryEntry]:
    if not old_runtime.exists():
        return []
    if old_runtime.is_symlink() or not old_runtime.is_dir():
        raise ProfileMigrationError("Runtime source absent, symlinké ou non-régulier.")
    entries: list[MigrationInventoryEntry] = []
    for source in sorted(old_runtime.rglob("*"), key=str):
        if source.is_symlink():
            raise ProfileMigrationError(f"Runtime contient un symlink ambigu : {source}.")
        if source.is_file():
            entries.append(_file_entry(source, new_runtime / source.relative_to(old_runtime), "runtime-file"))
    return entries


def _workspace_moves(old_workspace: Any, new_root: Path, new_additional: list[Path]) -> tuple[dict[str, str], ...]:
    targets = [new_root, *new_additional]
    if len(old_workspace.roots) != len(targets):
        raise ProfileMigrationError("Le nombre de racines workspace doit rester stable pour cette migration.")
    moves: list[dict[str, str]] = []
    for index, (source, target) in enumerate(zip(old_workspace.roots, targets)):
        if source.is_symlink() or not source.is_dir():
            raise ProfileMigrationError(f"Racine workspace source absente, symlinkée ou non-régulière : {source}.")
        if target.exists() and (target.is_symlink() or not target.is_dir()):
            raise ProfileMigrationError(f"Racine workspace cible ambiguë : {target}.")
        if source != target:
            moves.append({"source": str(source), "target": str(target), "kind": f"workspace-root[{index}]"})
    return tuple(moves)


def _workspace_inventory(workspace_moves: tuple[dict[str, str], ...]) -> list[MigrationInventoryEntry]:
    entries: list[MigrationInventoryEntry] = []
    for move in workspace_moves:
        source_root = Path(move["source"])
        target_root = Path(move["target"])
        for source in sorted(source_root.rglob("*"), key=str):
            if source.is_symlink():
                raise ProfileMigrationError(f"Racine workspace contient un symlink ambigu : {source}.")
            if source.is_file():
                entries.append(_file_entry(source, target_root / source.relative_to(source_root), "workspace-file"))
            elif not source.is_dir():
                raise ProfileMigrationError(f"Racine workspace contient une entrée non régulière : {source}.")
    return entries


def _device_for_target(path: Path) -> int:
    current = path
    while not current.exists():
        parent = current.parent
        if parent == current:
            raise ProfileMigrationError(f"Filesystem cible introuvable : {path}.")
        current = parent
    return current.stat().st_dev


def _copy_tree_verified(
    source: Path,
    target: Path,
    *,
    progress: Callable[[str, str], None] | None = None,
    journal_path: str | Path | None = None,
    progress_prefix: str = "",
) -> None:
    """Copy and verify a regular tree, optionally persisting each file transition."""
    if source.is_symlink() or not source.is_dir() or target.exists():
        raise ProfileMigrationError("Source ou cible de copie inter-filesystems ambiguë.")
    target.mkdir(parents=True)
    try:
        for item in sorted(source.rglob("*"), key=str):
            relative = item.relative_to(source)
            destination = target / relative
            if item.is_symlink():
                raise ProfileMigrationError(f"Symlink refusé dans la copie : {item}.")
            if item.is_dir():
                destination.mkdir()
                continue
            if not item.is_file():
                raise ProfileMigrationError(f"Entrée non régulière dans la copie : {item}.")
            destination.parent.mkdir(parents=True, exist_ok=True)
            relative_path = relative.as_posix()
            journal_relative_path = (Path(progress_prefix) / relative).as_posix() if progress_prefix else relative_path
            if journal_path is not None:
                record_copy_progress(journal_path, journal_relative_path, "COPYING")
            if progress is not None:
                progress(relative_path, "COPYING")
            shutil.copy2(item, destination)
            source_hash = sha256(item.read_bytes()).hexdigest()
            target_hash = sha256(destination.read_bytes()).hexdigest()
            if source_hash != target_hash or item.stat().st_size != destination.stat().st_size:
                raise ProfileMigrationError(f"Vérification de copie échouée : {item}.")
            if journal_path is not None:
                record_copy_progress(journal_path, journal_relative_path, "VERIFIED")
            if progress is not None:
                progress(relative_path, "VERIFIED")
    except Exception:
        shutil.rmtree(target, ignore_errors=True)
        raise


def preview_profile_physical_migration(profile_path: str | Path, new_profile: Mapping[str, Any]) -> ProfileMigrationPreview:
    """Build a complete, non-mutating physical migration preview."""
    path = _profile_file(profile_path)
    old_profile = load_profile(path)
    try:
        old_workspace = resolve_workspace(old_profile, path)
        old_locator = RuntimeLocator.from_workspace(old_profile, old_workspace)
    except (WorkspaceError, ValueError) as exc:
        raise ProfileMigrationError("Profile source impossible à résoudre pour migration.") from exc
    normalized = validate_profile(new_profile)
    anchor = old_workspace.project_root
    workspace = normalized["workspace"]
    storage = normalized["storage"]
    new_root = _candidate(anchor, workspace["root"], "workspace.root", allow_dot=True)
    additional = [_candidate(anchor, value, f"workspace.additional_roots[{index}]") for index, value in enumerate(workspace["additional_roots"])]
    new_runtime = _candidate(anchor, storage["memory_dir"], "storage.memory_dir")
    new_sqlite = _candidate(new_runtime, storage["sqlite_file"], "storage.sqlite_file")
    new_artifacts = _candidate(new_runtime, storage["artifacts_dir"], "storage.artifacts_dir")
    roots = {"workspace.root": new_root, **{f"workspace.additional_roots[{i}]": value for i, value in enumerate(additional)}}
    _assert_non_overlapping(roots, anchor)
    if new_runtime == anchor or new_sqlite == new_runtime or new_artifacts == new_runtime:
        raise ProfileMigrationError("Les chemins de migration doivent désigner des enfants distincts.")
    if new_runtime == new_root or any(new_runtime == root for root in additional):
        raise ProfileMigrationError("storage.memory_dir ne doit pas être une racine workspace.")
    workspace_moves = _workspace_moves(old_workspace, new_root, additional)
    workspace_inventory = _workspace_inventory(workspace_moves)
    devices = [old_locator.runtime_dir.stat().st_dev, _device_for_target(new_runtime)]
    devices.extend(source.stat().st_dev for source, target in ((Path(item["source"]), Path(item["target"])) for item in workspace_moves))
    devices.extend(_device_for_target(Path(item["target"])) for item in workspace_moves)
    migration_strategy = "RENAME_ATOMIC" if len(set(devices)) == 1 else "COPY_VERIFY_SWITCH"
    for label, target in (("storage.memory_dir", new_runtime), ("storage.sqlite_file", new_sqlite), ("storage.artifacts_dir", new_artifacts)):
        if target.exists() and target.is_symlink():
            raise ProfileMigrationError(f"Cible {label} symlinkée.")
    old_content = path.read_bytes()
    new_content = (canonical_json(normalized) + "\n").encode("utf-8")
    old_identity = project_identity(old_profile, old_workspace).as_dict()
    new_identity = project_identity(normalized, None).as_dict()
    inventory = [_file_entry(path, path, "profile")]
    inventory.extend(_runtime_entries(old_locator.runtime_dir, new_runtime))
    for source, target, kind in (
        (old_locator.sqlite_path, new_sqlite, "sqlite"),
        (old_locator.artifacts_dir, new_artifacts, "artifacts-root"),
    ):
        if source.exists() and source.is_file():
            inventory.append(_file_entry(source, target, kind))
    payload = {
        "profile_path": str(path),
        "old_profile_hash": sha256(old_content).hexdigest(),
        "new_profile_hash": sha256(new_content).hexdigest(),
        "old_identity": old_identity,
        "new_identity": new_identity,
        "old_runtime": str(old_locator.runtime_dir),
        "new_runtime": str(new_runtime),
        "inventory": [entry.as_dict() for entry in inventory],
        "workspace_moves": [dict(item) for item in workspace_moves],
        "workspace_inventory": [entry.as_dict() for entry in workspace_inventory],
        "migration_strategy": migration_strategy,
    }
    preview_hash = sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    return ProfileMigrationPreview(
        profile_path=str(path),
        old_profile_hash=payload["old_profile_hash"],
        new_profile_hash=payload["new_profile_hash"],
        old_identity=old_identity,
        new_identity=new_identity,
        old_runtime=str(old_locator.runtime_dir),
        new_runtime=str(new_runtime),
        inventory=tuple(inventory),
        workspace_moves=workspace_moves,
        workspace_inventory=tuple(workspace_inventory),
        migration_strategy=migration_strategy,
        preview_hash=preview_hash,
    )


def _write_json_atomic(path: Path, payload: Mapping[str, object]) -> None:
    temporary: Path | None = None
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, prefix=".vera-profile-migration-", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    except OSError as exc:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise ProfileMigrationError("Journal durable de migration impossible à écrire.") from exc


def transition_profile_migration_state(journal_path: str | Path, target_state: str) -> dict[str, object]:
    """Apply one explicit, atomic and allowlisted migration-state transition."""
    journal = Path(journal_path).expanduser()
    if journal.is_symlink() or not journal.is_file():
        raise ProfileMigrationError("Journal de migration absent ou ambigu.")
    if target_state not in _MIGRATION_STATES:
        raise ProfileMigrationError("État global de migration inconnu.")
    try:
        record = json.loads(journal.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProfileMigrationError("Journal de migration illisible.") from exc
    if not isinstance(record, dict) or record.get("format") != "vera-profile-physical-migration-journal/v1":
        raise ProfileMigrationError("Journal de migration non canonique.")
    current_state = record.get("state")
    if current_state not in _MIGRATION_STATES:
        raise ProfileMigrationError("État global de migration invalide.")
    if target_state not in _MIGRATION_TRANSITIONS[current_state]:
        raise ProfileMigrationError(f"Transition de migration refusée : {current_state} → {target_state}.")
    record["state"] = target_state
    _write_json_atomic(journal, record)
    return {
        "format": "vera-profile-migration-state/v1",
        "previous_state": current_state,
        "state": target_state,
        "mutation": "JOURNAL_STATE_TRANSITION",
    }


def record_copy_progress(journal_path: str | Path, relative_path: str, state: str) -> dict[str, object]:
    """Append one verified copy transition to a migration journal atomically."""
    journal = Path(journal_path).expanduser()
    if journal.is_symlink() or not journal.is_file():
        raise ProfileMigrationError("Journal de progression absent ou ambigu.")
    _relative(relative_path, "copy_progress.path")
    if state not in {"COPYING", "VERIFIED"}:
        raise ProfileMigrationError("État de progression de copie invalide.")
    try:
        record = json.loads(journal.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProfileMigrationError("Journal de progression illisible.") from exc
    if not isinstance(record, dict) or record.get("format") != "vera-profile-physical-migration-journal/v1" or record.get("state") not in {"PLANNED", "COPYING", "EXECUTING"}:
        raise ProfileMigrationError("Journal de progression non exécutable.")
    progress = record.get("copy_progress")
    if not isinstance(progress, list) or any(not isinstance(item, dict) or set(item) != {"path", "state"} for item in progress):
        raise ProfileMigrationError("Progression de copie non canonique.")
    last = next((item["state"] for item in reversed(progress) if item["path"] == relative_path), None)
    if (state == "COPYING" and last is not None) or (state == "VERIFIED" and last != "COPYING"):
        raise ProfileMigrationError("Transition de progression de copie invalide.")
    progress.append({"path": relative_path, "state": state})
    record["copy_progress"] = progress
    if state == "COPYING" and record["state"] == "PLANNED":
        record["state"] = "COPYING"
    _write_json_atomic(journal, record)
    return {"format": "vera-profile-copy-progress/v1", "path": relative_path, "state": state, "mutation": "JOURNAL_APPEND"}


def prepare_profile_migration_journal(
    profile_path: str | Path,
    new_profile: Mapping[str, Any],
    preview: ProfileMigrationPreview,
    *,
    confirm: bool,
) -> dict[str, object]:
    """Persist a fresh migration plan outside runtime; never moves project data."""
    if confirm is not True:
        raise ProfileMigrationError("Préparation du journal refusée sans confirmation explicite.")
    path = _profile_file(profile_path)
    if not isinstance(preview, ProfileMigrationPreview) or preview.profile_path != str(path):
        raise ProfileMigrationError("Preview de migration invalide ou étrangère.")
    current = preview_profile_physical_migration(path, new_profile)
    if current != preview:
        raise ProfileMigrationError("Preview de migration périmé ou altéré.")
    journal_dir = _journal_dir(path)
    journals = sorted(journal_dir.glob(".vera-profile-migration-*.json"))
    if journals:
        raise ProfileMigrationError("Journal de migration déjà présent : reprise Doctor requise.")
    normalized = validate_profile(new_profile)
    target_content = yaml.safe_dump(normalized, allow_unicode=True, default_flow_style=False, sort_keys=False)
    journal_path = journal_dir / f".vera-profile-migration-{preview.preview_hash}.json"
    payload: dict[str, object] = {
        "format": "vera-profile-physical-migration-journal/v1",
        "state": "PLANNED",
        "profile_path": str(path),
        "preview_hash": preview.preview_hash,
        "old_profile_hash": preview.old_profile_hash,
        "new_profile_hash": preview.new_profile_hash,
        "old_identity": preview.old_identity,
        "new_identity": preview.new_identity,
        "old_runtime": preview.old_runtime,
        "new_runtime": preview.new_runtime,
        "target_profile_content": target_content,
        "inventory": [item.as_dict() for item in preview.inventory],
        "workspace_moves": [dict(item) for item in preview.workspace_moves],
        "workspace_inventory": [item.as_dict() for item in preview.workspace_inventory],
        "migration_strategy": preview.migration_strategy,
        "copy_progress": [],
    }
    _write_json_atomic(journal_path, payload)
    return {
        "format": "vera-profile-physical-migration-journal/v1",
        "status": "PLANNED",
        "journal_path": str(journal_path),
        "preview_hash": preview.preview_hash,
        "mutation": "JOURNAL_ONLY",
    }


def inspect_profile_migration_journal(profile_path: str | Path) -> dict[str, object]:
    """Read one migration journal and classify divergence without repairing anything."""
    path = _profile_file(profile_path)
    journal_dir = _journal_dir(path)
    journals = sorted(journal_dir.glob(".vera-profile-migration-*.json"))
    if len(journals) != 1:
        raise ProfileMigrationError("Reprise impossible sans journal de migration unique.")
    journal_path = journals[0]
    if journal_path.is_symlink() or not journal_path.is_file():
        raise ProfileMigrationError("Journal de migration ambigu.")
    try:
        record = json.loads(journal_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProfileMigrationError("Journal de migration illisible.") from exc
    required = {
        "format", "state", "profile_path", "preview_hash", "old_profile_hash", "new_profile_hash",
        "old_identity", "new_identity", "old_runtime", "new_runtime", "target_profile_content", "inventory", "workspace_moves", "workspace_inventory", "migration_strategy", "copy_progress",
    }
    if not isinstance(record, dict) or set(record) != required and set(record) != required | {"backup_path"} or record.get("format") != "vera-profile-physical-migration-journal/v1" or record.get("state") not in {"PLANNED", "COPYING", "EXECUTING"}:
        raise ProfileMigrationError("Journal de migration non canonique ou état non reprenable.")
    if record.get("profile_path") != str(path) or journal_path.stem != f".vera-profile-migration-{record.get('preview_hash')}":
        raise ProfileMigrationError("Journal de migration étranger au Profile.")
    hashes = (record.get("preview_hash"), record.get("old_profile_hash"), record.get("new_profile_hash"))
    if any(not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value) for value in hashes):
        raise ProfileMigrationError("Hash de journal invalide.")
    inventory = record.get("inventory")
    if not isinstance(inventory, list) or any(not isinstance(item, dict) or set(item) != {"source", "target", "kind", "exists", "size", "sha256"} for item in inventory):
        raise ProfileMigrationError("Inventaire de journal invalide.")
    workspace_moves = record.get("workspace_moves")
    if not isinstance(workspace_moves, list) or any(
        not isinstance(item, dict) or set(item) != {"source", "target", "kind"}
        or any(not isinstance(item[key], str) or not item[key] for key in ("source", "target", "kind"))
        for item in workspace_moves
    ):
        raise ProfileMigrationError("Mouvements de racines workspace invalides.")
    if record.get("migration_strategy") not in {"RENAME_ATOMIC", "COPY_VERIFY_SWITCH"}:
        raise ProfileMigrationError("Stratégie de migration filesystem invalide.")
    copy_progress = record.get("copy_progress")
    if not isinstance(copy_progress, list) or any(
        not isinstance(item, dict) or set(item) != {"path", "state"}
        or not isinstance(item["path"], str) or not item["path"]
        or item["state"] not in {"COPYING", "VERIFIED"}
        for item in copy_progress
    ):
        raise ProfileMigrationError("Progression de copie invalide.")
    status = "RECOVERY_REQUIRED" if record["state"] in {"COPYING", "EXECUTING"} else "READY_FOR_EXECUTOR"
    issues: list[dict[str, str]] = []
    for item in inventory:
        source = Path(item["source"]) if isinstance(item["source"], str) else None
        target = Path(item["target"]) if isinstance(item["target"], str) else None
        if source is None or target is None or not isinstance(item["exists"], bool) or not isinstance(item["size"], int) or item["size"] < 0:
            raise ProfileMigrationError("Entrée d’inventaire non canonique.")
        if source.is_symlink():
            issues.append({"code": "SOURCE_SYMLINK", "path": str(source)})
        elif item["exists"]:
            if not source.is_file():
                issues.append({"code": "SOURCE_MISSING", "path": str(source)})
            else:
                digest = sha256(source.read_bytes()).hexdigest()
                if digest != item["sha256"] or source.stat().st_size != item["size"]:
                    issues.append({"code": "SOURCE_DIVERGED", "path": str(source)})
        elif source.exists():
            issues.append({"code": "UNEXPECTED_SOURCE", "path": str(source)})
        if target != source and target.exists():
            issues.append({"code": "TARGET_OCCUPIED", "path": str(target)})
    if issues:
        status = "DIVERGED"
    return {
        "format": "vera-profile-physical-migration-recovery/v1",
        "status": status,
        "journal_path": str(journal_path),
        "preview_hash": record["preview_hash"],
        "issues": issues,
        "mutation": "NONE",
    }


def validate_profile_migration_inventory(journal_path: str | Path) -> dict[str, object]:
    """Validate every expected copied file before a migration switch."""
    journal = Path(journal_path).expanduser()
    if journal.is_symlink() or not journal.is_file():
        raise ProfileMigrationError("Journal de validation absent ou ambigu.")
    try:
        record = json.loads(journal.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProfileMigrationError("Journal de validation illisible.") from exc
    required = {
        "format", "state", "old_runtime", "new_runtime", "inventory", "copy_progress",
    }
    if not isinstance(record, dict) or not required.issubset(record) or record.get("format") != "vera-profile-physical-migration-journal/v1":
        raise ProfileMigrationError("Journal de validation non canonique.")
    if record["state"] not in {"COPYING", "VERIFIED", "SWITCHING"}:
        raise ProfileMigrationError("Journal non positionné sur une phase de validation.")
    inventory = record["inventory"]
    progress = record["copy_progress"]
    if not isinstance(inventory, list) or not isinstance(progress, list):
        raise ProfileMigrationError("Inventaire ou progression non canoniques.")
    expected: dict[str, dict[str, object]] = {}
    new_runtime = Path(str(record["new_runtime"]))
    old_runtime = Path(str(record["old_runtime"]))
    try:
        profile_relative = Path(str(record["profile_path"])).relative_to(old_runtime)
    except (KeyError, ValueError) as exc:
        raise ProfileMigrationError("Profile hors du runtime source journalisé.") from exc
    issues: list[dict[str, str]] = []
    workspace_moves = record.get("workspace_moves")
    if not isinstance(workspace_moves, list):
        raise ProfileMigrationError("Mouvements workspace non canoniques.")
    workspace_inventory = record.get("workspace_inventory")
    if not isinstance(workspace_inventory, list):
        raise ProfileMigrationError("Inventaire workspace non canonique.")
    for item in inventory:
        if not isinstance(item, dict) or set(item) != {"source", "target", "kind", "exists", "size", "sha256"}:
            raise ProfileMigrationError("Entrée d’inventaire non canonique.")
        if not item["exists"] or item["target"] == item["source"]:
            continue
        target = Path(str(item["target"]))
        try:
            relative = target.relative_to(new_runtime)
        except ValueError as exc:
            raise ProfileMigrationError("Cible d’inventaire hors du runtime cible.") from exc
        expected[relative.as_posix()] = item
    progress_states: dict[str, list[str]] = {}
    for item in progress:
        if not isinstance(item, dict) or set(item) != {"path", "state"} or not isinstance(item["path"], str) or item["state"] not in {"COPYING", "VERIFIED"}:
            raise ProfileMigrationError("Progression de copie non canonique.")
        progress_states.setdefault(item["path"], []).append(item["state"])
    for relative, item in expected.items():
        states = progress_states.get(relative, [])
        source = Path(str(item["source"]))
        if item["exists"]:
            if source.is_symlink() or not source.is_file():
                issues.append({"code": "SOURCE_MISSING", "path": str(source)})
            elif source.stat().st_size != item["size"] or sha256(source.read_bytes()).hexdigest() != item["sha256"]:
                issues.append({"code": "SOURCE_DIVERGED", "path": str(source)})
        target = new_runtime / relative
        if states != ["COPYING", "VERIFIED"]:
            issues.append({"code": "COPY_NOT_VERIFIED", "path": relative})
            continue
        if target.is_symlink():
            issues.append({"code": "TARGET_SYMLINK", "path": str(target)})
        elif not target.is_file():
            issues.append({"code": "TARGET_MISSING", "path": str(target)})
        elif relative != profile_relative.as_posix():
            digest = sha256(target.read_bytes()).hexdigest()
            if digest != item["sha256"] or target.stat().st_size != item["size"]:
                issues.append({"code": "TARGET_DIVERGED", "path": str(target)})
        if item["kind"] == "sqlite" and source.is_file() and target.is_file():
            sqlite_report = validate_sqlite_migration_target(source, target)
            issues.extend(
                {"code": issue["code"], "path": issue["path"]}
                for issue in sqlite_report["issues"]
            )
    target_profile = new_runtime / profile_relative
    if target_profile.is_symlink():
        issues.append({"code": "TARGET_PROFILE_SYMLINK", "path": str(target_profile)})
    elif not target_profile.is_file():
        issues.append({"code": "TARGET_PROFILE_MISSING", "path": str(target_profile)})
    elif target_profile.read_text(encoding="utf-8") != record.get("target_profile_content"):
            issues.append({"code": "TARGET_PROFILE_DIVERGED", "path": str(target_profile)})
    workspace_expected: set[str] = set()
    for item in workspace_inventory:
        if not isinstance(item, dict) or set(item) != {"source", "target", "kind", "exists", "size", "sha256"}:
            raise ProfileMigrationError("Entrée d’inventaire workspace non canonique.")
        if not item["exists"]:
            continue
        source = Path(str(item["source"]))
        target = Path(str(item["target"]))
        workspace_expected.add(str(target))
        workspace_progress = None
        for index, move in enumerate(workspace_moves):
            try:
                relative = target.relative_to(Path(str(move["target"])))
            except ValueError:
                continue
            workspace_progress = progress_states.get((Path("workspace") / str(index) / relative).as_posix(), [])
            break
        if workspace_progress != ["COPYING", "VERIFIED"]:
            issues.append({"code": "WORKSPACE_COPY_NOT_VERIFIED", "path": str(target)})
        if source.is_symlink() or not source.is_file():
            issues.append({"code": "WORKSPACE_SOURCE_MISSING", "path": str(source)})
        elif source.stat().st_size != item["size"] or sha256(source.read_bytes()).hexdigest() != item["sha256"]:
            issues.append({"code": "WORKSPACE_SOURCE_DIVERGED", "path": str(source)})
        if target.is_symlink():
            issues.append({"code": "WORKSPACE_TARGET_SYMLINK", "path": str(target)})
        elif not target.is_file():
            issues.append({"code": "WORKSPACE_TARGET_MISSING", "path": str(target)})
        elif target.stat().st_size != item["size"] or sha256(target.read_bytes()).hexdigest() != item["sha256"]:
            issues.append({"code": "WORKSPACE_TARGET_DIVERGED", "path": str(target)})
    for move in workspace_moves:
        target_root = Path(str(move["target"]))
        if target_root.is_symlink() or (target_root.exists() and not target_root.is_dir()):
            issues.append({"code": "WORKSPACE_TARGET_AMBIGUOUS", "path": str(target_root)})
        elif target_root.is_dir():
            for target in sorted(target_root.rglob("*"), key=str):
                if target.is_symlink():
                    issues.append({"code": "WORKSPACE_TARGET_SYMLINK", "path": str(target)})
                elif target.is_file() and str(target) not in workspace_expected:
                    issues.append({"code": "WORKSPACE_UNEXPECTED_TARGET", "path": str(target)})
    actual_files: set[str] = set()
    if new_runtime.exists():
        if new_runtime.is_symlink() or not new_runtime.is_dir():
            issues.append({"code": "TARGET_RUNTIME_AMBIGUOUS", "path": str(new_runtime)})
        else:
            for target in sorted(new_runtime.rglob("*"), key=str):
                if target.is_symlink():
                    issues.append({"code": "TARGET_SYMLINK", "path": str(target)})
                elif target.is_file():
                    actual_files.add(target.relative_to(new_runtime).as_posix())
    for relative in sorted(actual_files - set(expected)):
        issues.append({"code": "UNEXPECTED_TARGET", "path": relative})
    status = "READY_FOR_SWITCH" if not issues and record["state"] == "VERIFIED" else "RECOVERY_REQUIRED"
    if any(issue["code"] in {"TARGET_SYMLINK", "TARGET_DIVERGED", "UNEXPECTED_TARGET", "TARGET_RUNTIME_AMBIGUOUS", "WORKSPACE_TARGET_SYMLINK", "WORKSPACE_TARGET_DIVERGED", "WORKSPACE_UNEXPECTED_TARGET", "WORKSPACE_TARGET_AMBIGUOUS"} for issue in issues):
        status = "DIVERGED"
    return {
        "format": "vera-profile-migration-inventory-validation/v1",
        "status": status,
        "journal_path": str(journal),
        "expected_files": len(expected),
        "verified_files": sum(1 for states in progress_states.values() if states == ["COPYING", "VERIFIED"]),
        "issues": issues,
        "mutation": "NONE",
    }


def _write_text_atomic(path: Path, content: str, prefix: str) -> None:
    temporary: Path | None = None
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, prefix=prefix, suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    except OSError as exc:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise ProfileMigrationError("Écriture atomique du Profile impossible.") from exc


def _checkpoint_sqlite(path: Path) -> None:
    if not path.exists():
        return
    if path.is_symlink() or not path.is_file():
        raise ProfileMigrationError("SQLite source non régulière ou symlinkée.")
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(path, isolation_level=None, timeout=5.0)
        mode = connection.execute("PRAGMA journal_mode=WAL").fetchone()
        if mode is None or str(mode[0]).lower() != "wal":
            raise ProfileMigrationError("Mode WAL SQLite non confirmé.")
        result = connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
        if result is None or len(result) < 3:
            raise ProfileMigrationError("Checkpoint WAL SQLite non confirmé : PRAGMA sans verdict.")
        busy, log_pages, checkpointed = int(result[0]), int(result[1]), int(result[2])
        # A refusal that does not say what it observed cannot be diagnosed from a CI log.
        if busy != 0 or log_pages != 0:
            raise ProfileMigrationError(
                f"Checkpoint WAL SQLite non confirmé (busy={busy}, log={log_pages}, checkpointed={checkpointed})."
            )
        integrity = connection.execute("PRAGMA integrity_check").fetchone()
        if integrity is None or integrity[0] != "ok":
            raise ProfileMigrationError("Intégrité SQLite non confirmée avant migration.")
    except sqlite3.Error as exc:
        raise ProfileMigrationError("Checkpoint ou intégrité SQLite impossible.") from exc
    finally:
        if connection is not None:
            connection.close()


def _sqlite_artifact_manifest(path: Path) -> list[dict[str, object]]:
    artifacts: list[dict[str, object]] = []
    for candidate in (path, Path(f"{path}-wal"), Path(f"{path}-shm")):
        if candidate.is_symlink():
            artifacts.append({"path": str(candidate), "exists": True, "symlink": True})
        elif candidate.exists():
            if not candidate.is_file():
                artifacts.append({"path": str(candidate), "exists": True, "regular": False})
            else:
                data = candidate.read_bytes()
                artifacts.append({
                    "path": str(candidate),
                    "exists": True,
                    "regular": True,
                    "size": len(data),
                    "sha256": sha256(data).hexdigest(),
                })
        else:
            artifacts.append({"path": str(candidate), "exists": False})
    return artifacts


def _sqlite_readonly_fingerprint(path: Path) -> tuple[str, list[tuple[str, str, str, str]]]:
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=5.0)
        integrity = connection.execute("PRAGMA integrity_check").fetchone()
        if integrity is None or integrity[0] != "ok":
            raise ProfileMigrationError("Intégrité SQLite cible non confirmée.")
        schema = connection.execute(
            "SELECT type, name, tbl_name, COALESCE(sql, '') FROM sqlite_master "
            "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name, tbl_name, sql"
        ).fetchall()
        schema_rows = [tuple(str(value) for value in row) for row in schema]
        schema_hash = sha256(canonical_json(schema_rows).encode("utf-8")).hexdigest()
        return schema_hash, schema_rows
    except sqlite3.Error as exc:
        raise ProfileMigrationError("Lecture ou intégrité SQLite impossible.") from exc
    finally:
        if connection is not None:
            connection.close()


def validate_sqlite_migration_target(source_path: str | Path, target_path: str | Path) -> dict[str, object]:
    """Validate SQLite, WAL/SHM artifacts and target schema without mutating them."""
    source = Path(source_path).expanduser()
    target = Path(target_path).expanduser()
    for label, path in (("source", source), ("target", target)):
        if path.is_symlink() or not path.is_file():
            raise ProfileMigrationError(f"SQLite {label} absente, non régulière ou symlinkée.")
    source_artifacts = _sqlite_artifact_manifest(source)
    target_artifacts = _sqlite_artifact_manifest(target)
    issues: list[dict[str, str]] = []
    for artifact in (*source_artifacts, *target_artifacts):
        if artifact.get("symlink") or artifact.get("regular") is False:
            issues.append({"code": "SQLITE_ARTIFACT_AMBIGUOUS", "path": str(artifact["path"])})
    source_hash = sha256(source.read_bytes()).hexdigest()
    target_hash = sha256(target.read_bytes()).hexdigest()
    if source.stat().st_size != target.stat().st_size or source_hash != target_hash:
        issues.append({"code": "SQLITE_DIVERGED", "path": str(target)})
    try:
        source_schema_hash, source_schema = _sqlite_readonly_fingerprint(source)
        target_schema_hash, target_schema = _sqlite_readonly_fingerprint(target)
    except ProfileMigrationError as exc:
        issues.append({"code": "SQLITE_INTEGRITY_ERROR", "path": str(target), "detail": str(exc)})
        source_schema_hash = target_schema_hash = ""
        source_schema = target_schema = []
    if source_schema_hash != target_schema_hash or source_schema != target_schema:
        issues.append({"code": "SQLITE_SCHEMA_DIVERGED", "path": str(target)})
    for source_artifact, target_artifact in zip(source_artifacts[1:], target_artifacts[1:]):
        if source_artifact.get("exists") != target_artifact.get("exists"):
            issues.append({"code": "SQLITE_ARTIFACT_DIVERGED", "path": str(target_artifact["path"])})
        elif source_artifact.get("exists") and (
            source_artifact.get("sha256") != target_artifact.get("sha256")
            or source_artifact.get("size") != target_artifact.get("size")
        ):
            issues.append({"code": "SQLITE_ARTIFACT_DIVERGED", "path": str(target_artifact["path"])})
    return {
        "format": "vera-profile-sqlite-validation/v1",
        "status": "READY_FOR_SWITCH" if not issues else "DIVERGED",
        "source": str(source),
        "target": str(target),
        "source_schema_sha256": source_schema_hash,
        "target_schema_sha256": target_schema_hash,
        "source_artifacts": source_artifacts,
        "target_artifacts": target_artifacts,
        "issues": issues,
        "mutation": "NONE",
    }


def prepare_sqlite_migration_artifacts(
    source_path: str | Path,
    target_path: str | Path,
    *,
    journal_path: str | Path | None = None,
) -> dict[str, object]:
    """Checkpoint, copy and verify SQLite plus WAL/SHM artifacts before switching."""
    source = Path(source_path).expanduser()
    target = Path(target_path).expanduser()
    if source.is_symlink() or not source.is_file() or target.exists() or target.is_symlink():
        raise ProfileMigrationError("Source ou cible SQLite ambiguë.")
    _checkpoint_sqlite(source)
    source_artifacts = _sqlite_artifact_manifest(source)
    present_sources = [Path(str(item["path"])) for item in source_artifacts if item.get("exists")]
    target.parent.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    journal_record: dict[str, object] | None = None
    if journal_path is not None:
        journal = Path(journal_path).expanduser()
        try:
            journal_record = json.loads(journal.read_text(encoding="utf-8"))
            new_runtime = Path(str(journal_record["new_runtime"]))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError) as exc:
            raise ProfileMigrationError("Journal SQLite absent ou non canonique.") from exc
    try:
        for source_artifact in present_sources:
            suffix = source_artifact.name[len(source.name):]
            destination = target.with_name(target.name + suffix)
            relative = destination.relative_to(new_runtime).as_posix() if journal_record is not None else None
            if relative is not None:
                record_copy_progress(journal_path, relative, "COPYING")
            temporary = destination.with_name(f".{destination.name}.vera-copy-tmp")
            if temporary.exists() or destination.exists():
                raise ProfileMigrationError(f"Cible SQLite déjà occupée : {destination}.")
            shutil.copy2(source_artifact, temporary)
            source_data = source_artifact.read_bytes()
            target_data = temporary.read_bytes()
            if len(source_data) != len(target_data) or sha256(source_data).hexdigest() != sha256(target_data).hexdigest():
                raise ProfileMigrationError(f"Vérification de copie SQLite échouée : {source_artifact}.")
            os.replace(temporary, destination)
            created.append(destination)
            if relative is not None:
                record_copy_progress(journal_path, relative, "VERIFIED")
        report = validate_sqlite_migration_target(source, target)
        if report["status"] != "READY_FOR_SWITCH":
            raise ProfileMigrationError("Validation SQLite cible refusée avant bascule.")
        return {
            "format": "vera-profile-sqlite-preparation/v1",
            "status": "READY_FOR_SWITCH",
            "source": str(source),
            "target": str(target),
            "artifacts": report["target_artifacts"],
            "mutation": "SQLITE_ARTIFACT_COPY",
        }
    except Exception:
        for path in reversed(created):
            path.unlink(missing_ok=True)
        for path in target.parent.glob(f".{target.name}*.vera-copy-tmp"):
            path.unlink(missing_ok=True)
        raise


def prepare_workspace_migration_roots(
    workspace_moves: list[dict[str, str]] | tuple[dict[str, str], ...],
    *,
    journal_path: str | Path,
) -> dict[str, object]:
    """Copy isolated workspace roots with per-file journal progress."""
    if not isinstance(workspace_moves, (list, tuple)):
        raise ProfileMigrationError("Mouvements workspace non canoniques.")
    created: list[Path] = []
    try:
        for index, move in enumerate(workspace_moves):
            if not isinstance(move, dict) or set(move) != {"source", "target", "kind"}:
                raise ProfileMigrationError("Mouvement workspace non canonique.")
            source = Path(move["source"])
            target = Path(move["target"])
            _copy_tree_verified(source, target, journal_path=journal_path, progress_prefix=f"workspace/{index}")
            created.append(target)
        return {
            "format": "vera-profile-workspace-preparation/v1",
            "status": "READY_FOR_SWITCH",
            "roots": len(workspace_moves),
            "mutation": "WORKSPACE_COPY",
        }
    except Exception:
        for target in reversed(created):
            shutil.rmtree(target, ignore_errors=True)
        raise


def _execute_copy_verify_switch(
    path: Path,
    new_profile: Mapping[str, Any],
    preview: ProfileMigrationPreview,
    report: Mapping[str, object],
) -> dict[str, object]:
    journal_path = Path(str(report["journal_path"]))
    journal = json.loads(journal_path.read_text(encoding="utf-8"))
    old_runtime = Path(preview.old_runtime)
    new_runtime = Path(preview.new_runtime)
    old_profile = load_profile(path)
    backup_path = _journal_dir(path) / f".vera-profile-migration-{preview.preview_hash}.profile-backup"
    backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    os.chmod(backup_path, 0o600)
    target_profile = new_runtime / path.relative_to(old_runtime)
    try:
        transition_profile_migration_state(journal_path, "COPYING")
        _copy_tree_verified(old_runtime, new_runtime, journal_path=journal_path)
        prepare_workspace_migration_roots(preview.workspace_moves, journal_path=journal_path)
        target_profile.parent.mkdir(parents=True, exist_ok=True)
        _write_text_atomic(
            target_profile,
            yaml.safe_dump(validate_profile(new_profile), allow_unicode=True, default_flow_style=False, sort_keys=False),
            ".vera-profile-copy-",
        )
        transition_profile_migration_state(journal_path, "VERIFIED")
        validation = validate_profile_migration_inventory(journal_path)
        if validation["status"] != "READY_FOR_SWITCH":
            raise ProfileMigrationError("Validation complète refusée avant bascule inter-filesystems.")
        transition_profile_migration_state(journal_path, "SWITCHING")
        for move in preview.workspace_moves:
            source = Path(move["source"])
            if source.exists():
                shutil.rmtree(source)
        if old_runtime.exists():
            shutil.rmtree(old_runtime)
        transition_profile_migration_state(journal_path, "COMMITTED")
        backup_path.unlink(missing_ok=True)
        journal_path.unlink(missing_ok=True)
        return {
            "format": "vera-profile-physical-migration/v1",
            "status": "COMMITTED",
            "preview_hash": preview.preview_hash,
            "profile_path": str(target_profile),
            "mutation": "COPY_VERIFY_SWITCH",
        }
    except Exception as exc:
        current = json.loads(journal_path.read_text(encoding="utf-8"))
        if current.get("state") == "SWITCHING":
            transition_profile_migration_state(journal_path, "RECOVERY_REQUIRED")
            raise ProfileMigrationError("Interruption pendant SWITCHING : reprise externe requise.") from exc
        shutil.rmtree(new_runtime, ignore_errors=True)
        for move in preview.workspace_moves:
            shutil.rmtree(Path(move["target"]), ignore_errors=True)
        transition_profile_migration_state(journal_path, "ROLLED_BACK")
        backup_path.unlink(missing_ok=True)
        raise


def execute_profile_physical_migration(
    profile_path: str | Path,
    new_profile: Mapping[str, Any],
    preview: ProfileMigrationPreview,
    *,
    confirm: bool,
) -> dict[str, object]:
    """Execute only a fresh, same-filesystem runtime move with rollback on failure."""
    if confirm is not True:
        raise ProfileMigrationError("Migration physique refusée sans confirmation explicite.")
    path = _profile_file(profile_path)
    current = preview_profile_physical_migration(path, new_profile)
    if current != preview:
        raise ProfileMigrationError("Preview de migration périmé ou altéré.")
    if preview.migration_strategy == "COPY_VERIFY_SWITCH":
        report = inspect_profile_migration_journal(path)
        if report["status"] != "READY_FOR_EXECUTOR":
            raise ProfileMigrationError("Journal non exécutable : divergence ou collision détectée.")
        return _execute_copy_verify_switch(path, new_profile, preview, report)
    if preview.migration_strategy != "RENAME_ATOMIC":
        raise ProfileMigrationError("Stratégie de migration physique inconnue ou refusée.")
    old_profile = load_profile(path)
    old_workspace = resolve_workspace(old_profile, path)
    new_normalized = validate_profile(new_profile)
    root_moves = [
        (Path(item["source"]), Path(item["target"]))
        for item in preview.workspace_moves
    ]
    report = inspect_profile_migration_journal(path)
    if report["status"] != "READY_FOR_EXECUTOR":
        raise ProfileMigrationError("Journal non exécutable : divergence ou collision détectée.")
    old_runtime = Path(preview.old_runtime)
    new_runtime = Path(preview.new_runtime)
    try:
        new_profile_path = new_runtime / path.relative_to(old_runtime)
    except ValueError as exc:
        raise ProfileMigrationError("Le Profile doit rester dans le runtime migré pour cette étape.") from exc
    if old_runtime == new_runtime or old_runtime.stat().st_dev != new_runtime.parent.stat().st_dev:
        raise ProfileMigrationError("Le runtime doit changer de chemin sur le même filesystem.")
    if new_runtime.exists():
        raise ProfileMigrationError("La cible runtime est déjà occupée.")
    project_anchor = old_workspace.project_root
    for source, target in root_moves:
        if source == project_anchor or path.parent in source.parents or old_runtime in source.parents:
            raise ProfileMigrationError("Déplacement de racine refusé : la source englobe le Profile ou le runtime.")
        if source == target or source in target.parents or target in source.parents:
            raise ProfileMigrationError("Déplacement de racine chevauchant ou nul.")
        if source.stat().st_dev != target.parent.stat().st_dev:
            raise ProfileMigrationError("Les racines workspace doivent rester sur le même filesystem.")
        if target.exists():
            raise ProfileMigrationError("La cible d’une racine workspace est déjà occupée.")
    journal_path = Path(str(report["journal_path"]))
    backup_path = _journal_dir(path) / f".vera-profile-migration-{preview.preview_hash}.profile-backup"
    journal = json.loads(journal_path.read_text(encoding="utf-8"))
    journal["backup_path"] = str(backup_path)
    _write_json_atomic(journal_path, journal)
    transition_profile_migration_state(journal_path, "EXECUTING")
    old_content = path.read_text(encoding="utf-8")
    backup_path.write_text(old_content, encoding="utf-8")
    os.chmod(backup_path, 0o600)
    moved = False
    moved_roots: list[tuple[Path, Path]] = []
    try:
        sqlite_source = Path(preview.old_runtime) / str(old_profile["storage"]["sqlite_file"])
        _checkpoint_sqlite(sqlite_source)
        sqlite_schema_hash, _ = _sqlite_readonly_fingerprint(sqlite_source)
        sqlite_artifacts = _sqlite_artifact_manifest(sqlite_source)
        new_runtime.parent.mkdir(parents=True, exist_ok=True)
        target_content = yaml.safe_dump(new_normalized, allow_unicode=True, default_flow_style=False, sort_keys=False)
        transition_profile_migration_state(journal_path, "SWITCHING")
        _write_text_atomic(path, target_content, ".vera-profile-migration-")
        os.replace(old_runtime, new_runtime)
        moved = True
        for source, target in root_moves:
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(source, target)
            moved_roots.append((source, target))
        sqlite_target = new_runtime / str(new_normalized["storage"]["sqlite_file"])
        target_schema_hash, _ = _sqlite_readonly_fingerprint(sqlite_target)
        target_artifacts = _sqlite_artifact_manifest(sqlite_target)
        if sqlite_schema_hash != target_schema_hash or [item.get("exists") for item in sqlite_artifacts] != [item.get("exists") for item in target_artifacts]:
            raise ProfileMigrationError("Validation SQLite cible échouée avant commit.")
        transition_profile_migration_state(journal_path, "COMMITTED")
        backup_path.unlink(missing_ok=True)
        journal_path.unlink(missing_ok=True)
        return {"format": "vera-profile-physical-migration/v1", "status": "COMMITTED", "preview_hash": preview.preview_hash, "profile_path": str(new_profile_path), "mutation": "RUNTIME_AND_PROFILE"}
    except Exception:
        try:
            if moved and new_runtime.exists() and not old_runtime.exists():
                os.replace(new_runtime, old_runtime)
            for source, target in reversed(moved_roots):
                if target.exists() and not source.exists():
                    os.replace(target, source)
            if backup_path.exists():
                _write_text_atomic(path, backup_path.read_text(encoding="utf-8"), ".vera-profile-rollback-")
            transition_profile_migration_state(journal_path, "ROLLED_BACK")
            backup_path.unlink(missing_ok=True)
        except Exception as rollback_error:
            raise ProfileMigrationError("Migration interrompue et rollback incomplet : journal conservé.") from rollback_error
        raise


def recover_profile_physical_migration(journal_path: str | Path, *, confirm: bool) -> dict[str, object]:
    """Recover one interrupted physical migration; ambiguous states are refused."""
    if confirm is not True:
        raise ProfileMigrationError("Reprise physique refusée sans confirmation explicite.")
    journal = Path(journal_path).expanduser()
    if journal.is_symlink() or not journal.is_file() or journal.name != journal.name.strip():
        raise ProfileMigrationError("Journal de reprise ambigu.")
    try:
        record = json.loads(journal.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProfileMigrationError("Journal de reprise illisible.") from exc
    if not isinstance(record, dict) or record.get("format") != "vera-profile-physical-migration-journal/v1" or record.get("state") not in {"EXECUTING", "SWITCHING"}:
        raise ProfileMigrationError("Seul un journal EXECUTING ou SWITCHING peut être repris par cette opération.")
    required = {"profile_path", "old_runtime", "new_runtime", "backup_path", "old_profile_hash", "new_profile_hash", "preview_hash"}
    if not required.issubset(record) or any(not isinstance(record[key], str) for key in required) or "workspace_moves" not in record:
        raise ProfileMigrationError("Journal EXECUTING incomplet.")
    old_runtime = Path(record["old_runtime"])
    new_runtime = Path(record["new_runtime"])
    old_profile = Path(record["profile_path"])
    try:
        new_profile = new_runtime / old_profile.relative_to(old_runtime)
    except ValueError as exc:
        raise ProfileMigrationError("Profile hors des runtimes journalisés.") from exc
    backup = Path(record["backup_path"])
    if backup.is_symlink() or not backup.is_file():
        raise ProfileMigrationError("Sauvegarde Profile absente ou ambiguë.")
    workspace_moves = record["workspace_moves"]
    if not isinstance(workspace_moves, list) or any(
        not isinstance(item, dict) or set(item) != {"source", "target", "kind"}
        for item in workspace_moves
    ):
        raise ProfileMigrationError("Mouvements workspace absents ou non canoniques.")
    root_moves = [(Path(item["source"]), Path(item["target"])) for item in workspace_moves]
    if old_runtime.exists() and new_runtime.exists():
        transition_profile_migration_state(journal, "RECOVERY_REQUIRED")
        raise ProfileMigrationError("Sources et cibles présentes simultanément : reprise ambiguë.")
    if not old_runtime.exists() and not new_runtime.exists():
        transition_profile_migration_state(journal, "RECOVERY_REQUIRED")
        raise ProfileMigrationError("Source et cible absentes : reprise impossible sans décision externe.")
    if old_runtime.exists():
        if not old_profile.is_file():
            transition_profile_migration_state(journal, "RECOVERY_REQUIRED")
            raise ProfileMigrationError("Profile source absent pendant la reprise.")
        for source, target in root_moves:
            if target.exists() and not source.exists():
                os.replace(target, source)
            elif source.exists() and not target.exists():
                continue
            else:
                transition_profile_migration_state(journal, "RECOVERY_REQUIRED")
                raise ProfileMigrationError("État de racine workspace ambigu pendant le rollback.")
        current_hash = sha256(old_profile.read_bytes()).hexdigest()
        if current_hash == record["new_profile_hash"]:
            _write_text_atomic(old_profile, backup.read_text(encoding="utf-8"), ".vera-profile-recovery-")
        elif current_hash != record["old_profile_hash"]:
            transition_profile_migration_state(journal, "RECOVERY_REQUIRED")
            raise ProfileMigrationError("Profile source divergent pendant la reprise.")
        transition_profile_migration_state(journal, "PLANNED")
        record = json.loads(journal.read_text(encoding="utf-8"))
        record.pop("backup_path", None)
        _write_json_atomic(journal, record)
        backup.unlink(missing_ok=True)
        return {"format": "vera-profile-physical-migration-recovery/v1", "status": "ROLLED_BACK_TO_PLANNED", "preview_hash": record["preview_hash"], "mutation": "RECOVERY"}
    if not new_profile.is_file() or new_profile.read_text(encoding="utf-8") != record.get("target_profile_content"):
        transition_profile_migration_state(journal, "RECOVERY_REQUIRED")
        raise ProfileMigrationError("Profile cible absent ou divergent pendant la reprise.")
    for source, target in root_moves:
        if not target.exists() or source.exists():
            transition_profile_migration_state(journal, "RECOVERY_REQUIRED")
            raise ProfileMigrationError("État de racine workspace incomplet pendant la finalisation.")
    sqlite_entries = [item for item in record.get("inventory", []) if isinstance(item, dict) and item.get("kind") == "sqlite"]
    for item in sqlite_entries:
        target = Path(str(item["target"]))
        if target.is_symlink() or not target.is_file():
            transition_profile_migration_state(journal, "RECOVERY_REQUIRED")
            raise ProfileMigrationError("SQLite cible absente ou ambiguë pendant la finalisation.")
        try:
            _sqlite_readonly_fingerprint(target)
        except ProfileMigrationError as exc:
            transition_profile_migration_state(journal, "RECOVERY_REQUIRED")
            raise ProfileMigrationError("SQLite cible non intègre pendant la finalisation.") from exc
        for sidecar in (Path(f"{target}-wal"), Path(f"{target}-shm")):
            if sidecar.is_symlink() or (sidecar.exists() and not sidecar.is_file()):
                transition_profile_migration_state(journal, "RECOVERY_REQUIRED")
                raise ProfileMigrationError("Sidecar SQLite cible ambigu pendant la finalisation.")
    backup.unlink(missing_ok=True)
    journal.unlink()
    return {"format": "vera-profile-physical-migration-recovery/v1", "status": "RECOVERED_COMMITTED", "preview_hash": record["preview_hash"], "mutation": "RECOVERY"}
