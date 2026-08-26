from __future__ import annotations

from dataclasses import dataclass
import re

from vera_mmu.identity import ProjectIdentity
from vera_mmu.store import MemoryStore

from .brick_projection import AretV1BrickProjection
from .function_symbol_projection import AretV1FunctionSymbolProjection
from .structural_import_preflight import AretV1StructuralImportPreflight
from .structural_target_collision import (
    AretStructuralTargetCollisionError,
    AretV1StructuralTargetClearCheck,
    check_aret_v1_structural_target_clear,
)


_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,127}$")


class AretStructuralImportAuthorizationError(ValueError):
    """Raised when a structural import permission is not explicitly and safely bound."""


@dataclass(frozen=True)
class AretV1StructuralImportAuthorization:
    """One explicit no-effect permission for a bounded structural page; it is not an import result."""

    target_identity: ProjectIdentity
    request_id: str
    preflight_id: str
    source_snapshot_sha256: str
    legacy_table: str
    resource_kind: str
    mapping_id: str
    source_record_count: int
    source_first_id: str
    source_last_id: str
    authorization_id: str
    authorized_by: str
    target_series_state: str
    lifecycle_policy: str
    collision_policy: str = "REJECT_EXISTING_TARGET"
    merge_policy: str = "FORBID"
    promotion_policy: str = "FORBID"
    authorization_state: str = "EXPLICIT_STRUCTURAL_IMPORT_ALLOWED"


def _require_identifier(value: object, label: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise AretStructuralImportAuthorizationError(f"{label} doit être un identifiant canonique borné.")
    return value


def _require_actor(value: object) -> str:
    if not isinstance(value, str) or not value.strip() or "\r" in value or "\n" in value:
        raise AretStructuralImportAuthorizationError("authorized_by doit être une chaîne non vide sur une ligne.")
    return value.strip()


def _mapping_id(preflight: AretV1StructuralImportPreflight) -> str:
    if preflight.legacy_table == "function_symbol" and preflight.resource_kind == "SYMBOL":
        return "aret-v1-function-symbol-to-symbol-v1"
    if preflight.legacy_table == "brick" and preflight.resource_kind == "WORK_ITEM":
        return "aret-v1-brick-to-work-item-v1"
    raise AretStructuralImportAuthorizationError("Le préflight ne correspond à aucun mapping structurel autorisable.")


def _require_clear_check(
    value: object, expected: AretV1StructuralTargetClearCheck, preflight: AretV1StructuralImportPreflight
) -> AretV1StructuralTargetClearCheck:
    if not isinstance(value, AretV1StructuralTargetClearCheck) or value != expected or (
        value.target_identity != preflight.target_identity
        or value.resource_kind != preflight.resource_kind
        or value.checked_resource_count != preflight.source_record_count
        or value.target_series_state not in {
            "INITIAL_EMPTY_RESOURCE_TARGET_REQUIRED",
            "MATCHING_PRIOR_SERIES_REQUIRED",
        }
        or value.clear_state != "TARGET_CLEAR_NOT_WRITABLE"
    ):
        raise AretStructuralImportAuthorizationError("clear_check doit être le contrôle de collision exact, courant et non écrivable.")
    return value


def authorize_aret_v1_structural_import(
    *,
    preflight: AretV1StructuralImportPreflight,
    projection: AretV1FunctionSymbolProjection | AretV1BrickProjection,
    clear_check: AretV1StructuralTargetClearCheck,
    target_store: MemoryStore,
    authorization_id: str,
    authorized_by: str,
) -> AretV1StructuralImportAuthorization:
    """Issue one explicit permission only after rechecking the bound clear target; no resource is created."""
    if not isinstance(preflight, AretV1StructuralImportPreflight):
        raise AretStructuralImportAuthorizationError("preflight doit être un préflight structurel ARET V1.")
    try:
        current_clear = check_aret_v1_structural_target_clear(
            preflight=preflight,
            projection=projection,
            target_store=target_store,
        )
    except AretStructuralTargetCollisionError as exc:
        raise AretStructuralImportAuthorizationError("Le binding projection/cible doit rester conforme et sans collision.") from exc
    _require_clear_check(clear_check, current_clear, preflight)
    mapping_id = _mapping_id(preflight)
    return AretV1StructuralImportAuthorization(
        target_identity=preflight.target_identity,
        request_id=preflight.request_id,
        preflight_id=preflight.preflight_id,
        source_snapshot_sha256=preflight.source_snapshot_sha256,
        legacy_table=preflight.legacy_table,
        resource_kind=preflight.resource_kind,
        mapping_id=mapping_id,
        source_record_count=preflight.source_record_count,
        source_first_id=preflight.source_first_id,
        source_last_id=preflight.source_last_id,
        authorization_id=_require_identifier(authorization_id, "authorization_id"),
        authorized_by=_require_actor(authorized_by),
        target_series_state=current_clear.target_series_state,
        lifecycle_policy=preflight.lifecycle_policy,
    )
