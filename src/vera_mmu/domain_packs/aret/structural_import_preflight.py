from __future__ import annotations

from dataclasses import dataclass
import re

from vera_mmu.identity import ProjectIdentity

from .brick_reader import AretV1BrickSourcePage, AretV1BrickSourceRecord
from .function_symbol_reader import AretV1FunctionSymbolSourcePage, AretV1FunctionSymbolSourceRecord
from .schema import aret_v1_schema_manifest
from .sqlite_schema import AretV1SchemaSnapshotInspection
from .structural_import_preparation import AretStructuralImportPreparation
from .structural_schema_conformance import AretV1BrickSchemaConformance, AretV1FunctionSymbolSchemaConformance


_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,127}$")
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_BRICK_STATES = frozenset({"PLANNED", "ACTIVE", "BLOCKED", "DONE", "OBSOLETE"})


class AretStructuralImportPreflightError(ValueError):
    """Raised when a structural import preflight is not fully bound, read-only and fail-closed."""


@dataclass(frozen=True)
class AretV1StructuralImportPreflight:
    """A non-executable structural preflight; it approves neither an import nor a VERA write."""

    target_identity: ProjectIdentity
    request_id: str
    preflight_id: str
    confirmed_by: str
    legacy_table: str
    vera_resource: str
    resource_kind: str
    source_snapshot_sha256: str
    source_record_count: int
    source_first_id: str
    source_last_id: str
    lifecycle_policy: str
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
        raise AretStructuralImportPreflightError(f"{label} doit être un identifiant canonique borné.")
    return value


def _require_actor(value: object) -> str:
    if not isinstance(value, str) or not value.strip() or "\r" in value or "\n" in value:
        raise AretStructuralImportPreflightError("confirmed_by doit être une chaîne non vide sur une ligne.")
    return value.strip()


def _require_preparation(value: object) -> AretStructuralImportPreparation:
    if not isinstance(value, AretStructuralImportPreparation):
        raise AretStructuralImportPreflightError("preparation doit être une préparation structurelle ARET V1.")
    expected_resource = "symbol" if value.legacy_table == "function_symbol" else "work_item"
    if (
        value.legacy_table not in {"function_symbol", "brick"}
        or value.vera_resource != expected_resource
        or value.source_schema_version != 6
        or value.requires_explicit_import is not True
        or value.execution_state != "PREPARED_NOT_EXECUTED"
        or value.source_attestation_state != "UNVERIFIED_DECLARATION"
        or not isinstance(value.target_identity, ProjectIdentity)
        or not _HASH_RE.fullmatch(value.source_snapshot_sha256)
    ):
        raise AretStructuralImportPreflightError("preparation doit rester structurelle, explicitement gated et non exécutée.")
    return value


def _require_inspection(value: object) -> AretV1SchemaSnapshotInspection:
    if not isinstance(value, AretV1SchemaSnapshotInspection):
        raise AretStructuralImportPreflightError("schema_inspection doit être une inspection ARET V1.")
    manifest = aret_v1_schema_manifest()
    if (
        value.migration_versions != manifest.migration_versions
        or value.application_tables != manifest.application_tables
        or value.source_access_mode != "SQLITE_READ_ONLY_SCHEMA"
        or value.inspection_state != "SCHEMA_MANIFEST_VERIFIED"
        or not _HASH_RE.fullmatch(value.source_snapshot_sha256)
    ):
        raise AretStructuralImportPreflightError("schema_inspection doit rester liée au manifeste ARET V1 vérifié.")
    return value


def _require_function_page(value: object, inspection: AretV1SchemaSnapshotInspection) -> AretV1FunctionSymbolSourcePage:
    if not isinstance(value, AretV1FunctionSymbolSourcePage) or (
        value.source_path != inspection.source_path
        or value.source_snapshot_sha256 != inspection.source_snapshot_sha256
        or value.read_state != "SOURCE_ROWS_OBSERVED"
        or not 1 <= len(value.records) <= 100
    ):
        raise AretStructuralImportPreflightError("source_page function_symbol doit rester liée au snapshot inspecté.")
    previous_id = ""
    for record in value.records:
        if not isinstance(record, AretV1FunctionSymbolSourceRecord) or not all(
            isinstance(field, str) for field in (
                record.source_id, record.component_id, record.module, record.symbol,
                record.calling_convention, record.created_at, record.created_by,
            )
        ) or not record.component_id or not record.symbol:
            raise AretStructuralImportPreflightError("source_page function_symbol contient un record invalide.")
        if record.source_id != f"{record.component_id}:{record.module}!{record.symbol}" or record.source_id <= previous_id:
            raise AretStructuralImportPreflightError("source_page function_symbol viole son ID stable ou son ordre source.")
        previous_id = record.source_id
    if value.next_after_id is not None and value.next_after_id != value.records[-1].source_id:
        raise AretStructuralImportPreflightError("next_after_id function_symbol doit être absent ou égal au dernier source_id.")
    return value


def _require_brick_page(value: object, inspection: AretV1SchemaSnapshotInspection) -> AretV1BrickSourcePage:
    if not isinstance(value, AretV1BrickSourcePage) or (
        value.source_path != inspection.source_path
        or value.source_snapshot_sha256 != inspection.source_snapshot_sha256
        or value.read_state != "SOURCE_ROWS_OBSERVED"
        or not 1 <= len(value.records) <= 100
    ):
        raise AretStructuralImportPreflightError("source_page brick doit rester liée au snapshot inspecté.")
    previous_id = ""
    for record in value.records:
        if not isinstance(record, AretV1BrickSourceRecord) or not isinstance(record.source_id, str) or not record.source_id:
            raise AretStructuralImportPreflightError("source_page brick contient un record invalide.")
        if (
            (record.component_id is not None and not isinstance(record.component_id, str))
            or not isinstance(record.title, str) or not record.title
            or record.state not in _BRICK_STATES
            or not isinstance(record.description, str)
            or (record.milestone is not None and not isinstance(record.milestone, str))
            or (record.target_platform is not None and not isinstance(record.target_platform, str))
            or isinstance(record.priority, bool) or not isinstance(record.priority, int) or not 1 <= record.priority <= 5
            or not isinstance(record.created_at, str) or not isinstance(record.created_by, str)
            or record.source_id <= previous_id
        ):
            raise AretStructuralImportPreflightError("source_page brick viole son contrat V1 d’état, priorité ou ordre.")
        previous_id = record.source_id
    if value.next_after_id is not None and value.next_after_id != value.records[-1].source_id:
        raise AretStructuralImportPreflightError("next_after_id brick doit être absent ou égal au dernier source_id.")
    return value


def structural_import_preflight(
    *,
    preparation: AretStructuralImportPreparation,
    schema_inspection: AretV1SchemaSnapshotInspection,
    schema_conformance: AretV1FunctionSymbolSchemaConformance | AretV1BrickSchemaConformance,
    source_page: AretV1FunctionSymbolSourcePage | AretV1BrickSourcePage,
    preflight_id: str,
    confirmed_by: str,
) -> AretV1StructuralImportPreflight:
    """Bind structural source facts to a zero-write policy only; this never authorizes or imports a record."""
    pending = _require_preparation(preparation)
    inspection = _require_inspection(schema_inspection)
    if pending.source_snapshot_sha256 != inspection.source_snapshot_sha256:
        raise AretStructuralImportPreflightError("preparation et schema_inspection doivent porter le même hash source.")
    if pending.legacy_table == "function_symbol":
        if not isinstance(schema_conformance, AretV1FunctionSymbolSchemaConformance) or (
            schema_conformance.source_path != inspection.source_path
            or schema_conformance.source_snapshot_sha256 != inspection.source_snapshot_sha256
            or schema_conformance.conformance_state != "FUNCTION_SYMBOL_SCHEMA_CONFORMANT"
        ):
            raise AretStructuralImportPreflightError("conformance function_symbol doit rester liée au snapshot inspecté.")
        page = _require_function_page(source_page, inspection)
        resource_kind, lifecycle_policy = "SYMBOL", "NOT_APPLICABLE"
    else:
        if not isinstance(schema_conformance, AretV1BrickSchemaConformance) or (
            schema_conformance.source_path != inspection.source_path
            or schema_conformance.source_snapshot_sha256 != inspection.source_snapshot_sha256
            or schema_conformance.conformance_state != "BRICK_SCHEMA_CONFORMANT"
        ):
            raise AretStructuralImportPreflightError("conformance brick doit rester liée au snapshot inspecté.")
        page = _require_brick_page(source_page, inspection)
        resource_kind, lifecycle_policy = "WORK_ITEM", "PRESERVE_LEGACY_STATE_AS_METADATA"
    return AretV1StructuralImportPreflight(
        target_identity=pending.target_identity,
        request_id=pending.request_id,
        preflight_id=_require_identifier(preflight_id, "preflight_id"),
        confirmed_by=_require_actor(confirmed_by),
        legacy_table=pending.legacy_table,
        vera_resource=pending.vera_resource,
        resource_kind=resource_kind,
        source_snapshot_sha256=inspection.source_snapshot_sha256,
        source_record_count=len(page.records),
        source_first_id=page.records[0].source_id,
        source_last_id=page.records[-1].source_id,
        lifecycle_policy=lifecycle_policy,
    )
