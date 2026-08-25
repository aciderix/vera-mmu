from __future__ import annotations

from dataclasses import dataclass
import sqlite3

from .store import MemoryStore, StoreError


HMAC_ALGORITHM = "HMAC_SHA256"


class ProofPolicyError(StoreError):
    pass


@dataclass(frozen=True)
class ProofPolicy:
    algorithm: str
    hmac_required: bool
    created_at: str
    created_by: str


class ProofPolicyService:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def declare(self, algorithm: str, *, hmac_required: bool, actor: str = "system") -> ProofPolicy:
        if algorithm != HMAC_ALGORITHM:
            raise ProofPolicyError("Algorithme de policy de preuve hors catalogue fermé.")
        if not isinstance(hmac_required, bool):
            raise ProofPolicyError("hmac_required doit être booléen.")
        if not isinstance(actor, str) or not actor or actor != actor.strip() or len(actor) > 256:
            raise ProofPolicyError("Actor invalide.")
        try:
            with self.store.transaction() as connection:
                connection.execute(
                    "INSERT INTO proof_policy(singleton, algorithm, hmac_required, created_at, created_by) "
                    "VALUES(1, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
                    (algorithm, int(hmac_required), actor),
                )
                row = connection.execute(
                    "SELECT algorithm, hmac_required, created_at, created_by FROM proof_policy WHERE singleton = 1"
                ).fetchone()
                self.store.append_audit(
                    connection,
                    "PROOF_POLICY_DECLARED",
                    {"algorithm": algorithm, "hmac_required": hmac_required, "actor": actor},
                )
        except sqlite3.IntegrityError as exc:
            raise ProofPolicyError("Policy de preuve déjà déclarée ou invalide.") from exc
        if row is None:
            raise ProofPolicyError("Policy de preuve non lisible.")
        return _policy(row)

    def get(self) -> ProofPolicy:
        row = self.store.connection.execute(
            "SELECT algorithm, hmac_required, created_at, created_by FROM proof_policy WHERE singleton = 1"
        ).fetchone()
        if row is None:
            raise ProofPolicyError("Policy de preuve introuvable.")
        return _policy(row)


def _policy(row: sqlite3.Row) -> ProofPolicy:
    return ProofPolicy(
        algorithm=str(row["algorithm"]),
        hmac_required=bool(row["hmac_required"]),
        created_at=str(row["created_at"]),
        created_by=str(row["created_by"]),
    )
