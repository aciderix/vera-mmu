"""Immutable, hash-verified binary assets stored in the VERA SQLite Core (M2.7)."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import re
import sqlite3

from .addressing import AddressError, make_address
from .store import MemoryStore, StoreError


MAX_ASSET_BYTES = 1_048_576
_MEDIA_TYPE_RE = re.compile(r"[a-z0-9][a-z0-9!#$&^_.+-]{0,126}/[a-z0-9][a-z0-9!#$&^_.+-]{0,126}")
_HASH_RE = re.compile(r"[0-9a-f]{64}")


class AssetError(StoreError):
    """Raised when an immutable Core asset is invalid, inconsistent or cannot be recorded."""


class AssetNotFoundError(AssetError):
    """Raised when an exact asset identifier does not exist."""


@dataclass(frozen=True)
class Asset:
    """Exact immutable metadata for one binary Core asset; content requires explicit verified reading."""

    id: str
    address: str
    content_hash: str
    byte_length: int
    media_type: str
    created_at: str
    created_by: str


class AssetService:
    """Persist and read small Core-owned bytes without paths, import, execution or proof semantics."""

    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def record(
        self,
        identifier: str,
        content: bytes,
        *,
        media_type: str,
        actor: str = "system",
    ) -> Asset:
        """Append one asset and its creation audit atomically after fully validating its bytes."""
        asset_id = _require_asset_identifier(self.store, identifier)
        normalized_content = _require_content(content)
        normalized_media_type = _require_media_type(media_type)
        normalized_actor = _require_actor(actor)
        content_hash = sha256(normalized_content).hexdigest()
        try:
            with self.store.transaction() as connection:
                connection.execute(
                    "INSERT INTO asset(id, content_hash, byte_length, media_type, content, created_at, created_by) "
                    "VALUES(?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
                    (
                        asset_id,
                        content_hash,
                        len(normalized_content),
                        normalized_media_type,
                        normalized_content,
                        normalized_actor,
                    ),
                )
                row = connection.execute(
                    "SELECT id, content_hash, byte_length, media_type, created_at, created_by "
                    "FROM asset WHERE id = ?",
                    (asset_id,),
                ).fetchone()
                if row is None:
                    raise AssetError("Asset non lisible après enregistrement.")
                self.store.append_audit(
                    connection,
                    "ASSET_RECORDED",
                    {
                        "asset_id": asset_id,
                        "content_hash": content_hash,
                        "byte_length": len(normalized_content),
                        "media_type": normalized_media_type,
                        "actor": normalized_actor,
                    },
                )
        except sqlite3.IntegrityError as exc:
            raise AssetError("Asset dupliqué ou invalide.") from exc
        return _asset_from_row(self.store, row)

    def get(self, identifier: str) -> Asset:
        """Read exact asset metadata without exposing its binary content."""
        asset_id = _require_asset_identifier(self.store, identifier)
        row = self.store.connection.execute(
            "SELECT id, content_hash, byte_length, media_type, created_at, created_by FROM asset WHERE id = ?",
            (asset_id,),
        ).fetchone()
        if row is None:
            raise AssetNotFoundError("Asset introuvable.")
        return _asset_from_row(self.store, row)

    def read(self, identifier: str) -> bytes:
        """Read exact binary content only after stored hash, declared size and metadata all verify."""
        asset_id = _require_asset_identifier(self.store, identifier)
        row = self.store.connection.execute(
            "SELECT id, content_hash, byte_length, media_type, content, created_at, created_by FROM asset WHERE id = ?",
            (asset_id,),
        ).fetchone()
        if row is None:
            raise AssetNotFoundError("Asset introuvable.")
        _asset_from_row(self.store, row)
        content = row["content"]
        if not isinstance(content, bytes):
            raise AssetError("Contenu d’asset non binaire.")
        byte_length = int(row["byte_length"])
        content_hash = str(row["content_hash"])
        if len(content) != byte_length or sha256(content).hexdigest() != content_hash:
            raise AssetError("Intégrité d’asset invalide : hash ou taille incohérent.")
        return content


def _require_asset_identifier(store: MemoryStore, value: str) -> str:
    try:
        make_address(store.identity.project_id, "asset", value)
    except AddressError as exc:
        raise AssetError("Identifiant asset VERA invalide.") from exc
    return value


def _require_content(value: bytes) -> bytes:
    if not isinstance(value, bytes):
        raise AssetError("Le contenu d’asset doit être binaire (bytes).")
    if not value or len(value) > MAX_ASSET_BYTES:
        raise AssetError(f"Le contenu d’asset doit contenir entre 1 et {MAX_ASSET_BYTES} bytes.")
    return value


def _require_media_type(value: str) -> str:
    if not isinstance(value, str) or not _MEDIA_TYPE_RE.fullmatch(value) or len(value) > 255:
        raise AssetError("media_type doit être un type MIME canonique en minuscules.")
    return value


def _require_actor(value: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > 256:
        raise AssetError("actor doit être une chaîne canonique non vide.")
    return value


def _asset_from_row(store: MemoryStore, row: sqlite3.Row) -> Asset:
    identifier = str(row["id"])
    content_hash = str(row["content_hash"])
    byte_length = row["byte_length"]
    if not _HASH_RE.fullmatch(content_hash):
        raise AssetError("Hash d’asset stocké invalide.")
    if not isinstance(byte_length, int) or isinstance(byte_length, bool) or not 1 <= byte_length <= MAX_ASSET_BYTES:
        raise AssetError("Taille d’asset stockée invalide.")
    media_type = _require_media_type(str(row["media_type"]))
    created_by = _require_actor(str(row["created_by"]))
    try:
        address = make_address(store.identity.project_id, "asset", identifier)
    except AddressError as exc:
        raise AssetError("Identifiant d’asset stocké invalide.") from exc
    return Asset(
        id=identifier,
        address=address,
        content_hash=content_hash,
        byte_length=byte_length,
        media_type=media_type,
        created_at=str(row["created_at"]),
        created_by=created_by,
    )
