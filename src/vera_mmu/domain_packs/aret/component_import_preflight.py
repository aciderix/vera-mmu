from __future__ import annotations

from dataclasses import dataclass
import re

from vera_mmu.identity import ProjectIdentity

from .component_reader import AretV1ComponentSourcePage, AretV1ComponentSourceRecord
from .import_preparation import AretComponentImportPreparation
from .schema import aret_v1_schema_manifest
from .sqlite_schema import AretV1SchemaSnapshotInspection


_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,127}$")
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


class AretComponentImportPreflightError(ValueError):
    """Raised when an ARET V1 component import preflight is not fully bound and fail-closed."""


@dataclass(frozen=True)
class AretV1ComponentImportPreflight:
    """A non-executable import preflight; it approves neither an import run nor any VERA write."""

    target_identity: ProjectIdentity
    request_id: str
    preflight_id: str
    confirmed_by: str
    source_snapshot_sha256: str
    source_record_count: int
    source_first_id: str
    source_last_id: str
    collision_policy: str = "REJECT_EXISTING_TARGET"
    merge_policy: str = "FORBID"
    promotion_policy: str = "FORBID"
    write_policy: str = "FORBID"
    rollback_requirement: str = "REQUIRED_BEFORE_WRITE"
    audit_requirement: str = "REQUIRED_BEFORE_WRITE"
    provenance_requirement: str = "REQUIRED_BEFORE_WRITE"
    preflight_state: str = "PREFLIGHT_NOT_EXECUTABLE"


def _require_identifier(value: object, label: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise AretComponentImportPreflightError(
            f"{label} doit contenir 3 à 128 caractères minuscules alphanumériques ou des tirets."
        )
    return value


def _require_actor(value: object) -> str:
    if not isinstance(value, str) or not value.strip() or "\r" in value or "\n" in value:
        raise AretComponentImportPreflightError("confirmed_by doit être une chaîne non vide sur une ligne.")
    return value.strip()


def _require_preparation(value: object) -> AretComponentImportPreparation:
    if not isinstance(value, AretComponentImportPreparation):
        raise AretComponentImportPreflightError("preparation doit être une préparation component ARET V1.")
    if (
        value.legacy_table,
        value.vera_resource,
        value.vera_type,
        value.source_schema_version,
        value.requires_explicit_import,
        value.execution_state,
        value.source_attestation_state,
    ) != (
        "component",
        "entity",
        "COMPONENT",
        6,
        True,
        "PREPARED_NOT_EXECUTED",
        "UNVERIFIED_DECLARATION",
    ):
        raise AretComponentImportPreflightError("preparation doit rester une demande component non exécutée et explicitement import-gated.")
    if not isinstance(value.target_identity, ProjectIdentity) or not _HASH_RE.fullmatch(value.source_snapshot_sha256):
        raise AretComponentImportPreflightError("preparation doit porter une identité VERA et un hash source canoniques.")
    return value


def _require_schema_inspection(value: object) -> AretV1SchemaSnapshotInspection:
    if not isinstance(value, AretV1SchemaSnapshotInspection):
        raise AretComponentImportPreflightError("schema_inspection doit être une inspection M4.9 ARET V1.")
    manifest = aret_v1_schema_manifest()
    if (
        value.migration_versions != manifest.migration_versions
        or value.application_tables != manifest.application_tables
        or value.source_access_mode != "SQLITE_READ_ONLY_SCHEMA"
        or value.inspection_state != "SCHEMA_MANIFEST_VERIFIED"
        or not _HASH_RE.fullmatch(value.source_snapshot_sha256)
    ):
        raise AretComponentImportPreflightError("schema_inspection doit rester vérifiée contre le manifeste ARET V1.")
    return value


def _require_page(value: object, inspection: AretV1SchemaSnapshotInspection) -> AretV1ComponentSourcePage:
    if not isinstance(value, AretV1ComponentSourcePage):
        raise AretComponentImportPreflightError("source_page doit être une page component M4.10.")
    if (
        value.source_path != inspection.source_path
        or value.source_snapshot_sha256 != inspection.source_snapshot_sha256
        or value.read_state != "SOURCE_ROWS_OBSERVED"
        or not value.records
        or len(value.records) > 100
    ):
        raise AretComponentImportPreflightError("source_page doit rester liée au snapshot inspecté et contenir 1 à 100 records observés.")
    previous_id = ""
    for record in value.records:
        if not isinstance(record, AretV1ComponentSourceRecord) or not isinstance(record.source_id, str) or not record.source_id:
            raise AretComponentImportPreflightError("source_page contient un record component invalide.")
        if record.source_id <= previous_id:
            raise AretComponentImportPreflightError("source_page doit rester strictement ordonnée par source_id.")
        previous_id = record.source_id
    if value.next_after_id is not None and value.next_after_id != value.records[-1].source_id:
        raise AretComponentImportPreflightError("next_after_id doit être absent ou égal au dernier source_id observé.")
    return value


def component_import_preflight(
    *,
    preparation: AretComponentImportPreparation,
    schema_inspection: AretV1SchemaSnapshotInspection,
    source_page: AretV1ComponentSourcePage,
    preflight_id: str,
    confirmed_by: str,
) -> AretV1ComponentImportPreflight:
    """Bind one observed component page to a zero-write import policy; this never imports anything."""
    pending = _require_preparation(preparation)
    inspection = _require_schema_inspection(schema_inspection)
    page = _require_page(source_page, inspection)
    if pending.source_snapshot_sha256 != inspection.source_snapshot_sha256:
        raise AretComponentImportPreflightError("preparation et schema_inspection doivent porter le même hash source.")
    return AretV1ComponentImportPreflight(
        target_identity=pending.target_identity,
        request_id=pending.request_id,
        preflight_id=_require_identifier(preflight_id, "preflight_id"),
        confirmed_by=_require_actor(confirmed_by),
        source_snapshot_sha256=inspection.source_snapshot_sha256,
        source_record_count=len(page.records),
        source_first_id=page.records[0].source_id,
        source_last_id=page.records[-1].source_id,
    )
