"""Preview and confirm atomic admission-gate structures from exact existing endpoints."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable

from .gates import GateError, GateService
from .identity import canonical_json
from .store import MemoryStore, StoreError


class GateStructureBuilderError(StoreError):
    pass


@dataclass(frozen=True)
class GateStructureDraftPreview:
    gate_id: str
    work_item_id: str
    primary_evidence_id: str
    requirement_evidence_ids: tuple[str, ...]
    snapshot_hash: str
    preview_hash: str

    def as_dict(self) -> dict[str, object]:
        return {
            "format": "vera-gate-structure-draft/v1",
            "gate_id": self.gate_id,
            "work_item_id": self.work_item_id,
            "primary_evidence_id": self.primary_evidence_id,
            "requirement_evidence_ids": list(self.requirement_evidence_ids),
            "snapshot_hash": self.snapshot_hash,
            "preview_hash": self.preview_hash,
            "status": "PREVIEW",
        }


def _identifier(value: object, name: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "/" in value:
        raise GateStructureBuilderError(f"{name} invalide.")
    return value


def _requirements(value: Iterable[object]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise GateStructureBuilderError("Exigences de gate invalides.")
    values = tuple(_identifier(item, "Evidence requise") for item in value)
    if len(values) != len(set(values)):
        raise GateStructureBuilderError("Exigences de gate dupliquées.")
    return values


def preview_gate_structure_draft(
    store: MemoryStore,
    *,
    gate_id: str,
    work_item_id: str,
    primary_evidence_id: str,
    requirement_evidence_ids: Iterable[str],
) -> GateStructureDraftPreview:
    gate_id = _identifier(gate_id, "Identifiant de gate")
    work_item_id = _identifier(work_item_id, "Identifiant de work item")
    primary_evidence_id = _identifier(primary_evidence_id, "Evidence principale")
    requirements = _requirements(requirement_evidence_ids)
    if primary_evidence_id in requirements:
        raise GateStructureBuilderError("Evidence principale déjà exigée.")
    connection = store.connection
    if connection.execute("SELECT 1 FROM admission_gate WHERE id=?", (gate_id,)).fetchone() is not None:
        raise GateStructureBuilderError("Gate déjà déclarée : preview refusé.")
    if connection.execute("SELECT 1 FROM work_item WHERE id=?", (work_item_id,)).fetchone() is None:
        raise GateStructureBuilderError("Work item inconnu.")
    evidence_ids = (primary_evidence_id, *requirements)
    if any(connection.execute("SELECT 1 FROM evidence WHERE id=?", (evidence_id,)).fetchone() is None for evidence_id in evidence_ids):
        raise GateStructureBuilderError("Evidence de gate inconnue.")
    snapshot = {"gate_id": gate_id, "work_item_id": work_item_id, "evidence_ids": evidence_ids, "gate_absent": True}
    snapshot_hash = sha256(canonical_json(snapshot).encode()).hexdigest()
    payload = {"gate_id": gate_id, "work_item_id": work_item_id, "primary_evidence_id": primary_evidence_id, "requirement_evidence_ids": requirements, "snapshot_hash": snapshot_hash}
    return GateStructureDraftPreview(gate_id, work_item_id, primary_evidence_id, requirements, snapshot_hash, sha256(canonical_json(payload).encode()).hexdigest())


def apply_gate_structure_draft(store: MemoryStore, preview: GateStructureDraftPreview, *, confirm: bool) -> dict[str, object]:
    if confirm is not True:
        raise GateStructureBuilderError("Création de gate refusée sans confirmation explicite.")
    if not isinstance(preview, GateStructureDraftPreview):
        raise GateStructureBuilderError("Preview de structure Gate invalide.")
    expected = preview_gate_structure_draft(
        store,
        gate_id=preview.gate_id,
        work_item_id=preview.work_item_id,
        primary_evidence_id=preview.primary_evidence_id,
        requirement_evidence_ids=preview.requirement_evidence_ids,
    )
    if expected != preview:
        raise GateStructureBuilderError("Preview de structure Gate altéré ou périmé.")
    try:
        GateService(store).declare_with_requirements(
            preview.gate_id,
            preview.work_item_id,
            preview.primary_evidence_id,
            preview.requirement_evidence_ids,
            actor="DASHBOARD",
        )
    except GateError as exc:
        raise GateStructureBuilderError("Déclaration de structure Gate refusée.") from exc
    return {"status": "DECLARED", "preview_hash": preview.preview_hash, "gate": {"gate_id": preview.gate_id, "work_item_id": preview.work_item_id, "primary_evidence_id": preview.primary_evidence_id, "requirement_evidence_ids": list(preview.requirement_evidence_ids)}}
