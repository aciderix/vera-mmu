"""Generic entity registry for the VERA-MMU Core (M2.2)."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
import sqlite3
from typing import Any, Mapping, Sequence

from .addressing import AddressError, make_address
from .identity import ProfileError, canonical_json
from .store import MemoryStore, StoreError


ENTITY_TYPE_ID_RE = re.compile(r"^[a-z][a-z0-9-]{0,63}$")


class EntityError(StoreError):
    """Raised when generic entity input is invalid or violates the registry contract."""


class EntityNotFoundError(EntityError):
    """Raised when an exact entity read finds no matching identifier."""


@dataclass(frozen=True)
class EntityType:
    """One registered generic entity type, independent of a project domain."""

    id: str
    label: str
    description: str
    schema: dict[str, Any]
    created_at: str
    created_by: str


@dataclass(frozen=True)
class Entity:
    """One immutable entity creation record exposed through an exact VERA address."""

    id: str
    type_id: str
    title: str
    description: str
    metadata: dict[str, Any]
    created_at: str
    created_by: str
    address: str


@dataclass(frozen=True)
class EntityCreateInput:
    """One validated caller-side input for an atomic generic entity batch."""

    identifier: str
    title: str
    description: str = ""
    metadata: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class EntityBatchResult:
    """The committed result of one atomic type-registration and entity-creation batch."""

    entity_type: EntityType
    entities: tuple[Entity, ...]


class EntityService:
    """Create and read generic entities; search, mutation and relations are out of scope."""

    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def register_type(
        self,
        type_id: str,
        label: str,
        *,
        description: str = "",
        schema: Mapping[str, Any] | None = None,
        actor: str = "system",
    ) -> EntityType:
        """Register one generic type exactly once and audit the atomic mutation."""
        normalized_type = _require_type_id(type_id)
        normalized_label = _require_text(label, "label", maximum=256)
        normalized_description = _require_optional_text(description, "description")
        normalized_schema = _require_json_object(schema, "schema")
        normalized_actor = _require_text(actor, "actor", maximum=256)
        try:
            with self.store.transaction() as connection:
                connection.execute(
                    "INSERT INTO entity_type(id, label, description, schema_json, created_at, created_by) "
                    "VALUES(?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
                    (
                        normalized_type,
                        normalized_label,
                        normalized_description,
                        canonical_json(normalized_schema),
                        normalized_actor,
                    ),
                )
                row = connection.execute(
                    "SELECT id, label, description, schema_json, created_at, created_by "
                    "FROM entity_type WHERE id = ?",
                    (normalized_type,),
                ).fetchone()
                if row is None:
                    raise EntityError("Création de type d’entité non lisible.")
                self.store.append_audit(
                    connection,
                    "ENTITY_TYPE_REGISTERED",
                    {"entity_type_id": normalized_type, "actor": normalized_actor},
                )
        except sqlite3.IntegrityError as exc:
            raise EntityError("Type d’entité déjà enregistré ou invalide.") from exc
        return _entity_type_from_row(row)

    def create(
        self,
        identifier: str,
        type_id: str,
        title: str,
        *,
        description: str = "",
        metadata: Mapping[str, Any] | None = None,
        actor: str = "system",
    ) -> Entity:
        """Create one entity of a registered type and audit it in the same transaction."""
        normalized_identifier = _require_entity_identifier(self.store, identifier)
        normalized_type = _require_type_id(type_id)
        normalized_title = _require_text(title, "title", maximum=1024)
        normalized_description = _require_optional_text(description, "description")
        normalized_metadata = _require_json_object(metadata, "metadata")
        normalized_actor = _require_text(actor, "actor", maximum=256)
        try:
            with self.store.transaction() as connection:
                if connection.execute("SELECT 1 FROM entity_type WHERE id = ?", (normalized_type,)).fetchone() is None:
                    raise EntityError("Type d’entité inconnu ou non enregistré.")
                connection.execute(
                    "INSERT INTO entity(id, type_id, title, description, metadata_json, created_at, created_by) "
                    "VALUES(?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
                    (
                        normalized_identifier,
                        normalized_type,
                        normalized_title,
                        normalized_description,
                        canonical_json(normalized_metadata),
                        normalized_actor,
                    ),
                )
                row = connection.execute(
                    "SELECT id, type_id, title, description, metadata_json, created_at, created_by "
                    "FROM entity WHERE id = ?",
                    (normalized_identifier,),
                ).fetchone()
                if row is None:
                    raise EntityError("Création d’entité non lisible.")
                self.store.append_audit(
                    connection,
                    "ENTITY_CREATED",
                    {
                        "entity_id": normalized_identifier,
                        "entity_type_id": normalized_type,
                        "actor": normalized_actor,
                    },
                )
        except sqlite3.IntegrityError as exc:
            raise EntityError("Identifiant d’entité déjà utilisé ou entité invalide.") from exc
        return _entity_from_row(self.store, row)

    def create_batch_for_registered_type(
        self,
        type_id: str,
        entities: Sequence[EntityCreateInput],
        *,
        actor: str = "system",
    ) -> EntityBatchResult:
        """Atomically create a bounded batch for one existing generic entity type.

        The type must already exist and is read in the same transaction as the inserts.
        All input validation happens before the transaction; any conflict rolls back every
        entity and audit record from this batch, without changing the existing type.
        """
        normalized_type = _require_type_id(type_id)
        normalized_actor = _require_text(actor, "actor", maximum=256)
        if not isinstance(entities, Sequence) or isinstance(entities, (str, bytes)) or not 1 <= len(entities) <= 100:
            raise EntityError("Le batch d’entités doit contenir entre 1 et 100 entrées.")

        normalized_inputs: list[tuple[str, str, str, dict[str, Any]]] = []
        for item in entities:
            if not isinstance(item, EntityCreateInput):
                raise EntityError("Chaque entrée du batch doit être un EntityCreateInput.")
            normalized_inputs.append(
                (
                    _require_entity_identifier(self.store, item.identifier),
                    _require_text(item.title, "title", maximum=1024),
                    _require_optional_text(item.description, "description"),
                    _require_json_object(item.metadata, "metadata"),
                )
            )
        identifiers = tuple(item[0] for item in normalized_inputs)
        if len(set(identifiers)) != len(identifiers):
            raise EntityError("Les identifiants d’entité du batch doivent être uniques.")

        try:
            with self.store.transaction() as connection:
                type_row = connection.execute(
                    "SELECT id, label, description, schema_json, created_at, created_by "
                    "FROM entity_type WHERE id = ?",
                    (normalized_type,),
                ).fetchone()
                if type_row is None:
                    raise EntityError("Type d’entité inconnu ou non enregistré.")
                rows = []
                for identifier, title, description, metadata in normalized_inputs:
                    connection.execute(
                        "INSERT INTO entity(id, type_id, title, description, metadata_json, created_at, created_by) "
                        "VALUES(?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
                        (
                            identifier,
                            normalized_type,
                            title,
                            description,
                            canonical_json(metadata),
                            normalized_actor,
                        ),
                    )
                    row = connection.execute(
                        "SELECT id, type_id, title, description, metadata_json, created_at, created_by "
                        "FROM entity WHERE id = ?",
                        (identifier,),
                    ).fetchone()
                    if row is None:
                        raise EntityError("Création atomique d’entité non lisible.")
                    rows.append(row)
                    self.store.append_audit(
                        connection,
                        "ENTITY_CREATED",
                        {
                            "entity_id": identifier,
                            "entity_type_id": normalized_type,
                            "actor": normalized_actor,
                        },
                    )
        except sqlite3.IntegrityError as exc:
            raise EntityError("Identifiant d’entité déjà utilisé ou entité invalide.") from exc
        return EntityBatchResult(
            entity_type=_entity_type_from_row(type_row),
            entities=tuple(_entity_from_row(self.store, row) for row in rows),
        )

    def register_type_and_create_batch(
        self,
        type_id: str,
        label: str,
        entities: Sequence[EntityCreateInput],
        *,
        type_description: str = "",
        type_schema: Mapping[str, Any] | None = None,
        actor: str = "system",
    ) -> EntityBatchResult:
        """Atomically register one absent generic type and create a bounded batch of its entities.

        All validation occurs before the transaction. Any storage conflict or internal failure
        rolls back both the type registration and every entity/audit insertion from this batch.
        """
        normalized_type = _require_type_id(type_id)
        normalized_label = _require_text(label, "label", maximum=256)
        normalized_description = _require_optional_text(type_description, "type_description")
        normalized_schema = _require_json_object(type_schema, "type_schema")
        normalized_actor = _require_text(actor, "actor", maximum=256)
        if not isinstance(entities, Sequence) or isinstance(entities, (str, bytes)) or not 1 <= len(entities) <= 100:
            raise EntityError("Le batch d’entités doit contenir entre 1 et 100 entrées.")

        normalized_inputs: list[tuple[str, str, str, dict[str, Any]]] = []
        for item in entities:
            if not isinstance(item, EntityCreateInput):
                raise EntityError("Chaque entrée du batch doit être un EntityCreateInput.")
            normalized_inputs.append(
                (
                    _require_entity_identifier(self.store, item.identifier),
                    _require_text(item.title, "title", maximum=1024),
                    _require_optional_text(item.description, "description"),
                    _require_json_object(item.metadata, "metadata"),
                )
            )
        identifiers = tuple(item[0] for item in normalized_inputs)
        if len(set(identifiers)) != len(identifiers):
            raise EntityError("Les identifiants d’entité du batch doivent être uniques.")

        try:
            with self.store.transaction() as connection:
                if connection.execute("SELECT 1 FROM entity_type WHERE id = ?", (normalized_type,)).fetchone() is not None:
                    raise EntityError("Type d’entité déjà enregistré ou invalide.")
                connection.execute(
                    "INSERT INTO entity_type(id, label, description, schema_json, created_at, created_by) "
                    "VALUES(?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
                    (
                        normalized_type,
                        normalized_label,
                        normalized_description,
                        canonical_json(normalized_schema),
                        normalized_actor,
                    ),
                )
                type_row = connection.execute(
                    "SELECT id, label, description, schema_json, created_at, created_by "
                    "FROM entity_type WHERE id = ?",
                    (normalized_type,),
                ).fetchone()
                if type_row is None:
                    raise EntityError("Création atomique de type d’entité non lisible.")
                self.store.append_audit(
                    connection,
                    "ENTITY_TYPE_REGISTERED",
                    {"entity_type_id": normalized_type, "actor": normalized_actor},
                )

                rows = []
                for identifier, title, description, metadata in normalized_inputs:
                    connection.execute(
                        "INSERT INTO entity(id, type_id, title, description, metadata_json, created_at, created_by) "
                        "VALUES(?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
                        (
                            identifier,
                            normalized_type,
                            title,
                            description,
                            canonical_json(metadata),
                            normalized_actor,
                        ),
                    )
                    row = connection.execute(
                        "SELECT id, type_id, title, description, metadata_json, created_at, created_by "
                        "FROM entity WHERE id = ?",
                        (identifier,),
                    ).fetchone()
                    if row is None:
                        raise EntityError("Création atomique d’entité non lisible.")
                    rows.append(row)
                    self.store.append_audit(
                        connection,
                        "ENTITY_CREATED",
                        {
                            "entity_id": identifier,
                            "entity_type_id": normalized_type,
                            "actor": normalized_actor,
                        },
                    )
        except sqlite3.IntegrityError as exc:
            raise EntityError("Type d’entité, identifiant d’entité ou batch invalide.") from exc
        return EntityBatchResult(
            entity_type=_entity_type_from_row(type_row),
            entities=tuple(_entity_from_row(self.store, row) for row in rows),
        )

    def get(self, identifier: str) -> Entity:
        """Read exactly one entity by its canonical VERA identifier; this is not FIND."""
        normalized_identifier = _require_entity_identifier(self.store, identifier)
        row = self.store.connection.execute(
            "SELECT id, type_id, title, description, metadata_json, created_at, created_by "
            "FROM entity WHERE id = ?",
            (normalized_identifier,),
        ).fetchone()
        if row is None:
            raise EntityNotFoundError("Entité VERA introuvable.")
        return _entity_from_row(self.store, row)


def _require_type_id(value: str) -> str:
    if not isinstance(value, str) or not ENTITY_TYPE_ID_RE.fullmatch(value):
        raise EntityError("Identifiant de type d’entité invalide.")
    return value


def _require_text(value: str, label: str, *, maximum: int) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > maximum:
        raise EntityError(f"{label} doit être une chaîne canonique non vide.")
    return value


def _require_optional_text(value: str, label: str) -> str:
    if not isinstance(value, str) or value != value.strip():
        raise EntityError(f"{label} doit être une chaîne canonique.")
    return value


def _require_json_object(value: Mapping[str, Any] | None, label: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise EntityError(f"{label} doit être un objet JSON.")
    try:
        return json.loads(canonical_json(dict(value)))
    except (ProfileError, TypeError, ValueError) as exc:
        raise EntityError(f"{label} doit être sérialisable de façon canonique.") from exc


def _require_entity_identifier(store: MemoryStore, value: str) -> str:
    try:
        make_address(store.identity.project_id, "entity", value)
    except AddressError as exc:
        raise EntityError("Identifiant d’entité VERA invalide.") from exc
    return value


def _entity_type_from_row(row: sqlite3.Row) -> EntityType:
    return EntityType(
        id=str(row["id"]),
        label=str(row["label"]),
        description=str(row["description"]),
        schema=_decode_json_object(row["schema_json"], "schema"),
        created_at=str(row["created_at"]),
        created_by=str(row["created_by"]),
    )


def _entity_from_row(store: MemoryStore, row: sqlite3.Row) -> Entity:
    identifier = str(row["id"])
    return Entity(
        id=identifier,
        type_id=str(row["type_id"]),
        title=str(row["title"]),
        description=str(row["description"]),
        metadata=_decode_json_object(row["metadata_json"], "metadata"),
        created_at=str(row["created_at"]),
        created_by=str(row["created_by"]),
        address=make_address(store.identity.project_id, "entity", identifier),
    )


def _decode_json_object(value: object, label: str) -> dict[str, Any]:
    try:
        decoded = json.loads(str(value))
    except (TypeError, ValueError) as exc:
        raise EntityError(f"{label} d’entité illisible.") from exc
    if not isinstance(decoded, dict):
        raise EntityError(f"{label} d’entité non objet.")
    return decoded
