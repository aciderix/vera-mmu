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


class AretKnowledgeReadError(ValueError):
    """Raised when a bounded ARET V1 knowledge page cannot be observed safely."""


@dataclass(frozen=True)
class AretV1KnowledgeSourceRecord:
    """One raw ARET V1 knowledge row; it is neither a VERA knowledge nor a proof."""

    source_id: str
    source_type: str
    source_status: str
    title: str
    content: str
    component_id: str | None
    function_id: str | None
    brick_id: str | None
    supersedes_id: str | None
    version: int
    content_hash: str
    created_at: str
    updated_at: str
    created_by: str
    effective_at: str


@dataclass(frozen=True)
class AretV1KnowledgeSourcePage:
    """One stable-order bounded knowledge source observation only."""

    source_path: Path
    source_snapshot_sha256: str
    records: tuple[AretV1KnowledgeSourceRecord, ...]
    next_after_id: str | None
    read_state: str = "SOURCE_ROWS_OBSERVED"


def _require_inspection(source_root: str | Path, value: object) -> tuple[Path, AretV1SchemaSnapshotInspection]:
    root = Path(source_root)
    manifest = aret_v1_schema_manifest()
    if not root.is_absolute() or root != root.resolve() or root.is_symlink() or not root.is_dir():
        raise AretKnowledgeReadError("source_root doit être un répertoire absolu, canonique, existant et non lié.")
    if not isinstance(value, AretV1SchemaSnapshotInspection):
        raise AretKnowledgeReadError("schema_inspection doit être une inspection SQLite ARET V1 vérifiée.")
    snapshot = value.source_path
    if (
        value.source_root not in {None, root}
        or value.migration_versions != manifest.migration_versions
        or value.application_tables != manifest.application_tables
        or not snapshot.is_absolute()
        or snapshot != snapshot.resolve()
        or snapshot.is_symlink()
        or not snapshot.is_file()
        or value.source_access_mode != "SQLITE_READ_ONLY_SCHEMA"
        or value.inspection_state != "SCHEMA_MANIFEST_VERIFIED"
        or not isinstance(value.source_snapshot_sha256, str)
        or not _SHA256_RE.fullmatch(value.source_snapshot_sha256)
    ):
        raise AretKnowledgeReadError("schema_inspection doit rester liée au snapshot ARET V1 inspecté et vérifié.")
    return snapshot, value


def _require_after_id(value: object) -> str:
    if value is None:
        return ""
    if not isinstance(value, str) or not value or len(value) > 256 or any(char in value for char in ("\x00", "\r", "\n")):
        raise AretKnowledgeReadError("after_id doit être absent ou un identifiant source non vide sur une ligne.")
    return value


def _require_limit(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= _MAX_PAGE_SIZE:
        raise AretKnowledgeReadError(f"limit doit être un entier entre 1 et {_MAX_PAGE_SIZE}.")
    return value


def _snapshot_hash(path: Path) -> str:
    digest = sha256()
    try:
        with path.open("rb") as stream:
            while chunk := stream.read(64 * 1024):
                digest.update(chunk)
    except OSError as exc:
        raise AretKnowledgeReadError("Lecture du snapshot ARET V1 impossible.") from exc
    return digest.hexdigest()


def _read_rows(snapshot: Path, after_id: str, limit: int) -> tuple[AretV1KnowledgeSourceRecord, ...]:
    try:
        connection = sqlite3.connect(f"{snapshot.as_uri()}?mode=ro&immutable=1", uri=True, isolation_level=None)
        connection.execute("PRAGMA query_only = ON")
        rows = tuple(
            connection.execute(
                "SELECT id, type, status, title, content, component_id, function_id, brick_id, supersedes_id, "
                "version, content_hash, created_at, updated_at, created_by, effective_at "
                "FROM knowledge WHERE id > ? ORDER BY id LIMIT ?",
                (after_id, limit + 1),
            )
        )
    except sqlite3.Error as exc:
        raise AretKnowledgeReadError("Lecture paginée de knowledge ARET V1 impossible.") from exc
    finally:
        try:
            connection.close()
        except UnboundLocalError:
            pass
    records: list[AretV1KnowledgeSourceRecord] = []
    for row in rows:
        if (
            not all(isinstance(row[index], str) for index in (0, 1, 2, 3, 4, 10, 11, 12, 13, 14))
            or any(row[index] is not None and not isinstance(row[index], str) for index in (5, 6, 7, 8))
            or isinstance(row[9], bool)
            or not isinstance(row[9], int)
            or not _SHA256_RE.fullmatch(str(row[10]))
            or sha256(str(row[4]).encode("utf-8")).hexdigest() != str(row[10])
        ):
            raise AretKnowledgeReadError("Une ligne knowledge ARET V1 est invalide ou son content_hash ne correspond pas au contenu.")
        records.append(AretV1KnowledgeSourceRecord(*row))
    return tuple(records)


def read_aret_v1_knowledge_page(
    *,
    source_root: str | Path,
    schema_inspection: AretV1SchemaSnapshotInspection,
    after_id: str | None,
    limit: int,
) -> AretV1KnowledgeSourcePage:
    """Observe exactly one ARET V1 knowledge page; no conversion, VERA write, or source mutation occurs."""
    snapshot, inspection = _require_inspection(source_root, schema_inspection)
    cursor = _require_after_id(after_id)
    bounded_limit = _require_limit(limit)
    before_hash = _snapshot_hash(snapshot)
    if before_hash != inspection.source_snapshot_sha256:
        raise AretKnowledgeReadError("Le snapshot ARET V1 ne correspond plus au hash de l’inspection vérifiée.")
    rows = _read_rows(snapshot, cursor, bounded_limit)
    if _snapshot_hash(snapshot) != before_hash:
        raise AretKnowledgeReadError("Le snapshot ARET V1 a changé pendant la lecture de knowledge.")
    records = rows[:bounded_limit]
    return AretV1KnowledgeSourcePage(snapshot, before_hash, records, records[-1].source_id if len(rows) > bounded_limit else None)
