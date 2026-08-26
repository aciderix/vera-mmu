from __future__ import annotations

from dataclasses import dataclass
import sqlite3

from .store import MemoryStore, StoreError


WORK_START_POLICY_MODES = frozenset({"OPEN", "REQUIRE_READY"})


class WorkStartPolicyError(StoreError):
    pass


@dataclass(frozen=True)
class WorkStartPolicy:
    mode: str
    created_at: str
    created_by: str


class WorkStartPolicyService:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def declare(self, mode: str, *, actor: str = "system") -> WorkStartPolicy:
        if mode not in WORK_START_POLICY_MODES:
            raise WorkStartPolicyError("Mode de policy de démarrage hors catalogue fermé.")
        if not isinstance(actor, str) or not actor or actor != actor.strip() or len(actor) > 256:
            raise WorkStartPolicyError("Actor invalide.")
        try:
            with self.store.transaction() as connection:
                connection.execute(
                    "INSERT INTO work_start_policy(id, mode, created_at, created_by) VALUES(1, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
                    (mode, actor),
                )
                row = connection.execute(
                    "SELECT mode, created_at, created_by FROM work_start_policy WHERE id = 1"
                ).fetchone()
                self.store.append_audit(
                    connection,
                    "WORK_START_POLICY_DECLARED",
                    {"mode": mode, "actor": actor},
                )
        except sqlite3.IntegrityError as exc:
            raise WorkStartPolicyError("Policy de démarrage déjà présente ou invalide.") from exc
        if row is None:
            raise WorkStartPolicyError("Policy de démarrage non lisible.")
        return _policy(row)

    def get(self) -> WorkStartPolicy:
        row = self.store.connection.execute(
            "SELECT mode, created_at, created_by FROM work_start_policy WHERE id = 1"
        ).fetchone()
        if row is None:
            raise WorkStartPolicyError("Policy de démarrage absente.")
        return _policy(row)


def _policy(row: sqlite3.Row) -> WorkStartPolicy:
    return WorkStartPolicy(str(row["mode"]), str(row["created_at"]), str(row["created_by"]))
