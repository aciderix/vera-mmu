from __future__ import annotations

from dataclasses import dataclass
import sqlite3

from .store import MemoryStore, StoreError


class WorkReadinessError(StoreError):
    pass


@dataclass(frozen=True)
class WorkReadiness:
    work_item_id: str
    status: str
    prerequisites_completed: int
    prerequisites_total: int
    gates_passed: int
    gates_total: int


class WorkReadinessService:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def evaluate(self, work_item_id: str) -> WorkReadiness:
        _require_identifier(work_item_id)
        return evaluate_work_readiness(self.store.connection, work_item_id)


def evaluate_work_readiness(connection: sqlite3.Connection, work_item_id: str) -> WorkReadiness:
    if connection.execute("SELECT 1 FROM work_item WHERE id = ?", (work_item_id,)).fetchone() is None:
        raise WorkReadinessError("Work item inconnu.")
    prerequisite_ids = [str(row["prerequisite_id"]) for row in connection.execute(
        "SELECT prerequisite_id FROM work_dependency WHERE dependent_id = ? ORDER BY prerequisite_id", (work_item_id,)
    ).fetchall()]
    prerequisites_completed = sum(1 for identifier in prerequisite_ids if _work_status(connection, identifier) == "COMPLETED")
    gate_ids = [str(row["id"]) for row in connection.execute(
        "SELECT id FROM admission_gate WHERE work_item_id = ? ORDER BY id", (work_item_id,)
    ).fetchall()]
    gates_passed = sum(1 for identifier in gate_ids if _gate_status(connection, identifier) == "PASS")
    return WorkReadiness(
        work_item_id,
        "READY" if prerequisites_completed == len(prerequisite_ids) and gates_passed == len(gate_ids) else "BLOCKED",
        prerequisites_completed,
        len(prerequisite_ids),
        gates_passed,
        len(gate_ids),
    )


def _work_status(connection: sqlite3.Connection, work_item_id: str) -> str:
    row = connection.execute(
        "SELECT event FROM work_lifecycle_event WHERE work_item_id = ? ORDER BY sequence DESC LIMIT 1", (work_item_id,)
    ).fetchone()
    return "PLANNED" if row is None else {"START": "ACTIVE", "COMPLETE": "COMPLETED", "CANCEL": "CANCELLED"}[str(row["event"])]


def _gate_status(connection: sqlite3.Connection, gate_id: str) -> str:
    evidence_ids = [str(row["evidence_id"]) for row in connection.execute(
        "SELECT evidence_id FROM admission_gate WHERE id = ? UNION ALL SELECT evidence_id FROM admission_gate_requirement WHERE gate_id = ?",
        (gate_id, gate_id),
    ).fetchall()]
    policy = connection.execute(
        "SELECT mode, minimum_admissions FROM admission_gate_policy WHERE gate_id = ?", (gate_id,)
    ).fetchone()
    mode = "ALL" if policy is None else str(policy["mode"])
    minimum = len(evidence_ids) if mode == "ALL" else 1 if mode == "ANY" else int(policy["minimum_admissions"])
    admitted = sum(1 for identifier in evidence_ids if (row := connection.execute(
        "SELECT decision FROM evidence_admission WHERE evidence_id = ?", (identifier,)
    ).fetchone()) is not None and row["decision"] == "ADMITTED")
    return "PASS" if admitted >= minimum else "FAIL"


def _require_identifier(value: str) -> None:
    if not isinstance(value, str) or not value or "/" in value or len(value) > 256:
        raise WorkReadinessError("Identifiant de work item invalide.")
