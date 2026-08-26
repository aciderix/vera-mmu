from __future__ import annotations

from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest

from vera_mmu.entities import EntityService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore
from vera_mmu.symbols import SymbolError, SymbolNotFoundError, SymbolService


PROFILE = """\
mmu:
  version: "2.0"
project:
  id: "symbol-project"
  name: "Symbol Project"
  domain: "generic"
workspace:
  root: "."
storage:
  memory_dir: ".vera-mmu"
  sqlite_file: "memory.sqlite"
  artifacts_dir: "artifacts"
identity:
  include_vcs_revision: false
  include_profile_hash: true
"""


class SymbolServiceTests(unittest.TestCase):
    """I001/I002/I003/I011/I014/I015: symbols are exact, immutable and domain-free."""

    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._directory.cleanup)
        self.runtime = Path(self._directory.name) / "project" / ".vera-mmu"
        self.runtime.mkdir(parents=True)
        self.profile_path = self.runtime / "project.yaml"
        self.profile_path.write_text(PROFILE, encoding="utf-8")

    def _open(self) -> MemoryStore:
        return MemoryStore.open(load_profile(self.profile_path), self.profile_path)

    @staticmethod
    def _create_owner(store: MemoryStore) -> None:
        entities = EntityService(store)
        entities.register_type("module", "Module", actor="test-suite")
        entities.create("module-001", "module", "Core module", actor="test-suite")

    def test_default_migrations_include_symbol_registry(self) -> None:
        with self._open() as store:
            self.assertEqual(store.migration_checksums.keys(), {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33})
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 33})

    def test_existing_m2_11_store_migrates_to_symbol_registry(self) -> None:
        schema = Path(self._directory.name) / "m2_11_schema"
        schema.mkdir()
        source_dir = Path(__file__).parents[1] / "src" / "vera_mmu" / "schema"
        for version in range(1, 12):
            source = next(source_dir.glob(f"{version:03d}_*.sql"))
            shutil.copyfile(source, schema / source.name)
        with MemoryStore.open(load_profile(self.profile_path), self.profile_path, schema_dir=schema) as m2_11_store:
            self.assertEqual(m2_11_store.metadata()["store_format"], {"schema_version": 11})
        source = next(source_dir.glob("012_*.sql"))
        shutil.copyfile(source, schema / source.name)
        with MemoryStore.open(load_profile(self.profile_path), self.profile_path, schema_dir=schema) as store:
            self._create_owner(store)
            service = SymbolService(store)
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 12})
            self.assertEqual(
                [event["action"] for event in store.audit_events()],
                ["STORE_INITIALIZED", "STORE_MIGRATED", "ENTITY_TYPE_REGISTERED", "ENTITY_CREATED"],
            )
            self.assertEqual(
                service.create("symbol-001", "module-001", "FUNCTION", "src/core.py", "run").id,
                "symbol-001",
            )

    def test_create_and_read_exact_symbol(self) -> None:
        with self._open() as store:
            self._create_owner(store)
            service = SymbolService(store)
            created = service.create(
                "symbol-001",
                "module-001",
                "FUNCTION",
                "src/core.py",
                "run",
                signature="() -> int",
                metadata={"language": "python", "visibility": "public"},
                actor="test-suite",
            )
            self.assertEqual(service.get("symbol-001"), created)
            self.assertEqual(created.address, "vera://symbol-project/symbol/symbol-001")
            self.assertEqual(created.entity_id, "module-001")
            self.assertEqual(created.kind, "FUNCTION")
            self.assertEqual(created.path, "src/core.py")
            self.assertEqual(created.identifier, "run")
            self.assertEqual(created.signature, "() -> int")
            self.assertEqual(created.metadata, {"language": "python", "visibility": "public"})
            self.assertEqual(
                [event["action"] for event in store.audit_events()],
                ["STORE_INITIALIZED", "ENTITY_TYPE_REGISTERED", "ENTITY_CREATED", "SYMBOL_CREATED"],
            )

    def test_rejects_unknown_owner_without_symbol_or_audit(self) -> None:
        with self._open() as store:
            service = SymbolService(store)
            with self.assertRaises(SymbolError):
                service.create("symbol-001", "unknown-001", "FUNCTION", "src/core.py", "run")
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM symbol").fetchone()[0], 0)
            self.assertEqual([event["action"] for event in store.audit_events()], ["STORE_INITIALIZED"])

    def test_rejects_duplicate_semantic_symbol_and_preserves_first_record(self) -> None:
        with self._open() as store:
            self._create_owner(store)
            service = SymbolService(store)
            first = service.create("symbol-001", "module-001", "FUNCTION", "src/core.py", "run")
            with self.assertRaises(SymbolError):
                service.create("symbol-002", "module-001", "METHOD", "src/core.py", "run")
            self.assertEqual(service.get("symbol-001"), first)
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM symbol").fetchone()[0], 1)
            self.assertEqual(
                [event["action"] for event in store.audit_events()],
                ["STORE_INITIALIZED", "ENTITY_TYPE_REGISTERED", "ENTITY_CREATED", "SYMBOL_CREATED"],
            )

    def test_rejects_invalid_inputs_without_side_effect(self) -> None:
        with self._open() as store:
            self._create_owner(store)
            service = SymbolService(store)
            invalid_calls = (
                lambda: service.create("../escape", "module-001", "FUNCTION", "src/core.py", "run"),
                lambda: service.create("symbol-001", "module-001", "function", "src/core.py", "run"),
                lambda: service.create("symbol-001", "module-001", "FUNCTION", "../core.py", "run"),
                lambda: service.create("symbol-001", "module-001", "FUNCTION", "src/core.py", " run"),
                lambda: service.create("symbol-001", "module-001", "FUNCTION", "src/core.py", "run", metadata=["bad"]),  # type: ignore[arg-type]
            )
            for call in invalid_calls:
                with self.assertRaises(SymbolError):
                    call()
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM symbol").fetchone()[0], 0)
            self.assertEqual(
                [event["action"] for event in store.audit_events()],
                ["STORE_INITIALIZED", "ENTITY_TYPE_REGISTERED", "ENTITY_CREATED"],
            )

    def test_read_requires_exact_existing_identifier(self) -> None:
        with self._open() as store:
            self._create_owner(store)
            service = SymbolService(store)
            service.create("symbol-001", "module-001", "FUNCTION", "src/core.py", "run")
            with self.assertRaises(SymbolNotFoundError):
                service.get("symbol-002")
            with self.assertRaises(SymbolError):
                service.get("symbol-001/other")

    def test_symbol_and_audit_rollback_together_when_audit_insert_fails(self) -> None:
        with self._open() as store:
            self._create_owner(store)
            service = SymbolService(store)
            store.connection.execute(
                "CREATE TRIGGER reject_symbol_audit BEFORE INSERT ON store_audit "
                "WHEN NEW.action = 'SYMBOL_CREATED' "
                "BEGIN SELECT RAISE(ABORT, 'audit rejected'); END"
            )
            with self.assertRaises(SymbolError):
                service.create("symbol-001", "module-001", "FUNCTION", "src/core.py", "run")
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM symbol").fetchone()[0], 0)
            self.assertEqual(
                [event["action"] for event in store.audit_events()],
                ["STORE_INITIALIZED", "ENTITY_TYPE_REGISTERED", "ENTITY_CREATED"],
            )

    def test_sqlite_rejects_symbol_update_and_delete(self) -> None:
        with self._open() as store:
            self._create_owner(store)
            service = SymbolService(store)
            service.create("symbol-001", "module-001", "FUNCTION", "src/core.py", "run")
            with self.assertRaises(sqlite3.IntegrityError):
                store.connection.execute("UPDATE symbol SET identifier = 'changed' WHERE id = 'symbol-001'")
            with self.assertRaises(sqlite3.IntegrityError):
                store.connection.execute("DELETE FROM symbol WHERE id = 'symbol-001'")
            self.assertEqual(service.get("symbol-001").identifier, "run")


if __name__ == "__main__":
    unittest.main()
