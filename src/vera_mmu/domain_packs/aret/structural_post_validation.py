from __future__ import annotations

from dataclasses import dataclass

from vera_mmu.identity import ProjectIdentity
from vera_mmu.store import MemoryStore
from vera_mmu.symbols import SymbolService
from vera_mmu.work_items import WorkItemService

from .authorized_structural_import import AretV1AuthorizedStructuralImportResult
from .brick_projection import AretV1BrickProjection, AretV1WorkItemDraft
from .function_symbol_projection import AretV1FunctionSymbolProjection, AretV1SymbolDraft
from .structural_import_authorization import AretV1StructuralImportAuthorization


class AretStructuralPostValidationError(ValueError):
    """Raised when a committed authorized structural page cannot be read back exactly."""


@dataclass(frozen=True)
class AretV1StructuralPostValidation:
    """Read-only confirmation of one committed structural page without any extra system effect."""

    target_identity: ProjectIdentity
    authorization_id: str
    source_snapshot_sha256: str
    resource_kind: str
    validated_resource_count: int
    source_identifiers: tuple[str, ...]
    validation_state: str = "POST_VALIDATED_NO_PROMOTION"


def _require_authorization(value: object) -> AretV1StructuralImportAuthorization:
    if not isinstance(value, AretV1StructuralImportAuthorization):
        raise AretStructuralPostValidationError("authorization doit être une autorisation structurelle ARET V1.")
    if (
        value.legacy_table not in {"function_symbol", "brick"}
        or value.resource_kind not in {"SYMBOL", "WORK_ITEM"}
        or value.target_series_state != "INITIAL_EMPTY_RESOURCE_TARGET_REQUIRED"
        or value.collision_policy != "REJECT_EXISTING_TARGET"
        or value.merge_policy != "FORBID"
        or value.promotion_policy != "FORBID"
        or value.authorization_state != "EXPLICIT_STRUCTURAL_IMPORT_ALLOWED"
        or not isinstance(value.target_identity, ProjectIdentity)
        or not 1 <= value.source_record_count <= 100
    ):
        raise AretStructuralPostValidationError("authorization doit rester une permission structurelle non fusionnelle exacte.")
    return value


def _require_result(
    value: object, authorization: AretV1StructuralImportAuthorization
) -> AretV1AuthorizedStructuralImportResult:
    if not isinstance(value, AretV1AuthorizedStructuralImportResult):
        raise AretStructuralPostValidationError("import_result doit être un résultat structurel autorisé.")
    if (
        value.target_identity != authorization.target_identity
        or value.request_id != authorization.request_id
        or value.preflight_id != authorization.preflight_id
        or value.authorization_id != authorization.authorization_id
        or value.source_snapshot_sha256 != authorization.source_snapshot_sha256
        or value.resource_kind != authorization.resource_kind
        or value.imported_resource_count != authorization.source_record_count
        or len(value.resources) != authorization.source_record_count
        or value.import_state != "IMPORTED_NO_PROMOTION"
    ):
        raise AretStructuralPostValidationError("import_result doit rester lié à l’autorisation sans changement d’état.")
    return value


def _require_store(value: object, authorization: AretV1StructuralImportAuthorization) -> MemoryStore:
    if not isinstance(value, MemoryStore) or value.identity != authorization.target_identity:
        raise AretStructuralPostValidationError("target_store doit être le store VERA explicitement lié à l’autorisation.")
    return value


def _expected_symbol_drafts(
    value: object, authorization: AretV1StructuralImportAuthorization
) -> tuple[AretV1SymbolDraft, ...]:
    if not isinstance(value, AretV1FunctionSymbolProjection) or (
        value.target_identity != authorization.target_identity
        or value.request_id != authorization.request_id
        or value.source_snapshot_sha256 != authorization.source_snapshot_sha256
        or value.projection_state != "PROJECTED_NOT_WRITABLE"
        or len(value.drafts) != authorization.source_record_count
    ):
        raise AretStructuralPostValidationError("projection symbol doit rester liée exactement à l’autorisation.")
    return value.drafts


def _expected_work_item_drafts(
    value: object, authorization: AretV1StructuralImportAuthorization
) -> tuple[AretV1WorkItemDraft, ...]:
    if not isinstance(value, AretV1BrickProjection) or (
        value.target_identity != authorization.target_identity
        or value.request_id != authorization.request_id
        or value.source_snapshot_sha256 != authorization.source_snapshot_sha256
        or value.projection_state != "PROJECTED_NOT_WRITABLE"
        or len(value.drafts) != authorization.source_record_count
    ):
        raise AretStructuralPostValidationError("projection work item doit rester liée exactement à l’autorisation.")
    return value.drafts


def _source_identifier(draft: AretV1SymbolDraft | AretV1WorkItemDraft, authorization: AretV1StructuralImportAuthorization) -> str:
    source = draft.metadata.get("source") if isinstance(draft.metadata, dict) else None
    if not isinstance(source, dict) or (
        source.get("domain_pack"),
        source.get("legacy_table"),
        source.get("source_snapshot_sha256"),
    ) != ("aret-v1", authorization.legacy_table, authorization.source_snapshot_sha256):
        raise AretStructuralPostValidationError("draft sans provenance source structurelle vérifiée.")
    source_id = source.get("source_id")
    if not isinstance(source_id, str) or not source_id:
        raise AretStructuralPostValidationError("draft sans identifiant source canonique.")
    return source_id


def post_validate_authorized_aret_v1_structural_page(
    *,
    authorization: AretV1StructuralImportAuthorization,
    projection: AretV1FunctionSymbolProjection | AretV1BrickProjection,
    import_result: AretV1AuthorizedStructuralImportResult,
    target_store: MemoryStore,
) -> AretV1StructuralPostValidation:
    """Read the Core ledger and resources exactly; this function has no mutation capability."""
    checked_authorization = _require_authorization(authorization)
    _require_result(import_result, checked_authorization)
    store = _require_store(target_store, checked_authorization)
    if checked_authorization.resource_kind == "SYMBOL":
        drafts = _expected_symbol_drafts(projection, checked_authorization)
    else:
        drafts = _expected_work_item_drafts(projection, checked_authorization)
    expected = tuple(
        (_source_identifier(draft, checked_authorization), draft.target_identifier, draft) for draft in drafts
    )
    source_identifiers = tuple(item[0] for item in expected)
    if len(set(source_identifiers)) != len(source_identifiers):
        raise AretStructuralPostValidationError("projection ne peut pas répéter un identifiant source.")
    batch = store.connection.execute(
        "SELECT source_system, source_snapshot_sha256, mapping_id, resource_kind "
        "FROM resource_import_batch WHERE id = ?",
        (checked_authorization.authorization_id,),
    ).fetchone()
    if batch is None or tuple(batch) != (
        "aret-v1",
        checked_authorization.source_snapshot_sha256,
        checked_authorization.mapping_id,
        checked_authorization.resource_kind,
    ):
        raise AretStructuralPostValidationError("Le ledger ne contient pas le batch structurel autorisé exact.")
    links = tuple(
        (str(row["source_identifier"]), str(row["target_identifier"]))
        for row in store.connection.execute(
            "SELECT source_identifier, target_identifier FROM resource_import_batch_record WHERE batch_id = ? ORDER BY source_identifier",
            (checked_authorization.authorization_id,),
        )
    )
    expected_links = tuple(sorted((source_id, target_id) for source_id, target_id, _ in expected))
    if links != expected_links:
        raise AretStructuralPostValidationError("Les liens du ledger ne correspondent pas exactement à la projection autorisée.")
    for _, target_identifier, draft in expected:
        if checked_authorization.resource_kind == "SYMBOL":
            symbol = SymbolService(store).get(target_identifier)
            if (
                symbol.entity_id != draft.owner_entity_id
                or symbol.kind != draft.kind
                or symbol.path != draft.path
                or symbol.identifier != draft.identifier
                or symbol.signature != draft.signature
                or symbol.metadata != draft.metadata
            ):
                raise AretStructuralPostValidationError("Un symbol importé ne correspond pas exactement à son draft autorisé.")
        else:
            item = WorkItemService(store).get(target_identifier)
            if (
                item.type != draft.item_type
                or item.title != draft.title
                or item.description != draft.description
                or item.status != "PLANNED"
                or item.priority != draft.priority
                or item.parent_id is not None
                or item.assignee is not None
                or item.metadata != draft.metadata
            ):
                raise AretStructuralPostValidationError("Un work item importé ne correspond pas exactement à son draft autorisé.")
    return AretV1StructuralPostValidation(
        target_identity=store.identity,
        authorization_id=checked_authorization.authorization_id,
        source_snapshot_sha256=checked_authorization.source_snapshot_sha256,
        resource_kind=checked_authorization.resource_kind,
        validated_resource_count=len(expected),
        source_identifiers=source_identifiers,
    )
