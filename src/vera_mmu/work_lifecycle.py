from __future__ import annotations

from dataclasses import dataclass
import sqlite3

from .store import MemoryStore, StoreError


STATE_BY_EVENT = {"START": "ACTIVE", "COMPLETE": "COMPLETED", "CANCEL": "CANCELLED"}
ALLOWED_EVENTS = {"PLANNED": frozenset({"START", "CANCEL"}), "ACTIVE": frozenset({"COMPLETE", "CANCEL"})}


class WorkLifecycleError(StoreError):
    pass


@dataclass(frozen=True)
class WorkLifecycleEvent:
    id: str
    work_item_id: str
    sequence: int
    event: str
    reason: str
    created_at: str
    created_by: str


@dataclass(frozen=True)
class WorkLifecycleState:
    work_item_id: str
    status: str
    last_event_id: str | None


class WorkLifecycleService:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def transition(self, identifier: str, work_item_id: str, event: str, reason: str, *, actor: str = "system") -> WorkLifecycleEvent:
        _require_identifier(identifier, "événement")
        _require_identifier(work_item_id, "work item")
        if event not in STATE_BY_EVENT:
            raise WorkLifecycleError("Événement de lifecycle hors catalogue fermé.")
        _require_text(reason, "Motif", 4096)
        _require_text(actor, "Actor", 256)
        try:
            with self.store.transaction() as connection:
                if connection.execute("SELECT 1 FROM work_item WHERE id = ?", (work_item_id,)).fetchone() is None:
                    raise WorkLifecycleError("Work item inconnu.")
                last = connection.execute(
                    "SELECT id, event, sequence FROM work_lifecycle_event WHERE work_item_id = ? ORDER BY sequence DESC LIMIT 1",
                    (work_item_id,),
                ).fetchone()
                current_status = "PLANNED" if last is None else STATE_BY_EVENT[str(last["event"])]
                if event not in ALLOWED_EVENTS.get(current_status, frozenset()):
                    raise WorkLifecycleError("Transition de lifecycle interdite.")
                sequence = 1 if last is None else int(last["sequence"]) + 1
                connection.execute(
                    "INSERT INTO work_lifecycle_event(id, work_item_id, sequence, event, reason, created_at, created_by) "
                    "VALUES(?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
                    (identifier, work_item_id, sequence, event, reason, actor),
                )
                row = connection.execute(
                    "SELECT id, work_item_id, sequence, event, reason, created_at, created_by FROM work_lifecycle_event WHERE id = ?",
                    (identifier,),
                ).fetchone()
                self.store.append_audit(
                    connection,
                    "WORK_LIFECYCLE_EVENT_RECORDED",
                    {"event_id": identifier, "work_item_id": work_item_id, "event": event, "actor": actor},
                )
        except sqlite3.IntegrityError as exc:
            raise WorkLifecycleError("Événement de lifecycle invalide ou dupliqué.") from exc
        if row is None:
            raise WorkLifecycleError("Événement de lifecycle non lisible.")
        return _event(row)

    def get_state(self, work_item_id: str) -> WorkLifecycleState:
        _require_identifier(work_item_id, "work item")
        if self.store.connection.execute("SELECT 1 FROM work_item WHERE id = ?", (work_item_id,)).fetchone() is None:
            raise WorkLifecycleError("Work item inconnu.")
        row = self.store.connection.execute(
            "SELECT id, event FROM work_lifecycle_event WHERE work_item_id = ? ORDER BY sequence DESC LIMIT 1",
            (work_item_id,),
        ).fetchone()
        return WorkLifecycleState(work_item_id, "PLANNED" if row is None else STATE_BY_EVENT[str(row["event"])], None if row is None else str(row["id"]))

    def history(self, work_item_id: str) -> tuple[WorkLifecycleEvent, ...]:
        _require_identifier(work_item_id, "work item")
        if self.store.connection.execute("SELECT 1 FROM work_item WHERE id = ?", (work_item_id,)).fetchone() is None:
            raise WorkLifecycleError("Work item inconnu.")
        rows = self.store.connection.execute(
            "SELECT id, work_item_id, sequence, event, reason, created_at, created_by "
            "FROM work_lifecycle_event WHERE work_item_id = ? ORDER BY sequence",
            (work_item_id,),
        ).fetchall()
        return tuple(_event(row) for row in rows)


def _require_identifier(value: str, label: str) -> None:
    if not isinstance(value, str) or not value or "/" in value or len(value) > 256:
        raise WorkLifecycleError(f"Identifiant de {label} invalide.")


def _require_text(value: str, label: str, maximum: int) -> None:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > maximum or "\x00" in value:
        raise WorkLifecycleError(f"{label} invalide.")


def _event(row: sqlite3.Row) -> WorkLifecycleEvent:
    return WorkLifecycleEvent(
        id=str(row["id"]),
        work_item_id=str(row["work_item_id"]),
        sequence=int(row["sequence"]),
        event=str(row["event"]),
        reason=str(row["reason"]),
        created_at=str(row["created_at"]),
        created_by=str(row["created_by"]),
    )
