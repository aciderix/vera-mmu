from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from vera_mmu.addressing import AddressError, make_address
from vera_mmu.identity import ProjectIdentity

from .component_import_preflight import AretV1ComponentImportPreflight
from .component_reader import AretV1ComponentSourcePage, AretV1ComponentSourceRecord


_ENTITY_TYPE_ID = "component"
_TARGET_PREFIX = "aret-component--"


class AretComponentEntityProjectionError(ValueError):
    """Raised when raw ARET V1 component rows cannot form a safe non-writable entity projection."""


@dataclass(frozen=True)
class AretV1EntityDraft:
    """One projected generic-entity draft; it is not stored, admitted, or imported."""

    target_identifier: str
    target_address: str
    entity_type_id: str
    title: str
    description: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class AretV1ComponentEntityProjection:
    """Deterministic page-level component projection that remains non-writable by construction."""

    target_identity: ProjectIdentity
    request_id: str
    preflight_id: str
    source_snapshot_sha256: str
    entity_type_id: str
    entity_type_registration_required: bool
    drafts: tuple[AretV1EntityDraft, ...]
    projection_state: str = "PROJECTED_NOT_WRITABLE"


def _require_preflight(value: object) -> AretV1ComponentImportPreflight:
    if not isinstance(value, AretV1ComponentImportPreflight):
        raise AretComponentEntityProjectionError("preflight doit être un préflight component ARET V1.")
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
        raise AretComponentEntityProjectionError("preflight doit rester fail-closed et non exécutable.")
    if not isinstance(value.target_identity, ProjectIdentity):
        raise AretComponentEntityProjectionError("preflight doit porter une identité VERA cible explicite.")
    return value


def _require_page(value: object, preflight: AretV1ComponentImportPreflight) -> AretV1ComponentSourcePage:
    if not isinstance(value, AretV1ComponentSourcePage):
        raise AretComponentEntityProjectionError("source_page doit être une page component ARET V1 observée.")
    if (
        value.source_snapshot_sha256 != preflight.source_snapshot_sha256
        or value.read_state != "SOURCE_ROWS_OBSERVED"
        or len(value.records) != preflight.source_record_count
        or not value.records
        or value.records[0].source_id != preflight.source_first_id
        or value.records[-1].source_id != preflight.source_last_id
    ):
        raise AretComponentEntityProjectionError("source_page doit rester exactement liée au préflight et au snapshot source.")
    return value


def _require_core_text(value: object, label: str, *, maximum: int, allow_empty: bool) -> str:
    if not isinstance(value, str) or value != value.strip() or len(value) > maximum or not allow_empty and not value:
        raise AretComponentEntityProjectionError(f"{label} source doit être compatible avec le contrat textuel générique VERA.")
    return value


def _project_record(target_identity: ProjectIdentity, record: object, source_hash: str) -> AretV1EntityDraft:
    if not isinstance(record, AretV1ComponentSourceRecord):
        raise AretComponentEntityProjectionError("source_page contient un record component invalide.")
    source_id = _require_core_text(record.source_id, "source_id", maximum=220, allow_empty=False)
    title = _require_core_text(record.title, "title", maximum=1024, allow_empty=False)
    description = _require_core_text(record.description, "description", maximum=1_000_000, allow_empty=True)
    created_at = _require_core_text(record.created_at, "created_at", maximum=256, allow_empty=False)
    created_by = _require_core_text(record.created_by, "created_by", maximum=256, allow_empty=False)
    identifier = f"{_TARGET_PREFIX}{source_id}"
    try:
        address = make_address(target_identity.project_id, "entity", identifier)
    except AddressError as exc:
        raise AretComponentEntityProjectionError("source_id ne produit pas un identifiant d’entité VERA canonique.") from exc
    return AretV1EntityDraft(
        target_identifier=identifier,
        target_address=address,
        entity_type_id=_ENTITY_TYPE_ID,
        title=title,
        description=description,
        metadata={
            "source": {
                "domain_pack": "aret-v1",
                "legacy_table": "component",
                "source_id": source_id,
                "source_snapshot_sha256": source_hash,
                "source_created_at": created_at,
                "source_created_by": created_by,
            }
        },
    )


def project_aret_v1_component_entities(
    *,
    preflight: AretV1ComponentImportPreflight,
    source_page: AretV1ComponentSourcePage,
) -> AretV1ComponentEntityProjection:
    """Project one verified raw page only; no entity type, entity, evidence, audit, or import is written."""
    bound_preflight = _require_preflight(preflight)
    page = _require_page(source_page, bound_preflight)
    drafts = tuple(
        _project_record(bound_preflight.target_identity, record, bound_preflight.source_snapshot_sha256)
        for record in page.records
    )
    identifiers = tuple(draft.target_identifier for draft in drafts)
    if len(set(identifiers)) != len(identifiers):
        raise AretComponentEntityProjectionError("La projection produit des identifiants d’entité VERA dupliqués.")
    return AretV1ComponentEntityProjection(
        target_identity=bound_preflight.target_identity,
        request_id=bound_preflight.request_id,
        preflight_id=bound_preflight.preflight_id,
        source_snapshot_sha256=bound_preflight.source_snapshot_sha256,
        entity_type_id=_ENTITY_TYPE_ID,
        entity_type_registration_required=True,
        drafts=drafts,
    )
