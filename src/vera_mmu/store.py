"""Canonical SQLite store substrate for the VERA-MMU Core (M2.1)."""

from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterator, Mapping

from .identity import ProjectIdentity, canonical_json, project_identity
from .migrations import Migration, MigrationError, MigrationRunner, migration_checksums
from .runtime import RuntimeLocator
from .workspace import Workspace, resolve_workspace


class StoreError(RuntimeError):
    """Raised when a local VERA store cannot be opened safely or consistently."""


class StoreIdentityError(StoreError):
    """Raised when an existing store belongs to a different ProjectIdentity."""


class MemoryStore:
    """Small transport-neutral SQLite substrate; domain services are intentionally absent."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        locator: RuntimeLocator,
        workspace: Workspace,
        identity: ProjectIdentity,
        migrations: tuple[Migration, ...],
    ) -> None:
        self._connection = connection
        self.locator = locator
        self.workspace = workspace
        self.identity = identity
        self.migrations = migrations
        self.last_sync_status: dict[str, object] = {"format": "vera-memory-sync/v1", "status": "NOT_ATTEMPTED"}

    @classmethod
    def open(
        cls,
        profile: Mapping[str, Any],
        profile_path: str | Path,
        *,
        schema_dir: str | Path | None = None,
    ) -> "MemoryStore":
        """Open one project-bound store, applying only validated Core migrations."""
        workspace = resolve_workspace(profile, profile_path)
        locator = RuntimeLocator.from_workspace(profile, workspace)
        identity = project_identity(profile, workspace)
        try:
            locator.runtime_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise StoreError(f"Création du runtime impossible : {locator.runtime_dir}") from exc

        try:
            connection = sqlite3.connect(locator.sqlite_path, timeout=5.0, isolation_level=None)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA busy_timeout = 5000")
        except sqlite3.DatabaseError as exc:
            raise StoreError(f"Ouverture SQLite impossible : {locator.sqlite_path}") from exc

        try:
            migrations = MigrationRunner(schema_dir).apply(connection)
            store = cls(connection, locator, workspace, identity, migrations)
            store._bind_identity()
            return store
        except Exception:
            connection.close()
            raise

    @property
    def connection(self) -> sqlite3.Connection:
        """Expose the connection for future transport-neutral services, not for client input."""
        return self._connection

    @property
    def migration_checksums(self) -> dict[int, str]:
        """Return the current migration ledger for diagnostics and future bundle manifests."""
        return migration_checksums(self.migrations)

    def metadata(self) -> dict[str, Any]:
        """Return decoded canonical metadata; malformed JSON is an integrity failure."""
        rows = self._connection.execute("SELECT key, value_json FROM store_metadata ORDER BY key").fetchall()
        try:
            return {str(row["key"]): json.loads(str(row["value_json"])) for row in rows}
        except (TypeError, ValueError) as exc:
            raise StoreError("Métadonnée de store non canonique ou illisible.") from exc

    def audit_events(self) -> list[dict[str, Any]]:
        """Return technical audit records in immutable creation order."""
        rows = self._connection.execute(
            "SELECT id, occurred_at, action, payload_json FROM store_audit ORDER BY id"
        ).fetchall()
        try:
            return [
                {
                    "id": int(row["id"]),
                    "occurred_at": str(row["occurred_at"]),
                    "action": str(row["action"]),
                    "payload": json.loads(str(row["payload_json"])),
                }
                for row in rows
            ]
        except (TypeError, ValueError) as exc:
            raise StoreError("Audit technique non canonique ou illisible.") from exc

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Provide one explicit atomic transaction, composing nested Core operations with a savepoint."""
        nested = self._connection.in_transaction
        savepoint = "vera_core_nested"
        try:
            if nested:
                self._connection.execute(f"SAVEPOINT {savepoint}")
            else:
                self._connection.execute("BEGIN IMMEDIATE")
            yield self._connection
            if nested:
                self._connection.execute(f"RELEASE SAVEPOINT {savepoint}")
            else:
                self._connection.execute("COMMIT")
                self._auto_sync_after_commit()
        except Exception:
            try:
                if nested:
                    self._connection.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
                    self._connection.execute(f"RELEASE SAVEPOINT {savepoint}")
                else:
                    self._connection.execute("ROLLBACK")
            except sqlite3.DatabaseError:
                pass
            raise

    def append_audit(
        self,
        connection: sqlite3.Connection,
        action: str,
        payload: Mapping[str, Any],
    ) -> None:
        """Append one Core audit record inside an already-open store transaction."""
        if connection is not self._connection:
            raise StoreError("La connexion d’audit doit appartenir au store actif.")
        if not isinstance(action, str) or not action or len(action) > 128:
            raise StoreError("Action d’audit invalide.")
        if not isinstance(payload, Mapping):
            raise StoreError("Payload d’audit invalide.")
        self._append_audit(connection, action, payload)

    def rebind_identity(self, identity: ProjectIdentity, *, actor: str) -> None:
        """Replace the bound identity only inside an explicit, auditable Core transaction."""
        if not isinstance(identity, ProjectIdentity):
            raise StoreError("Identité de rebind invalide.")
        if not isinstance(actor, str) or not actor or actor != actor.strip() or len(actor) > 256:
            raise StoreError("Actor de rebind invalide.")
        old_identity = self.metadata().get("project_identity")
        if old_identity != self.identity.as_dict():
            raise StoreIdentityError("Identité SQLite inattendue pendant le rebind.")
        with self.transaction() as connection:
            connection.execute(
                "UPDATE store_metadata SET value_json = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE key = 'project_identity'",
                (canonical_json(identity.as_dict()),),
            )
            self._append_audit(connection, "PROJECT_PROFILE_REBOUND", {"old_identity": old_identity, "new_identity": identity.as_dict(), "actor": actor})
        self.identity = identity

    def close(self) -> None:
        """Close the underlying SQLite connection without modifying the store."""
        self._connection.close()

    def _auto_sync_after_commit(self) -> None:
        """Persist only memory after a successful outer Core transaction.

        Git failure is retained for diagnostics and never rolls a committed SQLite
        transaction back or changes its business result.
        """
        try:
            from .memory_sync import automatic_memory_sync

            self.last_sync_status = automatic_memory_sync(self, "CORE_MUTATION")
        except Exception:
            self.last_sync_status = {
                "format": "vera-memory-sync/v1",
                "status": "ERROR",
                "committed": False,
                "pushed": False,
                "reason": "Synchronisation mémoire indisponible après mutation Core.",
            }

    def __enter__(self) -> "MemoryStore":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def _bind_identity(self) -> None:
        identity_value = self.identity.as_dict()
        latest_schema_version = max(migration.version for migration in self.migrations)
        expected = {
            "store_format": {"schema_version": latest_schema_version},
            "project_identity": identity_value,
        }
        existing = self.metadata()
        if not existing:
            with self.transaction() as connection:
                for key, value in expected.items():
                    connection.execute(
                        "INSERT INTO store_metadata(key, value_json, updated_at) "
                        "VALUES(?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'))",
                        (key, canonical_json(value)),
                    )
                self._append_audit(connection, "STORE_INITIALIZED", {"project_identity": identity_value})
            return
        if set(existing) != set(expected):
            raise StoreError("Registre de métadonnées de store incomplet ou inattendu.")
        if existing["project_identity"] != identity_value:
            raise StoreIdentityError("Le store SQLite appartient à une autre identité de projet.")
        format_value = existing["store_format"]
        if not isinstance(format_value, dict) or set(format_value) != {"schema_version"}:
            raise StoreError("Format de store invalide.")
        version = format_value["schema_version"]
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise StoreError("Version de format de store invalide.")
        if version > latest_schema_version:
            raise StoreError("Le store utilise un format plus récent que ce Core.")
        if version < latest_schema_version:
            with self.transaction() as connection:
                connection.execute(
                    "UPDATE store_metadata SET value_json = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') "
                    "WHERE key = 'store_format'",
                    (canonical_json(expected["store_format"]),),
                )
                self._append_audit(
                    connection,
                    "STORE_MIGRATED",
                    {"from_schema_version": version, "to_schema_version": latest_schema_version},
                )

    @staticmethod
    def _append_audit(connection: sqlite3.Connection, action: str, payload: Mapping[str, Any]) -> None:
        connection.execute(
            "INSERT INTO store_audit(occurred_at, action, payload_json) "
            "VALUES(strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?, ?)",
            (action, canonical_json(dict(payload))),
        )
