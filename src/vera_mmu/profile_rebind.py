"""Controlled Project Profile rebind; it changes a project-bound store only with recovery evidence."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import yaml

from .identity import canonical_json, load_profile, project_identity
from .store import MemoryStore, StoreError
from .workspace import resolve_workspace


class ProfileRebindError(StoreError):
    pass


@dataclass(frozen=True)
class ProjectProfileRebindPreview:
    profile_path: str
    old_profile_hash: str
    new_profile_hash: str
    old_identity: dict[str, str]
    new_identity: dict[str, str]
    project_name: str
    project_description: str
    preview_hash: str

    def as_dict(self) -> dict[str, object]:
        return {"format": "vera-profile-rebind/v1", "profile_path": self.profile_path, "old_profile_hash": self.old_profile_hash, "new_profile_hash": self.new_profile_hash, "old_identity": self.old_identity, "new_identity": self.new_identity, "project_name": self.project_name, "project_description": self.project_description, "preview_hash": self.preview_hash, "status": "PREVIEW"}


def _profile_path(value: str | Path) -> Path:
    path = Path(value)
    if path.is_symlink() or not path.is_file() or path.parent.is_symlink():
        raise ProfileRebindError("Project Profile ou son répertoire est ambigu.")
    return path.resolve(strict=True)


def _candidate(path: Path, *, project_name: str, project_description: str) -> tuple[dict[str, Any], str]:
    if not isinstance(project_name, str) or not project_name.strip() or len(project_name) > 160:
        raise ProfileRebindError("Nom de projet invalide.")
    if not isinstance(project_description, str) or len(project_description) > 2000:
        raise ProfileRebindError("Description de projet invalide.")
    profile = deepcopy(load_profile(path))
    project = profile.get("project")
    if not isinstance(project, dict):
        raise ProfileRebindError("Section project invalide.")
    project["name"] = project_name.strip()
    project["description"] = project_description
    content = yaml.safe_dump(profile, allow_unicode=True, default_flow_style=False, sort_keys=False)
    return profile, content


def preview_project_profile_rebind(profile_path: str | Path, *, project_name: str, project_description: str) -> ProjectProfileRebindPreview:
    path = _profile_path(profile_path)
    old_content = path.read_text(encoding="utf-8")
    old_profile = load_profile(path)
    workspace = resolve_workspace(old_profile, path)
    old_identity = project_identity(old_profile, workspace)
    new_profile, new_content = _candidate(path, project_name=project_name, project_description=project_description)
    new_identity = project_identity(new_profile, resolve_workspace(new_profile, path))
    old_hash = sha256(old_content.encode()).hexdigest()
    new_hash = sha256(new_content.encode()).hexdigest()
    payload = {"profile_path": str(path), "old_profile_hash": old_hash, "new_profile_hash": new_hash, "old_identity": old_identity.as_dict(), "new_identity": new_identity.as_dict()}
    return ProjectProfileRebindPreview(str(path), old_hash, new_hash, old_identity.as_dict(), new_identity.as_dict(), project_name.strip(), project_description, sha256(canonical_json(payload).encode()).hexdigest())


def _write_atomic(path: Path, content: str, prefix: str) -> None:
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
        raise ProfileRebindError("Écriture atomique du Project Profile impossible.") from exc


def apply_project_profile_rebind(profile_path: str | Path, preview: ProjectProfileRebindPreview, *, confirm: bool) -> dict[str, object]:
    if confirm is not True:
        raise ProfileRebindError("Rebind du Project Profile refusé sans confirmation explicite.")
    path = _profile_path(profile_path)
    if not isinstance(preview, ProjectProfileRebindPreview) or preview.profile_path != str(path):
        raise ProfileRebindError("Preview de rebind invalide ou lié à un autre profil.")
    current = preview_project_profile_rebind(path, project_name=preview.project_name, project_description=preview.project_description)
    if current != preview:
        raise ProfileRebindError("Preview de rebind altéré ou périmé.")
    new_profile, new_content = _candidate(path, project_name=preview.project_name, project_description=preview.project_description)
    backup = path.parent / f".profile-rebind-{preview.preview_hash}.backup"
    journal = path.parent / f".profile-rebind-{preview.preview_hash}.json"
    if backup.exists() or journal.exists():
        raise ProfileRebindError("Journal ou sauvegarde de rebind déjà présent : reprise Doctor requise.")
    old_content = path.read_text(encoding="utf-8")
    backup.write_text(old_content, encoding="utf-8")
    os.chmod(backup, 0o600)
    journal.write_text(json.dumps({"format": "vera-profile-rebind-journal/v1", "preview_hash": preview.preview_hash, "profile": path.name, "backup": backup.name, "old_profile_hash": preview.old_profile_hash, "new_profile_hash": preview.new_profile_hash, "new_profile_content": new_content, "old_identity": preview.old_identity, "new_identity": preview.new_identity}, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(journal, 0o600)
    try:
        old_profile = load_profile(path)
        with MemoryStore.open(old_profile, path) as store:
            store.rebind_identity(project_identity(new_profile, resolve_workspace(new_profile, path)), actor="PROFILE_REBIND")
        _write_atomic(path, new_content, ".vera-profile-rebind-")
    except Exception:
        raise
    finally:
        if path.exists() and sha256(path.read_text(encoding="utf-8").encode()).hexdigest() == preview.new_profile_hash:
            journal.unlink(missing_ok=True)
            backup.unlink(missing_ok=True)
    return {"status": "REBOUND", "preview_hash": preview.preview_hash, "project_identity": preview.new_identity}


def preview_project_profile_rebind_recovery(profile_path: str | Path) -> dict[str, object]:
    """Inspect exactly one persisted rebind journal without repairing it."""
    path = _profile_path(profile_path)
    journals = sorted(path.parent.glob(".profile-rebind-*.json"))
    if len(journals) != 1:
        raise ProfileRebindError("Reprise impossible sans journal de rebind unique.")
    journal = journals[0]
    if journal.is_symlink() or not journal.is_file():
        raise ProfileRebindError("Journal de rebind ambigu.")
    try:
        record = json.loads(journal.read_text(encoding="utf-8"))
        if not isinstance(record, dict) or record.get("format") != "vera-profile-rebind-journal/v1" or record.get("profile") != path.name:
            raise ValueError("format")
        preview_hash = record["preview_hash"]
        old_hash = record["old_profile_hash"]
        new_hash = record["new_profile_hash"]
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        raise ProfileRebindError("Journal de rebind illisible ou non canonique.") from exc
    if not all(isinstance(value, str) and value for value in (preview_hash, old_hash, new_hash)):
        raise ProfileRebindError("Journal de rebind invalide.")
    current_hash = sha256(path.read_text(encoding="utf-8").encode()).hexdigest()
    payload = {"journal": journal.name, "journal_hash": sha256(journal.read_bytes()).hexdigest(), "current_profile_hash": current_hash, "old_profile_hash": old_hash, "new_profile_hash": new_hash, "rebind_preview_hash": preview_hash}
    return {"format": "vera-profile-rebind-recovery/v1", **payload, "preview_hash": sha256(canonical_json(payload).encode()).hexdigest(), "status": "PREVIEW"}


def apply_project_profile_rebind_recovery(profile_path: str | Path, preview: dict[str, object], *, confirm: bool) -> dict[str, object]:
    if confirm is not True:
        raise ProfileRebindError("Reprise de rebind refusée sans confirmation explicite.")
    expected = preview_project_profile_rebind_recovery(profile_path)
    if preview != expected:
        raise ProfileRebindError("Preview de reprise altéré ou périmé.")
    return recover_project_profile_rebind(profile_path)


def recover_project_profile_rebind(profile_path: str | Path) -> dict[str, object]:
    """Complete or clear one durable rebind journal without accepting client input."""
    path = _profile_path(profile_path)
    journals = sorted(path.parent.glob(".profile-rebind-*.json"))
    if len(journals) > 1:
        raise ProfileRebindError("Plusieurs journaux de rebind présents : reprise ambiguë refusée.")
    if not journals:
        return {"status": "NO_RECOVERY_REQUIRED"}
    journal = journals[0]
    if journal.is_symlink() or not journal.is_file():
        raise ProfileRebindError("Journal de rebind ambigu.")
    try:
        record = json.loads(journal.read_text(encoding="utf-8"))
        if not isinstance(record, dict) or record.get("format") != "vera-profile-rebind-journal/v1" or record.get("profile") != path.name:
            raise ValueError("format")
        new_content = record["new_profile_content"]
        old_hash = record["old_profile_hash"]
        new_hash = record["new_profile_hash"]
        backup_name = record["backup"]
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        raise ProfileRebindError("Journal de rebind illisible ou non canonique.") from exc
    if not all(isinstance(value, str) and value for value in (new_content, old_hash, new_hash, backup_name)) or Path(backup_name).name != backup_name:
        raise ProfileRebindError("Journal de rebind invalide.")
    backup = path.parent / backup_name
    current_hash = sha256(path.read_text(encoding="utf-8").encode()).hexdigest()
    if current_hash == old_hash:
        _write_atomic(path, new_content, ".vera-profile-recover-")
    elif current_hash != new_hash:
        raise ProfileRebindError("Profile divergent pendant la reprise : refus fail-closed.")
    journal.unlink(missing_ok=True)
    backup.unlink(missing_ok=True)
    return {"status": "RECOVERED", "preview_hash": record["preview_hash"]}
