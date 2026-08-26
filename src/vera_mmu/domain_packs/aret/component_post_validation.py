from __future__ import annotations

from dataclasses import dataclass

from vera_mmu.entities import EntityService
from vera_mmu.identity import ProjectIdentity
from vera_mmu.store import MemoryStore

from .component_entity_projection import AretV1ComponentEntityProjection, AretV1EntityDraft
from .component_page_import import (
    AretV1AuthorizedComponentPageImportResult,
    AretV1ComponentPageImportAuthorization,
)


_SOURCE_SYSTEM = "aret-v1"
_MAPPING_ID = "aret-v1-component-entity-v1"


class AretComponentPostValidationError(ValueError):
    """Raised when an authorized component-page commit cannot be read back exactly and fail-closed."""


@dataclass(frozen=True)
class AretV1ComponentPostValidation:
    """Read-only confirmation of one committed component page; it never produces evidence, proof or promotion."""

    target_identity: ProjectIdentity
    authorization_id: str
    source_snapshot_sha256: str
    validated_entity_count: int
    source_identifiers: tuple[str, ...]
    validation_state: str = "POST_VALIDATED_NO_PROMOTION"


def _require_projection(value: object, authorization: AretV1ComponentPageImportAuthorization) -> AretV1ComponentEntityProjection:
    if not isinstance(value, AretV1ComponentEntityProjection):
        raise AretComponentPostValidationError("projection doit être une projection component ARET V1.")
    if (
        value.target_identity != authorization.target_identity
        or value.request_id != authorization.request_id
        or value.preflight_id != authorization.preflight_id
        or value.source_snapshot_sha256 != authorization.source_snapshot_sha256
        or value.entity_type_id != "component"
        or value.projection_state != "PROJECTED_NOT_WRITABLE"
        or len(value.drafts) != authorization.source_record_count
    ):
        raise AretComponentPostValidationError("projection doit rester exactement liée à l’autorisation de page.")
    return value


def _require_authorization(value: object) -> AretV1ComponentPageImportAuthorization:
    if not isinstance(value, AretV1ComponentPageImportAuthorization):
        raise AretComponentPostValidationError("authorization doit être une autorisation explicite de page M4-A.")
    if (
        value.authorization_state != "EXPLICIT_PAGE_IMPORT_ALLOWED"
        or value.collision_policy != "REJECT_EXISTING_TARGET"
        or value.merge_policy != "FORBID"
        or value.promotion_policy != "FORBID"
        or value.source_record_count < 1
        or value.source_record_count > 100
    ):
        raise AretComponentPostValidationError("authorization doit rester non fusionnelle et sans promotion.")
    return value


def _require_result(
    value: object,
    authorization: AretV1ComponentPageImportAuthorization,
) -> AretV1AuthorizedComponentPageImportResult:
    if not isinstance(value, AretV1AuthorizedComponentPageImportResult):
        raise AretComponentPostValidationError("import_result doit être le résultat de l’import component autorisé.")
    if (
        value.target_identity != authorization.target_identity
        or value.request_id != authorization.request_id
        or value.preflight_id != authorization.preflight_id
        or value.authorization_id != authorization.authorization_id
        or value.source_snapshot_sha256 != authorization.source_snapshot_sha256
        or value.import_state != "IMPORTED_NO_PROMOTION"
        or value.imported_entity_count != authorization.source_record_count
        or len(value.entities) != authorization.source_record_count
    ):
        raise AretComponentPostValidationError("import_result doit rester exactement lié à l’autorisation et sans promotion.")
    return value


def _require_store(value: object, authorization: AretV1ComponentPageImportAuthorization) -> MemoryStore:
    if not isinstance(value, MemoryStore) or value.identity != authorization.target_identity:
        raise AretComponentPostValidationError("target_store doit être le store VERA explicitement lié à l’autorisation.")
    return value


def _source_identifier(draft: AretV1EntityDraft, snapshot: str) -> str:
    source = draft.metadata.get("source") if isinstance(draft.metadata, dict) else None
    if not isinstance(source, dict) or (
        source.get("domain_pack"),
        source.get("legacy_table"),
        source.get("source_snapshot_sha256"),
    ) != ("aret-v1", "component", snapshot):
        raise AretComponentPostValidationError("draft sans provenance component ARET V1 vérifiée.")
    source_id = source.get("source_id")
    if not isinstance(source_id, str) or not source_id or draft.target_identifier != f"aret-component--{source_id}":
        raise AretComponentPostValidationError("draft sans identifiant source/cible component déterministe.")
    return source_id


def post_validate_authorized_aret_v1_component_page(
    *,
    authorization: AretV1ComponentPageImportAuthorization,
    projection: AretV1ComponentEntityProjection,
    import_result: AretV1AuthorizedComponentPageImportResult,
    target_store: MemoryStore,
) -> AretV1ComponentPostValidation:
    """Read the committed generic ledger and entities exactly; this does not admit, prove, promote or mutate any record."""
    checked_authorization = _require_authorization(authorization)
    checked_projection = _require_projection(projection, checked_authorization)
    _require_result(import_result, checked_authorization)
    store = _require_store(target_store, checked_authorization)
    expected = tuple(
        (_source_identifier(draft, checked_authorization.source_snapshot_sha256), draft.target_identifier, draft)
        for draft in checked_projection.drafts
    )
    source_ids = tuple(item[0] for item in expected)
    if len(set(source_ids)) != len(source_ids):
        raise AretComponentPostValidationError("projection ne peut pas répéter un identifiant source.")
    batch = store.connection.execute(
        "SELECT source_system, source_snapshot_sha256, mapping_id, target_type_id "
        "FROM import_batch WHERE id = ?",
        (checked_authorization.authorization_id,),
    ).fetchone()
    if batch is None or tuple(batch) != (
        _SOURCE_SYSTEM,
        checked_authorization.source_snapshot_sha256,
        _MAPPING_ID,
        "component",
    ):
        raise AretComponentPostValidationError("Le ledger ne contient pas le batch component autorisé exact.")
    links = tuple(
        (str(row["source_identifier"]), str(row["entity_id"]))
        for row in store.connection.execute(
            "SELECT source_identifier, entity_id FROM import_batch_entity WHERE batch_id = ? ORDER BY source_identifier",
            (checked_authorization.authorization_id,),
        )
    )
    expected_links = tuple(sorted((source_id, entity_id) for source_id, entity_id, _ in expected))
    if links != expected_links:
        raise AretComponentPostValidationError("Les liens du ledger ne correspondent pas exactement à la projection autorisée.")
    entities = EntityService(store)
    for _, entity_id, draft in expected:
        entity = entities.get(entity_id)
        if (
            entity.type_id != "component"
            or entity.title != draft.title
            or entity.description != draft.description
            or entity.metadata != draft.metadata
        ):
            raise AretComponentPostValidationError("Une entité importée ne correspond pas exactement à son draft autorisé.")
    return AretV1ComponentPostValidation(
        target_identity=store.identity,
        authorization_id=checked_authorization.authorization_id,
        source_snapshot_sha256=checked_authorization.source_snapshot_sha256,
        validated_entity_count=len(expected),
        source_identifiers=source_ids,
    )
