"""Typed immutable relations between generic VERA entities (M2.3)."""

from __future__ import annotations

from dataclasses import dataclass
import json
import sqlite3
from typing import Any, Iterable, Mapping

from .addressing import AddressError, make_address
from .entities import ENTITY_TYPE_ID_RE
from .identity import ProfileError, canonical_json
from .store import MemoryStore, StoreError


class RelationError(StoreError):
    """Raised when relation input or its declared entity-type constraints are invalid."""


class RelationNotFoundError(RelationError):
    """Raised when an exact relation read finds no matching identifier."""


@dataclass(frozen=True)
class RelationType:
    """One immutable, generic relation type with optional entity-type constraints."""

    id: str
    label: str
    description: str
    from_types: tuple[str, ...]
    to_types: tuple[str, ...]
    created_at: str
    created_by: str


@dataclass(frozen=True)
class Relation:
    """One immutable directed edge between two VERA entities."""

    id: str
    relation_type_id: str
    from_entity_id: str
    to_entity_id: str
    created_at: str
    created_by: str
    address: str
    from_address: str
    to_address: str


class RelationService:
    """Register and read exact entity relations; traversal and lifecycle are intentionally absent."""

    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def register_type(
        self,
        type_id: str,
        label: str,
        *,
        description: str = "",
        from_types: Iterable[str] | None = None,
        to_types: Iterable[str] | None = None,
        actor: str = "system",
    ) -> RelationType:
        """Register an immutable relation type whose endpoint constraints reference known entity types."""
        normalized_type = _require_relation_type_id(type_id)
        normalized_label = _require_text(label, "label", maximum=256)
        normalized_description = _require_optional_text(description, "description")
        normalized_from_types = _require_type_constraints(from_types, "from_types")
        normalized_to_types = _require_type_constraints(to_types, "to_types")
        normalized_actor = _require_text(actor, "actor", maximum=256)
        try:
            with self.store.transaction() as connection:
                _require_registered_entity_types(connection, normalized_from_types, "from_types")
                _require_registered_entity_types(connection, normalized_to_types, "to_types")
                connection.execute(
                    "INSERT INTO relation_type(id, label, description, from_types_json, to_types_json, created_at, created_by) "
                    "VALUES(?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
                    (
                        normalized_type,
                        normalized_label,
                        normalized_description,
                        canonical_json(list(normalized_from_types)),
                        canonical_json(list(normalized_to_types)),
                        normalized_actor,
                    ),
                )
                row = connection.execute(
                    "SELECT id, label, description, from_types_json, to_types_json, created_at, created_by "
                    "FROM relation_type WHERE id = ?",
                    (normalized_type,),
                ).fetchone()
                if row is None:
                    raise RelationError("Création de type relationnel non lisible.")
                self.store.append_audit(
                    connection,
                    "RELATION_TYPE_REGISTERED",
                    {"relation_type_id": normalized_type, "actor": normalized_actor},
                )
        except sqlite3.IntegrityError as exc:
            raise RelationError("Type relationnel déjà enregistré ou invalide.") from exc
        return _relation_type_from_row(row)

    def create(
        self,
        identifier: str,
        relation_type_id: str,
        from_entity_id: str,
        to_entity_id: str,
        *,
        actor: str = "system",
    ) -> Relation:
        """Create one exact immutable edge when registered type constraints allow its endpoints."""
        normalized_identifier = _require_relation_identifier(self.store, identifier)
        normalized_type = _require_relation_type_id(relation_type_id)
        normalized_from = _require_entity_identifier(self.store, from_entity_id)
        normalized_to = _require_entity_identifier(self.store, to_entity_id)
        normalized_actor = _require_text(actor, "actor", maximum=256)
        try:
            with self.store.transaction() as connection:
                type_row = connection.execute(
                    "SELECT from_types_json, to_types_json FROM relation_type WHERE id = ?",
                    (normalized_type,),
                ).fetchone()
                if type_row is None:
                    raise RelationError("Type relationnel inconnu ou non enregistré.")
                from_entity_type = _entity_type_for(connection, normalized_from, "source")
                to_entity_type = _entity_type_for(connection, normalized_to, "cible")
                _enforce_endpoint_constraint(type_row["from_types_json"], from_entity_type, "source")
                _enforce_endpoint_constraint(type_row["to_types_json"], to_entity_type, "cible")
                connection.execute(
                    "INSERT INTO relation(id, relation_type_id, from_entity_id, to_entity_id, created_at, created_by) "
                    "VALUES(?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
                    (normalized_identifier, normalized_type, normalized_from, normalized_to, normalized_actor),
                )
                row = connection.execute(
                    "SELECT id, relation_type_id, from_entity_id, to_entity_id, created_at, created_by "
                    "FROM relation WHERE id = ?",
                    (normalized_identifier,),
                ).fetchone()
                if row is None:
                    raise RelationError("Création de relation non lisible.")
                self.store.append_audit(
                    connection,
                    "RELATION_CREATED",
                    {
                        "relation_id": normalized_identifier,
                        "relation_type_id": normalized_type,
                        "from_entity_id": normalized_from,
                        "to_entity_id": normalized_to,
                        "actor": normalized_actor,
                    },
                )
        except sqlite3.IntegrityError as exc:
            raise RelationError("Relation dupliquée ou invalide.") from exc
        return _relation_from_row(self.store, row)

    def get(self, identifier: str) -> Relation:
        """Read exactly one relation by canonical identifier; traversal and FIND are excluded."""
        normalized_identifier = _require_relation_identifier(self.store, identifier)
        row = self.store.connection.execute(
            "SELECT id, relation_type_id, from_entity_id, to_entity_id, created_at, created_by "
            "FROM relation WHERE id = ?",
            (normalized_identifier,),
        ).fetchone()
        if row is None:
            raise RelationNotFoundError("Relation VERA introuvable.")
        return _relation_from_row(self.store, row)


def _require_relation_type_id(value: str) -> str:
    if not isinstance(value, str) or not ENTITY_TYPE_ID_RE.fullmatch(value):
        raise RelationError("Identifiant de type relationnel invalide.")
    return value


def _require_text(value: str, label: str, *, maximum: int) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > maximum:
        raise RelationError(f"{label} doit être une chaîne canonique non vide.")
    return value


def _require_optional_text(value: str, label: str) -> str:
    if not isinstance(value, str) or value != value.strip():
        raise RelationError(f"{label} doit être une chaîne canonique.")
    return value


def _require_type_constraints(value: Iterable[str] | None, label: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)):
        raise RelationError(f"{label} doit être une liste de types d’entité.")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise RelationError(f"{label} doit être une liste de types d’entité.") from exc
    if len(items) > 64:
        raise RelationError(f"{label} contient trop de contraintes.")
    normalized = tuple(sorted({_require_entity_type_id(item) for item in items}))
    if len(normalized) != len(items):
        raise RelationError(f"{label} ne doit pas contenir de doublon.")
    return normalized


def _require_entity_type_id(value: object) -> str:
    if not isinstance(value, str) or not ENTITY_TYPE_ID_RE.fullmatch(value):
        raise RelationError("Contrainte de type d’entité invalide.")
    return value


def _require_registered_entity_types(connection: sqlite3.Connection, type_ids: tuple[str, ...], label: str) -> None:
    if not type_ids:
        return
    placeholders = ", ".join("?" for _ in type_ids)
    found = {
        str(row[0])
        for row in connection.execute(f"SELECT id FROM entity_type WHERE id IN ({placeholders})", type_ids)
    }
    missing = set(type_ids) - found
    if missing:
        raise RelationError(f"{label} référence un type d’entité non enregistré.")


def _require_relation_identifier(store: MemoryStore, value: str) -> str:
    try:
        make_address(store.identity.project_id, "relation", value)
    except AddressError as exc:
        raise RelationError("Identifiant de relation VERA invalide.") from exc
    return value


def _require_entity_identifier(store: MemoryStore, value: str) -> str:
    try:
        make_address(store.identity.project_id, "entity", value)
    except AddressError as exc:
        raise RelationError("Identifiant d’entité VERA invalide.") from exc
    return value


def _entity_type_for(connection: sqlite3.Connection, entity_id: str, endpoint: str) -> str:
    row = connection.execute("SELECT type_id FROM entity WHERE id = ?", (entity_id,)).fetchone()
    if row is None:
        raise RelationError(f"Entité {endpoint} inconnue.")
    return str(row["type_id"])


def _enforce_endpoint_constraint(raw_constraints: object, entity_type_id: str, endpoint: str) -> None:
    constraints = _decode_type_constraints(raw_constraints, endpoint)
    if constraints and entity_type_id not in constraints:
        raise RelationError(f"Type d’entité {endpoint} non autorisé par le type relationnel.")


def _relation_type_from_row(row: sqlite3.Row) -> RelationType:
    return RelationType(
        id=str(row["id"]),
        label=str(row["label"]),
        description=str(row["description"]),
        from_types=_decode_type_constraints(row["from_types_json"], "source"),
        to_types=_decode_type_constraints(row["to_types_json"], "cible"),
        created_at=str(row["created_at"]),
        created_by=str(row["created_by"]),
    )


def _relation_from_row(store: MemoryStore, row: sqlite3.Row) -> Relation:
    identifier = str(row["id"])
    source = str(row["from_entity_id"])
    target = str(row["to_entity_id"])
    return Relation(
        id=identifier,
        relation_type_id=str(row["relation_type_id"]),
        from_entity_id=source,
        to_entity_id=target,
        created_at=str(row["created_at"]),
        created_by=str(row["created_by"]),
        address=make_address(store.identity.project_id, "relation", identifier),
        from_address=make_address(store.identity.project_id, "entity", source),
        to_address=make_address(store.identity.project_id, "entity", target),
    )


def _decode_type_constraints(value: object, endpoint: str) -> tuple[str, ...]:
    try:
        decoded = json.loads(str(value))
    except (TypeError, ValueError) as exc:
        raise RelationError(f"Contraintes de type {endpoint} illisibles.") from exc
    if not isinstance(decoded, list) or any(not isinstance(item, str) for item in decoded):
        raise RelationError(f"Contraintes de type {endpoint} invalides.")
    try:
        return _require_type_constraints(decoded, endpoint)
    except RelationError as exc:
        raise RelationError(f"Contraintes de type {endpoint} invalides.") from exc
