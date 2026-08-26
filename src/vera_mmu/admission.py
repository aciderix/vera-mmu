from __future__ import annotations

from dataclasses import dataclass
import sqlite3

from .store import MemoryStore, StoreError


class AdmissionError(StoreError):
    pass


@dataclass(frozen=True)
class Admission:
    id: str
    evidence_id: str
    decision: str
    reason: str
    created_at: str
    created_by: str
    validation_id: str | None


class AdmissionService:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def decide(
        self,
        identifier: str,
        evidence_id: str,
        decision: str,
        reason: str,
        *,
        validation_id: str | None = None,
        actor: str = "system",
    ) -> Admission:
        if not isinstance(identifier, str) or not identifier or "/" in identifier:
            raise AdmissionError("Décision d’admission invalide.")
        if not isinstance(evidence_id, str) or not evidence_id or "/" in evidence_id:
            raise AdmissionError("Décision d’admission invalide.")
        if decision not in {"ADMITTED", "REJECTED"}:
            raise AdmissionError("Décision d’admission invalide.")
        if not isinstance(reason, str) or not reason.strip():
            raise AdmissionError("Décision d’admission invalide.")
        if not isinstance(actor, str) or not actor:
            raise AdmissionError("Décision d’admission invalide.")
        if validation_id is not None and (not isinstance(validation_id, str) or not validation_id or "/" in validation_id):
            raise AdmissionError("Binding de validation invalide.")
        try:
            with self.store.transaction() as connection:
                evidence = connection.execute("SELECT verdict FROM evidence WHERE id = ?", (evidence_id,)).fetchone()
                if evidence is None:
                    raise AdmissionError("Evidence inconnue.")
                strict = False
                if decision == "ADMITTED":
                    if evidence["verdict"] != "PASS":
                        raise AdmissionError("Seule une evidence PASS est admissible.")
                    policy = connection.execute("SELECT mode FROM admission_policy WHERE id = 1").fetchone()
                    if policy is None:
                        raise AdmissionError("Policy d’admission absente.")
                    strict = policy["mode"] == "VALIDATED_PASS_EVIDENCE"
                    if strict:
                        if validation_id is None:
                            raise AdmissionError("Binding de validation PASS requis par la policy d’admission.")
                        validation = connection.execute(
                            "SELECT evidence_id, verdict FROM validation_result WHERE id = ?", (validation_id,)
                        ).fetchone()
                        if validation is None or validation["evidence_id"] != evidence_id or validation["verdict"] != "PASS":
                            raise AdmissionError("Binding de validation PASS de la même evidence requis.")
                    elif validation_id is not None:
                        raise AdmissionError("Binding de validation interdit par la policy permissive.")
                elif validation_id is not None:
                    raise AdmissionError("Binding de validation réservé à une admission stricte.")
                connection.execute(
                    "INSERT INTO evidence_admission(id, evidence_id, decision, reason, created_at, created_by) "
                    "VALUES(?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
                    (identifier, evidence_id, decision, reason.strip(), actor),
                )
                if strict:
                    connection.execute(
                        "INSERT INTO admission_validation_binding(admission_id, validation_id, evidence_id, created_at, created_by) "
                        "VALUES(?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
                        (identifier, validation_id, evidence_id, actor),
                    )
                result = connection.execute(
                    "SELECT admission.id, admission.evidence_id, admission.decision, admission.reason, admission.created_at, "
                    "admission.created_by, binding.validation_id FROM evidence_admission AS admission "
                    "LEFT JOIN admission_validation_binding AS binding ON binding.admission_id = admission.id "
                    "WHERE admission.id = ?",
                    (identifier,),
                ).fetchone()
                self.store.append_audit(
                    connection,
                    "EVIDENCE_ADMISSION_DECIDED",
                    {
                        "admission_id": identifier,
                        "evidence_id": evidence_id,
                        "decision": decision,
                        "validation_id": validation_id,
                        "actor": actor,
                    },
                )
        except sqlite3.IntegrityError as exc:
            raise AdmissionError("Décision d’admission ou binding de validation invalide.") from exc
        if result is None:
            raise AdmissionError("Décision non lisible.")
        return Admission(
            str(result["id"]),
            str(result["evidence_id"]),
            str(result["decision"]),
            str(result["reason"]),
            str(result["created_at"]),
            str(result["created_by"]),
            None if result["validation_id"] is None else str(result["validation_id"]),
        )
