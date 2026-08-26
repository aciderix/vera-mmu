"""Generic, append-only and idempotent entity-import batch ledger."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re
import sqlite3
from typing import Any, Mapping, Sequence

from .addressing import AddressError, make_address
from .entities import Entity, EntityBatchResult, EntityError, EntityService, EntityType
from .identity import ProjectIdentity, canonical_json
from .store import MemoryStore, StoreError


_ID_RE = re.compile(r"^[a-z][a-z0-9-]{2,127}$")
_TYPE_ID_RE = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ImportBatchError(StoreError):
    """Raised when a generic import batch is invalid, incompatible or cannot commit atomically."""


@dataclass(frozen=True)
class ImportEntityInput:
    """One source-addressable entity creation in a generic import batch."""

    identifier: str
    source_identifier: str
    title: str
    description: str = ""
    metadata: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class EntityImportBatchInput:
    """All immutable facts that define one deterministic generic entity-import transaction."""

    batch_id: str
    source_system: str
    source_snapshot_sha256: str
    mapping_id: str
    target_type_id: str
    target_type_label: str
    target_type_description: str = ""
    target_type_schema: Mapping[str, Any] | None = None
    actor: str = "system"
    entities: Sequence[ImportEntityInput] = ()


@dataclass(frozen=True)
class ImportBatch:
    """One committed immutable import batch recorded in the Core ledger."""

    id: str
    source_system: str
    source_snapshot_sha256: str
    mapping_id: str
    target_type_id: str
    fingerprint_sha256: str
    committed_at: str
    committed_by: str


@dataclass(frozen=True)
class EntityImportBatchResult:
    """The exact batch result, whether committed now or read idempotently from the ledger."""

    batch: ImportBatch
    entity_type: EntityType
    entities: tuple[Entity, ...]
    commit_state: str
    was_already_committed: bool


class ImportBatchService:
    """Commit or read generic entity-import batches without source I/O or domain semantics."""

    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def commit_entity_import_batch(self, batch: EntityImportBatchInput) -> EntityImportBatchResult:
        """Commit one exact entity import atomically, or return it without writing on exact replay."""
        prepared = _prepare_batch(self.store.identity, batch)
        try:
            with self.store.transaction() as connection:
                previous = connection.execute(
                    "SELECT id, source_system, source_snapshot_sha256, mapping_id, target_type_id, "
                    "fingerprint_sha256, committed_at, committed_by FROM import_batch WHERE id = ?",
                    (prepared.batch_id,),
                ).fetchone()
                if previous is not None:
                    existing = _batch_from_row(previous)
                    if existing.fingerprint_sha256 != prepared.fingerprint_sha256:
                        raise ImportBatchError("L’identifiant de batch existe avec un fingerprint différent.")
                    return _result_from_existing(self.store, connection, existing, prepared.source_identifiers)

                type_row = connection.execute(
                    "SELECT id, label, description, schema_json, created_at, created_by "
                    "FROM entity_type WHERE id = ?",
                    (prepared.target_type_id,),
                ).fetchone()
                created_type = type_row is None
                if created_type:
                    connection.execute(
                        "INSERT INTO entity_type(id, label, description, schema_json, created_at, created_by) "
                        "VALUES(?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
                        (
                            prepared.target_type_id,
                            prepared.target_type_label,
                            prepared.target_type_description,
                            canonical_json(prepared.target_type_schema),
                            prepared.actor,
                        ),
                    )
                    type_row = connection.execute(
                        "SELECT id, label, description, schema_json, created_at, created_by "
                        "FROM entity_type WHERE id = ?",
                        (prepared.target_type_id,),
                    ).fetchone()
                    if type_row is None:
                        raise ImportBatchError("Création de type d’import non lisible.")
                    self.store.append_audit(
                        connection,
                        "ENTITY_TYPE_REGISTERED",
                        {"entity_type_id": prepared.target_type_id, "actor": prepared.actor},
                    )
                elif not _type_row_matches(type_row, prepared):
                    raise ImportBatchError("Le type cible existant est incompatible avec le batch d’import.")

                entity_rows = []
                for item in prepared.entities:
                    connection.execute(
                        "INSERT INTO entity(id, type_id, title, description, metadata_json, created_at, created_by) "
                        "VALUES(?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
                        (
                            item.identifier,
                            prepared.target_type_id,
                            item.title,
                            item.description,
                            canonical_json(item.metadata),
                            prepared.actor,
                        ),
                    )
                    row = connection.execute(
                        "SELECT id, type_id, title, description, metadata_json, created_at, created_by "
                        "FROM entity WHERE id = ?",
                        (item.identifier,),
                    ).fetchone()
                    if row is None:
                        raise ImportBatchError("Création d’entité d’import non lisible.")
                    entity_rows.append(row)
                    self.store.append_audit(
                        connection,
                        "ENTITY_CREATED",
                        {
                            "entity_id": item.identifier,
                            "entity_type_id": prepared.target_type_id,
                            "actor": prepared.actor,
                        },
                    )

                connection.execute(
                    "INSERT INTO import_batch(id, source_system, source_snapshot_sha256, mapping_id, target_type_id, "
                    "fingerprint_sha256, committed_at, committed_by) "
                    "VALUES(?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
                    (
                        prepared.batch_id,
                        prepared.source_system,
                        prepared.source_snapshot_sha256,
                        prepared.mapping_id,
                        prepared.target_type_id,
                        prepared.fingerprint_sha256,
                        prepared.actor,
                    ),
                )
                for item in prepared.entities:
                    connection.execute(
                        "INSERT INTO import_batch_entity(batch_id, source_identifier, entity_id) VALUES(?, ?, ?)",
                        (prepared.batch_id, item.source_identifier, item.identifier),
                    )
                batch_row = connection.execute(
                    "SELECT id, source_system, source_snapshot_sha256, mapping_id, target_type_id, "
                    "fingerprint_sha256, committed_at, committed_by FROM import_batch WHERE id = ?",
                    (prepared.batch_id,),
                ).fetchone()
                if batch_row is None:
                    raise ImportBatchError("Création de batch d’import non lisible.")
                self.store.append_audit(
                    connection,
                    "IMPORT_BATCH_COMMITTED",
                    {
                        "batch_id": prepared.batch_id,
                        "source_system": prepared.source_system,
                        "mapping_id": prepared.mapping_id,
                        "target_type_id": prepared.target_type_id,
                        "entity_count": len(prepared.entities),
                        "actor": prepared.actor,
                    },
                )
        except sqlite3.IntegrityError as exc:
            raise ImportBatchError("Conflit d’entité, de batch ou de lien d’import : transaction rollbackée.") from exc
        return EntityImportBatchResult(
            batch=_batch_from_row(batch_row),
            entity_type=_entity_type_from_row(type_row),
            entities=tuple(_entity_from_row(self.store, row) for row in entity_rows),
            commit_state="COMMITTED",
            was_already_committed=False,
        )


def _prepare_batch(identity: ProjectIdentity, value: object) -> "_PreparedBatch":
    if not isinstance(value, EntityImportBatchInput):
        raise ImportBatchError("batch doit être un EntityImportBatchInput.")
    batch_id = _require_id(value.batch_id, "batch_id")
    source_system = _require_id(value.source_system, "source_system")
    source_snapshot_sha256 = _require_sha256(value.source_snapshot_sha256, "source_snapshot_sha256")
    mapping_id = _require_id(value.mapping_id, "mapping_id")
    target_type_id = _require_type_id(value.target_type_id)
    target_type_label = _require_text(value.target_type_label, "target_type_label", 256)
    target_type_description = _require_optional_text(value.target_type_description, "target_type_description")
    target_type_schema = _require_json_object(value.target_type_schema, "target_type_schema")
    actor = _require_text(value.actor, "actor", 256)
    if not isinstance(value.entities, Sequence) or isinstance(value.entities, (str, bytes)) or not 1 <= len(value.entities) <= 100:
        raise ImportBatchError("Le batch d’import doit contenir entre 1 et 100 entités.")

    entities: list[_PreparedEntity] = []
    for item in value.entities:
        if not isinstance(item, ImportEntityInput):
            raise ImportBatchError("Chaque entité importée doit être un ImportEntityInput.")
        identifier = _require_entity_identifier(identity, item.identifier)
        entities.append(
            _PreparedEntity(
                identifier=identifier,
                source_identifier=_require_source_identifier(item.source_identifier),
                title=_require_text(item.title, "title", 1024),
                description=_require_optional_text(item.description, "description"),
                metadata=_require_json_object(item.metadata, "metadata"),
            )
        )
    identifiers = tuple(item.identifier for item in entities)
    source_identifiers = tuple(item.source_identifier for item in entities)
    if len(set(identifiers)) != len(identifiers):
        raise ImportBatchError("Les identifiants cible d’un batch d’import doivent être uniques.")
    if len(set(source_identifiers)) != len(source_identifiers):
        raise ImportBatchError("Les identifiants source d’un batch d’import doivent être uniques.")
    payload = {
        "batch_id": batch_id,
        "source_system": source_system,
        "source_snapshot_sha256": source_snapshot_sha256,
        "mapping_id": mapping_id,
        "target_type": {
            "id": target_type_id,
            "label": target_type_label,
            "description": target_type_description,
            "schema": target_type_schema,
        },
        "entities": [
            {
                "identifier": item.identifier,
                "source_identifier": item.source_identifier,
                "title": item.title,
                "description": item.description,
                "metadata": item.metadata,
            }
            for item in entities
        ],
    }
    return _PreparedBatch(
        batch_id=batch_id,
        source_system=source_system,
        source_snapshot_sha256=source_snapshot_sha256,
        mapping_id=mapping_id,
        target_type_id=target_type_id,
        target_type_label=target_type_label,
        target_type_description=target_type_description,
        target_type_schema=target_type_schema,
        actor=actor,
        entities=tuple(entities),
        source_identifiers=source_identifiers,
        fingerprint_sha256=sha256(canonical_json(payload).encode("utf-8")).hexdigest(),
    )


def _result_from_existing(
    store: MemoryStore,
    connection: sqlite3.Connection,
    batch: ImportBatch,
    source_identifiers: tuple[str, ...],
) -> EntityImportBatchResult:
    type_row = connection.execute(
        "SELECT id, label, description, schema_json, created_at, created_by FROM entity_type WHERE id = ?",
        (batch.target_type_id,),
    ).fetchone()
    if type_row is None:
        raise ImportBatchError("Le type référencé par le batch existant est absent.")
    rows = []
    for source_identifier in source_identifiers:
        row = connection.execute(
            "SELECT e.id, e.type_id, e.title, e.description, e.metadata_json, e.created_at, e.created_by "
            "FROM import_batch_entity AS link JOIN entity AS e ON e.id = link.entity_id "
            "WHERE link.batch_id = ? AND link.source_identifier = ?",
            (batch.id, source_identifier),
        ).fetchone()
        if row is None:
            raise ImportBatchError("Le batch existant ne contient pas les liens d’entités attendus.")
        rows.append(row)
    return EntityImportBatchResult(
        batch=batch,
        entity_type=_entity_type_from_row(type_row),
        entities=tuple(_entity_from_row(store, row) for row in rows),
        commit_state="COMMITTED",
        was_already_committed=True,
    )


def _type_row_matches(row: sqlite3.Row, batch: "_PreparedBatch") -> bool:
    return (
        str(row[1]) == batch.target_type_label
        and str(row[2]) == batch.target_type_description
        and str(row[3]) == canonical_json(batch.target_type_schema)
    )


def _batch_from_row(row: sqlite3.Row) -> ImportBatch:
    return ImportBatch(
        id=str(row[0]),
        source_system=str(row[1]),
        source_snapshot_sha256=str(row[2]),
        mapping_id=str(row[3]),
        target_type_id=str(row[4]),
        fingerprint_sha256=str(row[5]),
        committed_at=str(row[6]),
        committed_by=str(row[7]),
    )


def _entity_type_from_row(row: sqlite3.Row) -> EntityType:
    return EntityType(
        id=str(row[0]),
        label=str(row[1]),
        description=str(row[2]),
        schema=json.loads(str(row[3])),
        created_at=str(row[4]),
        created_by=str(row[5]),
    )


def _entity_from_row(store: MemoryStore, row: sqlite3.Row) -> Entity:
    identifier = str(row[0])
    return Entity(
        id=identifier,
        type_id=str(row[1]),
        title=str(row[2]),
        description=str(row[3]),
        metadata=json.loads(str(row[4])),
        created_at=str(row[5]),
        created_by=str(row[6]),
        address=make_address(store.identity.project_id, "entity", identifier),
    )


def _require_id(value: object, label: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise ImportBatchError(f"{label} doit contenir 3 à 128 caractères minuscules alphanumériques ou des tirets.")
    return value


def _require_type_id(value: object) -> str:
    if not isinstance(value, str) or not _TYPE_ID_RE.fullmatch(value):
        raise ImportBatchError("target_type_id est invalide.")
    return value


def _require_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise ImportBatchError(f"{label} doit être un SHA-256 canonique.")
    return value


def _require_text(value: object, label: str, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip() or "\r" in value or "\n" in value or len(value) > maximum:
        raise ImportBatchError(f"{label} doit être une chaîne non vide d’au plus {maximum} caractères sur une ligne.")
    return value


def _require_optional_text(value: object, label: str) -> str:
    if not isinstance(value, str) or "\r" in value or "\n" in value or len(value) > 4096:
        raise ImportBatchError(f"{label} doit contenir au plus 4096 caractères sur une ligne.")
    return value


def _require_json_object(value: object, label: str) -> dict[str, Any]:
    candidate = {} if value is None else value
    if not isinstance(candidate, Mapping):
        raise ImportBatchError(f"{label} doit être un objet JSON.")
    try:
        normalized = json.loads(canonical_json(dict(candidate)))
    except (TypeError, ValueError) as exc:
        raise ImportBatchError(f"{label} doit être un objet JSON canonisable.") from exc
    if not isinstance(normalized, dict):
        raise ImportBatchError(f"{label} doit être un objet JSON.")
    return normalized


def _require_entity_identifier(identity: ProjectIdentity, value: object) -> str:
    if not isinstance(value, str):
        raise ImportBatchError("identifier doit être une chaîne.")
    try:
        make_address(identity.project_id, "entity", value)
    except AddressError as exc:
        raise ImportBatchError("identifier d’entité invalide.") from exc
    return value


def _require_source_identifier(value: object) -> str:
    if not isinstance(value, str) or not value or len(value) > 512 or "\x00" in value or "\r" in value or "\n" in value:
        raise ImportBatchError("source_identifier doit être une chaîne non vide, bornée et sur une ligne.")
    return value


@dataclass(frozen=True)
class _PreparedEntity:
    identifier: str
    source_identifier: str
    title: str
    description: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class _PreparedBatch:
    batch_id: str
    source_system: str
    source_snapshot_sha256: str
    mapping_id: str
    target_type_id: str
    target_type_label: str
    target_type_description: str
    target_type_schema: dict[str, Any]
    actor: str
    entities: tuple[_PreparedEntity, ...]
    source_identifiers: tuple[str, ...]
    fingerprint_sha256: str
