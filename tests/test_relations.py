from __future__ import annotations

from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest

from vera_mmu.entities import EntityService
from vera_mmu.identity import load_profile
from vera_mmu.relations import RelationError, RelationNotFoundError, RelationService
from vera_mmu.store import MemoryStore


PROFILE = """\
mmu:
  version: "2.0"
project:
  id: "relation-project"
  name: "Relation Project"
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


class RelationServiceTests(unittest.TestCase):
    """I001/I002/I003/I011/I014/I015: relations are typed, exact, immutable and auditable."""

    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._directory.cleanup)
        self.runtime = Path(self._directory.name) / "project" / ".vera-mmu"
        self.runtime.mkdir(parents=True)
        self.profile_path = self.runtime / "project.yaml"
        self.profile_path.write_text(PROFILE, encoding="utf-8")

    def _profile(self) -> dict[str, object]:
        return load_profile(self.profile_path)

    def _open(self) -> MemoryStore:
        return MemoryStore.open(self._profile(), self.profile_path)

    @staticmethod
    def _seed(service: EntityService) -> None:
        service.register_type("dataset", "Dataset", actor="test-suite")
        service.register_type("report", "Report", actor="test-suite")
        service.create("dataset-001", "dataset", "Baseline dataset", actor="test-suite")
        service.create("report-001", "report", "Assessment report", actor="test-suite")
        service.create("report-002", "report", "Second report", actor="test-suite")

    def test_default_migrations_include_relation_registry(self) -> None:
        with self._open() as store:
            self.assertEqual(store.migration_checksums.keys(), {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37})
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 37})

    def test_existing_m2_2_store_migrates_to_relation_registry(self) -> None:
        schema = Path(self._directory.name) / "m2_2_schema"
        schema.mkdir()
        source_dir = Path(__file__).parents[1] / "src" / "vera_mmu" / "schema"
        shutil.copyfile(source_dir / "001_core_store.sql", schema / "001_core_store.sql")
        shutil.copyfile(source_dir / "002_entity_registry.sql", schema / "002_entity_registry.sql")
        with MemoryStore.open(self._profile(), self.profile_path, schema_dir=schema) as m2_2_store:
            self.assertEqual(m2_2_store.metadata()["store_format"], {"schema_version": 2})
        shutil.copyfile(source_dir / "003_relation_registry.sql", schema / "003_relation_registry.sql")
        with MemoryStore.open(self._profile(), self.profile_path, schema_dir=schema) as store:
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 3})
            self.assertEqual(
                [event["action"] for event in store.audit_events()],
                ["STORE_INITIALIZED", "STORE_MIGRATED"],
            )

    def test_register_create_and_read_exact_relation(self) -> None:
        with self._open() as store:
            entities = EntityService(store)
            relations = RelationService(store)
            self._seed(entities)
            registered = relations.register_type(
                "derived-from",
                "Derived from",
                from_types=["report"],
                to_types=["dataset"],
                actor="test-suite",
            )
            created = relations.create(
                "relation-001",
                "derived-from",
                "report-001",
                "dataset-001",
                actor="test-suite",
            )
            self.assertEqual(registered.from_types, ("report",))
            self.assertEqual(registered.to_types, ("dataset",))
            self.assertEqual(relations.get("relation-001"), created)
            self.assertEqual(created.address, "vera://relation-project/relation/relation-001")
            self.assertEqual(created.from_address, "vera://relation-project/entity/report-001")
            self.assertEqual(created.to_address, "vera://relation-project/entity/dataset-001")
            self.assertEqual(
                [event["action"] for event in store.audit_events()][-2:],
                ["RELATION_TYPE_REGISTERED", "RELATION_CREATED"],
            )

    def test_rejects_unknown_type_constraints_and_duplicate_relation_type(self) -> None:
        with self._open() as store:
            entities = EntityService(store)
            relations = RelationService(store)
            self._seed(entities)
            with self.assertRaises(RelationError):
                relations.register_type("invalid", "Invalid", from_types=["unknown"])
            relations.register_type("derived-from", "Derived from", from_types=["report"], to_types=["dataset"])
            with self.assertRaises(RelationError):
                relations.register_type("derived-from", "Duplicate")
            self.assertEqual(
                [event["action"] for event in store.audit_events()][-1],
                "RELATION_TYPE_REGISTERED",
            )

    def test_rejects_unknown_endpoints_invalid_identifier_and_type_mismatch(self) -> None:
        with self._open() as store:
            entities = EntityService(store)
            relations = RelationService(store)
            self._seed(entities)
            relations.register_type("derived-from", "Derived from", from_types=["report"], to_types=["dataset"])
            with self.assertRaises(RelationError):
                relations.create("relation-001", "missing", "report-001", "dataset-001")
            with self.assertRaises(RelationError):
                relations.create("relation-001", "derived-from", "missing", "dataset-001")
            with self.assertRaises(RelationError):
                relations.create("relation-001", "derived-from", "dataset-001", "report-001")
            with self.assertRaises(RelationError):
                relations.create("../escape", "derived-from", "report-001", "dataset-001")
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM relation").fetchone()[0], 0)

    def test_rejects_duplicate_edge_and_requires_exact_read(self) -> None:
        with self._open() as store:
            entities = EntityService(store)
            relations = RelationService(store)
            self._seed(entities)
            relations.register_type("derived-from", "Derived from", from_types=["report"], to_types=["dataset"])
            first = relations.create("relation-001", "derived-from", "report-001", "dataset-001")
            with self.assertRaises(RelationError):
                relations.create("relation-002", "derived-from", "report-001", "dataset-001")
            self.assertEqual(relations.get("relation-001"), first)
            with self.assertRaises(RelationNotFoundError):
                relations.get("relation-002")

    def test_database_rejects_relation_and_type_rewrites(self) -> None:
        with self._open() as store:
            entities = EntityService(store)
            relations = RelationService(store)
            self._seed(entities)
            relations.register_type("derived-from", "Derived from", from_types=["report"], to_types=["dataset"])
            relations.create("relation-001", "derived-from", "report-001", "dataset-001")
            with self.assertRaises(sqlite3.DatabaseError):
                store.connection.execute("UPDATE relation SET to_entity_id = 'report-002' WHERE id = 'relation-001'")
            with self.assertRaises(sqlite3.DatabaseError):
                store.connection.execute("UPDATE relation_type SET label = 'Rewrite' WHERE id = 'derived-from'")
            with self.assertRaises(sqlite3.DatabaseError):
                store.connection.execute("DELETE FROM relation WHERE id = 'relation-001'")
            with self.assertRaises(sqlite3.DatabaseError):
                store.connection.execute("DELETE FROM relation_type WHERE id = 'derived-from'")
            self.assertEqual(relations.get("relation-001").to_entity_id, "dataset-001")

    def test_relation_and_audit_rollback_together_when_audit_insert_fails(self) -> None:
        with self._open() as store:
            entities = EntityService(store)
            relations = RelationService(store)
            self._seed(entities)
            relations.register_type("derived-from", "Derived from", from_types=["report"], to_types=["dataset"])
            store.connection.execute(
                "CREATE TRIGGER reject_relation_audit BEFORE INSERT ON store_audit "
                "WHEN NEW.action = 'RELATION_CREATED' "
                "BEGIN SELECT RAISE(ABORT, 'audit rejected'); END"
            )
            with self.assertRaises(RelationError):
                relations.create("relation-001", "derived-from", "report-001", "dataset-001")
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM relation").fetchone()[0], 0)
            self.assertNotIn("RELATION_CREATED", [event["action"] for event in store.audit_events()])


if __name__ == "__main__":
    unittest.main()
