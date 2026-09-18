"""Reading a declared gate exactly as §33 displays it — step 10 of the eighteen-step journey.

§33's screen names a gate, the capability behind it, its requirements one by one, and two lines
under « Promotion » : can this gate be satisfied, and can it create a proof. Everything here is
**derived** from what the Core already holds; nothing is declared twice.

**The capability is derived, not re-declared.** `admission_gate` links a work item to evidence,
and an evidence carries its execution, which carries its capability. So the « Capability » line of
§33 is read through that chain rather than asked of whoever builds the gate — a second declaration
would be a second thing to keep true.

**The two promotion lines say different things, and neither is decorative.** A gate is satisfiable
when its policy's threshold can still be met by its requirements. It is proof-capable only when at
least one of them is a technical validation, because that is the only class `ProofService.promote`
accepts. A gate made only of appreciations is not refused — a human sign-off gate is a legitimate
thing to want — but it is reported as never able to found a proof, which is the honest answer
rather than a refusal that would forbid a real use.
"""
from __future__ import annotations

from dataclasses import dataclass
import sqlite3

from .evidence_classes import (
    SEMANTIC_APPRECIATION,
    SIMPLE_OBSERVATION,
    TECHNICAL_VALIDATION,
    classify,
    describe,
    reason as class_reason,
)
from .gates import GateError, GateService
from .store import MemoryStore, StoreError


GATE_REPORT_FORMAT = "vera-gate-report/v1"


class GateReportError(StoreError):
    """Raised when a gate cannot be reported because the Core holds no such gate."""


@dataclass(frozen=True)
class GateRequirementView:
    """One requirement of a gate, with the class §33 asks to be shown."""

    evidence_id: str
    evidence_type: str
    evidence_class: str
    verdict: str
    admission: str
    primary: bool
    satisfied: bool
    may_create_proof: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "evidence_id": self.evidence_id,
            "evidence_type": self.evidence_type,
            "evidence_class": self.evidence_class,
            "verdict": self.verdict,
            "admission": self.admission,
            "primary": self.primary,
            "satisfied": self.satisfied,
            "may_create_proof": self.may_create_proof,
            "reason": class_reason(self.evidence_class),
        }


def report_gate(store: MemoryStore, gate_id: str) -> dict[str, object]:
    """Report one declared gate as §33 displays it. Writes nothing."""
    if not isinstance(store, MemoryStore):
        raise GateReportError("Lecture de gate impossible : store invalide.")
    if not isinstance(gate_id, str) or not gate_id or "/" in gate_id:
        raise GateReportError("Identifiant de gate invalide.")
    connection = store.connection
    gate = connection.execute(
        "SELECT id, work_item_id, evidence_id FROM admission_gate WHERE id = ?", (gate_id,)
    ).fetchone()
    if gate is None:
        raise GateReportError(f"Gate `{gate_id}` introuvable.")
    primary_evidence_id = str(gate["evidence_id"])

    requirements = [
        _requirement(connection, evidence_id, primary=evidence_id == primary_evidence_id)
        for evidence_id in GateService(store)._requirements(connection, gate_id)
    ]
    evaluation = GateService(store).evaluate(gate_id)
    try:
        policy = GateService(store).get_policy(gate_id)
        policy_view: dict[str, object] = {
            "status": "DECLARED",
            "mode": policy.mode,
            "minimum_admissions": policy.minimum_admissions,
        }
    except GateError:
        # An undeclared policy is reported as such. The engine evaluates an absent policy as
        # `ALL`, but writing "ALL" here would report a decision nobody took.
        policy_view = {"status": "NOT_DECLARED", "mode": None, "minimum_admissions": None}

    proof_capable = [item for item in requirements if item.may_create_proof]
    by_class = {
        name: [item.evidence_id for item in requirements if item.evidence_class == name]
        for name in (TECHNICAL_VALIDATION, SIMPLE_OBSERVATION, SEMANTIC_APPRECIATION)
    }
    return {
        "format": GATE_REPORT_FORMAT,
        "gate_id": gate_id,
        "work_item_id": str(gate["work_item_id"]),
        "capability": _capability(connection, primary_evidence_id),
        "requirements": [item.as_dict() for item in requirements],
        "classes": by_class,
        "policy": policy_view,
        "evaluation": {
            "status": evaluation.status,
            "mode": evaluation.mode,
            "admitted_count": evaluation.admitted_count,
            "required_count": evaluation.required_count,
            "minimum_admissions": evaluation.minimum_admissions,
        },
        "promotion": _promotion(evaluation, proof_capable, by_class),
        "mutation": "NONE",
    }


def _promotion(evaluation: object, proof_capable: list[GateRequirementView], by_class: dict[str, list[str]]) -> dict[str, object]:
    """The two lines §33 shows under « Promotion », each with the reason behind it."""
    satisfied = getattr(evaluation, "status", "FAIL") == "PASS"
    if proof_capable:
        proof_reason = (
            "Au moins une exigence est une validation technique : une promotion peut s’appuyer sur "
            f"{', '.join(item.evidence_id for item in proof_capable)}."
        )
    elif by_class[SEMANTIC_APPRECIATION]:
        proof_reason = (
            "Aucune validation technique : cette gate ne repose que sur des appréciations et des "
            "observations. " + class_reason(SEMANTIC_APPRECIATION)
        )
    else:
        proof_reason = "Aucune validation technique : " + class_reason(SIMPLE_OBSERVATION)
    return {
        "can_satisfy_gate": satisfied,
        "can_create_proof": bool(proof_capable),
        "satisfaction_reason": (
            "Les admissions atteignent le seuil de la policy."
            if satisfied
            else f"{getattr(evaluation, 'admitted_count', 0)} admission(s) sur "
            f"{getattr(evaluation, 'minimum_admissions', 0)} exigée(s)."
        ),
        "proof_reason": proof_reason,
    }


def _requirement(connection: sqlite3.Connection, evidence_id: str, *, primary: bool) -> GateRequirementView:
    row = connection.execute(
        "SELECT evidence_type, verdict FROM evidence WHERE id = ?", (evidence_id,)
    ).fetchone()
    if row is None:
        raise GateReportError(f"Evidence `{evidence_id}` exigée par la gate est introuvable.")
    admission = connection.execute(
        "SELECT decision FROM evidence_admission WHERE evidence_id = ?", (evidence_id,)
    ).fetchone()
    decision = "NOT_DECIDED" if admission is None else str(admission["decision"])
    evidence_type = str(row["evidence_type"])
    classified = describe(evidence_type)
    return GateRequirementView(
        evidence_id=evidence_id,
        evidence_type=evidence_type,
        evidence_class=classify(evidence_type),
        verdict=str(row["verdict"]),
        admission=decision,
        primary=primary,
        satisfied=decision == "ADMITTED",
        may_create_proof=bool(classified["may_create_proof"]),
    )


def _capability(connection: sqlite3.Connection, evidence_id: str) -> dict[str, object]:
    """Read the capability behind a gate through evidence → execution, or report its absence."""
    row = connection.execute(
        "SELECT execution.capability_id FROM evidence "
        "JOIN execution ON execution.id = evidence.execution_id WHERE evidence.id = ?",
        (evidence_id,),
    ).fetchone()
    if row is None:
        return {"status": "NOT_OBSERVABLE", "capability_id": None}
    return {"status": "DERIVED", "capability_id": str(row["capability_id"])}
