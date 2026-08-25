"""Immutable, explicit supersession links between append-only VERA knowledge records (M2.6)."""

from __future__ import annotations

from dataclasses import dataclass
import sqlite3

from .addressing import AddressError, make_address
from .store import MemoryStore, StoreError


class KnowledgeSupersessionError(StoreError):
    """Raised when a knowledge supersession violates immutable lifecycle constraints."""


class KnowledgeSupersessionNotFoundError(KnowledgeSupersessionError):
    """Raised when an exact predecessor or successor lookup finds no supersession link."""


@dataclass(frozen=True)
class KnowledgeSupersession:
    """One immutable direct statement that ``successor_id`` supersedes ``predecessor_id``."""

    predecessor_id: str
    successor_id: str
    created_at: str
    created_by: str


class KnowledgeSupersessionService:
    """Record direct knowledge succession without mutating the knowledge records themselves."""

    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def supersede(self, predecessor_id: str, successor_id: str, *, actor: str = "system") -> KnowledgeSupersession:
        """Record one direct immutable replacement after validating existence, uniqueness and acyclicity."""
        predecessor = _require_knowledge_identifier(self.store, predecessor_id)
        successor = _require_knowledge_identifier(self.store, successor_id)
        normalized_actor = _require_actor(actor)
        if predecessor == successor:
            raise KnowledgeSupersessionError("Une knowledge ne peut pas se superséder elle-même.")
        try:
            with self.store.transaction() as connection:
                _require_existing_knowledge(connection, predecessor, "prédécesseur")
                _require_existing_knowledge(connection, successor, "successeur")
                if connection.execute(
                    "SELECT 1 FROM knowledge_supersession WHERE predecessor_id = ?", (predecessor,)
                ).fetchone() is not None:
                    raise KnowledgeSupersessionError("Cette knowledge possède déjà un successeur déclaré.")
                if connection.execute(
                    "SELECT 1 FROM knowledge_supersession WHERE successor_id = ?", (successor,)
                ).fetchone() is not None:
                    raise KnowledgeSupersessionError("Cette knowledge est déjà déclarée comme successeur.")
                if _would_create_cycle(connection, predecessor, successor):
                    raise KnowledgeSupersessionError("La supersession créerait un cycle interdit.")
                connection.execute(
                    "INSERT INTO knowledge_supersession(predecessor_id, successor_id, created_at, created_by) "
                    "VALUES(?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
                    (predecessor, successor, normalized_actor),
                )
                row = connection.execute(
                    "SELECT predecessor_id, successor_id, created_at, created_by "
                    "FROM knowledge_supersession WHERE predecessor_id = ?",
                    (predecessor,),
                ).fetchone()
                if row is None:
                    raise KnowledgeSupersessionError("Supersession non lisible après création.")
                self.store.append_audit(
                    connection,
                    "KNOWLEDGE_SUPERSESSION_RECORDED",
                    {
                        "predecessor_id": predecessor,
                        "successor_id": successor,
                        "actor": normalized_actor,
                    },
                )
        except sqlite3.IntegrityError as exc:
            raise KnowledgeSupersessionError("Supersession dupliquée ou invalide.") from exc
        return _supersession_from_row(row)

    def successor_of(self, predecessor_id: str) -> KnowledgeSupersession:
        """Read the direct successor link of one exact knowledge identifier; lineage traversal is excluded."""
        predecessor = _require_knowledge_identifier(self.store, predecessor_id)
        row = self.store.connection.execute(
            "SELECT predecessor_id, successor_id, created_at, created_by "
            "FROM knowledge_supersession WHERE predecessor_id = ?",
            (predecessor,),
        ).fetchone()
        if row is None:
            raise KnowledgeSupersessionNotFoundError("Aucun successeur direct déclaré.")
        return _supersession_from_row(row)

    def predecessor_of(self, successor_id: str) -> KnowledgeSupersession:
        """Read the direct predecessor link of one exact knowledge identifier; lineage traversal is excluded."""
        successor = _require_knowledge_identifier(self.store, successor_id)
        row = self.store.connection.execute(
            "SELECT predecessor_id, successor_id, created_at, created_by "
            "FROM knowledge_supersession WHERE successor_id = ?",
            (successor,),
        ).fetchone()
        if row is None:
            raise KnowledgeSupersessionNotFoundError("Aucun prédécesseur direct déclaré.")
        return _supersession_from_row(row)


def _require_knowledge_identifier(store: MemoryStore, value: str) -> str:
    try:
        make_address(store.identity.project_id, "knowledge", value)
    except AddressError as exc:
        raise KnowledgeSupersessionError("Identifiant knowledge VERA invalide.") from exc
    return value


def _require_actor(value: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > 256:
        raise KnowledgeSupersessionError("actor doit être une chaîne canonique non vide.")
    return value


def _require_existing_knowledge(connection: sqlite3.Connection, identifier: str, label: str) -> None:
    if connection.execute("SELECT 1 FROM knowledge WHERE id = ?", (identifier,)).fetchone() is None:
        raise KnowledgeSupersessionError(f"Knowledge {label} inconnue.")


def _would_create_cycle(connection: sqlite3.Connection, predecessor_id: str, successor_id: str) -> bool:
    row = connection.execute(
        "WITH RECURSIVE successor_chain(id) AS ("
        "SELECT successor_id FROM knowledge_supersession WHERE predecessor_id = ? "
        "UNION "
        "SELECT link.successor_id FROM knowledge_supersession AS link "
        "JOIN successor_chain AS chain ON link.predecessor_id = chain.id"
        ") SELECT 1 FROM successor_chain WHERE id = ? LIMIT 1",
        (successor_id, predecessor_id),
    ).fetchone()
    return row is not None


def _supersession_from_row(row: sqlite3.Row) -> KnowledgeSupersession:
    predecessor_id = str(row["predecessor_id"])
    successor_id = str(row["successor_id"])
    if not predecessor_id or not successor_id or predecessor_id == successor_id:
        raise KnowledgeSupersessionError("Supersession stockée incohérente.")
    created_by = _require_actor(str(row["created_by"]))
    return KnowledgeSupersession(
        predecessor_id=predecessor_id,
        successor_id=successor_id,
        created_at=str(row["created_at"]),
        created_by=created_by,
    )
