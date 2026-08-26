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


class AretFunctionSymbolReadError(ValueError):
    """Raised when a bounded ARET V1 function-symbol page cannot be observed safely."""


@dataclass(frozen=True)
class AretV1FunctionSymbolSourceRecord:
    """One raw legacy function-symbol row; it is not a VERA Symbol or imported record."""

    source_id: str
    component_id: str
    module: str
    symbol: str
    calling_convention: str
    created_at: str
    created_by: str


@dataclass(frozen=True)
class AretV1FunctionSymbolSourcePage:
    """A bounded stable-order observation page from the legacy function_symbol table only."""

    source_path: Path
    source_snapshot_sha256: str
    records: tuple[AretV1FunctionSymbolSourceRecord, ...]
    next_after_id: str | None
    read_state: str = "SOURCE_ROWS_OBSERVED"


def _require_schema_inspection(source_root: str | Path, value: object) -> tuple[Path, AretV1SchemaSnapshotInspection]:
    root = Path(source_root)
    if not root.is_absolute() or root != root.resolve() or root.is_symlink() or not root.is_dir():
        raise AretFunctionSymbolReadError("source_root doit être un répertoire absolu, canonique, existant et non lié.")
    if not isinstance(value, AretV1SchemaSnapshotInspection):
        raise AretFunctionSymbolReadError("schema_inspection doit être une inspection M4.9 ARET V1 vérifiée.")
    snapshot = value.source_path
    manifest = aret_v1_schema_manifest()
    if (
        value.source_root not in {None, root}
        or not snapshot.is_absolute()
        or snapshot != snapshot.resolve()
        or snapshot.is_symlink()
        or not snapshot.is_file()
        or value.migration_versions != manifest.migration_versions
        or value.application_tables != manifest.application_tables
        or value.source_access_mode != "SQLITE_READ_ONLY_SCHEMA"
        or value.inspection_state != "SCHEMA_MANIFEST_VERIFIED"
        or not isinstance(value.source_snapshot_sha256, str)
        or not _SHA256_RE.fullmatch(value.source_snapshot_sha256)
    ):
        raise AretFunctionSymbolReadError("schema_inspection doit rester liée au snapshot ARET V1 inspecté et vérifié.")
    return snapshot, value


def _require_after_id(value: object) -> str:
    if value is None:
        return ""
    if not isinstance(value, str) or not value or len(value) > 256 or any(char in value for char in ("\x00", "\r", "\n")):
        raise AretFunctionSymbolReadError("after_id doit être absent ou un identifiant source non vide sur une ligne.")
    return value


def _require_limit(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= _MAX_PAGE_SIZE:
        raise AretFunctionSymbolReadError(f"limit doit être un entier entre 1 et {_MAX_PAGE_SIZE}.")
    return value


def _snapshot_hash(snapshot: Path) -> str:
    digest = sha256()
    try:
        with snapshot.open("rb") as stream:
            while chunk := stream.read(64 * 1024):
                digest.update(chunk)
    except OSError as exc:
        raise AretFunctionSymbolReadError("Lecture du snapshot ARET V1 impossible.") from exc
    return digest.hexdigest()


def _read_rows(snapshot: Path, after_id: str, limit: int) -> tuple[AretV1FunctionSymbolSourceRecord, ...]:
    try:
        connection = sqlite3.connect(f"{snapshot.as_uri()}?mode=ro&immutable=1", uri=True, isolation_level=None)
    except sqlite3.Error as exc:
        raise AretFunctionSymbolReadError("Ouverture SQLite read-only du snapshot ARET V1 impossible.") from exc
    try:
        connection.execute("PRAGMA query_only = ON")
        rows = tuple(connection.execute(
            "SELECT id, component_id, module, symbol, calling_convention, created_at, created_by "
            "FROM function_symbol WHERE id > ? ORDER BY id LIMIT ?", (after_id, limit + 1)
        ))
    except sqlite3.Error as exc:
        raise AretFunctionSymbolReadError("Lecture paginée de function_symbol ARET V1 impossible.") from exc
    finally:
        connection.close()
    if not all(all(isinstance(value, str) for value in row) for row in rows):
        raise AretFunctionSymbolReadError("Une ligne function_symbol ARET V1 contient une valeur non textuelle inattendue.")
    return tuple(AretV1FunctionSymbolSourceRecord(*row) for row in rows)


def read_aret_v1_function_symbol_page(*, source_root: str | Path, schema_inspection: AretV1SchemaSnapshotInspection, after_id: str | None, limit: int) -> AretV1FunctionSymbolSourcePage:
    """Observe one raw function_symbol page only; no conversion, import or VERA store write occurs."""
    snapshot, inspection = _require_schema_inspection(source_root, schema_inspection)
    cursor = _require_after_id(after_id)
    bounded_limit = _require_limit(limit)
    before_hash = _snapshot_hash(snapshot)
    if before_hash != inspection.source_snapshot_sha256:
        raise AretFunctionSymbolReadError("Le snapshot ARET V1 ne correspond plus au hash de l’inspection vérifiée.")
    rows = _read_rows(snapshot, cursor, bounded_limit)
    if _snapshot_hash(snapshot) != before_hash:
        raise AretFunctionSymbolReadError("Le snapshot ARET V1 a changé pendant la lecture de function_symbol.")
    records = rows[:bounded_limit]
    return AretV1FunctionSymbolSourcePage(snapshot, before_hash, records, records[-1].source_id if len(rows) > bounded_limit else None)
