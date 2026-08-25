"""Deterministic SQLite migration support for the VERA-MMU Core (M2.1)."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
import sqlite3
from typing import Iterable


MIGRATION_RE = re.compile(r"^(?P<version>0*[1-9][0-9]*)_(?P<name>[a-z0-9][a-z0-9_-]*)\.sql$")


class MigrationError(RuntimeError):
    """Raised when a migration inventory is invalid or no longer matches its ledger."""


@dataclass(frozen=True)
class Migration:
    """One versioned SQL migration with an immutable content checksum."""

    version: int
    name: str
    path: Path
    checksum: str

    @property
    def sql(self) -> str:
        try:
            return self.path.read_text(encoding="utf-8")
        except OSError as exc:
            raise MigrationError(f"Migration illisible : {self.path.name}") from exc


class MigrationRunner:
    """Discover and apply a closed SQL migration inventory to one SQLite database."""

    def __init__(self, schema_dir: str | Path | None = None) -> None:
        self.schema_dir = Path(schema_dir) if schema_dir is not None else Path(__file__).with_name("schema")

    def discover(self) -> tuple[Migration, ...]:
        """Return a sorted, validated migration inventory without applying it."""
        if not self.schema_dir.is_dir():
            raise MigrationError(f"Répertoire de migrations introuvable : {self.schema_dir}")
        migrations: list[Migration] = []
        versions: set[int] = set()
        for path in sorted(self.schema_dir.glob("*.sql")):
            match = MIGRATION_RE.fullmatch(path.name)
            if match is None:
                raise MigrationError(f"Nom de migration invalide : {path.name}")
            version = int(match.group("version"))
            if version in versions:
                raise MigrationError(f"Version de migration dupliquée : {version}")
            try:
                checksum = sha256(path.read_bytes()).hexdigest()
            except OSError as exc:
                raise MigrationError(f"Migration illisible : {path.name}") from exc
            versions.add(version)
            migrations.append(Migration(version, match.group("name"), path, checksum))
        ordered = tuple(sorted(migrations, key=lambda item: item.version))
        if not ordered or ordered[0].version != 1:
            raise MigrationError("La migration initiale 001 est requise.")
        expected_versions = tuple(range(1, ordered[-1].version + 1))
        if tuple(migration.version for migration in ordered) != expected_versions:
            raise MigrationError("Les versions de migration doivent être continues à partir de 001.")
        return ordered

    def apply(self, connection: sqlite3.Connection) -> tuple[Migration, ...]:
        """Apply missing migrations and reject any mutation of an applied migration."""
        migrations = self.discover()
        applied = self._applied(connection)
        for migration in migrations:
            recorded = applied.get(migration.version)
            if recorded is not None:
                recorded_name, recorded_checksum = recorded
                if recorded_name != migration.name or recorded_checksum != migration.checksum:
                    raise MigrationError(f"Checksum de migration modifié : {migration.path.name}")
                continue
            self._apply_one(connection, migration)
        return migrations

    @staticmethod
    def _applied(connection: sqlite3.Connection) -> dict[int, tuple[str, str]]:
        exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'schema_migrations'"
        ).fetchone()
        if exists is None:
            return {}
        return {
            int(row[0]): (str(row[1]), str(row[2]))
            for row in connection.execute("SELECT version, name, checksum FROM schema_migrations")
        }

    @staticmethod
    def _apply_one(connection: sqlite3.Connection, migration: Migration) -> None:
        """Apply SQL and its ledger entry in one transaction, rolling back on any failure."""
        escaped_name = migration.name.replace("'", "''")
        script = (
            "BEGIN IMMEDIATE;\n"
            f"{migration.sql}\n"
            "INSERT INTO schema_migrations(version, name, checksum, applied_at) "
            f"VALUES({migration.version}, '{escaped_name}', '{migration.checksum}', strftime('%Y-%m-%dT%H:%M:%fZ','now'));\n"
            "COMMIT;\n"
        )
        try:
            connection.executescript(script)
        except sqlite3.DatabaseError as exc:
            try:
                connection.rollback()
            except sqlite3.DatabaseError:
                pass
            raise MigrationError(f"Échec de migration {migration.path.name}") from exc


def migration_checksums(migrations: Iterable[Migration]) -> dict[int, str]:
    """Return a deterministic version-to-checksum map for diagnostics and bundles."""
    return {migration.version: migration.checksum for migration in migrations}
