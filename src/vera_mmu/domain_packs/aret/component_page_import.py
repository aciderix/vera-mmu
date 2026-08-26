from __future__ import annotations

from dataclasses import dataclass
import re

from vera_mmu.entities import Entity
from vera_mmu.identity import ProjectIdentity, canonical_json
from vera_mmu.import_batches import (
    EntityImportBatchInput,
    ImportBatchError,
    ImportBatchService,
    ImportEntityInput,
)
from vera_mmu.store import MemoryStore

from .component_entity_projection import AretV1ComponentEntityProjection, AretV1EntityDraft
from .component_import_preflight import AretV1ComponentImportPreflight
from .component_schema_conformance import AretV1ComponentSchemaConformance


_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_COMPONENT_COLUMNS = (
    ("id", "TEXT", True, True, None),
    ("title", "TEXT", True, False, None),
    ("description", "TEXT", True, False, "''"),
    ("created_at", "TEXT", True, False, None),
    ("created_by", "TEXT", True, False, None),
)
_SOURCE_SYSTEM = "aret-v1"
_MAPPING_ID = "aret-v1-component-entity-v1"
_TYPE_DESCRIPTION = "Generic component entities created through an explicitly authorized paged ARET import."
_TYPE_SCHEMA = {"kind": "generic", "resource": "entity"}


class AretComponentPageImportError(ValueError):
    """Raised when an explicitly authorized page cannot remain isolated, bound and non-promoting."""


@dataclass(frozen=True)
class AretV1ComponentPageImportAuthorization:
    """One explicit no-effect permission for a single bounded component page in an ARET V1 series."""

    target_identity: ProjectIdentity
    request_id: str
    preflight_id: str
    source_snapshot_sha256: str
    source_record_count: int
    source_first_id: str
    source_last_id: str
    authorization_id: str
    authorized_by: str
    target_series_state: str
    collision_policy: str = "REJECT_EXISTING_TARGET"
    merge_policy: str = "FORBID"
    promotion_policy: str = "FORBID"
    authorization_state: str = "EXPLICIT_PAGE_IMPORT_ALLOWED"


@dataclass(frozen=True)
class AretV1AuthorizedComponentPageImportResult:
    """The exact result of one ledger-backed component page, without evidence or proof promotion."""

    target_identity: ProjectIdentity
    request_id: str
    preflight_id: str
    authorization_id: str
    source_snapshot_sha256: str
    imported_entity_count: int
    entities: tuple[Entity, ...]
    was_already_imported: bool
    import_state: str = "IMPORTED_NO_PROMOTION"


def _require_identifier(value: object, label: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise AretComponentPageImportError(
            f"{label} doit contenir 3 à 128 caractères minuscules alphanumériques ou des tirets."
        )
    return value


def _require_actor(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\r" in value or "\n" in value:
        raise AretComponentPageImportError(f"{label} doit être une chaîne non vide sur une ligne.")
    return value.strip()


def _require_preflight(value: object) -> AretV1ComponentImportPreflight:
    if not isinstance(value, AretV1ComponentImportPreflight):
        raise AretComponentPageImportError("preflight doit être un préflight component ARET V1.")
    if (
        value.collision_policy,
        value.merge_policy,
        value.promotion_policy,
        value.write_policy,
        value.rollback_requirement,
        value.audit_requirement,
        value.provenance_requirement,
        value.preflight_state,
    ) != (
        "REJECT_EXISTING_TARGET",
        "FORBID",
        "FORBID",
        "FORBID",
        "REQUIRED_BEFORE_WRITE",
        "REQUIRED_BEFORE_WRITE",
        "REQUIRED_BEFORE_WRITE",
        "PREFLIGHT_NOT_EXECUTABLE",
    ):
        raise AretComponentPageImportError("preflight doit conserver toutes les politiques fail-closed M4.11.")
    if (
        not isinstance(value.target_identity, ProjectIdentity)
        or not _SHA256_RE.fullmatch(value.source_snapshot_sha256)
        or not isinstance(value.source_record_count, int)
        or not 1 <= value.source_record_count <= 100
        or not isinstance(value.source_first_id, str)
        or not value.source_first_id
        or not isinstance(value.source_last_id, str)
        or not value.source_last_id
    ):
        raise AretComponentPageImportError("preflight doit porter une identité, un hash et des bornes de page canoniques.")
    return value


def _require_projection(value: object, preflight: AretV1ComponentImportPreflight) -> AretV1ComponentEntityProjection:
    if not isinstance(value, AretV1ComponentEntityProjection):
        raise AretComponentPageImportError("projection doit être une projection component ARET V1.")
    if (
        value.target_identity != preflight.target_identity
        or value.request_id != preflight.request_id
        or value.preflight_id != preflight.preflight_id
        or value.source_snapshot_sha256 != preflight.source_snapshot_sha256
        or value.entity_type_id != "component"
        or value.entity_type_registration_required is not True
        or value.projection_state != "PROJECTED_NOT_WRITABLE"
        or len(value.drafts) != preflight.source_record_count
    ):
        raise AretComponentPageImportError("projection doit rester exactement liée au préflight et non écrivable.")
    source_ids = tuple(_require_draft(draft, preflight.source_snapshot_sha256) for draft in value.drafts)
    if source_ids[0] != preflight.source_first_id or source_ids[-1] != preflight.source_last_id:
        raise AretComponentPageImportError("Les bornes source de projection doivent correspondre au préflight.")
    if len(set(source_ids)) != len(source_ids):
        raise AretComponentPageImportError("La projection ne doit pas contenir deux fois le même component source.")
    return value


def _require_draft(value: object, source_hash: str) -> str:
    if not isinstance(value, AretV1EntityDraft):
        raise AretComponentPageImportError("projection contient un brouillon d’entité invalide.")
    if value.entity_type_id != "component" or not isinstance(value.metadata, dict):
        raise AretComponentPageImportError("brouillon d’entité component invalide.")
    source = value.metadata.get("source")
    if not isinstance(source, dict) or (
        source.get("domain_pack"),
        source.get("legacy_table"),
        source.get("source_snapshot_sha256"),
    ) != ("aret-v1", "component", source_hash):
        raise AretComponentPageImportError("brouillon sans métadonnées de source ARET V1 vérifiées.")
    source_id = source.get("source_id")
    if not isinstance(source_id, str) or not source_id or value.target_identifier != f"aret-component--{source_id}":
        raise AretComponentPageImportError("brouillon sans identifiant component cible déterministe.")
    return source_id


def _require_component_schema(
    value: object,
    preflight: AretV1ComponentImportPreflight,
) -> AretV1ComponentSchemaConformance:
    if not isinstance(value, AretV1ComponentSchemaConformance):
        raise AretComponentPageImportError("component_schema doit être une conformité component ARET V1.")
    if (
        value.source_snapshot_sha256 != preflight.source_snapshot_sha256
        or value.columns != _COMPONENT_COLUMNS
        or value.source_access_mode != "SQLITE_READ_ONLY_COMPONENT_SCHEMA"
        or value.conformance_state != "COMPONENT_SCHEMA_CONFORMANT"
    ):
        raise AretComponentPageImportError("component_schema doit rester conforme, read-only et liée au snapshot du préflight.")
    return value


def _require_store(value: object, preflight: AretV1ComponentImportPreflight) -> MemoryStore:
    if not isinstance(value, MemoryStore) or value.identity != preflight.target_identity:
        raise AretComponentPageImportError("target_store doit être le store VERA explicitement lié au préflight.")
    return value


def _is_exact_prior_batch(store: MemoryStore, authorization_id: str) -> bool:
    return store.connection.execute("SELECT 1 FROM import_batch WHERE id = ?", (authorization_id,)).fetchone() is not None


def _target_series_state(store: MemoryStore, preflight: AretV1ComponentImportPreflight) -> str:
    type_row = store.connection.execute(
        "SELECT label, description, schema_json FROM entity_type WHERE id = 'component'"
    ).fetchone()
    matching_count = store.connection.execute(
        "SELECT COUNT(*) FROM import_batch WHERE source_system = ? AND source_snapshot_sha256 = ? "
        "AND mapping_id = ? AND target_type_id = 'component'",
        (_SOURCE_SYSTEM, preflight.source_snapshot_sha256, _MAPPING_ID),
    ).fetchone()[0]
    other_series_count = store.connection.execute(
        "SELECT COUNT(*) FROM import_batch WHERE source_system = ? AND mapping_id = ? AND target_type_id = 'component' "
        "AND source_snapshot_sha256 <> ?",
        (_SOURCE_SYSTEM, _MAPPING_ID, preflight.source_snapshot_sha256),
    ).fetchone()[0]
    if type_row is None:
        if matching_count or other_series_count:
            raise AretComponentPageImportError("Le ledger component est incohérent : un batch référence un type absent.")
        return "INITIAL_EMPTY_TARGET_REQUIRED"
    if (
        str(type_row[0]) != "Component"
        or str(type_row[1]) != _TYPE_DESCRIPTION
        or str(type_row[2]) != canonical_json(_TYPE_SCHEMA)
        or other_series_count
        or not matching_count
    ):
        raise AretComponentPageImportError("Le type component existant n’est pas une série ARET V1 compatible et non fusionnelle.")
    return "MATCHING_PRIOR_SERIES_REQUIRED"


def authorize_aret_v1_component_page_import(
    *,
    preflight: AretV1ComponentImportPreflight,
    projection: AretV1ComponentEntityProjection,
    component_schema: AretV1ComponentSchemaConformance,
    target_store: MemoryStore,
    authorization_id: str,
    authorized_by: str,
) -> AretV1ComponentPageImportAuthorization:
    """Create one explicit, no-effect authorization after all read-only page bindings are verified."""
    checked_preflight = _require_preflight(preflight)
    _require_projection(projection, checked_preflight)
    _require_component_schema(component_schema, checked_preflight)
    store = _require_store(target_store, checked_preflight)
    return AretV1ComponentPageImportAuthorization(
        target_identity=checked_preflight.target_identity,
        request_id=checked_preflight.request_id,
        preflight_id=checked_preflight.preflight_id,
        source_snapshot_sha256=checked_preflight.source_snapshot_sha256,
        source_record_count=checked_preflight.source_record_count,
        source_first_id=checked_preflight.source_first_id,
        source_last_id=checked_preflight.source_last_id,
        authorization_id=_require_identifier(authorization_id, "authorization_id"),
        authorized_by=_require_actor(authorized_by, "authorized_by"),
        target_series_state=_target_series_state(store, checked_preflight),
    )


def _require_authorization(
    value: object,
    preflight: AretV1ComponentImportPreflight,
) -> AretV1ComponentPageImportAuthorization:
    if not isinstance(value, AretV1ComponentPageImportAuthorization):
        raise AretComponentPageImportError("authorization doit être une autorisation explicite de page M4-A.")
    if (
        value.target_identity != preflight.target_identity
        or value.request_id != preflight.request_id
        or value.preflight_id != preflight.preflight_id
        or value.source_snapshot_sha256 != preflight.source_snapshot_sha256
        or value.source_record_count != preflight.source_record_count
        or value.source_first_id != preflight.source_first_id
        or value.source_last_id != preflight.source_last_id
        or value.target_series_state not in {"INITIAL_EMPTY_TARGET_REQUIRED", "MATCHING_PRIOR_SERIES_REQUIRED"}
        or value.collision_policy != "REJECT_EXISTING_TARGET"
        or value.merge_policy != "FORBID"
        or value.promotion_policy != "FORBID"
        or value.authorization_state != "EXPLICIT_PAGE_IMPORT_ALLOWED"
    ):
        raise AretComponentPageImportError("authorization doit rester liée à une page, sans fusion ni promotion.")
    _require_identifier(value.authorization_id, "authorization.authorization_id")
    _require_actor(value.authorized_by, "authorization.authorized_by")
    return value


def import_authorized_aret_v1_component_page(
    *,
    authorization: AretV1ComponentPageImportAuthorization,
    preflight: AretV1ComponentImportPreflight,
    projection: AretV1ComponentEntityProjection,
    component_schema: AretV1ComponentSchemaConformance,
    target_store: MemoryStore,
) -> AretV1AuthorizedComponentPageImportResult:
    """Commit one bound page through the generic ledger; no source read, direct SQL write, proof or promotion occurs."""
    checked_preflight = _require_preflight(preflight)
    checked_projection = _require_projection(projection, checked_preflight)
    _require_component_schema(component_schema, checked_preflight)
    checked_authorization = _require_authorization(authorization, checked_preflight)
    store = _require_store(target_store, checked_preflight)
    if not _is_exact_prior_batch(store, checked_authorization.authorization_id):
        current_state = _target_series_state(store, checked_preflight)
        if current_state != checked_authorization.target_series_state:
            raise AretComponentPageImportError("La série cible a changé entre l’autorisation et l’écriture de la page.")

    entities = tuple(
        ImportEntityInput(
            identifier=draft.target_identifier,
            source_identifier=_require_draft(draft, checked_preflight.source_snapshot_sha256),
            title=draft.title,
            description=draft.description,
            metadata=draft.metadata,
        )
        for draft in checked_projection.drafts
    )
    try:
        result = ImportBatchService(store).commit_entity_import_batch(
            EntityImportBatchInput(
                batch_id=checked_authorization.authorization_id,
                source_system=_SOURCE_SYSTEM,
                source_snapshot_sha256=checked_preflight.source_snapshot_sha256,
                mapping_id=_MAPPING_ID,
                target_type_id="component",
                target_type_label="Component",
                target_type_description=_TYPE_DESCRIPTION,
                target_type_schema=_TYPE_SCHEMA,
                actor=checked_authorization.authorized_by,
                entities=entities,
            )
        )
    except ImportBatchError as exc:
        raise AretComponentPageImportError("Le ledger Core a refusé ou rollbacké la page component autorisée.") from exc
    return AretV1AuthorizedComponentPageImportResult(
        target_identity=store.identity,
        request_id=checked_authorization.request_id,
        preflight_id=checked_authorization.preflight_id,
        authorization_id=checked_authorization.authorization_id,
        source_snapshot_sha256=checked_authorization.source_snapshot_sha256,
        imported_entity_count=len(result.entities),
        entities=result.entities,
        was_already_imported=result.was_already_committed,
    )
