"""Editing the declared policies of a project (§29.2, step 11).

`policies.yaml` shipped with every project, contributed to `policy_hash`, and **could not be
changed by anything**. No CLI, no bridge, no write API reached it. The same defect as the taxonomy
before B4 and the transition policies before B5 — an excellent lock with no door.

The cycle is the one every sensitive write here uses: preview, freshness check against the file's
own bytes, explicit confirmation, atomic write or refusal.

**What this editor will not let anyone do, and why it is the Core that refuses.** The closed value
set lives in `policy_catalog`, so writing `network: {default: allow}` by hand is refused by the
loader exactly as it is refused here. An editor that merely greyed out the option would stop
protecting anything the moment a text editor opened the file.

**And it never hides which lines are real.** Each line is reported with `ENFORCED` and the module
that reads it, or `DECLARED_ONLY` saying plainly that nothing does. Letting someone tighten
`filesystem.read` while believing it will be honoured would be the politest kind of lie.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from hashlib import sha256
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Mapping

import yaml

from .identity import ProfileError, canonical_json, load_profile
from .policy_catalog import POLICY_CATALOG_FORMAT, POLICY_LINES, describe_policies
from .project_catalogs import ProjectCatalogError, load_project_catalogs
from .store import StoreError
from .workspace import WorkspaceError, resolve_workspace


POLICY_EDIT_FORMAT = "vera-policy-edit/v1"


class PolicyEditorError(StoreError):
    """Raised when a policy edit cannot be planned or applied exactly as reviewed."""


@dataclass(frozen=True)
class PolicyChange:
    """One line the edit would change."""

    section: str
    key: str
    before: Any
    after: Any

    def as_dict(self) -> dict[str, Any]:
        return {"section": self.section, "key": self.key, "before": self.before, "after": self.after}


@dataclass(frozen=True)
class PolicyEditPreview:
    """What an edit would declare, reviewed before anything is written."""

    format: str
    policies_path: str
    changes: tuple[PolicyChange, ...]
    lines: tuple[dict[str, Any], ...]
    blockers: tuple[str, ...]
    status: str
    preview_hash: str
    mutation: str = "NONE"
    _content: str = field(default="", repr=False, compare=False)

    def as_dict(self) -> dict[str, object]:
        return {
            "format": self.format,
            "policies_path": self.policies_path,
            "changes": [item.as_dict() for item in self.changes],
            "lines": [dict(item) for item in self.lines],
            "blockers": list(self.blockers),
            "status": self.status,
            "preview_hash": self.preview_hash,
            "mutation": self.mutation,
        }


def policy_options(profile_path: str | Path) -> dict[str, object]:
    """Report every policy line: its value, its closed set, and what enforces it. Writes nothing."""
    path = _profile_path(profile_path)
    catalog = _catalog(path)
    return {
        "format": POLICY_EDIT_FORMAT,
        "policies_path": str(_policies_path(path)),
        "lines": describe_policies(catalog),
        "mutation": "NONE",
    }


def preview_policy_edit(profile_path: str | Path, changes: Mapping[str, Any]) -> PolicyEditPreview:
    """Plan an edit of named policy lines, keyed `section.key`. Writes nothing."""
    if not isinstance(changes, Mapping) or not changes:
        raise PolicyEditorError("Aucune ligne de policy nommée : rien à prévisualiser.")
    path = _profile_path(profile_path)
    policies_path = _policies_path(path)
    catalog = _catalog(path)
    candidate = deepcopy(catalog)

    planned: list[PolicyChange] = []
    for name, value in sorted(changes.items()):
        section, separator, key = str(name).partition(".")
        if not separator or section not in POLICY_LINES or key not in POLICY_LINES[section]:
            raise PolicyEditorError(f"Ligne de policy inconnue : `{name}`.")
        before = catalog[section][key]
        candidate[section][key] = list(value) if isinstance(value, (list, tuple)) else value
        planned.append(PolicyChange(section, key, before, candidate[section][key]))

    blockers: list[str] = []
    try:
        _validate_candidate(path, candidate)
    except ProjectCatalogError as exc:
        blockers.append(str(exc))

    ordered = tuple(planned)
    if blockers:
        status = "REFUSED"
    elif all(item.before == item.after for item in ordered):
        status = "NOTHING_TO_CHANGE"
    else:
        status = "PREVIEW"
    content = yaml.safe_dump(candidate, allow_unicode=True, default_flow_style=False, sort_keys=False)
    payload = {
        "format": POLICY_EDIT_FORMAT,
        "policies_path": str(policies_path),
        "current_policies_sha256": sha256(policies_path.read_bytes()).hexdigest(),
        "changes": [item.as_dict() for item in ordered],
        "blockers": sorted(blockers),
        "status": status,
    }
    return PolicyEditPreview(
        format=POLICY_EDIT_FORMAT,
        policies_path=str(policies_path),
        changes=ordered,
        lines=tuple(describe_policies(candidate)),
        blockers=tuple(sorted(blockers)),
        status=status,
        preview_hash=sha256(canonical_json(payload).encode("utf-8")).hexdigest(),
        _content="" if blockers else content,
    )


def apply_policy_edit(profile_path: str | Path, preview: PolicyEditPreview, *, confirm: bool) -> dict[str, object]:
    """Write exactly the policy lines the reviewed preview described, atomically."""
    if confirm is not True:
        raise PolicyEditorError("Édition de policies refusée sans confirmation explicite.")
    if not isinstance(preview, PolicyEditPreview):
        raise PolicyEditorError("Preview d’édition de policies invalide.")
    if preview.status == "REFUSED":
        raise PolicyEditorError("Édition refusée : " + " ".join(preview.blockers))
    path = _profile_path(profile_path)
    if str(_policies_path(path)) != preview.policies_path:
        raise PolicyEditorError("Preview lié à un autre catalogue de policies.")
    if preview.status == "NOTHING_TO_CHANGE":
        return {"format": POLICY_EDIT_FORMAT, "status": "NOTHING_TO_CHANGE", "policies_path": preview.policies_path, "changes": []}

    current = preview_policy_edit(path, {f"{item.section}.{item.key}": item.after for item in preview.changes})
    if current.preview_hash != preview.preview_hash:
        raise PolicyEditorError("Preview périmé : le catalogue de policies a changé depuis sa relecture.")

    _write_atomic(Path(preview.policies_path), preview._content)
    try:
        load_project_catalogs(path)
    except ProjectCatalogError as exc:
        raise PolicyEditorError(f"Policies écrites mais refusées par le Core : {exc}") from exc
    return {
        "format": POLICY_EDIT_FORMAT,
        "status": "APPLIED",
        "policies_path": preview.policies_path,
        "changes": [item.as_dict() for item in preview.changes],
        "preview_hash": preview.preview_hash,
    }


def _validate_candidate(profile_path: Path, candidate: Mapping[str, Any]) -> None:
    """Replay the Core's own catalogue validation on the candidate, including the runner cross-check."""
    from .project_catalogs import _policy_catalog, _validate_declared_runners

    validated = _policy_catalog(dict(candidate))
    _validate_declared_runners(load_project_catalogs(profile_path).capabilities, validated)


def _profile_path(value: str | Path) -> Path:
    path = Path(value)
    if path.is_symlink() or not path.is_file() or path.parent.is_symlink():
        raise PolicyEditorError("Project Profile ou son répertoire est ambigu.")
    return path.resolve(strict=True)


def _policies_path(profile_path: Path) -> Path:
    """Resolve the declared policy file, refusing anything outside the runtime or symlinked."""
    try:
        profile = load_profile(profile_path)
        workspace = resolve_workspace(profile, profile_path)
    except (ProfileError, WorkspaceError, OSError, ValueError) as exc:
        raise PolicyEditorError(f"Project Profile invalide : édition de policies refusée ({exc}).") from exc
    relative = profile.get("policies", {}).get("file")
    if not isinstance(relative, str) or not relative:
        raise PolicyEditorError("Le Project Profile ne déclare aucun fichier de policies.")
    path = workspace.project_root / relative
    try:
        path.relative_to(workspace.runtime_dir)
    except ValueError as exc:
        raise PolicyEditorError("Le fichier de policies doit rester sous le runtime VERA.") from exc
    current = workspace.project_root
    for part in Path(relative).parts:
        current = current / part
        if current.is_symlink():
            raise PolicyEditorError("Fichier de policies symlinké refusé.")
    if not path.is_file():
        raise PolicyEditorError("Fichier de policies introuvable ou non régulier.")
    return path


def _catalog(profile_path: Path) -> dict[str, Any]:
    try:
        catalog = load_project_catalogs(profile_path).policies
    except ProjectCatalogError as exc:
        raise PolicyEditorError(f"Catalogue de policies invalide : {exc}") from exc
    if catalog.get("format") != POLICY_CATALOG_FORMAT:
        raise PolicyEditorError("Format de catalogue de policies inattendu.")
    return dict(catalog)


def _write_atomic(path: Path, content: str) -> None:
    temporary: Path | None = None
    try:
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=path.parent, prefix=".policies-", suffix=".tmp", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    except OSError as exc:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise PolicyEditorError("Écriture atomique du catalogue de policies impossible.") from exc
