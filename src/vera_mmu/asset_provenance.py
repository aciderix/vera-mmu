"""Immutable declared provenance references for existing VERA assets (M2.10)."""

from __future__ import annotations

from dataclasses import dataclass
import re
import sqlite3

from .addressing import AddressError, make_address
from .store import MemoryStore, StoreError


SOURCE_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._~-]{0,255}")
SHA256_RE = re.compile(r"[0-9a-f]{64}")
MAX_ASSET_SOURCE_LIST_LIMIT = 100


class AssetSourceError(StoreError):
    """Raised when an immutable declared asset-source reference is invalid or cannot be recorded."""


class AssetSourceNotFoundError(AssetSourceError):
    """Raised when an exact asset-source reference is not found."""


@dataclass(frozen=True)
class AssetSource:
    """One immutable declared document slice reference attached to a VERA asset."""

    id: str
    asset_id: str
    source_repository: str
    source_revision: str
    source_path: str
    source_start_line: int
    source_end_line: int
    source_section: str
    source_hash: str
    created_at: str
    created_by: str


class AssetSourceService:
    """Attach and read declared asset provenance only; file access, fetching, comparison and proof are excluded."""

    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def attach(
        self,
        identifier: str,
        asset_id: str,
        *,
        repository: str,
        revision: str,
        path: str,
        start_line: int,
        end_line: int,
        section: str,
        source_hash: str,
        actor: str = "system",
    ) -> AssetSource:
        """Attach one declared source slice to an existing asset without opening or comparing it."""
        normalized_identifier = _require_source_identifier(identifier)
        normalized_asset_id = _require_asset_identifier(self.store, asset_id)
        normalized_repository = _require_text(repository, "repository", maximum=512)
        normalized_revision = _require_text(revision, "revision", maximum=512)
        normalized_path = _require_relative_path(path)
        normalized_start, normalized_end = _require_line_range(start_line, end_line)
        normalized_section = _require_text(section, "section", maximum=1024)
        normalized_hash = _require_hash(source_hash)
        normalized_actor = _require_text(actor, "actor", maximum=256)
        try:
            with self.store.transaction() as connection:
                if connection.execute("SELECT 1 FROM asset WHERE id = ?", (normalized_asset_id,)).fetchone() is None:
                    raise AssetSourceError("Asset cible inconnu.")
                connection.execute(
                    "INSERT INTO asset_source("
                    "id, asset_id, source_repository, source_revision, source_path, source_start_line, "
                    "source_end_line, source_section, source_hash, created_at, created_by"
                    ") VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
                    (
                        normalized_identifier,
                        normalized_asset_id,
                        normalized_repository,
                        normalized_revision,
                        normalized_path,
                        normalized_start,
                        normalized_end,
                        normalized_section,
                        normalized_hash,
                        normalized_actor,
                    ),
                )
                row = connection.execute(
                    "SELECT id, asset_id, source_repository, source_revision, source_path, source_start_line, "
                    "source_end_line, source_section, source_hash, created_at, created_by "
                    "FROM asset_source WHERE id = ?",
                    (normalized_identifier,),
                ).fetchone()
                if row is None:
                    raise AssetSourceError("Attache de provenance d’asset non lisible.")
                self.store.append_audit(
                    connection,
                    "ASSET_SOURCE_ATTACHED",
                    {
                        "asset_source_id": normalized_identifier,
                        "asset_id": normalized_asset_id,
                        "source_repository": normalized_repository,
                        "source_revision": normalized_revision,
                        "source_path": normalized_path,
                        "source_start_line": normalized_start,
                        "source_end_line": normalized_end,
                        "source_hash": normalized_hash,
                        "actor": normalized_actor,
                    },
                )
        except sqlite3.IntegrityError as exc:
            raise AssetSourceError("Référence de provenance d’asset dupliquée ou invalide.") from exc
        return _source_from_row(row)

    def get(self, identifier: str) -> AssetSource:
        """Read exactly one declared source reference; this does not open the source document."""
        normalized_identifier = _require_source_identifier(identifier)
        row = self.store.connection.execute(
            "SELECT id, asset_id, source_repository, source_revision, source_path, source_start_line, "
            "source_end_line, source_section, source_hash, created_at, created_by "
            "FROM asset_source WHERE id = ?",
            (normalized_identifier,),
        ).fetchone()
        if row is None:
            raise AssetSourceNotFoundError("Référence de provenance d’asset introuvable.")
        return _source_from_row(row)

    def list_for(self, asset_id: str, *, limit: int = MAX_ASSET_SOURCE_LIST_LIMIT) -> tuple[AssetSource, ...]:
        """Read a bounded, ordered source list for one exact asset identifier; no endpoint content is read."""
        normalized_asset_id = _require_asset_identifier(self.store, asset_id)
        normalized_limit = _require_limit(limit)
        if self.store.connection.execute("SELECT 1 FROM asset WHERE id = ?", (normalized_asset_id,)).fetchone() is None:
            raise AssetSourceError("Asset cible inconnu.")
        rows = self.store.connection.execute(
            "SELECT id, asset_id, source_repository, source_revision, source_path, source_start_line, "
            "source_end_line, source_section, source_hash, created_at, created_by "
            "FROM asset_source WHERE asset_id = ? "
            "ORDER BY source_path, source_start_line, source_end_line, id LIMIT ?",
            (normalized_asset_id, normalized_limit),
        ).fetchall()
        return tuple(_source_from_row(row) for row in rows)


def _require_source_identifier(value: str) -> str:
    if not isinstance(value, str) or not SOURCE_ID_RE.fullmatch(value):
        raise AssetSourceError("Identifiant de source d’asset invalide.")
    return value


def _require_asset_identifier(store: MemoryStore, value: str) -> str:
    try:
        make_address(store.identity.project_id, "asset", value)
    except AddressError as exc:
        raise AssetSourceError("Identifiant asset VERA invalide.") from exc
    return value


def _require_text(value: str, label: str, *, maximum: int) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > maximum:
        raise AssetSourceError(f"{label} doit être une chaîne canonique non vide.")
    return value


def _require_relative_path(value: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > 4096:
        raise AssetSourceError("Chemin de source d’asset invalide.")
    if value.startswith(("/", "\\")) or "\\" in value or re.match(r"^[A-Za-z]:", value):
        raise AssetSourceError("Chemin de source d’asset absolu ou à lecteur interdit.")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise AssetSourceError("Chemin de source d’asset traversant ou non canonique.")
    return value


def _require_line_range(start_line: int, end_line: int) -> tuple[int, int]:
    if isinstance(start_line, bool) or isinstance(end_line, bool) or not isinstance(start_line, int) or not isinstance(end_line, int):
        raise AssetSourceError("Les lignes de source d’asset doivent être numériques.")
    if start_line < 1 or end_line < start_line:
        raise AssetSourceError("Plage de lignes de source d’asset invalide.")
    return start_line, end_line


def _require_hash(value: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise AssetSourceError("Hash de source d’asset SHA-256 hexadécimal invalide.")
    return value


def _require_limit(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= MAX_ASSET_SOURCE_LIST_LIMIT:
        raise AssetSourceError("Limite de lecture de sources d’asset invalide.")
    return value


def _source_from_row(row: sqlite3.Row) -> AssetSource:
    identifier = _require_source_identifier(str(row["id"]))
    asset_id = str(row["asset_id"])
    repository = _require_text(str(row["source_repository"]), "repository", maximum=512)
    revision = _require_text(str(row["source_revision"]), "revision", maximum=512)
    path = _require_relative_path(str(row["source_path"]))
    start_line, end_line = _require_line_range(int(row["source_start_line"]), int(row["source_end_line"]))
    section = _require_text(str(row["source_section"]), "section", maximum=1024)
    source_hash = _require_hash(str(row["source_hash"]))
    created_by = _require_text(str(row["created_by"]), "created_by", maximum=256)
    return AssetSource(
        id=identifier,
        asset_id=asset_id,
        source_repository=repository,
        source_revision=revision,
        source_path=path,
        source_start_line=start_line,
        source_end_line=end_line,
        source_section=section,
        source_hash=source_hash,
        created_at=str(row["created_at"]),
        created_by=created_by,
    )
