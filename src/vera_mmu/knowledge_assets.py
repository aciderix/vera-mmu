"""Immutable, declarative links between existing VERA knowledge and assets (M2.8)."""

from __future__ import annotations

from dataclasses import dataclass
import sqlite3

from .addressing import AddressError, make_address
from .store import MemoryStore, StoreError


class KnowledgeAssetLinkError(StoreError):
    """Raised when an exact knowledge–asset link is invalid or cannot be recorded."""


class KnowledgeAssetLinkNotFoundError(KnowledgeAssetLinkError):
    """Raised when an exact knowledge–asset pair is not linked."""


@dataclass(frozen=True)
class KnowledgeAssetLink:
    """One immutable declarative association; it is neither evidence nor an admission decision."""

    knowledge_id: str
    asset_id: str
    created_at: str
    created_by: str


class KnowledgeAssetLinkService:
    """Record exact knowledge–asset associations without reading assets or altering knowledge."""

    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def link(self, knowledge_id: str, asset_id: str, *, actor: str = "system") -> KnowledgeAssetLink:
        """Append one exact association and its audit in the same transaction."""
        normalized_knowledge_id = _require_identifier(self.store, "knowledge", knowledge_id)
        normalized_asset_id = _require_identifier(self.store, "asset", asset_id)
        normalized_actor = _require_actor(actor)
        try:
            with self.store.transaction() as connection:
                _require_existing(connection, "knowledge", normalized_knowledge_id)
                _require_existing(connection, "asset", normalized_asset_id)
                connection.execute(
                    "INSERT INTO knowledge_asset_link(knowledge_id, asset_id, created_at, created_by) "
                    "VALUES(?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
                    (normalized_knowledge_id, normalized_asset_id, normalized_actor),
                )
                row = connection.execute(
                    "SELECT knowledge_id, asset_id, created_at, created_by "
                    "FROM knowledge_asset_link WHERE knowledge_id = ? AND asset_id = ?",
                    (normalized_knowledge_id, normalized_asset_id),
                ).fetchone()
                if row is None:
                    raise KnowledgeAssetLinkError("Association knowledge–asset non lisible après création.")
                self.store.append_audit(
                    connection,
                    "KNOWLEDGE_ASSET_LINK_RECORDED",
                    {
                        "knowledge_id": normalized_knowledge_id,
                        "asset_id": normalized_asset_id,
                        "actor": normalized_actor,
                    },
                )
        except sqlite3.IntegrityError as exc:
            raise KnowledgeAssetLinkError("Association knowledge–asset dupliquée ou invalide.") from exc
        return _link_from_row(row)

    def get(self, knowledge_id: str, asset_id: str) -> KnowledgeAssetLink:
        """Read one exact declared pair; listing and traversal are intentionally absent."""
        normalized_knowledge_id = _require_identifier(self.store, "knowledge", knowledge_id)
        normalized_asset_id = _require_identifier(self.store, "asset", asset_id)
        row = self.store.connection.execute(
            "SELECT knowledge_id, asset_id, created_at, created_by "
            "FROM knowledge_asset_link WHERE knowledge_id = ? AND asset_id = ?",
            (normalized_knowledge_id, normalized_asset_id),
        ).fetchone()
        if row is None:
            raise KnowledgeAssetLinkNotFoundError("Association knowledge–asset introuvable.")
        return _link_from_row(row)


def _require_identifier(store: MemoryStore, resource_type: str, value: str) -> str:
    try:
        make_address(store.identity.project_id, resource_type, value)
    except AddressError as exc:
        raise KnowledgeAssetLinkError(f"Identifiant VERA {resource_type} invalide.") from exc
    return value


def _require_actor(value: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > 256:
        raise KnowledgeAssetLinkError("actor doit être une chaîne canonique non vide.")
    return value


def _require_existing(connection: sqlite3.Connection, table: str, identifier: str) -> None:
    if connection.execute(f"SELECT 1 FROM {table} WHERE id = ?", (identifier,)).fetchone() is None:
        raise KnowledgeAssetLinkError(f"Endpoint {table} inconnu.")


def _link_from_row(row: sqlite3.Row) -> KnowledgeAssetLink:
    knowledge_id = str(row["knowledge_id"])
    asset_id = str(row["asset_id"])
    if not knowledge_id or not asset_id:
        raise KnowledgeAssetLinkError("Association knowledge–asset stockée incohérente.")
    return KnowledgeAssetLink(
        knowledge_id=knowledge_id,
        asset_id=asset_id,
        created_at=str(row["created_at"]),
        created_by=_require_actor(str(row["created_by"])),
    )
