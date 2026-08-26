from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import sqlite3

from .component_reader import _require_after_id, _require_limit
from .sqlite_schema import AretV1SchemaSnapshotInspection


class AretBrickReadError(ValueError):
    """Raised when a bounded ARET V1 brick page cannot be observed safely."""


@dataclass(frozen=True)
class AretV1BrickSourceRecord:
    source_id: str
    component_id: str | None
    title: str
    state: str
    description: str
    milestone: str | None
    target_platform: str | None
    priority: int
    created_at: str
    created_by: str


@dataclass(frozen=True)
class AretV1BrickSourcePage:
    source_path: Path
    source_snapshot_sha256: str
    records: tuple[AretV1BrickSourceRecord, ...]
    next_after_id: str | None
    read_state: str = "SOURCE_ROWS_OBSERVED"


def _hash(path: Path) -> str:
    digest = sha256()
    try:
        with path.open("rb") as stream:
            while chunk := stream.read(64 * 1024):
                digest.update(chunk)
    except OSError as exc:
        raise AretBrickReadError("Lecture du snapshot ARET V1 impossible.") from exc
    return digest.hexdigest()


def _require_inspection(source_root: str | Path, value: object) -> tuple[Path, AretV1SchemaSnapshotInspection]:
    root = Path(source_root)
    if not root.is_absolute() or root != root.resolve() or root.is_symlink() or not root.is_dir():
        raise AretBrickReadError("source_root doit être un répertoire absolu, canonique, existant et non lié.")
    if not isinstance(value, AretV1SchemaSnapshotInspection) or value.source_root not in {None, root}:
        raise AretBrickReadError("schema_inspection doit être lié à la racine source ARET vérifiée.")
    snapshot = value.source_path
    if not snapshot.is_absolute() or snapshot != snapshot.resolve() or snapshot.is_symlink() or not snapshot.is_file() or value.source_access_mode != "SQLITE_READ_ONLY_SCHEMA" or value.inspection_state != "SCHEMA_MANIFEST_VERIFIED":
        raise AretBrickReadError("schema_inspection ne fournit pas un snapshot ARET V1 admissible.")
    return snapshot, value


def read_aret_v1_brick_page(*, source_root: str | Path, schema_inspection: AretV1SchemaSnapshotInspection, after_id: str | None, limit: int) -> AretV1BrickSourcePage:
    """Observe one brick page only through SQLite mode=ro&immutable=1; no conversion or VERA write occurs."""
    snapshot, inspection = _require_inspection(source_root, schema_inspection)
    cursor, bounded = _require_after_id(after_id), _require_limit(limit)
    before = _hash(snapshot)
    if before != inspection.source_snapshot_sha256:
        raise AretBrickReadError("Le snapshot ARET V1 a divergé de son inspection.")
    try:
        connection = sqlite3.connect(f"{snapshot.as_uri()}?mode=ro&immutable=1", uri=True, isolation_level=None)
        connection.execute("PRAGMA query_only = ON")
        rows = tuple(connection.execute("SELECT id, component_id, title, state, description, milestone, target_platform, priority, created_at, created_by FROM brick WHERE id > ? ORDER BY id LIMIT ?", (cursor, bounded + 1)))
    except sqlite3.Error as exc:
        raise AretBrickReadError("Lecture paginée de brick ARET V1 impossible.") from exc
    finally:
        try:
            connection.close()
        except UnboundLocalError:
            pass
    if _hash(snapshot) != before:
        raise AretBrickReadError("Le snapshot ARET V1 a changé pendant la lecture de brick.")
    try:
        records = tuple(AretV1BrickSourceRecord(*row) for row in rows)
    except TypeError as exc:
        raise AretBrickReadError("Une ligne brick ARET V1 est de forme inattendue.") from exc
    page = records[:bounded]
    return AretV1BrickSourcePage(snapshot, before, page, page[-1].source_id if len(records) > bounded else None)
