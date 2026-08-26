from __future__ import annotations

from dataclasses import dataclass
import re

from vera_mmu.identity import ProjectIdentity

from .mapping import AretStructuralMapping, aret_v1_structural_mappings


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_REQUEST_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,127}$")


class AretComponentImportPreparationError(ValueError):
    """Raised when an unexecuted ARET V1 component import request is not explicitly bound."""


@dataclass(frozen=True)
class AretComponentImportPreparation:
    """One non-executable, non-attesting preparation for a future explicit component import.

    This object neither locates nor reads a legacy source. Its snapshot digest is
    an unverified declaration supplied by a caller, never a digest computed here.
    """

    target_identity: ProjectIdentity
    source_snapshot_sha256: str
    request_id: str
    requested_by: str
    legacy_table: str
    vera_resource: str
    vera_type: str | None
    source_schema_version: int = 6
    requires_explicit_import: bool = True
    execution_state: str = "PREPARED_NOT_EXECUTED"
    source_attestation_state: str = "UNVERIFIED_DECLARATION"


def _require_canonical_hash(value: object, label: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise AretComponentImportPreparationError(f"{label} doit être un SHA-256 hexadécimal canonique en minuscules.")
    return value


def _require_target_identity(value: object) -> ProjectIdentity:
    if not isinstance(value, ProjectIdentity):
        raise AretComponentImportPreparationError("target_identity doit être une identité de projet VERA explicite.")
    if not isinstance(value.project_id, str) or not value.project_id:
        raise AretComponentImportPreparationError("target_identity.project_id doit être non vide.")
    if not isinstance(value.profile_version, str) or not value.profile_version:
        raise AretComponentImportPreparationError("target_identity.profile_version doit être non vide.")
    _require_canonical_hash(value.profile_hash, "target_identity.profile_hash")
    _require_canonical_hash(value.workspace_hash, "target_identity.workspace_hash")
    _require_canonical_hash(value.project_hash, "target_identity.project_hash")
    return value


def _require_request_id(value: object) -> str:
    if not isinstance(value, str) or not _REQUEST_ID_RE.fullmatch(value):
        raise AretComponentImportPreparationError(
            "request_id doit contenir 3 à 128 caractères minuscules alphanumériques ou des tirets."
        )
    return value


def _require_requested_by(value: object) -> str:
    if not isinstance(value, str) or not value.strip() or "\r" in value or "\n" in value:
        raise AretComponentImportPreparationError("requested_by doit être une chaîne non vide sur une ligne.")
    return value.strip()


def _component_mapping() -> AretStructuralMapping:
    mappings = [mapping for mapping in aret_v1_structural_mappings() if mapping.legacy_table == "component"]
    if len(mappings) != 1:
        raise AretComponentImportPreparationError("Le mapping structurel ARET V1 component doit être unique.")
    mapping = mappings[0]
    if (mapping.vera_resource, mapping.vera_type, mapping.requires_explicit_import) != ("entity", "COMPONENT", True):
        raise AretComponentImportPreparationError("Le mapping structurel ARET V1 component n’est pas admissible.")
    return mapping


def component_import_preparation(
    *,
    target_identity: ProjectIdentity,
    source_snapshot_sha256: str,
    request_id: str,
    requested_by: str,
) -> AretComponentImportPreparation:
    """Build a fail-closed request only; no source or VERA store is opened or changed."""
    mapping = _component_mapping()
    return AretComponentImportPreparation(
        target_identity=_require_target_identity(target_identity),
        source_snapshot_sha256=_require_canonical_hash(source_snapshot_sha256, "source_snapshot_sha256"),
        request_id=_require_request_id(request_id),
        requested_by=_require_requested_by(requested_by),
        legacy_table=mapping.legacy_table,
        vera_resource=mapping.vera_resource,
        vera_type=mapping.vera_type,
    )
