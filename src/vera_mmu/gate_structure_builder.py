"""Preview and confirm atomic admission-gate structures from exact existing endpoints.

The preview also carries the distinction §33 requires a gate to show — technical validation,
simple observation, semantic appreciation — for each endpoint it is about to bind, together with
the one consequence that matters: whether a gate built this way could ever found a proof. It is
reported before the gate exists rather than discovered afterwards at promotion, and it is derived
from the stored evidence types by `evidence_classes`, not decided here.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable

from .evidence_classes import SEMANTIC_APPRECIATION, describe, reason as class_reason
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
    endpoints: tuple[tuple[str, str, str, bool], ...]
    can_create_proof: bool
    proof_reason: str
    snapshot_hash: str
    preview_hash: str

    def as_dict(self) -> dict[str, object]:
        return {
            "format": "vera-gate-structure-draft/v1",
            "gate_id": self.gate_id,
            "work_item_id": self.work_item_id,
            "primary_evidence_id": self.primary_evidence_id,
            "requirement_evidence_ids": list(self.requirement_evidence_ids),
            "endpoints": [
                {
                    "evidence_id": evidence_id,
                    "evidence_type": evidence_type,
                    "evidence_class": evidence_class,
                    "may_create_proof": may_create_proof,
                    "reason": class_reason(evidence_class),
                }
                for evidence_id, evidence_type, evidence_class, may_create_proof in self.endpoints
            ],
            "promotion": {"can_create_proof": self.can_create_proof, "proof_reason": self.proof_reason},
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
    endpoints: list[tuple[str, str, str, bool]] = []
    for evidence_id in evidence_ids:
        row = connection.execute("SELECT evidence_type FROM evidence WHERE id=?", (evidence_id,)).fetchone()
        if row is None:
            raise GateStructureBuilderError("Evidence de gate inconnue.")
        classified = describe(str(row["evidence_type"]))
        endpoints.append((evidence_id, str(classified["evidence_type"]), str(classified["evidence_class"]), bool(classified["may_create_proof"])))
    provable = [item[0] for item in endpoints if item[3]]
    can_create_proof = bool(provable)
    if can_create_proof:
        proof_reason = f"Au moins une exigence est une validation technique : {', '.join(provable)}."
    else:
        # Not a refusal: a sign-off gate is a legitimate thing to declare. It simply can never
        # found a promotion, and saying so here is more useful than discovering it at promotion.
        blocking = SEMANTIC_APPRECIATION if any(item[2] == SEMANTIC_APPRECIATION for item in endpoints) else endpoints[0][2]
        proof_reason = "Aucune validation technique parmi les exigences. " + class_reason(blocking)
    snapshot = {"gate_id": gate_id, "work_item_id": work_item_id, "evidence_ids": evidence_ids, "endpoints": endpoints, "gate_absent": True}
    snapshot_hash = sha256(canonical_json(snapshot).encode()).hexdigest()
    payload = {"gate_id": gate_id, "work_item_id": work_item_id, "primary_evidence_id": primary_evidence_id, "requirement_evidence_ids": requirements, "can_create_proof": can_create_proof, "snapshot_hash": snapshot_hash}
    return GateStructureDraftPreview(gate_id, work_item_id, primary_evidence_id, requirements, tuple(endpoints), can_create_proof, proof_reason, snapshot_hash, sha256(canonical_json(payload).encode()).hexdigest())


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
