"""Append-only, evidence-safe generic knowledge records (M2.4)."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import sqlite3
from typing import Any, Mapping

from .addressing import AddressError, make_address
from .entities import ENTITY_TYPE_ID_RE
from .identity import canonical_json
from .store import MemoryStore, StoreError


INITIAL_KNOWLEDGE_STATUSES = frozenset({"ACTIVE", "OBSERVED", "HYPOTHESIS", "CONFLICTING"})
FORBIDDEN_INITIAL_KNOWLEDGE_STATUSES = frozenset({"PROVEN", "SUPERSEDED", "OBSOLETE"})


class KnowledgeError(StoreError):
    """Raised when a knowledge record violates Core append-only or epistemic rules."""


class KnowledgeNotFoundError(KnowledgeError):
    """Raised when an exact knowledge read finds no matching identifier."""


class KnowledgeAdmissionError(KnowledgeError):
    """Raised when a knowledge status requires a service that the Core does not yet provide."""


@dataclass(frozen=True)
class KnowledgeType:
    """One immutable generic knowledge type."""

    id: str
    label: str
    description: str
    created_at: str
    created_by: str


@dataclass(frozen=True)
class Knowledge:
    """One immutable knowledge assertion with a content hash and exact VERA address."""

    id: str
    type_id: str
    status: str
    title: str
    content: str
    content_hash: str
    metadata: dict[str, Any]
    created_at: str
    created_by: str
    address: str


class KnowledgeService:
    """Register types and append exact knowledge; promotion, search and supersession are excluded."""

    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def register_type(
        self,
        type_id: str,
        label: str,
        *,
        description: str = "",
        actor: str = "system",
    ) -> KnowledgeType:
        """Register one immutable generic knowledge type."""
        normalized_type = _require_type_id(type_id)
        normalized_label = _require_text(label, "label", maximum=256)
        normalized_description = _require_optional_text(description, "description")
        normalized_actor = _require_text(actor, "actor", maximum=256)
        try:
            with self.store.transaction() as connection:
                connection.execute(
                    "INSERT INTO knowledge_type(id, label, description, created_at, created_by) "
                    "VALUES(?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
                    (normalized_type, normalized_label, normalized_description, normalized_actor),
                )
                row = connection.execute(
                    "SELECT id, label, description, created_at, created_by FROM knowledge_type WHERE id = ?",
                    (normalized_type,),
                ).fetchone()
                if row is None:
                    raise KnowledgeError("Création de type knowledge non lisible.")
                self.store.append_audit(
                    connection,
                    "KNOWLEDGE_TYPE_REGISTERED",
                    {"knowledge_type_id": normalized_type, "actor": normalized_actor},
                )
        except sqlite3.IntegrityError as exc:
            raise KnowledgeError("Type knowledge déjà enregistré ou invalide.") from exc
        return _knowledge_type_from_row(row)

    def append(
        self,
        identifier: str,
        type_id: str,
        status: str,
        title: str,
        content: str,
        *,
        metadata: Mapping[str, Any] | None = None,
        actor: str = "system",
    ) -> Knowledge:
        """Append one exact knowledge record; ``PROVEN`` is rejected until Evidence Store exists."""
        normalized_identifier = _require_knowledge_identifier(self.store, identifier)
        normalized_type = _require_type_id(type_id)
        normalized_status = _require_initial_status(status)
        normalized_title = _require_text(title, "title", maximum=512)
        normalized_content = _require_content(content)
        normalized_metadata = _require_metadata(metadata)
        normalized_actor = _require_text(actor, "actor", maximum=256)
        content_hash = sha256(normalized_content.encode("utf-8")).hexdigest()
        try:
            with self.store.transaction() as connection:
                if connection.execute("SELECT 1 FROM knowledge_type WHERE id = ?", (normalized_type,)).fetchone() is None:
                    raise KnowledgeError("Type knowledge inconnu ou non enregistré.")
                connection.execute(
                    "INSERT INTO knowledge(id, type_id, status, title, content, content_hash, metadata_json, created_at, created_by) "
                    "VALUES(?, ?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
                    (
                        normalized_identifier,
                        normalized_type,
                        normalized_status,
                        normalized_title,
                        normalized_content,
                        content_hash,
                        canonical_json(normalized_metadata),
                        normalized_actor,
                    ),
                )
                row = connection.execute(
                    "SELECT id, type_id, status, title, content, content_hash, metadata_json, created_at, created_by "
                    "FROM knowledge WHERE id = ?",
                    (normalized_identifier,),
                ).fetchone()
                if row is None:
                    raise KnowledgeError("Append knowledge non lisible.")
                self.store.append_audit(
                    connection,
                    "KNOWLEDGE_APPENDED",
                    {
                        "knowledge_id": normalized_identifier,
                        "knowledge_type_id": normalized_type,
                        "status": normalized_status,
                        "content_hash": content_hash,
                        "actor": normalized_actor,
                    },
                )
        except sqlite3.IntegrityError as exc:
            raise KnowledgeError("Enregistrement knowledge dupliqué ou invalide.") from exc
        return _knowledge_from_row(self.store, row)

    def get(self, identifier: str) -> Knowledge:
        """Read exactly one knowledge record by canonical identifier; FIND is intentionally absent."""
        normalized_identifier = _require_knowledge_identifier(self.store, identifier)
        row = self.store.connection.execute(
            "SELECT id, type_id, status, title, content, content_hash, metadata_json, created_at, created_by "
            "FROM knowledge WHERE id = ?",
            (normalized_identifier,),
        ).fetchone()
        if row is None:
            raise KnowledgeNotFoundError("Knowledge VERA introuvable.")
        return _knowledge_from_row(self.store, row)


def _require_type_id(value: str) -> str:
    if not isinstance(value, str) or not ENTITY_TYPE_ID_RE.fullmatch(value):
        raise KnowledgeError("Identifiant de type knowledge invalide.")
    return value


def _require_text(value: str, label: str, *, maximum: int) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > maximum:
        raise KnowledgeError(f"{label} doit être une chaîne canonique non vide.")
    return value


def _require_optional_text(value: str, label: str) -> str:
    if not isinstance(value, str) or value != value.strip():
        raise KnowledgeError(f"{label} doit être une chaîne canonique.")
    return value


def _require_content(value: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 1048576:
        raise KnowledgeError("content doit être une chaîne non vide dans la borne autorisée.")
    return value


def _require_initial_status(value: str) -> str:
    if not isinstance(value, str):
        raise KnowledgeError("Statut knowledge invalide.")
    if value in FORBIDDEN_INITIAL_KNOWLEDGE_STATUSES:
        if value == "PROVEN":
            raise KnowledgeAdmissionError("PROVEN exige une Evidence Store admissible ; statut indisponible dans M2.4.")
        raise KnowledgeAdmissionError("Ce statut ne peut pas être attribué lors de l’append initial.")
    if value not in INITIAL_KNOWLEDGE_STATUSES:
        raise KnowledgeError("Statut knowledge inconnu ou non autorisé.")
    return value


def _require_metadata(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise KnowledgeError("metadata doit être un objet JSON.")
    try:
        canonical_json(dict(value))
    except (TypeError, ValueError) as exc:
        raise KnowledgeError("metadata doit être un objet JSON canonisable.") from exc
    return dict(value)


def _require_knowledge_identifier(store: MemoryStore, value: str) -> str:
    try:
        make_address(store.identity.project_id, "knowledge", value)
    except AddressError as exc:
        raise KnowledgeError("Identifiant knowledge VERA invalide.") from exc
    return value


def _knowledge_type_from_row(row: sqlite3.Row) -> KnowledgeType:
    return KnowledgeType(
        id=str(row["id"]),
        label=str(row["label"]),
        description=str(row["description"]),
        created_at=str(row["created_at"]),
        created_by=str(row["created_by"]),
    )


def _knowledge_from_row(store: MemoryStore, row: sqlite3.Row) -> Knowledge:
    try:
        metadata = json.loads(str(row["metadata_json"]))
    except (TypeError, ValueError) as exc:
        raise KnowledgeError("Métadonnées knowledge illisibles.") from exc
    if not isinstance(metadata, dict):
        raise KnowledgeError("Métadonnées knowledge invalides.")
    identifier = str(row["id"])
    content = str(row["content"])
    content_hash = str(row["content_hash"])
    if sha256(content.encode("utf-8")).hexdigest() != content_hash:
        raise KnowledgeError("Hash de contenu knowledge incohérent.")
    return Knowledge(
        id=identifier,
        type_id=str(row["type_id"]),
        status=str(row["status"]),
        title=str(row["title"]),
        content=content,
        content_hash=content_hash,
        metadata=metadata,
        created_at=str(row["created_at"]),
        created_by=str(row["created_by"]),
        address=make_address(store.identity.project_id, "knowledge", identifier),
    )
