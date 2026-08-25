"""Generic immutable symbol registry for the VERA-MMU Core (M2.12)."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
import sqlite3
from typing import Any, Mapping

from .addressing import AddressError, make_address
from .identity import ProfileError, canonical_json
from .store import MemoryStore, StoreError


SYMBOL_KIND_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")


class SymbolError(StoreError):
    """Raised when a symbol violates the generic registry contract."""


class SymbolNotFoundError(SymbolError):
    """Raised when an exact symbol read finds no matching identifier."""


@dataclass(frozen=True)
class Symbol:
    """One immutable, declarative technical or structural symbol."""

    id: str
    entity_id: str
    kind: str
    path: str
    identifier: str
    signature: str
    metadata: dict[str, Any]
    created_at: str
    created_by: str
    address: str


class SymbolService:
    """Create and read exact generic symbols; scanning and resolution are out of scope."""

    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def create(
        self,
        identifier: str,
        entity_id: str,
        kind: str,
        path: str,
        symbol_identifier: str,
        *,
        signature: str = "",
        metadata: Mapping[str, Any] | None = None,
        actor: str = "system",
    ) -> Symbol:
        """Create one immutable symbol for a pre-existing entity and audit it atomically."""
        normalized_identifier = _require_symbol_identifier(self.store, identifier)
        normalized_entity_id = _require_entity_identifier(self.store, entity_id)
        normalized_kind = _require_kind(kind)
        normalized_path = _require_path(path)
        normalized_symbol_identifier = _require_text(symbol_identifier, "identifier", maximum=512)
        normalized_signature = _require_optional_text(signature, "signature", maximum=2048)
        normalized_metadata = _require_json_object(metadata, "metadata")
        normalized_actor = _require_text(actor, "actor", maximum=256)
        try:
            with self.store.transaction() as connection:
                if connection.execute("SELECT 1 FROM entity WHERE id = ?", (normalized_entity_id,)).fetchone() is None:
                    raise SymbolError("Entité propriétaire inconnue ou non enregistrée.")
                connection.execute(
                    "INSERT INTO symbol("
                    "id, entity_id, kind, path, identifier, signature, metadata_json, created_at, created_by"
                    ") VALUES(?, ?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
                    (
                        normalized_identifier,
                        normalized_entity_id,
                        normalized_kind,
                        normalized_path,
                        normalized_symbol_identifier,
                        normalized_signature,
                        canonical_json(normalized_metadata),
                        normalized_actor,
                    ),
                )
                row = connection.execute(
                    "SELECT id, entity_id, kind, path, identifier, signature, metadata_json, created_at, created_by "
                    "FROM symbol WHERE id = ?",
                    (normalized_identifier,),
                ).fetchone()
                if row is None:
                    raise SymbolError("Création de symbole non lisible.")
                self.store.append_audit(
                    connection,
                    "SYMBOL_CREATED",
                    {"symbol_id": normalized_identifier, "entity_id": normalized_entity_id, "actor": normalized_actor},
                )
        except sqlite3.IntegrityError as exc:
            raise SymbolError("Identifiant ou emplacement sémantique de symbole déjà utilisé ou invalide.") from exc
        return _symbol_from_row(self.store, row)

    def get(self, identifier: str) -> Symbol:
        """Read exactly one symbol by canonical VERA identifier; this is not FIND."""
        normalized_identifier = _require_symbol_identifier(self.store, identifier)
        row = self.store.connection.execute(
            "SELECT id, entity_id, kind, path, identifier, signature, metadata_json, created_at, created_by "
            "FROM symbol WHERE id = ?",
            (normalized_identifier,),
        ).fetchone()
        if row is None:
            raise SymbolNotFoundError("Symbole VERA introuvable.")
        return _symbol_from_row(self.store, row)


def _require_symbol_identifier(store: MemoryStore, value: str) -> str:
    try:
        make_address(store.identity.project_id, "symbol", value)
    except AddressError as exc:
        raise SymbolError("Identifiant de symbole VERA invalide.") from exc
    return value


def _require_entity_identifier(store: MemoryStore, value: str) -> str:
    try:
        make_address(store.identity.project_id, "entity", value)
    except AddressError as exc:
        raise SymbolError("Identifiant d’entité propriétaire VERA invalide.") from exc
    return value


def _require_kind(value: str) -> str:
    if not isinstance(value, str) or not SYMBOL_KIND_RE.fullmatch(value):
        raise SymbolError("kind de symbole invalide : une forme majuscule déclarative est requise.")
    return value


def _require_path(value: str) -> str:
    if not isinstance(value, str) or value != value.strip() or len(value) > 2048:
        raise SymbolError("path de symbole doit être une chaîne déclarative canonique.")
    if "\x00" in value or "\\" in value or value.startswith("/") or ".." in value.split("/"):
        raise SymbolError("path de symbole invalide ou traversant.")
    return value


def _require_text(value: str, label: str, *, maximum: int) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > maximum:
        raise SymbolError(f"{label} doit être une chaîne canonique non vide.")
    if "\x00" in value or "/" in value or "\\" in value:
        raise SymbolError(f"{label} de symbole contient un séparateur interdit.")
    return value


def _require_optional_text(value: str, label: str, *, maximum: int) -> str:
    if not isinstance(value, str) or value != value.strip() or len(value) > maximum or "\x00" in value:
        raise SymbolError(f"{label} doit être une chaîne canonique.")
    return value


def _require_json_object(value: Mapping[str, Any] | None, label: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise SymbolError(f"{label} doit être un objet JSON.")
    try:
        return json.loads(canonical_json(dict(value)))
    except (ProfileError, TypeError, ValueError) as exc:
        raise SymbolError(f"{label} doit être sérialisable de façon canonique.") from exc


def _decode_json_object(value: object, label: str) -> dict[str, Any]:
    try:
        decoded = json.loads(str(value))
    except (TypeError, ValueError) as exc:
        raise SymbolError(f"{label} de symbole illisible.") from exc
    if not isinstance(decoded, dict):
        raise SymbolError(f"{label} de symbole non objet.")
    return decoded


def _symbol_from_row(store: MemoryStore, row: sqlite3.Row) -> Symbol:
    symbol_id = str(row["id"])
    return Symbol(
        id=symbol_id,
        entity_id=str(row["entity_id"]),
        kind=str(row["kind"]),
        path=str(row["path"]),
        identifier=str(row["identifier"]),
        signature=str(row["signature"]),
        metadata=_decode_json_object(row["metadata_json"], "metadata"),
        created_at=str(row["created_at"]),
        created_by=str(row["created_by"]),
        address=make_address(store.identity.project_id, "symbol", symbol_id),
    )
