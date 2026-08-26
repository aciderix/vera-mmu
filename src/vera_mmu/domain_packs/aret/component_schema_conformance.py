from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import sqlite3

from .sqlite_schema import AretV1SchemaSnapshotInspection


_EXPECTED_COMPONENT_COLUMNS = (
    ("id", "TEXT", True, True, None),
    ("title", "TEXT", True, False, None),
    ("description", "TEXT", True, False, "''"),
    ("created_at", "TEXT", True, False, None),
    ("created_by", "TEXT", True, False, None),
)


class AretComponentSchemaConformanceError(ValueError):
    """Raised when the read-only component-table contract differs from ARET V1."""


@dataclass(frozen=True)
class AretV1ComponentSchemaConformance:
    """Exact read-only component-table metadata required before a structural import."""

    source_path: Path
    source_snapshot_sha256: str
    columns: tuple[tuple[str, str, bool, bool, str | None], ...]
    source_access_mode: str = "SQLITE_READ_ONLY_COMPONENT_SCHEMA"
    conformance_state: str = "COMPONENT_SCHEMA_CONFORMANT"


def _snapshot_hash(path: Path) -> str:
    digest = sha256()
    try:
        with path.open("rb") as stream:
            while chunk := stream.read(64 * 1024):
                digest.update(chunk)
    except OSError as exc:
        raise AretComponentSchemaConformanceError("Le snapshot component ARET V1 est illisible.") from exc
    return digest.hexdigest()


def _require_inspection(value: object) -> AretV1SchemaSnapshotInspection:
    if not isinstance(value, AretV1SchemaSnapshotInspection):
        raise AretComponentSchemaConformanceError("inspection doit être une inspection SQLite ARET V1.")
    if (
        value.source_access_mode,
        value.inspection_state,
    ) != ("SQLITE_READ_ONLY_SCHEMA", "SCHEMA_MANIFEST_VERIFIED"):
        raise AretComponentSchemaConformanceError("inspection doit rester un manifeste ARET V1 vérifié en lecture seule.")
    if not value.source_path.is_absolute() or value.source_path.is_symlink() or not value.source_path.is_file():
        raise AretComponentSchemaConformanceError("Le snapshot inspecté doit rester un fichier absolu, régulier et non lié.")
    if _snapshot_hash(value.source_path) != value.source_snapshot_sha256:
        raise AretComponentSchemaConformanceError("Le snapshot a dérivé depuis l’inspection de manifeste.")
    return value


def _read_component_columns(snapshot: Path) -> tuple[tuple[str, str, bool, bool, str | None], ...]:
    uri = f"{snapshot.as_uri()}?mode=ro&immutable=1"
    try:
        connection = sqlite3.connect(uri, uri=True, isolation_level=None)
    except sqlite3.Error as exc:
        raise AretComponentSchemaConformanceError("Ouverture SQLite read-only de component impossible.") from exc
    try:
        connection.execute("PRAGMA query_only = ON")
        rows = connection.execute("PRAGMA table_info(component)").fetchall()
    except sqlite3.Error as exc:
        raise AretComponentSchemaConformanceError("Lecture read-only des métadonnées component impossible.") from exc
    finally:
        connection.close()
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


def inspect_aret_v1_component_schema(
    *,
    inspection: AretV1SchemaSnapshotInspection,
) -> AretV1ComponentSchemaConformance:
    """Verify exact component import columns using only read-only SQLite metadata queries."""
    verified = _require_inspection(inspection)
    before_hash = _snapshot_hash(verified.source_path)
    columns = _read_component_columns(verified.source_path)
    if _snapshot_hash(verified.source_path) != before_hash:
        raise AretComponentSchemaConformanceError("Le snapshot a changé pendant la conformité component.")
    if columns != _EXPECTED_COMPONENT_COLUMNS:
        raise AretComponentSchemaConformanceError("Les colonnes component ne correspondent pas au contrat ARET V1 importable.")
    return AretV1ComponentSchemaConformance(
        source_path=verified.source_path,
        source_snapshot_sha256=before_hash,
        columns=columns,
    )
