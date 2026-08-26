from __future__ import annotations

from dataclasses import dataclass
import sqlite3

from .store import MemoryStore, StoreError


WORK_COMPLETION_POLICY_MODES = frozenset({"OPEN", "REQUIRE_READY_FOR_COMPLETE"})


class WorkCompletionPolicyError(StoreError):
    pass


@dataclass(frozen=True)
class WorkCompletionPolicy:
    mode: str
    created_at: str
    created_by: str


class WorkCompletionPolicyService:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def declare(self, mode: str, *, actor: str = "system") -> WorkCompletionPolicy:
        if mode not in WORK_COMPLETION_POLICY_MODES:
            raise WorkCompletionPolicyError("Mode de policy de complétion hors catalogue fermé.")
        if not isinstance(actor, str) or not actor or actor != actor.strip() or len(actor) > 256:
            raise WorkCompletionPolicyError("Actor invalide.")
        try:
            with self.store.transaction() as connection:
                connection.execute(
                    "INSERT INTO work_completion_policy(id, mode, created_at, created_by) "
                    "VALUES(1, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
                    (mode, actor),
                )
                row = connection.execute(
                    "SELECT mode, created_at, created_by FROM work_completion_policy WHERE id = 1"
                ).fetchone()
                self.store.append_audit(
                    connection,
                    "WORK_COMPLETION_POLICY_DECLARED",
                    {"mode": mode, "actor": actor},
                )
        except sqlite3.IntegrityError as exc:
            raise WorkCompletionPolicyError("Policy de complétion déjà présente ou invalide.") from exc
        if row is None:
            raise WorkCompletionPolicyError("Policy de complétion non lisible.")
        return _policy(row)

    def get(self) -> WorkCompletionPolicy:
        row = self.store.connection.execute(
            "SELECT mode, created_at, created_by FROM work_completion_policy WHERE id = 1"
        ).fetchone()
        if row is None:
            raise WorkCompletionPolicyError("Policy de complétion absente.")
        return _policy(row)


def _policy(row: sqlite3.Row) -> WorkCompletionPolicy:
    return WorkCompletionPolicy(str(row["mode"]), str(row["created_at"]), str(row["created_by"]))
