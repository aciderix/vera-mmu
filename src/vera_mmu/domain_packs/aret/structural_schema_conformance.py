from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
import sqlite3

from .schema import aret_v1_schema_manifest
from .sqlite_schema import AretV1SchemaSnapshotInspection


_EXPECTED_FUNCTION_COLUMNS = (
    ("id", "TEXT", True, True, None),
    ("component_id", "TEXT", True, False, None),
    ("module", "TEXT", True, False, "''"),
    ("symbol", "TEXT", True, False, None),
    ("calling_convention", "TEXT", True, False, "''"),
    ("created_at", "TEXT", True, False, None),
    ("created_by", "TEXT", True, False, None),
)
_EXPECTED_BRICK_COLUMNS = (
    ("id", "TEXT", True, True, None),
    ("component_id", "TEXT", False, False, None),
    ("title", "TEXT", True, False, None),
    ("state", "TEXT", True, False, None),
    ("description", "TEXT", True, False, "''"),
    ("created_at", "TEXT", True, False, None),
    ("created_by", "TEXT", True, False, None),
    ("milestone", "TEXT", False, False, None),
    ("target_platform", "TEXT", False, False, None),
    ("priority", "INTEGER", True, False, "3"),
)
_EXPECTED_COMPONENT_FOREIGN_KEY = (("component", "component_id", "id"),)
_EXPECTED_FUNCTION_UNIQUE = (("component_id", "module", "symbol"),)
_EXPECTED_BRICK_STATES = ("PLANNED", "ACTIVE", "BLOCKED", "DONE", "OBSOLETE")
_EXPECTED_PRIORITY_RANGE = (1, 5)
_EXPECTED_ROADMAP_INDEX = ("milestone", "target_platform", "priority", "state", "component_id", "id")
_STATE_CHECK_RE = re.compile(
    r"CHECK\s*\(\s*STATE\s+IN\s*\(\s*'PLANNED'\s*,\s*'ACTIVE'\s*,\s*'BLOCKED'\s*,\s*'DONE'\s*,\s*'OBSOLETE'\s*\)\s*\)",
    re.IGNORECASE,
)
_PRIORITY_CHECK_RE = re.compile(r"CHECK\s*\(\s*PRIORITY\s+BETWEEN\s+1\s+AND\s+5\s*\)", re.IGNORECASE)


class AretStructuralSchemaConformanceError(ValueError):
    """Raised when read-only structural metadata differs from the ARET V1 import contract."""


@dataclass(frozen=True)
class AretV1FunctionSymbolSchemaConformance:
    """Exact read-only function-symbol metadata required before any structural import."""

    source_path: Path
    source_snapshot_sha256: str
    columns: tuple[tuple[str, str, bool, bool, str | None], ...]
    foreign_keys: tuple[tuple[str, str, str], ...]
    unique_constraints: tuple[tuple[str, ...], ...]
    source_access_mode: str = "SQLITE_READ_ONLY_FUNCTION_SYMBOL_SCHEMA"
    conformance_state: str = "FUNCTION_SYMBOL_SCHEMA_CONFORMANT"


@dataclass(frozen=True)
class AretV1BrickSchemaConformance:
    """Exact read-only brick metadata required before any structural import."""

    source_path: Path
    source_snapshot_sha256: str
    columns: tuple[tuple[str, str, bool, bool, str | None], ...]
    foreign_keys: tuple[tuple[str, str, str], ...]
    state_values: tuple[str, ...]
    priority_range: tuple[int, int]
    roadmap_index_columns: tuple[str, ...]
    source_access_mode: str = "SQLITE_READ_ONLY_BRICK_SCHEMA"
    conformance_state: str = "BRICK_SCHEMA_CONFORMANT"


def _snapshot_hash(path: Path) -> str:
    digest = sha256()
    try:
        with path.open("rb") as stream:
            while chunk := stream.read(64 * 1024):
                digest.update(chunk)
    except OSError as exc:
        raise AretStructuralSchemaConformanceError("Le snapshot structurel ARET V1 est illisible.") from exc
    return digest.hexdigest()


def _require_inspection(value: object) -> AretV1SchemaSnapshotInspection:
    if not isinstance(value, AretV1SchemaSnapshotInspection):
        raise AretStructuralSchemaConformanceError("inspection doit être une inspection SQLite ARET V1.")
    manifest = aret_v1_schema_manifest()
    if (
        value.migration_versions != manifest.migration_versions
        or value.application_tables != manifest.application_tables
        or value.source_access_mode != "SQLITE_READ_ONLY_SCHEMA"
        or value.inspection_state != "SCHEMA_MANIFEST_VERIFIED"
        or not value.source_path.is_absolute()
        or value.source_path.is_symlink()
        or not value.source_path.is_file()
        or _snapshot_hash(value.source_path) != value.source_snapshot_sha256
    ):
        raise AretStructuralSchemaConformanceError("inspection doit rester liée au snapshot ARET V1 vérifié et stable.")
    return value


def _column_rows(connection: sqlite3.Connection, table_name: str) -> tuple[tuple[str, str, bool, bool, str | None], ...]:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return tuple(
        (
            str(row[1]),
            str(row[2]).upper(),
            bool(row[3]) or bool(row[5]),
            bool(row[5]),
            None if row[4] is None else str(row[4]),
        )
        for row in rows
    )


def _foreign_keys(connection: sqlite3.Connection, table_name: str) -> tuple[tuple[str, str, str], ...]:
    rows = connection.execute(f"PRAGMA foreign_key_list({table_name})").fetchall()
    return tuple(sorted((str(row[2]), str(row[3]), str(row[4])) for row in rows))


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _unique_constraints(connection: sqlite3.Connection) -> tuple[tuple[str, ...], ...]:
    constraints: list[tuple[str, ...]] = []
    for row in connection.execute("PRAGMA index_list(function_symbol)"):
        if not bool(row[2]) or str(row[3]) != "u":
            continue
        index_name = str(row[1])
        fields = tuple(str(info[2]) for info in connection.execute(f"PRAGMA index_info({_quote_identifier(index_name)})"))
        constraints.append(fields)
    return tuple(sorted(constraints))


def _table_sql(connection: sqlite3.Connection, table_name: str) -> str:
    row = connection.execute(
        "SELECT sql FROM sqlite_schema WHERE type = 'table' AND name = ?", (table_name,)
    ).fetchone()
    if row is None or not isinstance(row[0], str):
        raise AretStructuralSchemaConformanceError("La déclaration SQL structurelle attendue est absente.")
    return str(row[0])


def _roadmap_index_columns(connection: sqlite3.Connection) -> tuple[str, ...]:
    for row in connection.execute("PRAGMA index_list(brick)"):
        if str(row[1]) != "idx_brick_roadmap":
            continue
        index_name = str(row[1])
        return tuple(str(info[2]) for info in connection.execute(f"PRAGMA index_info({_quote_identifier(index_name)})"))
    return ()


def _open_read_only(snapshot: Path) -> sqlite3.Connection:
    try:
        connection = sqlite3.connect(f"{snapshot.as_uri()}?mode=ro&immutable=1", uri=True, isolation_level=None)
        connection.execute("PRAGMA query_only = ON")
        return connection
    except sqlite3.Error as exc:
        raise AretStructuralSchemaConformanceError("Ouverture SQLite structurelle read-only impossible.") from exc


def inspect_aret_v1_function_symbol_schema(
    *, inspection: AretV1SchemaSnapshotInspection
) -> AretV1FunctionSymbolSchemaConformance:
    """Verify function_symbol metadata through bounded read-only SQLite metadata queries only."""
    verified = _require_inspection(inspection)
    before_hash = _snapshot_hash(verified.source_path)
    connection = _open_read_only(verified.source_path)
    try:
        columns = _column_rows(connection, "function_symbol")
        foreign_keys = _foreign_keys(connection, "function_symbol")
        unique_constraints = _unique_constraints(connection)
    except sqlite3.Error as exc:
        raise AretStructuralSchemaConformanceError("Lecture des métadonnées function_symbol impossible.") from exc
    finally:
        connection.close()
    if _snapshot_hash(verified.source_path) != before_hash:
        raise AretStructuralSchemaConformanceError("Le snapshot a changé pendant la conformité function_symbol.")
    if columns != _EXPECTED_FUNCTION_COLUMNS or foreign_keys != _EXPECTED_COMPONENT_FOREIGN_KEY or unique_constraints != _EXPECTED_FUNCTION_UNIQUE:
        raise AretStructuralSchemaConformanceError("function_symbol ne correspond pas au contrat ARET V1 importable.")
    return AretV1FunctionSymbolSchemaConformance(
        source_path=verified.source_path,
        source_snapshot_sha256=before_hash,
        columns=columns,
        foreign_keys=foreign_keys,
        unique_constraints=unique_constraints,
    )


def inspect_aret_v1_brick_schema(*, inspection: AretV1SchemaSnapshotInspection) -> AretV1BrickSchemaConformance:
    """Verify brick metadata through bounded read-only SQLite metadata queries only."""
    verified = _require_inspection(inspection)
    before_hash = _snapshot_hash(verified.source_path)
    connection = _open_read_only(verified.source_path)
    try:
        columns = _column_rows(connection, "brick")
        foreign_keys = _foreign_keys(connection, "brick")
        table_sql = _table_sql(connection, "brick")
        roadmap_index_columns = _roadmap_index_columns(connection)
    except sqlite3.Error as exc:
        raise AretStructuralSchemaConformanceError("Lecture des métadonnées brick impossible.") from exc
    finally:
        connection.close()
    if _snapshot_hash(verified.source_path) != before_hash:
        raise AretStructuralSchemaConformanceError("Le snapshot a changé pendant la conformité brick.")
    if (
        columns != _EXPECTED_BRICK_COLUMNS
        or foreign_keys != _EXPECTED_COMPONENT_FOREIGN_KEY
        or not _STATE_CHECK_RE.search(table_sql)
        or not _PRIORITY_CHECK_RE.search(table_sql)
        or roadmap_index_columns != _EXPECTED_ROADMAP_INDEX
    ):
        raise AretStructuralSchemaConformanceError("brick ne correspond pas au contrat ARET V1 importable.")
    return AretV1BrickSchemaConformance(
        source_path=verified.source_path,
        source_snapshot_sha256=before_hash,
        columns=columns,
        foreign_keys=foreign_keys,
        state_values=_EXPECTED_BRICK_STATES,
        priority_range=_EXPECTED_PRIORITY_RANGE,
        roadmap_index_columns=roadmap_index_columns,
    )
