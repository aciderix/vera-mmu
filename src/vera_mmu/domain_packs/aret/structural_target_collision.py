from __future__ import annotations

from dataclasses import dataclass

from vera_mmu.identity import ProjectIdentity
from vera_mmu.store import MemoryStore

from .brick_projection import AretV1BrickProjection, AretV1WorkItemDraft
from .function_symbol_projection import AretV1FunctionSymbolProjection, AretV1SymbolDraft
from .structural_import_preflight import AretV1StructuralImportPreflight


class AretStructuralTargetCollisionError(ValueError):
    """Raised when a structural projection cannot target a strictly clear VERA resource surface."""


@dataclass(frozen=True)
class AretV1StructuralTargetClearCheck:
    """A read-only non-merge finding; it neither authorizes nor imports any structural resource."""

    target_identity: ProjectIdentity
    resource_kind: str
    checked_resource_count: int
    checked_parent_entity_count: int
    target_series_state: str
    lifecycle_state: str
    clear_state: str = "TARGET_CLEAR_NOT_WRITABLE"


def _require_preflight(value: object) -> AretV1StructuralImportPreflight:
    if not isinstance(value, AretV1StructuralImportPreflight):
        raise AretStructuralTargetCollisionError("preflight doit être un préflight structurel ARET V1.")
    expected_resource = "symbol" if value.legacy_table == "function_symbol" else "work_item"
    expected_kind = "SYMBOL" if value.legacy_table == "function_symbol" else "WORK_ITEM"
    expected_lifecycle = "NOT_APPLICABLE" if value.legacy_table == "function_symbol" else "PRESERVE_LEGACY_STATE_AS_METADATA"
    if (
        value.legacy_table not in {"function_symbol", "brick"}
        or value.vera_resource != expected_resource
        or value.resource_kind != expected_kind
        or value.lifecycle_policy != expected_lifecycle
        or value.collision_policy != "REJECT_EXISTING_TARGET"
        or value.merge_policy != "FORBID"
        or value.promotion_policy != "FORBID"
        or value.write_policy != "FORBID"
        or value.rollback_requirement != "REQUIRED_BEFORE_WRITE"
        or value.audit_requirement != "REQUIRED_BEFORE_WRITE"
        or value.provenance_requirement != "REQUIRED_BEFORE_WRITE"
        or value.preflight_state != "PREFLIGHT_NOT_EXECUTABLE"
        or not isinstance(value.target_identity, ProjectIdentity)
        or not 1 <= value.source_record_count <= 100
    ):
        raise AretStructuralTargetCollisionError("preflight structurel doit rester non exécutable et fail-closed.")
    return value


def _require_store(value: object, preflight: AretV1StructuralImportPreflight) -> MemoryStore:
    if not isinstance(value, MemoryStore) or value.identity != preflight.target_identity:
        raise AretStructuralTargetCollisionError("target_store doit être le store VERA explicitement lié au préflight.")
    return value


def _require_symbol_projection(
    value: object, preflight: AretV1StructuralImportPreflight
) -> tuple[AretV1SymbolDraft, ...]:
    if not isinstance(value, AretV1FunctionSymbolProjection) or (
        value.target_identity != preflight.target_identity
        or value.request_id != preflight.request_id
        or value.source_snapshot_sha256 != preflight.source_snapshot_sha256
        or value.projection_state != "PROJECTED_NOT_WRITABLE"
        or len(value.drafts) != preflight.source_record_count
    ):
        raise AretStructuralTargetCollisionError("projection symbol doit rester liée au préflight et non écrivable.")
    source_ids: list[str] = []
    target_ids: list[str] = []
    for draft in value.drafts:
        if not isinstance(draft, AretV1SymbolDraft) or (
            draft.kind != "FUNCTION"
            or not isinstance(draft.target_identifier, str)
            or not isinstance(draft.owner_entity_id, str)
            or not draft.target_identifier
            or not draft.owner_entity_id
            or not isinstance(draft.metadata, dict)
        ):
            raise AretStructuralTargetCollisionError("projection symbol contient un brouillon invalide.")
        source = draft.metadata.get("source")
        if not isinstance(source, dict) or (
            source.get("domain_pack"), source.get("legacy_table"), source.get("source_snapshot_sha256")
        ) != ("aret-v1", "function_symbol", preflight.source_snapshot_sha256):
            raise AretStructuralTargetCollisionError("brouillon symbol sans provenance ARET liée au préflight.")
        source_id = source.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            raise AretStructuralTargetCollisionError("brouillon symbol sans source_id canonique.")
        source_ids.append(source_id)
        target_ids.append(draft.target_identifier)
    if (
        len(set(source_ids)) != len(source_ids)
        or len(set(target_ids)) != len(target_ids)
        or source_ids[0] != preflight.source_first_id
        or source_ids[-1] != preflight.source_last_id
    ):
        raise AretStructuralTargetCollisionError("projection symbol porte des IDs source ou cible ambigus.")
    return value.drafts


def _require_work_item_projection(
    value: object, preflight: AretV1StructuralImportPreflight
) -> tuple[AretV1WorkItemDraft, ...]:
    if not isinstance(value, AretV1BrickProjection) or (
        value.target_identity != preflight.target_identity
        or value.request_id != preflight.request_id
        or value.source_snapshot_sha256 != preflight.source_snapshot_sha256
        or value.projection_state != "PROJECTED_NOT_WRITABLE"
        or len(value.drafts) != preflight.source_record_count
    ):
        raise AretStructuralTargetCollisionError("projection work item doit rester liée au préflight et non écrivable.")
    source_ids: list[str] = []
    target_ids: list[str] = []
    for draft in value.drafts:
        if not isinstance(draft, AretV1WorkItemDraft) or (
            draft.item_type != "WORK_ITEM"
            or not isinstance(draft.target_identifier, str)
            or not draft.target_identifier
            or not isinstance(draft.metadata, dict)
        ):
            raise AretStructuralTargetCollisionError("projection work item contient un brouillon invalide.")
        source = draft.metadata.get("source")
        if not isinstance(source, dict) or (
            source.get("domain_pack"), source.get("legacy_table"), source.get("source_snapshot_sha256")
        ) != ("aret-v1", "brick", preflight.source_snapshot_sha256):
            raise AretStructuralTargetCollisionError("brouillon work item sans provenance ARET liée au préflight.")
        source_id = source.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            raise AretStructuralTargetCollisionError("brouillon work item sans source_id canonique.")
        source_ids.append(source_id)
        target_ids.append(draft.target_identifier)
    if (
        len(set(source_ids)) != len(source_ids)
        or len(set(target_ids)) != len(target_ids)
        or source_ids[0] != preflight.source_first_id
        or source_ids[-1] != preflight.source_last_id
    ):
        raise AretStructuralTargetCollisionError("projection work item porte des IDs source ou cible ambigus.")
    return value.drafts


def _require_existing_entities(store: MemoryStore, entity_ids: tuple[str, ...]) -> None:
    if not entity_ids:
        return
    placeholders = ", ".join("?" for _ in entity_ids)
    count = store.connection.execute(
        f"SELECT COUNT(*) FROM entity WHERE id IN ({placeholders})", entity_ids
    ).fetchone()[0]
    if int(count) != len(entity_ids):
        raise AretStructuralTargetCollisionError("Un parent component VERA requis est absent : le préflight interdit l’import.")


def _target_series_state(
    store: MemoryStore,
    *,
    resource_table: str,
    resource_kind: str,
    mapping_id: str,
    source_snapshot_sha256: str,
) -> str:
    resource_count = int(store.connection.execute(f"SELECT COUNT(*) FROM {resource_table}").fetchone()[0])
    matching_batch_count = int(
        store.connection.execute(
            "SELECT COUNT(*) FROM resource_import_batch WHERE source_system = 'aret-v1' "
            "AND source_snapshot_sha256 = ? AND mapping_id = ? AND resource_kind = ?",
            (source_snapshot_sha256, mapping_id, resource_kind),
        ).fetchone()[0]
    )
    other_series_count = int(
        store.connection.execute(
            "SELECT COUNT(*) FROM resource_import_batch WHERE resource_kind = ? "
            "AND (source_system <> 'aret-v1' OR source_snapshot_sha256 <> ? OR mapping_id <> ?)",
            (resource_kind, source_snapshot_sha256, mapping_id),
        ).fetchone()[0]
    )
    matching_resource_count = int(
        store.connection.execute(
            "SELECT COUNT(DISTINCT record.target_identifier) "
            "FROM resource_import_batch_record AS record "
            "JOIN resource_import_batch AS batch ON batch.id = record.batch_id "
            "WHERE batch.source_system = 'aret-v1' AND batch.source_snapshot_sha256 = ? "
            "AND batch.mapping_id = ? AND batch.resource_kind = ?",
            (source_snapshot_sha256, mapping_id, resource_kind),
        ).fetchone()[0]
    )
    if resource_count == 0:
        if matching_batch_count or other_series_count or matching_resource_count:
            raise AretStructuralTargetCollisionError("Le ledger structurel est incohérent : une série référence une cible vide.")
        return "INITIAL_EMPTY_RESOURCE_TARGET_REQUIRED"
    if not matching_batch_count or other_series_count or matching_resource_count != resource_count:
        raise AretStructuralTargetCollisionError(
            "La surface ressource cible ne correspond pas exactement à une série ARET V1 compatible et non fusionnelle."
        )
    return "MATCHING_PRIOR_SERIES_REQUIRED"


def check_aret_v1_structural_target_clear(
    *,
    preflight: AretV1StructuralImportPreflight,
    projection: AretV1FunctionSymbolProjection | AretV1BrickProjection,
    target_store: MemoryStore,
) -> AretV1StructuralTargetClearCheck:
    """Read exact target conflicts only; no authorization, audit, transaction or resource creation occurs."""
    checked_preflight = _require_preflight(preflight)
    store = _require_store(target_store, checked_preflight)
    if checked_preflight.legacy_table == "function_symbol":
        drafts = _require_symbol_projection(projection, checked_preflight)
        parents = tuple(sorted({draft.owner_entity_id for draft in drafts}))
        _require_existing_entities(store, parents)
        resource_kind, lifecycle_state = "SYMBOL", "NOT_APPLICABLE"
        target_series_state = _target_series_state(
            store,
            resource_table="symbol",
            resource_kind=resource_kind,
            mapping_id="aret-v1-function-symbol-to-symbol-v1",
            source_snapshot_sha256=checked_preflight.source_snapshot_sha256,
        )
    else:
        drafts = _require_work_item_projection(projection, checked_preflight)
        component_ids = tuple(
            sorted(
                {
                    f"aret-component--{draft.metadata['source']['component_id']}"
                    for draft in drafts
                    if draft.metadata["source"].get("component_id") is not None
                }
            )
        )
        _require_existing_entities(store, component_ids)
        resource_kind, lifecycle_state = "WORK_ITEM", "DEFERRED_NOT_EXECUTABLE"
        target_series_state = _target_series_state(
            store,
            resource_table="work_item",
            resource_kind=resource_kind,
            mapping_id="aret-v1-brick-to-work-item-v1",
            source_snapshot_sha256=checked_preflight.source_snapshot_sha256,
        )
    return AretV1StructuralTargetClearCheck(
        target_identity=store.identity,
        resource_kind=resource_kind,
        checked_resource_count=len(drafts),
        checked_parent_entity_count=len(parents) if checked_preflight.legacy_table == "function_symbol" else len(component_ids),
        target_series_state=target_series_state,
        lifecycle_state=lifecycle_state,
    )
