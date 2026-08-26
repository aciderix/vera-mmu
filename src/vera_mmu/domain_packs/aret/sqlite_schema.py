from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
import sqlite3

from .git_identity import AretV1GitSourceIdentity
from .source_attestation import ARET_V1_BASELINE_REVISION
from .schema import aret_v1_schema_manifest


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class AretSqliteSchemaInspectionError(ValueError):
    """Raised when an attested ARET V1 snapshot cannot satisfy the bounded schema inspection."""


@dataclass(frozen=True)
class AretV1SchemaSnapshotInspection:
    """Read-only verification of migration and table-name metadata; never a legacy data import."""

    source_path: Path
    source_snapshot_sha256: str
    migration_versions: tuple[int, ...]
    application_tables: tuple[str, ...]
    source_access_mode: str = "SQLITE_READ_ONLY_SCHEMA"
    inspection_state: str = "SCHEMA_MANIFEST_VERIFIED"


def _require_verified_source_identity(source_root: str | Path, value: object) -> tuple[Path, AretV1GitSourceIdentity]:
    root = Path(source_root)
    if not root.is_absolute() or root != root.resolve() or root.is_symlink() or not root.is_dir():
        raise AretSqliteSchemaInspectionError("source_root doit être un répertoire absolu, canonique, existant et non lié.")
    if not isinstance(value, AretV1GitSourceIdentity):
        raise AretSqliteSchemaInspectionError("source_identity doit être une identité Git ARET V1 vérifiée.")
    snapshot = root / ".aret-memory" / "aret_memory.sqlite"
    if (
        value.source_root != root
        or value.expected_legacy_revision != ARET_V1_BASELINE_REVISION
        or value.commit_hash != ARET_V1_BASELINE_REVISION
        or value.working_tree_state != "CLEAN"
        or value.identity_state != "VERIFIED_CLEAN_BASELINE"
        or not isinstance(value.source_snapshot_sha256, str)
        or not _SHA256_RE.fullmatch(value.source_snapshot_sha256)
        or snapshot.is_symlink()
        or not snapshot.is_file()
    ):
        raise AretSqliteSchemaInspectionError("source_identity doit rester liée à un snapshot ARET V1 propre et vérifié.")
    return snapshot, value


def _snapshot_hash(snapshot: Path) -> str:
    digest = sha256()
    try:
        with snapshot.open("rb") as stream:
            while chunk := stream.read(64 * 1024):
                digest.update(chunk)
    except OSError as exc:
        raise AretSqliteSchemaInspectionError("Lecture du snapshot ARET V1 impossible.") from exc
    return digest.hexdigest()


def _read_schema_metadata(snapshot: Path) -> tuple[tuple[int, ...], tuple[str, ...]]:
    uri = f"{snapshot.as_uri()}?mode=ro&immutable=1"
    try:
        connection = sqlite3.connect(uri, uri=True, isolation_level=None)
    except sqlite3.Error as exc:
        raise AretSqliteSchemaInspectionError("Ouverture SQLite read-only du snapshot ARET V1 impossible.") from exc
    try:
        connection.execute("PRAGMA query_only = ON")
        migration_versions = tuple(
            row[0] for row in connection.execute("SELECT version FROM schema_migrations ORDER BY version")
        )
        application_tables = tuple(
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_schema "
                "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'knowledge_fts%' "
                "ORDER BY name"
            )
        )
    except sqlite3.Error as exc:
        raise AretSqliteSchemaInspectionError("Lecture des seules métadonnées de schéma ARET V1 impossible.") from exc
    finally:
        connection.close()
    return migration_versions, application_tables


def inspect_aret_v1_schema_snapshot(
    *,
    source_root: str | Path,
    source_identity: AretV1GitSourceIdentity,
) -> AretV1SchemaSnapshotInspection:
    """Verify only the V1 migration/table manifest; no business row is read or converted."""
    snapshot, identity = _require_verified_source_identity(source_root, source_identity)
    before_hash = _snapshot_hash(snapshot)
    if before_hash != identity.source_snapshot_sha256:
        raise AretSqliteSchemaInspectionError("Le snapshot ARET V1 ne correspond plus au hash de l’identité vérifiée.")
    migration_versions, application_tables = _read_schema_metadata(snapshot)
    if _snapshot_hash(snapshot) != before_hash:
        raise AretSqliteSchemaInspectionError("Le snapshot ARET V1 a changé pendant l’inspection de schéma.")

    manifest = aret_v1_schema_manifest()
    if migration_versions != manifest.migration_versions or application_tables != manifest.application_tables:
        raise AretSqliteSchemaInspectionError("Le manifeste SQLite du snapshot ne correspond pas au schéma applicatif ARET V1 observé.")
    return AretV1SchemaSnapshotInspection(
        source_path=snapshot,
        source_snapshot_sha256=before_hash,
        migration_versions=migration_versions,
        application_tables=application_tables,
    )
