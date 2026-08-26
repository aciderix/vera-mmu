from __future__ import annotations

from dataclasses import dataclass
import sqlite3

from .store import MemoryStore, StoreError


ADMISSION_POLICY_MODES = frozenset({"PASS_EVIDENCE", "VALIDATED_PASS_EVIDENCE"})


class AdmissionPolicyError(StoreError):
    pass


@dataclass(frozen=True)
class AdmissionPolicy:
    mode: str
    created_at: str
    created_by: str


class AdmissionPolicyService:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def declare(self, mode: str, *, actor: str = "system") -> AdmissionPolicy:
        if mode not in ADMISSION_POLICY_MODES:
            raise AdmissionPolicyError("Mode de policy d’admission hors catalogue fermé.")
        if not isinstance(actor, str) or not actor or actor != actor.strip() or len(actor) > 256:
            raise AdmissionPolicyError("Actor invalide.")
        try:
            with self.store.transaction() as connection:
                connection.execute(
                    "INSERT INTO admission_policy(id, mode, created_at, created_by) VALUES(1, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
                    (mode, actor),
                )
                row = connection.execute(
                    "SELECT mode, created_at, created_by FROM admission_policy WHERE id = 1"
                ).fetchone()
                self.store.append_audit(
                    connection,
                    "ADMISSION_POLICY_DECLARED",
                    {"mode": mode, "actor": actor},
                )
        except sqlite3.IntegrityError as exc:
            raise AdmissionPolicyError("Policy d’admission déjà présente ou invalide.") from exc
        if row is None:
            raise AdmissionPolicyError("Policy d’admission non lisible.")
        return _policy(row)

    def get(self) -> AdmissionPolicy:
        row = self.store.connection.execute(
            "SELECT mode, created_at, created_by FROM admission_policy WHERE id = 1"
        ).fetchone()
        if row is None:
            raise AdmissionPolicyError("Policy d’admission absente.")
        return _policy(row)


def _policy(row: sqlite3.Row) -> AdmissionPolicy:
    return AdmissionPolicy(str(row["mode"]), str(row["created_at"]), str(row["created_by"]))
