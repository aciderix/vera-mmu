from __future__ import annotations

from dataclasses import dataclass

from vera_mmu.identity import ProjectIdentity
from vera_mmu.store import MemoryStore

from .component_entity_projection import AretV1ComponentEntityProjection, AretV1EntityDraft


class AretComponentTargetCollisionError(ValueError):
    """Raised when a non-writable ARET V1 component projection cannot target a clear VERA store."""


@dataclass(frozen=True)
class AretV1ComponentTargetClearCheck:
    """A read-only finding; this object neither registers a type nor creates an entity."""

    target_identity: ProjectIdentity
    entity_type_id: str
    entity_type_state: str
    checked_entity_count: int
    clear_state: str = "TARGET_CLEAR_NOT_WRITABLE"


def _require_projection(value: object) -> AretV1ComponentEntityProjection:
    if not isinstance(value, AretV1ComponentEntityProjection):
        raise AretComponentTargetCollisionError("projection doit être une projection component ARET V1.")
    if (
        value.entity_type_id,
        value.entity_type_registration_required,
        value.projection_state,
    ) != ("component", True, "PROJECTED_NOT_WRITABLE"):
        raise AretComponentTargetCollisionError("projection doit rester un brouillon component non écrivable.")
    if not isinstance(value.target_identity, ProjectIdentity) or not value.drafts or len(value.drafts) > 100:
        raise AretComponentTargetCollisionError("projection doit porter une identité VERA et 1 à 100 brouillons.")
    identifiers: list[str] = []
    for draft in value.drafts:
        if not isinstance(draft, AretV1EntityDraft) or not isinstance(draft.target_identifier, str) or not draft.target_identifier:
            raise AretComponentTargetCollisionError("projection contient un brouillon d’entité invalide.")
        identifiers.append(draft.target_identifier)
    if len(set(identifiers)) != len(identifiers):
        raise AretComponentTargetCollisionError("projection contient des identifiants d’entité VERA dupliqués.")
    return value


def _require_store(value: object, projection: AretV1ComponentEntityProjection) -> MemoryStore:
    if not isinstance(value, MemoryStore):
        raise AretComponentTargetCollisionError("target_store doit être un store VERA existant explicitement fourni.")
    if value.identity != projection.target_identity:
        raise AretComponentTargetCollisionError("target_store doit appartenir exactement à l’identité cible de la projection.")
    return value


def check_aret_v1_component_target_clear(
    *,
    projection: AretV1ComponentEntityProjection,
    target_store: MemoryStore,
) -> AretV1ComponentTargetClearCheck:
    """Read exact target conflicts only; no store mutation, transaction, audit, or import occurs."""
    drafts = _require_projection(projection)
    store = _require_store(target_store, drafts)
    type_row = store.connection.execute(
        "SELECT 1 FROM entity_type WHERE id = ?",
        (drafts.entity_type_id,),
    ).fetchone()
    if type_row is not None:
        raise AretComponentTargetCollisionError("Le type d’entité cible component existe déjà : le préflight interdit toute fusion.")

    identifiers = tuple(draft.target_identifier for draft in drafts.drafts)
    placeholders = ", ".join("?" for _ in identifiers)
    collision_rows = store.connection.execute(
        f"SELECT id FROM entity WHERE id IN ({placeholders}) ORDER BY id",
        identifiers,
    ).fetchall()
    if collision_rows:
        raise AretComponentTargetCollisionError("Au moins un identifiant d’entité cible existe déjà : le préflight interdit toute fusion.")

    return AretV1ComponentTargetClearCheck(
        target_identity=store.identity,
        entity_type_id=drafts.entity_type_id,
        entity_type_state="ABSENT_REQUIRED",
        checked_entity_count=len(identifiers),
    )
