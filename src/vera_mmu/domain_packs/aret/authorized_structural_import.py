from __future__ import annotations

from dataclasses import dataclass

from vera_mmu.import_batches import ImportBatchError, ImportBatchService, ImportResourceInput, ResourceImportBatchInput
from vera_mmu.store import MemoryStore
from vera_mmu.symbols import Symbol
from vera_mmu.work_items import WorkItem

from .brick_projection import AretV1BrickProjection, AretV1WorkItemDraft
from .function_symbol_projection import AretV1FunctionSymbolProjection, AretV1SymbolDraft
from .structural_import_authorization import AretV1StructuralImportAuthorization
from .structural_import_preflight import AretV1StructuralImportPreflight
from .structural_target_collision import AretStructuralTargetCollisionError, check_aret_v1_structural_target_clear


class AretAuthorizedStructuralImportError(ValueError):
    """Raised when an explicitly authorized structural page cannot commit atomically and fail-closed."""


@dataclass(frozen=True)
class AretV1AuthorizedStructuralImportResult:
    """The exact structural resources returned by one authorized Core ledger batch without promotion."""

    target_identity: object
    request_id: str
    preflight_id: str
    authorization_id: str
    source_snapshot_sha256: str
    resource_kind: str
    imported_resource_count: int
    resources: tuple[Symbol | WorkItem, ...]
    was_already_imported: bool
    import_state: str = "IMPORTED_NO_PROMOTION"


def _require_authorization(
    value: object, preflight: AretV1StructuralImportPreflight
) -> AretV1StructuralImportAuthorization:
    if not isinstance(value, AretV1StructuralImportAuthorization):
        raise AretAuthorizedStructuralImportError("authorization doit être une autorisation structurelle ARET V1.")
    if (
        value.target_identity != preflight.target_identity
        or value.request_id != preflight.request_id
        or value.preflight_id != preflight.preflight_id
        or value.source_snapshot_sha256 != preflight.source_snapshot_sha256
        or value.legacy_table != preflight.legacy_table
        or value.resource_kind != preflight.resource_kind
        or value.source_record_count != preflight.source_record_count
        or value.source_first_id != preflight.source_first_id
        or value.source_last_id != preflight.source_last_id
        or value.lifecycle_policy != preflight.lifecycle_policy
        or value.target_series_state not in {
            "INITIAL_EMPTY_RESOURCE_TARGET_REQUIRED",
            "MATCHING_PRIOR_SERIES_REQUIRED",
        }
        or value.collision_policy != "REJECT_EXISTING_TARGET"
        or value.merge_policy != "FORBID"
        or value.promotion_policy != "FORBID"
        or value.authorization_state != "EXPLICIT_STRUCTURAL_IMPORT_ALLOWED"
    ):
        raise AretAuthorizedStructuralImportError("authorization doit rester exactement liée au préflight sans fusion ni promotion.")
    expected_mapping = (
        "aret-v1-function-symbol-to-symbol-v1"
        if preflight.resource_kind == "SYMBOL"
        else "aret-v1-brick-to-work-item-v1"
    )
    if value.mapping_id != expected_mapping:
        raise AretAuthorizedStructuralImportError("authorization doit porter le mapping structurel fermé attendu.")
    return value


def _require_symbol_drafts(
    value: object, preflight: AretV1StructuralImportPreflight
) -> tuple[AretV1SymbolDraft, ...]:
    if not isinstance(value, AretV1FunctionSymbolProjection) or len(value.drafts) != preflight.source_record_count:
        raise AretAuthorizedStructuralImportError("projection symbol doit contenir exactement la page autorisée.")
    return value.drafts


def _require_work_item_drafts(
    value: object, preflight: AretV1StructuralImportPreflight
) -> tuple[AretV1WorkItemDraft, ...]:
    if not isinstance(value, AretV1BrickProjection) or len(value.drafts) != preflight.source_record_count:
        raise AretAuthorizedStructuralImportError("projection work item doit contenir exactement la page autorisée.")
    return value.drafts


def _resource_inputs(
    preflight: AretV1StructuralImportPreflight,
    projection: AretV1FunctionSymbolProjection | AretV1BrickProjection,
) -> tuple[ImportResourceInput, ...]:
    if preflight.resource_kind == "SYMBOL":
        drafts = _require_symbol_drafts(projection, preflight)
        return tuple(
            ImportResourceInput(
                identifier=draft.target_identifier,
                source_identifier=str(draft.metadata["source"]["source_id"]),
                payload={
                    "entity_id": draft.owner_entity_id,
                    "kind": draft.kind,
                    "path": draft.path,
                    "symbol_identifier": draft.identifier,
                    "signature": draft.signature,
                    "metadata": draft.metadata,
                },
            )
            for draft in drafts
        )
    drafts = _require_work_item_drafts(projection, preflight)
    return tuple(
        ImportResourceInput(
            identifier=draft.target_identifier,
            source_identifier=str(draft.metadata["source"]["source_id"]),
            payload={
                "item_type": draft.item_type,
                "title": draft.title,
                "description": draft.description,
                "priority": draft.priority,
                "parent_id": None,
                "assignee": None,
                "metadata": draft.metadata,
            },
        )
        for draft in drafts
    )


def import_authorized_aret_v1_structural_page(
    *,
    preflight: AretV1StructuralImportPreflight,
    projection: AretV1FunctionSymbolProjection | AretV1BrickProjection,
    authorization: AretV1StructuralImportAuthorization,
    target_store: MemoryStore,
) -> AretV1AuthorizedStructuralImportResult:
    """Commit one exact authorized structural page through the generic Core ledger only."""
    checked_authorization = _require_authorization(authorization, preflight)
    service = ImportBatchService(target_store)
    if service.get_resource_import_batch(checked_authorization.authorization_id) is None:
        try:
            current_clear = check_aret_v1_structural_target_clear(
                preflight=preflight,
                projection=projection,
                target_store=target_store,
            )
        except AretStructuralTargetCollisionError as exc:
            raise AretAuthorizedStructuralImportError("La cible structurelle a dérivé ou n’est plus non fusionnelle.") from exc
        if current_clear.target_series_state != checked_authorization.target_series_state:
            raise AretAuthorizedStructuralImportError(
                "La série structurelle cible a changé entre l’autorisation et l’écriture de la page."
            )
    inputs = _resource_inputs(preflight, projection)
    try:
        committed = service.commit_resource_import_batch(
            ResourceImportBatchInput(
                batch_id=checked_authorization.authorization_id,
                source_system="aret-v1",
                source_snapshot_sha256=checked_authorization.source_snapshot_sha256,
                mapping_id=checked_authorization.mapping_id,
                resource_kind=checked_authorization.resource_kind,
                resources=inputs,
                actor=checked_authorization.authorized_by,
                require_empty_target=(
                    checked_authorization.target_series_state == "INITIAL_EMPTY_RESOURCE_TARGET_REQUIRED"
                ),
            )
        )
    except ImportBatchError as exc:
        raise AretAuthorizedStructuralImportError("Le batch structurel autorisé a refusé ou rollbacké atomiquement.") from exc
    return AretV1AuthorizedStructuralImportResult(
        target_identity=checked_authorization.target_identity,
        request_id=checked_authorization.request_id,
        preflight_id=checked_authorization.preflight_id,
        authorization_id=checked_authorization.authorization_id,
        source_snapshot_sha256=checked_authorization.source_snapshot_sha256,
        resource_kind=committed.resource_kind,
        imported_resource_count=len(committed.resources),
        resources=committed.resources,
        was_already_imported=committed.was_already_committed,
    )
