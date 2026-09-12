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
from tempfile import NamedTemporaryFile
from typing import Any, Mapping

import yaml

from .identity import canonical_json, load_profile, project_identity, validate_profile
from .runtime import RuntimeLocator
from .workspace import WorkspaceError, resolve_workspace


class ProfileMigrationError(ValueError):
    """Raised when a physical migration preview cannot be safely constructed."""


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
            "preview_hash": self.preview_hash,
            "mutation": "NONE",
        }


def _profile_file(path: str | Path) -> Path:
    source = Path(path).expanduser()
    if source.is_symlink() or not source.is_file() or source.parent.is_symlink():
        raise ProfileMigrationError("Project Profile ou son répertoire ambigu.")
    return source.resolve(strict=True)


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
    journals = sorted(path.parent.glob(".vera-profile-migration-*.json"))
    if journals:
        raise ProfileMigrationError("Journal de migration déjà présent : reprise Doctor requise.")
    normalized = validate_profile(new_profile)
    target_content = yaml.safe_dump(normalized, allow_unicode=True, default_flow_style=False, sort_keys=False)
    journal_path = path.parent / f".vera-profile-migration-{preview.preview_hash}.json"
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
    journals = sorted(path.parent.glob(".vera-profile-migration-*.json"))
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
        "old_identity", "new_identity", "old_runtime", "new_runtime", "target_profile_content", "inventory",
    }
    if not isinstance(record, dict) or set(record) != required or record.get("format") != "vera-profile-physical-migration-journal/v1" or record.get("state") != "PLANNED":
        raise ProfileMigrationError("Journal de migration non canonique ou état non reprenable.")
    if record.get("profile_path") != str(path) or journal_path.stem != f".vera-profile-migration-{record.get('preview_hash')}":
        raise ProfileMigrationError("Journal de migration étranger au Profile.")
    hashes = (record.get("preview_hash"), record.get("old_profile_hash"), record.get("new_profile_hash"))
    if any(not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value) for value in hashes):
        raise ProfileMigrationError("Hash de journal invalide.")
    inventory = record.get("inventory")
    if not isinstance(inventory, list) or any(not isinstance(item, dict) or set(item) != {"source", "target", "kind", "exists", "size", "sha256"} for item in inventory):
        raise ProfileMigrationError("Inventaire de journal invalide.")
    status = "READY_FOR_EXECUTOR"
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
