from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from vera_mmu.import_batches import ImportBatchError, ImportBatchService, ImportKnowledgeInput, KnowledgeImportBatchInput, KnowledgeImportBatchResult
from vera_mmu.knowledge import KnowledgeService, KnowledgeType
from vera_mmu.identity import ProjectIdentity
from vera_mmu.store import MemoryStore

from .knowledge_projection import AretV1KnowledgeDraft, AretV1KnowledgeProjection
from .knowledge_reader import AretV1KnowledgeSourcePage


_SOURCE_SYSTEM = "aret-v1"
_MAPPING_ID = "aret-v1-knowledge-to-knowledge-v1"
_TARGET_TYPE_ID = "aret-legacy-knowledge"
_TARGET_TYPE_LABEL = "ARET legacy knowledge"
_TARGET_TYPE_DESCRIPTION = "Immutable imported ARET knowledge preserving legacy semantics as source metadata."
_SERIES_INITIAL = "INITIAL_EMPTY_TARGET_REQUIRED"
_SERIES_MATCHING = "MATCHING_PRIOR_SERIES_REQUIRED"


class AretKnowledgeImportPreparationError(ValueError):
    """Raised when a knowledge import preflight cannot bind one exact source page and projection."""


class AretKnowledgeTargetCollisionError(ValueError):
    """Raised when the target knowledge surface is not an empty or matching non-merge series."""


class AretKnowledgeImportAuthorizationError(ValueError):
    """Raised when a knowledge import lacks the exact target and source authorization."""


class AretAuthorizedKnowledgeImportError(ValueError):
    """Raised when an authorized knowledge page cannot commit atomically through the Core ledger."""


class AretKnowledgePostValidationError(ValueError):
    """Raised when an imported knowledge page cannot be read back exactly without further writes."""


@dataclass(frozen=True)
class AretV1KnowledgeImportPreflight:
    target_identity: ProjectIdentity
    request_id: str
    preflight_id: str
    confirmed_by: str
    source_snapshot_sha256: str
    source_record_count: int
    source_first_id: str
    source_last_id: str
    mapping_id: str = _MAPPING_ID
    target_type_id: str = _TARGET_TYPE_ID
    status_policy: str = "PRESERVE_LEGACY_STATUS_NO_PROMOTION"
    preflight_state: str = "PREFLIGHT_NOT_EXECUTABLE"


@dataclass(frozen=True)
class AretV1KnowledgeTargetClearCheck:
    target_identity: ProjectIdentity
    source_snapshot_sha256: str
    mapping_id: str
    checked_resource_count: int
    target_series_state: str
    clear_state: str = "TARGET_CLEAR_NOT_WRITABLE"


@dataclass(frozen=True)
class AretV1KnowledgeImportAuthorization:
    target_identity: ProjectIdentity
    request_id: str
    preflight_id: str
    authorization_id: str
    authorized_by: str
    source_snapshot_sha256: str
    source_record_count: int
    source_first_id: str
    source_last_id: str
    mapping_id: str
    target_type_id: str
    target_series_state: str
    collision_policy: str = "REJECT_EXISTING_TARGET"
    merge_policy: str = "FORBID"
    promotion_policy: str = "FORBID"
    authorization_state: str = "EXPLICIT_KNOWLEDGE_IMPORT_ALLOWED"


@dataclass(frozen=True)
class AretV1AuthorizedKnowledgeImportResult:
    target_identity: ProjectIdentity
    request_id: str
    preflight_id: str
    authorization_id: str
    source_snapshot_sha256: str
    resources: tuple[Any, ...]
    imported_resource_count: int
    import_state: str = "IMPORTED_NO_PROMOTION"
    was_already_imported: bool = False


@dataclass(frozen=True)
class AretV1KnowledgePostValidation:
    target_identity: ProjectIdentity
    authorization_id: str
    source_snapshot_sha256: str
    validated_resource_count: int
    source_identifiers: tuple[str, ...]
    validation_state: str = "POST_VALIDATED_NO_PROMOTION"


def _require_identifier(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 128 or not value.replace("-", "").isalnum() or not value[0].islower():
        raise AretKnowledgeImportPreparationError(f"{label} doit être un identifiant canonique borné.")
    return value


def _require_actor(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > 256:
        raise AretKnowledgeImportPreparationError(f"{label} doit être une chaîne canonique non vide.")
    return value


def _require_projection(value: object, identity: ProjectIdentity, request_id: str, source_hash: str) -> AretV1KnowledgeProjection:
    if not isinstance(value, AretV1KnowledgeProjection) or (
        value.target_identity != identity
        or value.request_id != request_id
        or value.source_snapshot_sha256 != source_hash
        or value.projection_state != "PROJECTED_NOT_WRITABLE"
        or not 1 <= len(value.drafts) <= 100
    ):
        raise AretKnowledgeImportPreparationError("projection knowledge doit être liée exactement au préflight.")
    source_ids = tuple(str(draft.metadata.get("source", {}).get("source_id", "")) for draft in value.drafts)
    targets = tuple(draft.target_identifier for draft in value.drafts)
    if not all(source_ids) or len(set(source_ids)) != len(source_ids) or len(set(targets)) != len(targets):
        raise AretKnowledgeImportPreparationError("projection knowledge porte des identifiants ambigus.")
    return value


def ensure_aret_v1_knowledge_target_type(*, target_store: MemoryStore, actor: str) -> KnowledgeType:
    """Create the single explicit target type once, or verify the immutable compatible type without importing data."""
    if not isinstance(target_store, MemoryStore):
        raise AretKnowledgeImportAuthorizationError("target_store knowledge invalide.")
    actor_value = _require_actor(actor, "actor")
    row = target_store.connection.execute(
        "SELECT id, label, description, created_at, created_by FROM knowledge_type WHERE id = ?",
        (_TARGET_TYPE_ID,),
    ).fetchone()
    if row is None:
        return KnowledgeService(target_store).register_type(
            _TARGET_TYPE_ID,
            _TARGET_TYPE_LABEL,
            description=_TARGET_TYPE_DESCRIPTION,
            actor=actor_value,
        )
    existing = KnowledgeType(
        id=str(row["id"]),
        label=str(row["label"]),
        description=str(row["description"]),
        created_at=str(row["created_at"]),
        created_by=str(row["created_by"]),
    )
    if existing.id != _TARGET_TYPE_ID or existing.label != _TARGET_TYPE_LABEL or existing.description != _TARGET_TYPE_DESCRIPTION:
        raise AretKnowledgeImportAuthorizationError("Le type cible knowledge existe avec un contrat incompatible.")
    return existing


def prepare_aret_v1_knowledge_import(
    *,
    target_identity: ProjectIdentity,
    source_page: AretV1KnowledgeSourcePage,
    projection: AretV1KnowledgeProjection,
    preflight_id: str,
    confirmed_by: str,
) -> AretV1KnowledgeImportPreflight:
    """Bind one observed page and pure projection into a non-writable knowledge preflight."""
    if not isinstance(target_identity, ProjectIdentity) or not isinstance(source_page, AretV1KnowledgeSourcePage):
        raise AretKnowledgeImportPreparationError("source_page ou target_identity knowledge invalide.")
    request_id = _require_identifier(projection.request_id, "request_id")
    checked = _require_projection(projection, target_identity, request_id, source_page.source_snapshot_sha256)
    records = source_page.records
    if not 1 <= len(records) <= 100:
        raise AretKnowledgeImportPreparationError("source_page knowledge doit contenir entre 1 et 100 records.")
    source_ids = tuple(record.source_id for record in records)
    projection_ids = tuple(str(draft.metadata["source"]["source_id"]) for draft in checked.drafts)
    if source_ids != projection_ids or source_ids != tuple(sorted(source_ids)):
        raise AretKnowledgeImportPreparationError("source_page et projection knowledge doivent partager le même ordre source exact.")
    return AretV1KnowledgeImportPreflight(
        target_identity=target_identity,
        request_id=request_id,
        preflight_id=_require_identifier(preflight_id, "preflight_id"),
        confirmed_by=_require_actor(confirmed_by, "confirmed_by"),
        source_snapshot_sha256=source_page.source_snapshot_sha256,
        source_record_count=len(records),
        source_first_id=source_ids[0],
        source_last_id=source_ids[-1],
    )


def _require_preflight(value: object) -> AretV1KnowledgeImportPreflight:
    if not isinstance(value, AretV1KnowledgeImportPreflight) or (
        value.mapping_id != _MAPPING_ID
        or value.target_type_id != _TARGET_TYPE_ID
        or value.status_policy != "PRESERVE_LEGACY_STATUS_NO_PROMOTION"
        or value.preflight_state != "PREFLIGHT_NOT_EXECUTABLE"
        or not 1 <= value.source_record_count <= 100
        or not isinstance(value.target_identity, ProjectIdentity)
    ):
        raise AretKnowledgeTargetCollisionError("preflight knowledge invalide ou non exécutable.")
    return value


def _series_state(store: MemoryStore, preflight: AretV1KnowledgeImportPreflight) -> str:
    resource_count = int(store.connection.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0])
    matching_batches = int(
        store.connection.execute(
            "SELECT COUNT(*) FROM knowledge_import_batch WHERE source_system = ? AND source_snapshot_sha256 = ? AND mapping_id = ?",
            (_SOURCE_SYSTEM, preflight.source_snapshot_sha256, preflight.mapping_id),
        ).fetchone()[0]
    )
    other_batches = int(
        store.connection.execute(
            "SELECT COUNT(*) FROM knowledge_import_batch WHERE source_system <> ? OR source_snapshot_sha256 <> ? OR mapping_id <> ?",
            (_SOURCE_SYSTEM, preflight.source_snapshot_sha256, preflight.mapping_id),
        ).fetchone()[0]
    )
    matching_resources = int(
        store.connection.execute(
            "SELECT COUNT(DISTINCT record.target_identifier) FROM knowledge_import_batch_record AS record "
            "JOIN knowledge_import_batch AS batch ON batch.id = record.batch_id "
            "WHERE batch.source_system = ? AND batch.source_snapshot_sha256 = ? AND batch.mapping_id = ?",
            (_SOURCE_SYSTEM, preflight.source_snapshot_sha256, preflight.mapping_id),
        ).fetchone()[0]
    )
    if resource_count == 0:
        if matching_batches or other_batches or matching_resources:
            raise AretKnowledgeTargetCollisionError("Le ledger knowledge est incohérent avec une cible vide.")
        return _SERIES_INITIAL
    if not matching_batches or other_batches or matching_resources != resource_count:
        raise AretKnowledgeTargetCollisionError("La cible knowledge ne correspond pas exactement à une série ARET V1 compatible.")
    return _SERIES_MATCHING


def check_aret_v1_knowledge_target_clear(
    *,
    preflight: AretV1KnowledgeImportPreflight,
    projection: AretV1KnowledgeProjection,
    target_store: MemoryStore,
) -> AretV1KnowledgeTargetClearCheck:
    """Read target facts only; no type registration, authorization, transaction or knowledge write occurs."""
    checked = _require_preflight(preflight)
    _require_projection(projection, checked.target_identity, checked.request_id, checked.source_snapshot_sha256)
    if not isinstance(target_store, MemoryStore) or target_store.identity != checked.target_identity:
        raise AretKnowledgeTargetCollisionError("target_store doit être la cible VERA liée au preflight knowledge.")
    return AretV1KnowledgeTargetClearCheck(
        target_identity=target_store.identity,
        source_snapshot_sha256=checked.source_snapshot_sha256,
        mapping_id=checked.mapping_id,
        checked_resource_count=checked.source_record_count,
        target_series_state=_series_state(target_store, checked),
    )


def _require_clear(
    value: object,
    preflight: AretV1KnowledgeImportPreflight,
    projection: AretV1KnowledgeProjection,
    target_store: MemoryStore,
) -> AretV1KnowledgeTargetClearCheck:
    expected = check_aret_v1_knowledge_target_clear(preflight=preflight, projection=projection, target_store=target_store)
    if not isinstance(value, AretV1KnowledgeTargetClearCheck) or value != expected or value.target_series_state not in {_SERIES_INITIAL, _SERIES_MATCHING}:
        raise AretKnowledgeImportAuthorizationError("clear_check knowledge doit être exact, courant et non écrivable.")
    return value


def authorize_aret_v1_knowledge_import(
    *,
    preflight: AretV1KnowledgeImportPreflight,
    projection: AretV1KnowledgeProjection,
    clear_check: AretV1KnowledgeTargetClearCheck,
    target_store: MemoryStore,
    authorization_id: str,
    authorized_by: str,
) -> AretV1KnowledgeImportAuthorization:
    """Produce one explicit non-merge/non-promotion authorization after exact read-only checks."""
    checked = _require_preflight(preflight)
    _require_projection(projection, checked.target_identity, checked.request_id, checked.source_snapshot_sha256)
    if not isinstance(target_store, MemoryStore) or target_store.identity != checked.target_identity:
        raise AretKnowledgeImportAuthorizationError("target_store knowledge invalide.")
    row = target_store.connection.execute("SELECT 1 FROM knowledge_type WHERE id = ?", (_TARGET_TYPE_ID,)).fetchone()
    if row is None:
        raise AretKnowledgeImportAuthorizationError("Le type cible knowledge explicite doit être créé avant autorisation.")
    clear = _require_clear(clear_check, checked, projection, target_store)
    return AretV1KnowledgeImportAuthorization(
        target_identity=checked.target_identity,
        request_id=checked.request_id,
        preflight_id=checked.preflight_id,
        authorization_id=_require_identifier(authorization_id, "authorization_id"),
        authorized_by=_require_actor(authorized_by, "authorized_by"),
        source_snapshot_sha256=checked.source_snapshot_sha256,
        source_record_count=checked.source_record_count,
        source_first_id=checked.source_first_id,
        source_last_id=checked.source_last_id,
        mapping_id=checked.mapping_id,
        target_type_id=checked.target_type_id,
        target_series_state=clear.target_series_state,
    )


def _require_authorization(value: object, preflight: AretV1KnowledgeImportPreflight) -> AretV1KnowledgeImportAuthorization:
    if not isinstance(value, AretV1KnowledgeImportAuthorization) or (
        value.target_identity != preflight.target_identity
        or value.request_id != preflight.request_id
        or value.preflight_id != preflight.preflight_id
        or value.source_snapshot_sha256 != preflight.source_snapshot_sha256
        or value.source_record_count != preflight.source_record_count
        or value.source_first_id != preflight.source_first_id
        or value.source_last_id != preflight.source_last_id
        or value.mapping_id != _MAPPING_ID
        or value.target_type_id != _TARGET_TYPE_ID
        or value.target_series_state not in {_SERIES_INITIAL, _SERIES_MATCHING}
        or value.collision_policy != "REJECT_EXISTING_TARGET"
        or value.merge_policy != "FORBID"
        or value.promotion_policy != "FORBID"
        or value.authorization_state != "EXPLICIT_KNOWLEDGE_IMPORT_ALLOWED"
    ):
        raise AretAuthorizedKnowledgeImportError("authorization knowledge invalide ou incompatible avec le preflight.")
    return value


def _inputs(projection: AretV1KnowledgeProjection) -> tuple[ImportKnowledgeInput, ...]:
    return tuple(
        ImportKnowledgeInput(
            identifier=draft.target_identifier,
            source_identifier=str(draft.metadata["source"]["source_id"]),
            payload={
                "type_id": draft.type_id,
                "status": draft.status,
                "title": draft.title,
                "content": draft.content,
                "metadata": draft.metadata,
            },
        )
        for draft in projection.drafts
    )


def import_authorized_aret_v1_knowledge_page(
    *,
    preflight: AretV1KnowledgeImportPreflight,
    projection: AretV1KnowledgeProjection,
    authorization: AretV1KnowledgeImportAuthorization,
    target_store: MemoryStore,
) -> AretV1AuthorizedKnowledgeImportResult:
    """Commit one authorized knowledge page through the generic Core 035 ledger only."""
    checked = _require_preflight(preflight)
    try:
        checked_projection = _require_projection(
            projection,
            checked.target_identity,
            checked.request_id,
            checked.source_snapshot_sha256,
        )
    except AretKnowledgeImportPreparationError as exc:
        raise AretAuthorizedKnowledgeImportError("La projection knowledge a dérivé ou n’est plus non écrivable.") from exc
    checked_authorization = _require_authorization(authorization, checked)
    if not isinstance(target_store, MemoryStore) or target_store.identity != checked.target_identity:
        raise AretAuthorizedKnowledgeImportError("target_store knowledge invalide.")
    service = ImportBatchService(target_store)
    if service.get_knowledge_import_batch(checked_authorization.authorization_id) is None:
        try:
            current = check_aret_v1_knowledge_target_clear(preflight=checked, projection=checked_projection, target_store=target_store)
        except AretKnowledgeTargetCollisionError as exc:
            raise AretAuthorizedKnowledgeImportError("La cible knowledge a dérivé ou n’est plus non fusionnelle.") from exc
        if current.target_series_state != checked_authorization.target_series_state:
            raise AretAuthorizedKnowledgeImportError("La série knowledge cible a changé entre autorisation et écriture.")
    try:
        result: KnowledgeImportBatchResult = service.commit_knowledge_import_batch(
            KnowledgeImportBatchInput(
                batch_id=checked_authorization.authorization_id,
                source_system=_SOURCE_SYSTEM,
                source_snapshot_sha256=checked_authorization.source_snapshot_sha256,
                mapping_id=checked_authorization.mapping_id,
                resources=_inputs(checked_projection),
                actor=checked_authorization.authorized_by,
                require_empty_target=(checked_authorization.target_series_state == _SERIES_INITIAL),
            )
        )
    except ImportBatchError as exc:
        raise AretAuthorizedKnowledgeImportError("Le batch knowledge autorisé a refusé ou rollbacké atomiquement.") from exc
    return AretV1AuthorizedKnowledgeImportResult(
        target_identity=target_store.identity,
        request_id=checked_authorization.request_id,
        preflight_id=checked_authorization.preflight_id,
        authorization_id=checked_authorization.authorization_id,
        source_snapshot_sha256=checked_authorization.source_snapshot_sha256,
        resources=result.resources,
        imported_resource_count=len(result.resources),
        was_already_imported=result.was_already_committed,
    )


def post_validate_authorized_aret_v1_knowledge_page(
    *,
    authorization: AretV1KnowledgeImportAuthorization,
    projection: AretV1KnowledgeProjection,
    import_result: AretV1AuthorizedKnowledgeImportResult,
    target_store: MemoryStore,
) -> AretV1KnowledgePostValidation:
    """Read back exactly one committed knowledge page without mutation, promotion or supersession writes."""
    if not isinstance(authorization, AretV1KnowledgeImportAuthorization) or authorization.authorization_state != "EXPLICIT_KNOWLEDGE_IMPORT_ALLOWED":
        raise AretKnowledgePostValidationError("authorization knowledge invalide.")
    projection_value = _require_projection(projection, authorization.target_identity, authorization.request_id, authorization.source_snapshot_sha256)
    if not isinstance(import_result, AretV1AuthorizedKnowledgeImportResult) or (
        import_result.target_identity != authorization.target_identity
        or import_result.request_id != authorization.request_id
        or import_result.preflight_id != authorization.preflight_id
        or import_result.authorization_id != authorization.authorization_id
        or import_result.source_snapshot_sha256 != authorization.source_snapshot_sha256
        or import_result.imported_resource_count != authorization.source_record_count
        or len(import_result.resources) != authorization.source_record_count
        or import_result.import_state != "IMPORTED_NO_PROMOTION"
    ):
        raise AretKnowledgePostValidationError("import_result knowledge invalide.")
    if not isinstance(target_store, MemoryStore) or target_store.identity != authorization.target_identity:
        raise AretKnowledgePostValidationError("target_store knowledge invalide.")
    batch = target_store.connection.execute(
        "SELECT source_system, source_snapshot_sha256, mapping_id FROM knowledge_import_batch WHERE id = ?",
        (authorization.authorization_id,),
    ).fetchone()
    if batch is None or tuple(batch) != (_SOURCE_SYSTEM, authorization.source_snapshot_sha256, authorization.mapping_id):
        raise AretKnowledgePostValidationError("Le ledger knowledge ne contient pas le batch autorisé exact.")
    expected_links = tuple(sorted((str(draft.metadata["source"]["source_id"]), draft.target_identifier) for draft in projection_value.drafts))
    links = tuple(
        (str(row["source_identifier"]), str(row["target_identifier"]))
        for row in target_store.connection.execute(
            "SELECT source_identifier, target_identifier FROM knowledge_import_batch_record WHERE batch_id = ? ORDER BY source_identifier",
            (authorization.authorization_id,),
        )
    )
    if links != expected_links:
        raise AretKnowledgePostValidationError("Les liens du ledger knowledge ne correspondent pas à la projection autorisée.")
    service = KnowledgeService(target_store)
    for draft in projection_value.drafts:
        resource = service.get(draft.target_identifier)
        if (
            resource.type_id != draft.type_id
            or resource.status != draft.status
            or resource.title != draft.title
            or resource.content != draft.content
            or resource.metadata != draft.metadata
        ):
            raise AretKnowledgePostValidationError("Une knowledge importée ne correspond pas exactement au draft autorisé.")
    return AretV1KnowledgePostValidation(
        target_identity=target_store.identity,
        authorization_id=authorization.authorization_id,
        source_snapshot_sha256=authorization.source_snapshot_sha256,
        validated_resource_count=len(projection_value.drafts),
        source_identifiers=tuple(item[0] for item in expected_links),
    )
