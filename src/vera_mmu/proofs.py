from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
import sqlite3

from .evidence_classes import classify, may_create_proof, reason as evidence_class_reason
from .identity import canonical_json
from .store import MemoryStore, StoreError


class ProofError(StoreError):
    pass


@dataclass(frozen=True)
class KnowledgeProof:
    id: str
    knowledge_id: str
    evidence_id: str
    admission_id: str
    status: str
    hmac_required: bool
    hmac_digest: str | None
    created_at: str
    created_by: str


class ProofService:
    def __init__(self, store: MemoryStore, *, hmac_secret: bytes | None = None) -> None:
        self.store = store
        self.hmac_secret = hmac_secret

    def promote(
        self,
        identifier: str,
        knowledge_id: str,
        evidence_id: str,
        admission_id: str,
        *,
        actor: str = "system",
    ) -> KnowledgeProof:
        values = (identifier, knowledge_id, evidence_id, admission_id, actor)
        if not all(isinstance(value, str) and value and "/" not in value for value in values):
            raise ProofError("Identifiant de preuve invalide.")
        try:
            with self.store.transaction() as connection:
                policy = connection.execute(
                    "SELECT algorithm, hmac_required FROM proof_policy WHERE singleton=1"
                ).fetchone()
                if policy is None or policy["algorithm"] != "HMAC_SHA256":
                    raise ProofError("Policy de preuve explicite requise.")
                hmac_required = bool(policy["hmac_required"])
                if hmac_required and (not isinstance(self.hmac_secret, bytes) or not self.hmac_secret):
                    raise ProofError("Secret HMAC requis pour cette policy.")
                if not hmac_required and self.hmac_secret is not None:
                    raise ProofError("Secret HMAC interdit lorsque la policy ne le requiert pas.")
                if connection.execute("SELECT 1 FROM knowledge WHERE id=?", (knowledge_id,)).fetchone() is None:
                    raise ProofError("Knowledge inconnue.")
                evidence = connection.execute(
                    "SELECT evidence_type, verdict, content_json, content_hash FROM evidence WHERE id=?", (evidence_id,)
                ).fetchone()
                admission = connection.execute(
                    "SELECT evidence_id, decision FROM evidence_admission WHERE id=?", (admission_id,)
                ).fetchone()
                if (
                    evidence is None
                    or evidence["verdict"] != "PASS"
                    or admission is None
                    or admission["evidence_id"] != evidence_id
                    or admission["decision"] != "ADMITTED"
                ):
                    raise ProofError("Evidence non admissible pour promotion.")
                # §33: a gate may legitimately require an observation or an appreciation, but
                # neither can found a proof. Admitting one and promoting it would launder an
                # opinion into a verified fact (I004, I006).
                evidence_type = str(evidence["evidence_type"])
                if not may_create_proof(evidence_type):
                    raise ProofError(
                        f"Promotion refusée : `{evidence_type}` est une {classify(evidence_type)}. "
                        + evidence_class_reason(classify(evidence_type))
                    )
                try:
                    content = json.loads(str(evidence["content_json"]))
                except (TypeError, ValueError) as exc:
                    raise ProofError("Evidence non canonique pour promotion.") from exc
                if not isinstance(content, dict):
                    raise ProofError("Evidence non canonique pour promotion.")
                canonical_content = canonical_json(content)
                if hashlib.sha256(canonical_content.encode()).hexdigest() != str(evidence["content_hash"]):
                    raise ProofError("Hash de contenu evidence incohérent.")
                digest = None
                if hmac_required:
                    envelope = canonical_json(
                        {
                            "knowledge_id": knowledge_id,
                            "evidence_id": evidence_id,
                            "admission_id": admission_id,
                            "verdict": str(evidence["verdict"]),
                            "content_hash": str(evidence["content_hash"]),
                            "content": content,
                        }
                    )
                    digest = hmac.new(self.hmac_secret, envelope.encode(), hashlib.sha256).hexdigest()
                connection.execute(
                    "INSERT INTO knowledge_proof(id,knowledge_id,evidence_id,admission_id,status,hmac_required,hmac_digest,created_at,created_by) "
                    "VALUES(?,?,?,?, 'PROVEN',?,?,strftime('%Y-%m-%dT%H:%M:%fZ','now'),?)",
                    (identifier, knowledge_id, evidence_id, admission_id, int(hmac_required), digest, actor),
                )
                row = connection.execute(
                    "SELECT id,knowledge_id,evidence_id,admission_id,status,hmac_required,hmac_digest,created_at,created_by "
                    "FROM knowledge_proof WHERE id=?",
                    (identifier,),
                ).fetchone()
                self.store.append_audit(
                    connection,
                    "KNOWLEDGE_PROOF_PROMOTED",
                    {"proof_id": identifier, "knowledge_id": knowledge_id, "evidence_id": evidence_id, "actor": actor},
                )
        except sqlite3.IntegrityError as exc:
            raise ProofError("Preuve dérivée invalide ou dupliquée.") from exc
        if row is None:
            raise ProofError("Preuve non lisible.")
        return KnowledgeProof(
            str(row["id"]),
            str(row["knowledge_id"]),
            str(row["evidence_id"]),
            str(row["admission_id"]),
            str(row["status"]),
            bool(row["hmac_required"]),
            None if row["hmac_digest"] is None else str(row["hmac_digest"]),
            str(row["created_at"]),
            str(row["created_by"]),
        )
