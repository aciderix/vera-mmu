"""Validate a project's declarative files and the relations between them.

`load_project_catalogs` already refuses a malformed file. This module adds the second half of
what the specification asks of `validate`: that the catalogs agree with one another and with
the profile — a gate naming a capability nobody declares, a resume section the profile does not
require, an integration enabled without an agent profile behind it.

Nothing here opens the store, executes a capability or writes a byte.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from .identity import ProfileError, load_profile, profile_identity
from .playbook import PLAYBOOK_FILE_NAME
from .project_catalogs import ProjectCatalogError, load_project_catalogs
from .store import StoreError
from .workspace import WorkspaceError, resolve_workspace


VALIDATION_FORMAT = "vera-project-validation/v1"


class ProjectValidationError(StoreError):
    """Raised when the declarative files are invalid or disagree with one another."""


@dataclass(frozen=True)
class ProjectValidation:
    """The validated declarative surface of one project and its hashes."""

    format: str
    project_id: str
    profile_hash: str
    status: str
    catalog_hashes: dict[str, str]
    playbook_hash: str
    findings: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "format": self.format,
            "project_id": self.project_id,
            "profile_hash": self.profile_hash,
            "status": self.status,
            "catalog_hashes": dict(self.catalog_hashes),
            "playbook_hash": self.playbook_hash,
            "findings": list(self.findings),
        }


def validate_project(profile_path: str | Path) -> ProjectValidation:
    """Validate the profile, its catalogs, their cross-references and the project playbook."""
    source = Path(profile_path)
    try:
        profile = load_profile(source)
        workspace = resolve_workspace(profile, source)
        identity = profile_identity(profile)
    except (ProfileError, WorkspaceError, OSError, ValueError) as exc:
        raise ProjectValidationError(f"Project Profile invalide : {exc}") from exc
    try:
        catalogs = load_project_catalogs(source)
    except (ProjectCatalogError, OSError, ValueError) as exc:
        raise ProjectValidationError(f"Catalogues déclaratifs invalides : {exc}") from exc

    playbook_file = workspace.runtime_dir / PLAYBOOK_FILE_NAME
    if playbook_file.is_symlink() or not playbook_file.is_file():
        raise ProjectValidationError(
            f"Playbook projet absent ou ambigu : `{PLAYBOOK_FILE_NAME}` est attendu dans le runtime VERA."
        )
    try:
        raw = playbook_file.read_bytes()
    except OSError as exc:
        raise ProjectValidationError(f"Playbook projet illisible : {exc}") from exc
    if not raw.strip():
        raise ProjectValidationError("Playbook projet vide : déclarer au moins une règle de travail.")

    findings = _cross_references(profile, catalogs)
    if findings:
        raise ProjectValidationError("Relations déclaratives incohérentes : " + " ; ".join(findings))
    return ProjectValidation(
        format=VALIDATION_FORMAT,
        project_id=identity.project_id,
        profile_hash=identity.profile_hash,
        status="VALID",
        catalog_hashes={
            "capabilities": catalogs.capability_catalog_hash,
            "gates": catalogs.gate_catalog_hash,
            "policies": catalogs.policy_hash,
            "agent_profiles": catalogs.agent_profiles_hash,
        },
        playbook_hash=sha256(raw).hexdigest(),
        findings=(),
    )


def _cross_references(profile: dict[str, object], catalogs: object) -> tuple[str, ...]:
    """Report every relation a single-file validation cannot catch."""
    findings: list[str] = []
    capability_ids = {str(item["id"]) for item in catalogs.capabilities["capabilities"]}  # type: ignore[attr-defined]
    for gate in catalogs.gates["gates"]:  # type: ignore[attr-defined]
        capability_id = str(gate.get("capability_id"))
        if capability_id not in capability_ids:
            findings.append(f"la gate `{gate.get('id')}` référence une capability non déclarée `{capability_id}`")
    declared_profiles = set(catalogs.agent_profiles)  # type: ignore[arg-type]
    integrations = profile.get("integrations", {})
    enabled = integrations.get("enabled", []) if isinstance(integrations, dict) else []
    for name in enabled if isinstance(enabled, list) else []:
        if str(name) not in declared_profiles:
            findings.append(f"l’intégration activée `{name}` n’a aucun agent profile déclaré")
    resume = profile.get("resume", {})
    sections = resume.get("sections", []) if isinstance(resume, dict) else []
    required = [item for item in sections if isinstance(item, dict) and item.get("required") is True]
    if not required:
        findings.append("le contrat de reprise n’exige aucune section")
    return tuple(findings)
