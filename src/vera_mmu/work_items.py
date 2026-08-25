"""Generic immutable work-item backbone for the VERA-MMU Core (M2.13)."""

from __future__ import annotations

from dataclasses import dataclass
import json
import sqlite3
from typing import Any, Mapping

from .addressing import AddressError, make_address
from .identity import ProfileError, canonical_json
from .store import MemoryStore, StoreError


WORK_ITEM_TYPES = frozenset({"GOAL", "EPIC", "WORK_ITEM", "SUBTASK"})
INITIAL_WORK_ITEM_STATUS = "PLANNED"


class WorkItemError(StoreError):
    """Raised when a work item violates the generic backbone contract."""


class WorkItemNotFoundError(WorkItemError):
    """Raised when an exact work-item read finds no matching identifier."""


@dataclass(frozen=True)
class WorkItem:
    """One immutable planning record without lifecycle, graph or gate semantics."""

    id: str
    type: str
    title: str
    description: str
    status: str
    priority: int | None
    parent_id: str | None
    assignee: str | None
    metadata: dict[str, Any]
    created_at: str
    updated_at: str
    created_by: str
    address: str


class WorkItemService:
    """Create and read exact generic work items; transitions and graphs are out of scope."""

    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def create(
        self,
        identifier: str,
        item_type: str,
        title: str,
        *,
        description: str = "",
        priority: int | None = None,
        parent_id: str | None = None,
        assignee: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        actor: str = "system",
    ) -> WorkItem:
        """Create one immutable work item and record its audit event atomically."""
        normalized_identifier = _require_identifier(self.store, identifier)
        normalized_type = _require_type(item_type)
        normalized_title = _require_text(title, "title", maximum=1024)
        normalized_description = _require_optional_text(description, "description", maximum=4096)
        normalized_priority = _require_priority(priority)
        normalized_parent = _require_parent_identifier(self.store, parent_id)
        if normalized_parent == normalized_identifier:
            raise WorkItemError("Un work item ne peut pas être son propre parent.")
        normalized_assignee = _require_optional_text(assignee, "assignee", maximum=256)
        normalized_metadata = _require_json_object(metadata, "metadata")
        normalized_actor = _require_text(actor, "actor", maximum=256)
        try:
            with self.store.transaction() as connection:
                if normalized_parent is not None and connection.execute(
                    "SELECT 1 FROM work_item WHERE id = ?", (normalized_parent,)
                ).fetchone() is None:
                    raise WorkItemError("Parent de work item inconnu ou non enregistré.")
                timestamp_row = connection.execute("SELECT strftime('%Y-%m-%dT%H:%M:%fZ','now')").fetchone()
                if timestamp_row is None:
                    raise WorkItemError("Horodatage de création indisponible.")
                timestamp = str(timestamp_row[0])
                connection.execute(
                    "INSERT INTO work_item("
                    "id, type, title, description, status, priority, parent_id, assignee, metadata_json, "
                    "created_at, updated_at, created_by"
                    ") VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        normalized_identifier,
                        normalized_type,
                        normalized_title,
                        normalized_description,
                        INITIAL_WORK_ITEM_STATUS,
                        normalized_priority,
                        normalized_parent,
                        normalized_assignee,
                        canonical_json(normalized_metadata),
                        timestamp,
                        timestamp,
                        normalized_actor,
                    ),
                )
                row = connection.execute(
                    "SELECT id, type, title, description, status, priority, parent_id, assignee, metadata_json, "
                    "created_at, updated_at, created_by FROM work_item WHERE id = ?",
                    (normalized_identifier,),
                ).fetchone()
                if row is None:
                    raise WorkItemError("Création de work item non lisible.")
                self.store.append_audit(
                    connection,
                    "WORK_ITEM_CREATED",
                    {"work_item_id": normalized_identifier, "type": normalized_type, "actor": normalized_actor},
                )
        except sqlite3.IntegrityError as exc:
            raise WorkItemError("Identifiant ou structure de work item invalide ou déjà utilisée.") from exc
        return _work_item_from_row(self.store, row)

    def get(self, identifier: str) -> WorkItem:
        """Read exactly one work item by canonical VERA identifier; this is not FIND."""
        normalized_identifier = _require_identifier(self.store, identifier)
        row = self.store.connection.execute(
            "SELECT id, type, title, description, status, priority, parent_id, assignee, metadata_json, "
            "created_at, updated_at, created_by FROM work_item WHERE id = ?",
            (normalized_identifier,),
        ).fetchone()
        if row is None:
            raise WorkItemNotFoundError("Work item VERA introuvable.")
        return _work_item_from_row(self.store, row)


def _require_identifier(store: MemoryStore, value: str) -> str:
    try:
        make_address(store.identity.project_id, "work-item", value)
    except AddressError as exc:
        raise WorkItemError("Identifiant de work item VERA invalide.") from exc
    return value


def _require_parent_identifier(store: MemoryStore, value: str | None) -> str | None:
    if value is None:
        return None
    return _require_identifier(store, value)


def _require_type(value: str) -> str:
    if not isinstance(value, str) or value not in WORK_ITEM_TYPES:
        raise WorkItemError("Type de work item inconnu ou hors contrat M2.")
    return value


def _require_text(value: str, label: str, *, maximum: int) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > maximum or "\x00" in value:
        raise WorkItemError(f"{label} doit être une chaîne canonique non vide.")
    return value


def _require_optional_text(value: str | None, label: str, *, maximum: int) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or value != value.strip() or len(value) > maximum or "\x00" in value:
        raise WorkItemError(f"{label} doit être une chaîne canonique.")
    return value


def _require_priority(value: int | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < -(2**63) or value > (2**63 - 1):
        raise WorkItemError("priority doit être un entier SQLite borné ou absent.")
    return value


def _require_json_object(value: Mapping[str, Any] | None, label: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise WorkItemError(f"{label} doit être un objet JSON.")
    try:
        return json.loads(canonical_json(dict(value)))
    except (ProfileError, TypeError, ValueError) as exc:
        raise WorkItemError(f"{label} doit être sérialisable de façon canonique.") from exc


def _decode_json_object(value: object, label: str) -> dict[str, Any]:
    try:
        decoded = json.loads(str(value))
    except (TypeError, ValueError) as exc:
        raise WorkItemError(f"{label} de work item illisible.") from exc
    if not isinstance(decoded, dict):
        raise WorkItemError(f"{label} de work item non objet.")
    return decoded


def _work_item_from_row(store: MemoryStore, row: sqlite3.Row) -> WorkItem:
    item_id = str(row["id"])
    priority_value = row["priority"]
    return WorkItem(
        id=item_id,
        type=str(row["type"]),
        title=str(row["title"]),
        description=str(row["description"]),
        status=str(row["status"]),
        priority=None if priority_value is None else int(priority_value),
        parent_id=None if row["parent_id"] is None else str(row["parent_id"]),
        assignee=None if row["assignee"] is None else str(row["assignee"]),
        metadata=_decode_json_object(row["metadata_json"], "metadata"),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
        created_by=str(row["created_by"]),
        address=make_address(store.identity.project_id, "work-item", item_id),
    )
