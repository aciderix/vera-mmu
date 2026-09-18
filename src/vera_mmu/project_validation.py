"""Validate a project's declarative files and the relations between them.

`load_project_catalogs` already refuses a malformed file **and the two cross-catalog relations it
can see**: a gate naming a capability nobody declares, and an integration enabled without an agent
profile behind it. This module long carried its own copy of those two checks; neither could ever
fire, because the loader raises first and `validate_project` never reaches them. A second
implementation of a rule that lives elsewhere is not defence in depth — it is a rule nobody can
test, free to rot into disagreement with the one that runs. They were removed, and
`test_project_validation` now pins that `validate_project` still refuses both cases and quotes the
layer that refuses them, so relaxing the loader fails a test instead of opening a hole in silence.

What is left here is what the loader genuinely cannot see: the profile's own resume contract, and
the project playbook that generation will have to quote verbatim.

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

    findings = _declarative_relations(profile)
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


def _declarative_relations(profile: dict[str, object]) -> tuple[str, ...]:
    """Report what the catalog loader cannot see, because it never reads the profile's resume.

    A resume contract that requires nothing is a contract in name only: it lets any session resume
    against an empty accusation, and `resume_editor` refuses to write one (`NO_REQUIRED_SECTION`).
    A profile hand-edited past that editor would otherwise reach generation unnoticed.
    """
    findings: list[str] = []
    resume = profile.get("resume", {})
    sections = resume.get("sections", []) if isinstance(resume, dict) else []
    required = [item for item in sections if isinstance(item, dict) and item.get("required") is True]
    if not required:
        findings.append("le contrat de reprise n’exige aucune section")
    return tuple(findings)
