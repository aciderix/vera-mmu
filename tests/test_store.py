from __future__ import annotations

from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest

from vera_mmu.identity import load_profile
from vera_mmu.migrations import MigrationError, MigrationRunner
from vera_mmu.store import MemoryStore, StoreIdentityError


PROFILE = """\
mmu:
  version: "2.0"
project:
  id: "store-project"
  name: "Store Project"
  domain: "generic"
workspace:
  root: "."
  additional_roots: []
storage:
  memory_dir: ".vera-mmu"
  sqlite_file: "memory.sqlite"
  artifacts_dir: "artifacts"
identity:
  include_vcs_revision: false
  include_profile_hash: true
"""


class MemoryStoreTests(unittest.TestCase):
    """I001/I010/I011/I014/I015: the local SQLite substrate is canonical, bound, and fail-closed."""

    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._directory.cleanup)
        self.project = Path(self._directory.name) / "project"
        self.runtime = self.project / ".vera-mmu"
        self.runtime.mkdir(parents=True)
        self.profile_path = self.runtime / "project.yaml"
        self.profile_path.write_text(PROFILE, encoding="utf-8")

    def _profile(self) -> dict[str, object]:
        return load_profile(self.profile_path)

    def test_initialization_records_identity_migration_and_audit(self) -> None:
        with MemoryStore.open(self._profile(), self.profile_path) as store:
            self.assertTrue(store.locator.sqlite_path.is_file())
            self.assertEqual(store.migration_checksums.keys(), {1, 2, 3, 4, 5, 6, 7, 8, 9})
            self.assertEqual(store.metadata()["project_identity"], store.identity.as_dict())
            self.assertEqual(store.audit_events()[0]["action"], "STORE_INITIALIZED")
            self.assertEqual(store.connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)
            self.assertEqual(store.connection.execute("PRAGMA journal_mode").fetchone()[0].lower(), "wal")

    def test_reopen_is_idempotent_and_does_not_duplicate_initialization_audit(self) -> None:
        with MemoryStore.open(self._profile(), self.profile_path) as first:
            first_checksums = first.migration_checksums
        with MemoryStore.open(self._profile(), self.profile_path) as second:
            self.assertEqual(second.migration_checksums, first_checksums)
            self.assertEqual([event["action"] for event in second.audit_events()], ["STORE_INITIALIZED"])

    def test_store_rejects_another_project_identity(self) -> None:
        with MemoryStore.open(self._profile(), self.profile_path):
            pass
        self.profile_path.write_text(PROFILE.replace('domain: "generic"', 'domain: "research"'), encoding="utf-8")
        with self.assertRaises(StoreIdentityError):
            MemoryStore.open(self._profile(), self.profile_path)

    def test_transaction_rolls_back_on_error(self) -> None:
        with MemoryStore.open(self._profile(), self.profile_path) as store:
            with self.assertRaises(RuntimeError):
                with store.transaction() as connection:
                    connection.execute(
                        "INSERT INTO store_metadata(key, value_json, updated_at) VALUES('transient', 'null', 'now')"
                    )
                    raise RuntimeError("rollback requested")
            self.assertNotIn("transient", store.metadata())

    def test_rejects_mutated_applied_migration_checksum(self) -> None:
        schema = Path(self._directory.name) / "schema"
        schema.mkdir()
        source = Path(__file__).parents[1] / "src" / "vera_mmu" / "schema" / "001_core_store.sql"
        target = schema / source.name
        shutil.copyfile(source, target)
        with MemoryStore.open(self._profile(), self.profile_path, schema_dir=schema):
            pass
        target.write_text(target.read_text(encoding="utf-8") + "\n-- tampered\n", encoding="utf-8")
        with self.assertRaises(MigrationError):
            MemoryStore.open(self._profile(), self.profile_path, schema_dir=schema)

    def test_new_continuous_migration_advances_format_and_audits(self) -> None:
        schema = Path(self._directory.name) / "evolving-schema"
        schema.mkdir()
        source = Path(__file__).parents[1] / "src" / "vera_mmu" / "schema" / "001_core_store.sql"
        shutil.copyfile(source, schema / source.name)
        with MemoryStore.open(self._profile(), self.profile_path, schema_dir=schema):
            pass
        (schema / "002_store_extension.sql").write_text(
            "CREATE TABLE store_extension(key TEXT PRIMARY KEY, value TEXT NOT NULL) STRICT;\n",
            encoding="utf-8",
        )
        with MemoryStore.open(self._profile(), self.profile_path, schema_dir=schema) as store:
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 2})
            self.assertEqual(store.migration_checksums.keys(), {1, 2})
            self.assertEqual(
                [event["action"] for event in store.audit_events()],
                ["STORE_INITIALIZED", "STORE_MIGRATED"],
            )

    def test_rejects_inventory_without_initial_migration(self) -> None:
        schema = Path(self._directory.name) / "invalid-schema"
        schema.mkdir()
        (schema / "002_later.sql").write_text("CREATE TABLE later(id INTEGER);\n", encoding="utf-8")
        with self.assertRaises(MigrationError):
            MigrationRunner(schema).discover()

    def test_rejects_inventory_with_a_version_gap(self) -> None:
        schema = Path(self._directory.name) / "gapped-schema"
        schema.mkdir()
        source = Path(__file__).parents[1] / "src" / "vera_mmu" / "schema" / "001_core_store.sql"
        shutil.copyfile(source, schema / source.name)
        (schema / "003_later.sql").write_text("CREATE TABLE later(id INTEGER);\n", encoding="utf-8")
        with self.assertRaises(MigrationError):
            MigrationRunner(schema).discover()

    def test_failed_migration_is_atomic(self) -> None:
        schema = Path(self._directory.name) / "failing-schema"
        schema.mkdir()
        (schema / "001_core_store.sql").write_text(
            "CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY, name TEXT, checksum TEXT, applied_at TEXT);\n"
            "THIS IS NOT SQL;\n",
            encoding="utf-8",
        )
        with self.assertRaises(MigrationError):
            MemoryStore.open(self._profile(), self.profile_path, schema_dir=schema)
        connection = sqlite3.connect(self.runtime / "memory.sqlite")
        try:
            self.assertIsNone(
                connection.execute(
                    "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'schema_migrations'"
                ).fetchone()
            )
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
