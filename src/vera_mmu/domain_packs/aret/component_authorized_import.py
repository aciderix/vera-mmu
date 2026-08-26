from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from vera_mmu.entities import Entity, EntityCreateInput, EntityError, EntityService
from vera_mmu.identity import ProjectIdentity
from vera_mmu.store import MemoryStore

from .component_entity_projection import AretV1ComponentEntityProjection, AretV1EntityDraft
from .component_import_preflight import AretV1ComponentImportPreflight
from .component_target_collision import (
    AretComponentTargetCollisionError,
    AretV1ComponentTargetClearCheck,
    check_aret_v1_component_target_clear,
)


_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class AretComponentAuthorizedImportError(ValueError):
    """Raised when a bounded, explicitly authorized component import cannot remain fail-closed."""


@dataclass(frozen=True)
class AretV1ComponentImportAuthorization:
    """One caller-authorized, target-bound import permission that has no effect by itself."""

    target_identity: ProjectIdentity
    request_id: str
    preflight_id: str
    source_snapshot_sha256: str
    entity_type_id: str
    source_record_count: int
    authorization_id: str
    authorized_by: str
    collision_policy: str = "REJECT_EXISTING_TARGET"
    merge_policy: str = "FORBID"
    promotion_policy: str = "FORBID"
    authorization_state: str = "EXPLICIT_ONE_SHOT_IMPORT_ALLOWED"


@dataclass(frozen=True)
class AretV1AuthorizedComponentImportResult:
    """A completed bounded import; it creates entities only and never promotes them to proof."""

    target_identity: ProjectIdentity
    request_id: str
    preflight_id: str
    authorization_id: str
    source_snapshot_sha256: str
    imported_entity_count: int
    entities: tuple[Entity, ...]
    import_state: str = "IMPORTED_NO_PROMOTION"


def _require_identifier(value: object, label: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise AretComponentAuthorizedImportError(
            f"{label} doit contenir 3 à 128 caractères minuscules alphanumériques ou des tirets."
        )
    return value


def _require_actor(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\r" in value or "\n" in value:
        raise AretComponentAuthorizedImportError(f"{label} doit être une chaîne non vide sur une ligne.")
    return value.strip()


def _require_preflight(value: object) -> AretV1ComponentImportPreflight:
    if not isinstance(value, AretV1ComponentImportPreflight):
        raise AretComponentAuthorizedImportError("preflight doit être un préflight component ARET V1.")
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
        raise AretComponentAuthorizedImportError("preflight doit conserver toutes les politiques fail-closed M4.11.")
    if not isinstance(value.target_identity, ProjectIdentity) or not _SHA256_RE.fullmatch(value.source_snapshot_sha256):
        raise AretComponentAuthorizedImportError("preflight doit rester lié à une identité VERA et un hash source canoniques.")
    return value


def _require_projection(value: object, preflight: AretV1ComponentImportPreflight) -> AretV1ComponentEntityProjection:
    if not isinstance(value, AretV1ComponentEntityProjection):
        raise AretComponentAuthorizedImportError("projection doit être une projection component ARET V1.")
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
        raise AretComponentAuthorizedImportError("projection doit rester exactement liée au préflight et non écrivable.")
    source_ids = tuple(_require_draft(draft, preflight.source_snapshot_sha256) for draft in value.drafts)
    if source_ids[0] != preflight.source_first_id or source_ids[-1] != preflight.source_last_id:
        raise AretComponentAuthorizedImportError("Les bornes source de projection doivent correspondre au préflight.")
    return value


def _require_draft(value: object, source_hash: str) -> str:
    if not isinstance(value, AretV1EntityDraft):
        raise AretComponentAuthorizedImportError("projection contient un brouillon d’entité invalide.")
    if value.entity_type_id != "component" or not isinstance(value.metadata, dict):
        raise AretComponentAuthorizedImportError("brouillon d’entité component invalide.")
    source = value.metadata.get("source")
    if not isinstance(source, dict) or (
        source.get("domain_pack"),
        source.get("legacy_table"),
        source.get("source_snapshot_sha256"),
    ) != ("aret-v1", "component", source_hash):
        raise AretComponentAuthorizedImportError("brouillon sans métadonnées de source ARET V1 vérifiées.")
    source_id = source.get("source_id")
    if not isinstance(source_id, str) or not source_id or source_id not in value.target_identifier:
        raise AretComponentAuthorizedImportError("brouillon sans identifiant source cohérent.")
    return source_id


def _require_clear_check(value: object, preflight: AretV1ComponentImportPreflight) -> AretV1ComponentTargetClearCheck:
    if not isinstance(value, AretV1ComponentTargetClearCheck):
        raise AretComponentAuthorizedImportError("target_clear_check doit être le contrôle M4.13.")
    if (
        value.target_identity != preflight.target_identity
        or value.entity_type_id != "component"
        or value.entity_type_state != "ABSENT_REQUIRED"
        or value.checked_entity_count != preflight.source_record_count
        or value.clear_state != "TARGET_CLEAR_NOT_WRITABLE"
    ):
        raise AretComponentAuthorizedImportError("target_clear_check doit rester lié à la cible claire et au préflight.")
    return value


def authorize_aret_v1_component_import(
    *,
    preflight: AretV1ComponentImportPreflight,
    projection: AretV1ComponentEntityProjection,
    target_clear_check: AretV1ComponentTargetClearCheck,
    authorization_id: str,
    authorized_by: str,
) -> AretV1ComponentImportAuthorization:
    """Create one explicit no-effect authorization after every zero-write predecessor is verified."""
    checked_preflight = _require_preflight(preflight)
    _require_projection(projection, checked_preflight)
    _require_clear_check(target_clear_check, checked_preflight)
    return AretV1ComponentImportAuthorization(
        target_identity=checked_preflight.target_identity,
        request_id=checked_preflight.request_id,
        preflight_id=checked_preflight.preflight_id,
        source_snapshot_sha256=checked_preflight.source_snapshot_sha256,
        entity_type_id="component",
        source_record_count=checked_preflight.source_record_count,
        authorization_id=_require_identifier(authorization_id, "authorization_id"),
        authorized_by=_require_actor(authorized_by, "authorized_by"),
    )


def _require_authorization(
    value: object,
    preflight: AretV1ComponentImportPreflight,
) -> AretV1ComponentImportAuthorization:
    if not isinstance(value, AretV1ComponentImportAuthorization):
        raise AretComponentAuthorizedImportError("authorization doit être une autorisation M4.15 explicite.")
    if (
        value.target_identity != preflight.target_identity
        or value.request_id != preflight.request_id
        or value.preflight_id != preflight.preflight_id
        or value.source_snapshot_sha256 != preflight.source_snapshot_sha256
        or value.entity_type_id != "component"
        or value.source_record_count != preflight.source_record_count
        or value.collision_policy != "REJECT_EXISTING_TARGET"
        or value.merge_policy != "FORBID"
        or value.promotion_policy != "FORBID"
        or value.authorization_state != "EXPLICIT_ONE_SHOT_IMPORT_ALLOWED"
    ):
        raise AretComponentAuthorizedImportError("authorization doit rester explicitement liée et sans fusion ni promotion.")
    _require_identifier(value.authorization_id, "authorization.authorization_id")
    _require_actor(value.authorized_by, "authorization.authorized_by")
    return value


def import_authorized_aret_v1_component_entities(
    *,
    authorization: AretV1ComponentImportAuthorization,
    preflight: AretV1ComponentImportPreflight,
    projection: AretV1ComponentEntityProjection,
    target_clear_check: AretV1ComponentTargetClearCheck,
    target_store: MemoryStore,
) -> AretV1AuthorizedComponentImportResult:
    """Import one authorized projected page atomically after rechecking target collisions; no proof is created."""
    checked_preflight = _require_preflight(preflight)
    checked_projection = _require_projection(projection, checked_preflight)
    _require_clear_check(target_clear_check, checked_preflight)
    checked_authorization = _require_authorization(authorization, checked_preflight)
    if not isinstance(target_store, MemoryStore) or target_store.identity != checked_preflight.target_identity:
        raise AretComponentAuthorizedImportError("target_store doit être le store VERA explicitement lié à l’autorisation.")
    try:
        check_aret_v1_component_target_clear(projection=checked_projection, target_store=target_store)
    except AretComponentTargetCollisionError as exc:
        raise AretComponentAuthorizedImportError("La cible VERA n’est plus claire au moment de l’import autorisé.") from exc

    inputs = tuple(
        EntityCreateInput(
            identifier=draft.target_identifier,
            title=draft.title,
            description=draft.description,
            metadata=draft.metadata,
        )
        for draft in checked_projection.drafts
    )
    try:
        batch = EntityService(target_store).register_type_and_create_batch(
            "component",
            "Component",
            inputs,
            type_description="Generic component entities created through an explicitly authorized bounded import.",
            type_schema={"kind": "generic", "resource": "entity"},
            actor=checked_authorization.authorized_by,
        )
    except EntityError as exc:
        raise AretComponentAuthorizedImportError("Le batch Core de l’import autorisé a échoué et a été rollbacké.") from exc
    return AretV1AuthorizedComponentImportResult(
        target_identity=target_store.identity,
        request_id=checked_authorization.request_id,
        preflight_id=checked_authorization.preflight_id,
        authorization_id=checked_authorization.authorization_id,
        source_snapshot_sha256=checked_authorization.source_snapshot_sha256,
        imported_entity_count=len(batch.entities),
        entities=batch.entities,
    )
