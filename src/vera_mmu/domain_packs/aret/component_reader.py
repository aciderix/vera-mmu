from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
import sqlite3

from .schema import aret_v1_schema_manifest
from .sqlite_schema import AretV1SchemaSnapshotInspection


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_MAX_PAGE_SIZE = 100


class AretComponentSourceReadError(ValueError):
    """Raised when a bounded ARET V1 component-source page cannot be safely observed."""


@dataclass(frozen=True)
class AretV1ComponentSourceRecord:
    """One raw legacy component row; this is not an entity, mapping, or imported record."""

    source_id: str
    title: str
    description: str
    created_at: str
    created_by: str


@dataclass(frozen=True)
class AretV1ComponentSourcePage:
    """A bounded, stable-order observation page from the legacy component table only."""

    source_path: Path
    source_snapshot_sha256: str
    records: tuple[AretV1ComponentSourceRecord, ...]
    next_after_id: str | None
    read_state: str = "SOURCE_ROWS_OBSERVED"


def _require_schema_inspection(source_root: str | Path, value: object) -> tuple[Path, AretV1SchemaSnapshotInspection]:
    root = Path(source_root)
    if not root.is_absolute() or root != root.resolve() or root.is_symlink() or not root.is_dir():
        raise AretComponentSourceReadError("source_root doit être un répertoire absolu, canonique, existant et non lié.")
    if not isinstance(value, AretV1SchemaSnapshotInspection):
        raise AretComponentSourceReadError("schema_inspection doit être une inspection M4.9 ARET V1 vérifiée.")
    snapshot = value.source_path
    manifest = aret_v1_schema_manifest()
    if (
        value.source_path != snapshot
        or value.source_root not in {None, root}
        or not snapshot.is_absolute()
        or snapshot != snapshot.resolve()
        or value.migration_versions != manifest.migration_versions
        or value.application_tables != manifest.application_tables
        or value.source_access_mode != "SQLITE_READ_ONLY_SCHEMA"
        or value.inspection_state != "SCHEMA_MANIFEST_VERIFIED"
        or not isinstance(value.source_snapshot_sha256, str)
        or not _SHA256_RE.fullmatch(value.source_snapshot_sha256)
        or snapshot.is_symlink()
        or not snapshot.is_file()
    ):
        raise AretComponentSourceReadError("schema_inspection doit rester liée au snapshot ARET V1 inspecté et vérifié.")
    return snapshot, value


def _require_after_id(value: object) -> str:
    if value is None:
        return ""
    if not isinstance(value, str) or not value or len(value) > 256 or any(char in value for char in ("\x00", "\r", "\n")):
        raise AretComponentSourceReadError("after_id doit être absent ou un identifiant source non vide sur une ligne.")
    return value


def _require_limit(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= _MAX_PAGE_SIZE:
        raise AretComponentSourceReadError(f"limit doit être un entier entre 1 et {_MAX_PAGE_SIZE}.")
    return value


def _snapshot_hash(snapshot: Path) -> str:
    digest = sha256()
    try:
        with snapshot.open("rb") as stream:
            while chunk := stream.read(64 * 1024):
                digest.update(chunk)
    except OSError as exc:
        raise AretComponentSourceReadError("Lecture du snapshot ARET V1 impossible.") from exc
    return digest.hexdigest()


def _read_component_rows(snapshot: Path, after_id: str, limit: int) -> tuple[AretV1ComponentSourceRecord, ...]:
    uri = f"{snapshot.as_uri()}?mode=ro&immutable=1"
    try:
        connection = sqlite3.connect(uri, uri=True, isolation_level=None)
    except sqlite3.Error as exc:
        raise AretComponentSourceReadError("Ouverture SQLite read-only du snapshot ARET V1 impossible.") from exc
    try:
        connection.execute("PRAGMA query_only = ON")
        rows = tuple(
            connection.execute(
                "SELECT id, title, description, created_at, created_by "
                "FROM component WHERE id > ? ORDER BY id LIMIT ?",
                (after_id, limit + 1),
            )
        )
    except sqlite3.Error as exc:
        raise AretComponentSourceReadError("Lecture paginée de component ARET V1 impossible.") from exc
    finally:
        connection.close()

    records: list[AretV1ComponentSourceRecord] = []
    for row in rows:
        if not all(isinstance(value, str) for value in row):
            raise AretComponentSourceReadError("Une ligne component ARET V1 contient une valeur non textuelle inattendue.")
        records.append(AretV1ComponentSourceRecord(*row))
    return tuple(records)


def read_aret_v1_component_page(
    *,
    source_root: str | Path,
    schema_inspection: AretV1SchemaSnapshotInspection,
    after_id: str | None,
    limit: int,
) -> AretV1ComponentSourcePage:
    """Observe one raw component page only; no conversion, import, or VERA store write occurs."""
    snapshot, inspection = _require_schema_inspection(source_root, schema_inspection)
    cursor = _require_after_id(after_id)
    bounded_limit = _require_limit(limit)
    before_hash = _snapshot_hash(snapshot)
    if before_hash != inspection.source_snapshot_sha256:
        raise AretComponentSourceReadError("Le snapshot ARET V1 ne correspond plus au hash de l’inspection vérifiée.")
    rows = _read_component_rows(snapshot, cursor, bounded_limit)
    if _snapshot_hash(snapshot) != before_hash:
        raise AretComponentSourceReadError("Le snapshot ARET V1 a changé pendant la lecture de component.")

    page_records = rows[:bounded_limit]
    next_after_id = page_records[-1].source_id if len(rows) > bounded_limit else None
    return AretV1ComponentSourcePage(
        source_path=snapshot,
        source_snapshot_sha256=before_hash,
        records=page_records,
        next_after_id=next_after_id,
    )
