"""Preview and confirm immutable policies for already-declared admission gates."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from .gates import GATE_POLICY_MODES, GateError, GateService
from .identity import canonical_json
from .store import MemoryStore, StoreError


class GatePolicyBuilderError(StoreError):
    pass


@dataclass(frozen=True)
class GatePolicyDraftPreview:
    gate_id: str
    mode: str
    minimum_admissions: int | None
    requirements_hash: str
    preview_hash: str
    def as_dict(self) -> dict[str, object]:
        return {"format":"vera-gate-policy-draft/v1","gate_id":self.gate_id,"mode":self.mode,"minimum_admissions":self.minimum_admissions,"requirements_hash":self.requirements_hash,"preview_hash":self.preview_hash,"status":"PREVIEW"}


def preview_gate_policy_draft(store: MemoryStore, *, gate_id: str, mode: str, minimum_admissions: int | None) -> GatePolicyDraftPreview:
    if not isinstance(gate_id, str) or not gate_id or "/" in gate_id:
        raise GatePolicyBuilderError("Identifiant de gate invalide.")
    if mode not in GATE_POLICY_MODES:
        raise GatePolicyBuilderError("Mode de policy hors catalogue fermé.")
    requirements = GateService._requirements(store.connection, gate_id)
    if not requirements:
        raise GatePolicyBuilderError("Gate introuvable.")
    if mode in {"ALL", "ANY"} and minimum_admissions is not None:
        raise GatePolicyBuilderError("Seuil interdit pour ce mode.")
    if mode == "AT_LEAST" and (isinstance(minimum_admissions, bool) or not isinstance(minimum_admissions, int) or not 1 <= minimum_admissions <= len(requirements)):
        raise GatePolicyBuilderError("Seuil AT_LEAST hors borne.")
    try:
        GateService(store).get_policy(gate_id)
    except GateError:
        pass
    else:
        raise GatePolicyBuilderError("Policy déjà déclarée : preview refusé.")
    requirements_hash = sha256(canonical_json(requirements).encode()).hexdigest()
    payload = {"gate_id":gate_id,"mode":mode,"minimum_admissions":minimum_admissions,"requirements_hash":requirements_hash}
    return GatePolicyDraftPreview(gate_id, mode, minimum_admissions, requirements_hash, sha256(canonical_json(payload).encode()).hexdigest())


def apply_gate_policy_draft(store: MemoryStore, preview: GatePolicyDraftPreview, *, confirm: bool) -> dict[str, object]:
    if confirm is not True:
        raise GatePolicyBuilderError("Application de policy refusée sans confirmation explicite.")
    if not isinstance(preview, GatePolicyDraftPreview):
        raise GatePolicyBuilderError("Preview de policy invalide.")
    expected = preview_gate_policy_draft(store, gate_id=preview.gate_id, mode=preview.mode, minimum_admissions=preview.minimum_admissions)
    if expected != preview:
        raise GatePolicyBuilderError("Preview de policy altéré ou périmé.")
    try:
        policy = GateService(store).declare_policy(preview.gate_id, preview.mode, minimum_admissions=preview.minimum_admissions, actor="DASHBOARD")
    except GateError as exc:
        raise GatePolicyBuilderError("Déclaration de policy refusée.") from exc
    return {"status":"DECLARED","preview_hash":preview.preview_hash,"policy":{"gate_id":policy.gate_id,"mode":policy.mode,"minimum_admissions":policy.minimum_admissions}}
