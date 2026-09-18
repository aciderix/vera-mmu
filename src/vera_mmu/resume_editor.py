"""Editing the resume contract and the enabled integrations (§29.2, steps 12 and 13).

Two declarations, one module, because they live in the same file and one atomic write is the only
way to avoid leaving half an edit behind.

**Step 13 could never be completed.** `integrations.enabled` governs the journey's thirteenth step
and gates the MCP generation the project ends on. Nothing could write it — not the CLI, not the
bridge, not the write API — so a freshly initialised project stayed on that step for ever. The same
defect as the taxonomy before B4 and the transition policies before B5.

**Step 12 did not exist at all.** The resume contract — which sections a handoff must carry, and
the byte budget they share — was read by `profile_resume_requirements` and editable by nothing.

**What makes this edit different from the others: it invalidates something in flight.** The resume
guard binds a session to the exact `resume_contract_hash` of the dossier it was armed with, and
that dossier is compiled from these requirements and from the profile hash. Changing either makes
every armed acknowledgement impossible — which is the guarantee working, not a bug. So the preview
**names the guards it will invalidate**, with their hashes, before anything is written. An editor
that quietly broke a resume in progress would be the politest possible way to lose a session.

**The refusals are the contract's own feasibility.** A contract with no required section, or a
budget too small to hold the sections it requires, compiles into nothing: the guard could never be
armed. Those are refused here rather than discovered at the next handoff.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from hashlib import sha256
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Mapping, Sequence

import yaml

from .identity import ProfileError, canonical_json, load_profile
from .profile_rebind import ProfileRebindError, commit_profile_change
from .project_catalogs import ProjectCatalogError, load_project_catalogs
from .runtime import RuntimeLocator
from .session_lifecycle import RESUME_DOSSIER_MAX_BYTES
from .store import StoreError
from .workspace import WorkspaceError, resolve_workspace


RESUME_EDIT_FORMAT = "vera-resume-edit/v1"
# What `session_lifecycle._normalize_requirements` demands of every section.
MINIMUM_SECTION_CHARACTERS = 12


class ResumeEditorError(StoreError):
    """Raised when a resume or integration edit cannot be planned or applied as reviewed."""


@dataclass(frozen=True)
class ResumeBlocker:
    """One reason an edit is refused, with the code a screen can key on."""

    code: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


@dataclass(frozen=True)
class ResumeEditPreview:
    """What an edit would declare, and what it would invalidate, reviewed before any write."""

    format: str
    profile_path: str
    template: str
    sections: tuple[tuple[str, bool], ...]
    max_resume_bytes: int
    integrations: tuple[str, ...]
    requirements: tuple[dict[str, Any], ...]
    invalidates: tuple[dict[str, Any], ...]
    blockers: tuple[ResumeBlocker, ...]
    status: str
    preview_hash: str
    mutation: str = "NONE"
    _content: str = field(default="", repr=False, compare=False)

    def as_dict(self) -> dict[str, object]:
        return {
            "format": self.format,
            "profile_path": self.profile_path,
            "template": self.template,
            "sections": [{"id": identifier, "required": required} for identifier, required in self.sections],
            "max_resume_bytes": self.max_resume_bytes,
            "integrations": list(self.integrations),
            "requirements": [dict(item) for item in self.requirements],
            "invalidates": [dict(item) for item in self.invalidates],
            "refusals": [item.as_dict() for item in self.blockers],
            "blockers": [item.message for item in self.blockers],
            "status": self.status,
            "preview_hash": self.preview_hash,
            "mutation": self.mutation,
        }


def resume_contract_options(profile_path: str | Path) -> dict[str, object]:
    """Report the current contract, the integrations available, and what a change would break."""
    path = _profile_path(profile_path)
    profile = _profile(path)
    resume = profile["resume"]
    sections = tuple((str(item["id"]), bool(item["required"])) for item in resume["sections"])
    budget = _budget(profile)
    return {
        "format": RESUME_EDIT_FORMAT,
        "profile_path": str(path),
        "template": str(resume["template"]),
        "sections": [{"id": identifier, "required": required} for identifier, required in sections],
        "max_resume_bytes": {
            "value": budget,
            "ceiling": RESUME_DOSSIER_MAX_BYTES,
            "minimum_per_section": MINIMUM_SECTION_CHARACTERS,
        },
        "requirements": list(_requirements(sections, budget)),
        "integrations": {
            "enabled": list(profile["integrations"]["enabled"]),
            "available": _available_integrations(path),
        },
        "armed_guards": _armed_guards(profile, path),
        "mutation": "NONE",
    }


def preview_resume_edit(
    profile_path: str | Path,
    *,
    template: str | None = None,
    sections: Sequence[Mapping[str, Any]] | None = None,
    max_resume_bytes: int | None = None,
    integrations: Sequence[str] | None = None,
) -> ResumeEditPreview:
    """Plan an edit of the resume contract and the enabled integrations. Writes nothing."""
    if template is None and sections is None and max_resume_bytes is None and integrations is None:
        raise ResumeEditorError("Aucune section de reprise ni intégration nommée : rien à prévisualiser.")
    path = _profile_path(profile_path)
    profile = _profile(path)
    candidate = deepcopy(profile)

    blockers: list[ResumeBlocker] = []
    declared_sections = (
        _sections(sections)
        if sections is not None
        else tuple((str(item["id"]), bool(item["required"])) for item in profile["resume"]["sections"])
    )
    declared_template = str(template) if template is not None else str(profile["resume"]["template"])
    budget = int(max_resume_bytes) if max_resume_bytes is not None else _budget(profile)
    if isinstance(max_resume_bytes, bool) or (max_resume_bytes is not None and not isinstance(max_resume_bytes, int)):
        raise ResumeEditorError("`max_resume_bytes` doit être un entier.")
    declared_integrations = (
        tuple(_integration_ids(integrations)) if integrations is not None else tuple(profile["integrations"]["enabled"])
    )

    required = [identifier for identifier, is_required in declared_sections if is_required]
    if not required:
        blockers.append(
            ResumeBlocker(
                "NO_REQUIRED_SECTION",
                "Un contrat de reprise sans section requise ne compile aucun dossier : la barrière ne "
                "pourrait jamais être armée.",
            )
        )
    else:
        per_section = min(budget, RESUME_DOSSIER_MAX_BYTES) // len(required)
        if per_section < MINIMUM_SECTION_CHARACTERS:
            blockers.append(
                ResumeBlocker(
                    "RESUME_BUDGET_TOO_SMALL",
                    f"{budget} octets partagés entre {len(required)} section(s) requise(s) laissent "
                    f"{per_section} caractères chacune ; le Core en exige au moins {MINIMUM_SECTION_CHARACTERS}.",
                )
            )

    available = set(_available_integrations(path))
    undeclared = sorted(set(declared_integrations) - available)
    if undeclared:
        blockers.append(
            ResumeBlocker(
                "INTEGRATION_UNDECLARED",
                "Intégration absente du catalogue d’agent profiles du projet : " + ", ".join(undeclared) + ".",
            )
        )

    candidate["resume"] = {
        "template": declared_template,
        "sections": [{"id": identifier, "required": required_flag} for identifier, required_flag in declared_sections],
    }
    candidate.setdefault("storage", {})["max_resume_bytes"] = budget
    candidate.setdefault("integrations", {})["enabled"] = list(declared_integrations)
    content = yaml.safe_dump(candidate, allow_unicode=True, default_flow_style=False, sort_keys=False)
    if not blockers:
        try:
            # Replay the Core's own profile validation, so a preview never promises a file
            # `load_profile` would then refuse.
            load_profile_text(content)
        except ProfileError as exc:
            blockers.append(ResumeBlocker("RESUME_CONTRACT_INVALID", f"Contrat refusé par le Core : {exc}"))

    invalidates = _armed_guards(profile, path) if not blockers else []
    unchanged = (
        declared_template == str(profile["resume"]["template"])
        and declared_sections == tuple((str(item["id"]), bool(item["required"])) for item in profile["resume"]["sections"])
        and budget == _budget(profile)
        and declared_integrations == tuple(profile["integrations"]["enabled"])
    )
    if blockers:
        status = "REFUSED"
    elif unchanged:
        status = "NOTHING_TO_CHANGE"
        invalidates = []
    else:
        status = "PREVIEW"
    payload = {
        "format": RESUME_EDIT_FORMAT,
        "profile_path": str(path),
        "current_profile_sha256": sha256(path.read_bytes()).hexdigest(),
        "template": declared_template,
        "sections": [{"id": identifier, "required": flag} for identifier, flag in declared_sections],
        "max_resume_bytes": budget,
        "integrations": list(declared_integrations),
        "blockers": [item.as_dict() for item in blockers],
        "status": status,
    }
    return ResumeEditPreview(
        format=RESUME_EDIT_FORMAT,
        profile_path=str(path),
        template=declared_template,
        sections=declared_sections,
        max_resume_bytes=budget,
        integrations=declared_integrations,
        requirements=tuple(_requirements(declared_sections, budget)) if required else (),
        invalidates=tuple(invalidates),
        blockers=tuple(blockers),
        status=status,
        preview_hash=sha256(canonical_json(payload).encode("utf-8")).hexdigest(),
        _content="" if blockers else content,
    )


def apply_resume_edit(profile_path: str | Path, preview: ResumeEditPreview, *, confirm: bool) -> dict[str, object]:
    """Write exactly the contract the reviewed preview described, atomically."""
    if confirm is not True:
        raise ResumeEditorError("Édition du contrat de reprise refusée sans confirmation explicite.")
    if not isinstance(preview, ResumeEditPreview):
        raise ResumeEditorError("Preview d’édition de reprise invalide.")
    if preview.status == "REFUSED":
        raise ResumeEditorError("Édition refusée : " + " ".join(item.message for item in preview.blockers))
    path = _profile_path(profile_path)
    if str(path) != preview.profile_path:
        raise ResumeEditorError("Preview lié à un autre Project Profile.")
    if preview.status == "NOTHING_TO_CHANGE":
        return {"format": RESUME_EDIT_FORMAT, "status": "NOTHING_TO_CHANGE", "profile_path": str(path), "invalidated": []}

    current = preview_resume_edit(
        path,
        template=preview.template,
        sections=[{"id": identifier, "required": flag} for identifier, flag in preview.sections],
        max_resume_bytes=preview.max_resume_bytes,
        integrations=list(preview.integrations),
    )
    if current.preview_hash != preview.preview_hash:
        raise ResumeEditorError("Preview périmé : le Project Profile a changé depuis sa relecture.")

    # A profile edit changes `profile_hash`, and the store binds to it: writing without
    # realigning would leave the project's memory unopenable.
    try:
        identity = commit_profile_change(
            path,
            new_content=preview._content,
            new_profile=load_profile_text(preview._content),
            preview_hash=preview.preview_hash,
            actor="RESUME_EDIT",
        )
    except ProfileRebindError as exc:
        raise ResumeEditorError(f"Réalignement de l’identité du store impossible : {exc}") from exc
    try:
        profile = load_profile(path)
    except (ProfileError, OSError, ValueError) as exc:
        raise ResumeEditorError(f"Profile écrit mais invalide après édition : {exc}") from exc
    return {
        "format": RESUME_EDIT_FORMAT,
        "status": "APPLIED",
        "profile_path": str(path),
        "template": preview.template,
        "sections": [{"id": identifier, "required": flag} for identifier, flag in preview.sections],
        "max_resume_bytes": preview.max_resume_bytes,
        "integrations": list(preview.integrations),
        # What the guard will demand from now on: the requirements a dossier must carry, and the
        # profile hash it is bound to. Both changed, so every guard armed before is now unusable.
        "requirements": [dict(item) for item in preview.requirements],
        "invalidated": [dict(item) for item in preview.invalidates],
        "preview_hash": preview.preview_hash,
        "profile_hash": _profile_hash(profile),
        "store_identity": identity,
    }


def load_profile_text(content: str) -> dict[str, Any]:
    """Validate a candidate profile exactly as `load_profile` would, without writing it."""
    from .identity import validate_profile

    decoded = yaml.safe_load(content)
    if not isinstance(decoded, Mapping):
        raise ProfileError("Project Profile candidat non objet.")
    return validate_profile(dict(decoded))


def _requirements(sections: Sequence[tuple[str, bool]], budget: int) -> list[dict[str, Any]]:
    """The requirements a dossier will have to carry, derived exactly as the Core derives them."""
    required = [identifier for identifier, is_required in sections if is_required]
    if not required:
        return []
    per_section = min(16_384, min(budget, RESUME_DOSSIER_MAX_BYTES) // len(required))
    return [{"id": identifier, "minimum": MINIMUM_SECTION_CHARACTERS, "maximum": per_section} for identifier in required]


def _armed_guards(profile: Mapping[str, Any], path: Path) -> list[dict[str, Any]]:
    """List the resume guards this project currently holds, with the hash each one demands.

    Read from the runtime's own lifecycle directory rather than reconstructed: a guard armed by a
    session this process never saw is exactly the one an edit would silently break.
    """
    try:
        lifecycle = RuntimeLocator.from_profile(profile, path).runtime_dir / "lifecycle"
    except (OSError, ValueError, StoreError):
        return []
    if lifecycle.is_symlink() or not lifecycle.is_dir():
        return []
    guards: list[dict[str, Any]] = []
    for candidate in sorted(lifecycle.glob("*.json")):
        if candidate.is_symlink() or not candidate.is_file():
            continue
        try:
            state = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(state, Mapping) or not isinstance(state.get("resumeContractHash"), str):
            continue
        guards.append(
            {
                "adapter_id": str(state.get("adapterId", "")),
                "status": str(state.get("status", "")),
                "resume_contract_hash": str(state["resumeContractHash"]),
                "reason": "Ce contrat change : la barrière n’acceptera plus cet accusé de reprise.",
            }
        )
    return guards


def _available_integrations(path: Path) -> list[str]:
    """Agent profiles the project declares; an unreadable catalogue offers none rather than all."""
    try:
        return sorted(load_project_catalogs(path).agent_profiles)
    except ProjectCatalogError:
        return []


def _sections(value: Sequence[Mapping[str, Any]]) -> tuple[tuple[str, bool], ...]:
    if not isinstance(value, (list, tuple)) or not value or len(value) > 64:
        raise ResumeEditorError("`sections` doit être une liste bornée et non vide de sections de reprise.")
    declared: list[tuple[str, bool]] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, Mapping) or set(item) - {"id", "required"} or "id" not in item:
            raise ResumeEditorError("Chaque section de reprise déclare exactement `id` et `required`.")
        identifier = item["id"]
        required = item.get("required", True)
        if not isinstance(identifier, str) or not identifier or not isinstance(required, bool):
            raise ResumeEditorError("Section de reprise invalide : `id` textuel et `required` booléen attendus.")
        normalized = identifier.strip().replace("_", "-")
        if normalized in seen:
            raise ResumeEditorError(f"Section de reprise en double : `{normalized}`.")
        seen.add(normalized)
        declared.append((normalized, required))
    return tuple(declared)


def _integration_ids(value: Sequence[str]) -> list[str]:
    if not isinstance(value, (list, tuple)) or len(value) > 64:
        raise ResumeEditorError("`integrations` doit être une liste bornée d’identifiants.")
    identifiers: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item or item != item.strip():
            raise ResumeEditorError("Identifiant d’intégration invalide.")
        if item in identifiers:
            raise ResumeEditorError(f"Intégration en double : `{item}`.")
        identifiers.append(item)
    return identifiers


def _budget(profile: Mapping[str, Any]) -> int:
    storage = profile.get("storage")
    value = storage.get("max_resume_bytes", RESUME_DOSSIER_MAX_BYTES) if isinstance(storage, Mapping) else RESUME_DOSSIER_MAX_BYTES
    return int(value) if isinstance(value, int) and not isinstance(value, bool) else RESUME_DOSSIER_MAX_BYTES


def _profile_hash(profile: Mapping[str, Any]) -> str:
    from .identity import profile_identity

    return profile_identity(profile).profile_hash


def _profile(path: Path) -> dict[str, Any]:
    try:
        return load_profile(path)
    except (ProfileError, OSError, ValueError) as exc:
        raise ResumeEditorError(f"Project Profile invalide : édition de reprise refusée ({exc}).") from exc


def _profile_path(value: str | Path) -> Path:
    path = Path(value)
    if path.is_symlink() or not path.is_file() or path.parent.is_symlink():
        raise ResumeEditorError("Project Profile ou son répertoire est ambigu.")
    try:
        resolve_workspace(load_profile(path), path)
    except (ProfileError, WorkspaceError, OSError, ValueError) as exc:
        raise ResumeEditorError(f"Workspace invalide : édition de reprise refusée ({exc}).") from exc
    return path.resolve(strict=True)


def _write_atomic(path: Path, content: str) -> None:
    temporary: Path | None = None
    try:
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=path.parent, prefix=".resume-", suffix=".tmp", delete=False
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
        raise ResumeEditorError("Écriture atomique du Project Profile impossible.") from exc
