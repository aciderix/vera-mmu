from __future__ import annotations

from dataclasses import dataclass
import re

from vera_mmu.identity import ProjectIdentity

from .mapping import AretStructuralMapping, aret_v1_structural_mappings


_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,127}$")
_ALLOWED_TABLES = frozenset({"function_symbol", "brick"})


class AretStructuralImportPreparationError(ValueError):
    """Raised when an unexecuted explicit structural import request is not fully bounded."""


@dataclass(frozen=True)
class AretStructuralImportPreparation:
    """One non-executable request for a reviewed structural mapping; it has no source or store I/O."""

    target_identity: ProjectIdentity
    source_snapshot_sha256: str
    request_id: str
    requested_by: str
    legacy_table: str
    vera_resource: str
    source_schema_version: int = 6
    requires_explicit_import: bool = True
    execution_state: str = "PREPARED_NOT_EXECUTED"
    source_attestation_state: str = "UNVERIFIED_DECLARATION"


def _require_hash(value: object, label: str) -> str:
    if not isinstance(value, str) or not _HASH_RE.fullmatch(value):
        raise AretStructuralImportPreparationError(f"{label} doit être un SHA-256 canonique.")
    return value


def _require_identity(value: object) -> ProjectIdentity:
    if not isinstance(value, ProjectIdentity):
        raise AretStructuralImportPreparationError("target_identity doit être une identité VERA explicite.")
    if not isinstance(value.project_id, str) or not value.project_id:
        raise AretStructuralImportPreparationError("target_identity.project_id doit être non vide.")
    if not isinstance(value.profile_version, str) or not value.profile_version:
        raise AretStructuralImportPreparationError("target_identity.profile_version doit être non vide.")
    _require_hash(value.profile_hash, "target_identity.profile_hash")
    _require_hash(value.workspace_hash, "target_identity.workspace_hash")
    _require_hash(value.project_hash, "target_identity.project_hash")
    return value


def _require_identifier(value: object, label: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise AretStructuralImportPreparationError(f"{label} doit être un identifiant canonique borné.")
    return value


def _require_actor(value: object) -> str:
    if not isinstance(value, str) or not value.strip() or "\r" in value or "\n" in value:
        raise AretStructuralImportPreparationError("requested_by doit être une chaîne non vide sur une ligne.")
    return value.strip()


def _mapping_for_table(value: object) -> AretStructuralMapping:
    if not isinstance(value, str) or value not in _ALLOWED_TABLES:
        raise AretStructuralImportPreparationError("legacy_table doit être function_symbol ou brick.")
    matches = [mapping for mapping in aret_v1_structural_mappings() if mapping.legacy_table == value]
    if len(matches) != 1:
        raise AretStructuralImportPreparationError("Le mapping structurel ARET V1 doit être unique.")
    mapping = matches[0]
    expected_resource = "symbol" if value == "function_symbol" else "work_item"
    if (mapping.vera_resource, mapping.vera_type, mapping.requires_explicit_import) != (expected_resource, None, True):
        raise AretStructuralImportPreparationError("Le mapping structurel ARET V1 n’est pas admissible.")
    return mapping


def structural_import_preparation(
    *,
    target_identity: ProjectIdentity,
    source_snapshot_sha256: str,
    request_id: str,
    requested_by: str,
    legacy_table: str,
) -> AretStructuralImportPreparation:
    """Build a request only; this does not attest, read, authorize or import any source record."""
    mapping = _mapping_for_table(legacy_table)
    return AretStructuralImportPreparation(
        target_identity=_require_identity(target_identity),
        source_snapshot_sha256=_require_hash(source_snapshot_sha256, "source_snapshot_sha256"),
        request_id=_require_identifier(request_id, "request_id"),
        requested_by=_require_actor(requested_by),
        legacy_table=mapping.legacy_table,
        vera_resource=mapping.vera_resource,
    )
