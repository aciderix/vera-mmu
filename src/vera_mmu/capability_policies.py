from __future__ import annotations

from dataclasses import dataclass
import sqlite3

from .store import MemoryStore, StoreError


POLICY_DECISIONS = frozenset({"ALLOW", "DENY", "CONFIRM"})


class CapabilityPolicyError(StoreError):
    pass


@dataclass(frozen=True)
class CapabilityPolicy:
    capability_id: str
    decision: str
    reason: str
    created_at: str
    created_by: str


class CapabilityPolicyService:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def declare(self, capability_id: str, decision: str, reason: str, *, actor: str = "system") -> CapabilityPolicy:
        if not isinstance(capability_id, str) or not capability_id or "/" in capability_id:
            raise CapabilityPolicyError("Identifiant de capability invalide.")
        if decision not in POLICY_DECISIONS:
            raise CapabilityPolicyError("Décision de policy hors catalogue fermé.")
        if not isinstance(reason, str) or not reason.strip() or reason != reason.strip() or len(reason) > 4096:
            raise CapabilityPolicyError("Motif de policy invalide.")
        if not isinstance(actor, str) or not actor or actor != actor.strip() or len(actor) > 256:
            raise CapabilityPolicyError("Actor invalide.")
        try:
            with self.store.transaction() as connection:
                if connection.execute("SELECT 1 FROM capability WHERE id = ?", (capability_id,)).fetchone() is None:
                    raise CapabilityPolicyError("Capability inconnue.")
                connection.execute(
                    "INSERT INTO capability_policy(capability_id, decision, reason, created_at, created_by) "
                    "VALUES(?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
                    (capability_id, decision, reason, actor),
                )
                row = connection.execute(
                    "SELECT capability_id, decision, reason, created_at, created_by FROM capability_policy WHERE capability_id = ?",
                    (capability_id,),
                ).fetchone()
                self.store.append_audit(
                    connection,
                    "CAPABILITY_POLICY_DECLARED",
                    {"capability_id": capability_id, "decision": decision, "actor": actor},
                )
        except sqlite3.IntegrityError as exc:
            raise CapabilityPolicyError("Policy de capability invalide ou déjà déclarée.") from exc
        if row is None:
            raise CapabilityPolicyError("Policy non lisible.")
        return _policy(row)

    def get(self, capability_id: str) -> CapabilityPolicy:
        if not isinstance(capability_id, str) or not capability_id or "/" in capability_id:
            raise CapabilityPolicyError("Identifiant de capability invalide.")
        row = self.store.connection.execute(
            "SELECT capability_id, decision, reason, created_at, created_by FROM capability_policy WHERE capability_id = ?",
            (capability_id,),
        ).fetchone()
        if row is None:
            raise CapabilityPolicyError("Policy de capability introuvable.")
        return _policy(row)


def _policy(row: sqlite3.Row) -> CapabilityPolicy:
    return CapabilityPolicy(
        capability_id=str(row["capability_id"]),
        decision=str(row["decision"]),
        reason=str(row["reason"]),
        created_at=str(row["created_at"]),
        created_by=str(row["created_by"]),
    )
