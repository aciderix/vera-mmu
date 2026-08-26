from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import unittest

from vera_mmu.entities import EntityError, EntityNotFoundError, EntityService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore


PROFILE = """\
mmu:
  version: "2.0"
project:
  id: "entity-project"
  name: "Entity Project"
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


class EntityServiceTests(unittest.TestCase):
    """I001/I002/I003/I011/I014/I015: entities are typed, exact, auditable and atomic."""

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
    def _register(service: EntityService) -> None:
        service.register_type(
            "dataset",
            "Dataset",
            description="A generic data collection.",
            schema={"fields": {"uri": "string"}},
            actor="test-suite",
        )

    def test_default_migrations_include_entity_registry(self) -> None:
        with self._open() as store:
            self.assertEqual(store.migration_checksums.keys(), {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34})
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 34})

    def test_existing_m2_1_store_migrates_to_entity_registry(self) -> None:
        schema = Path(self._directory.name) / "m2_1_schema"
        schema.mkdir()
        source_dir = Path(__file__).parents[1] / "src" / "vera_mmu" / "schema"
        shutil.copyfile(source_dir / "001_core_store.sql", schema / "001_core_store.sql")
        with MemoryStore.open(load_profile(self.profile_path), self.profile_path, schema_dir=schema) as m2_1_store:
            self.assertEqual(m2_1_store.metadata()["store_format"], {"schema_version": 1})
        shutil.copyfile(source_dir / "002_entity_registry.sql", schema / "002_entity_registry.sql")
        with MemoryStore.open(load_profile(self.profile_path), self.profile_path, schema_dir=schema) as store:
            service = EntityService(store)
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 2})
            self.assertEqual(
                [event["action"] for event in store.audit_events()],
                ["STORE_INITIALIZED", "STORE_MIGRATED"],
            )
            self.assertEqual(service.register_type("dataset", "Dataset").id, "dataset")

    def test_register_create_and_read_exact_entity(self) -> None:
        with self._open() as store:
            service = EntityService(store)
            registered = service.register_type(
                "dataset",
                "Dataset",
                schema={"fields": {"uri": "string", "sha256": "string"}},
                actor="test-suite",
            )
            entity = service.create(
                "dataset-001",
                "dataset",
                "Baseline corpus",
                metadata={"sha256": "abc", "uri": "file://corpus"},
                actor="test-suite",
            )
            read = service.get("dataset-001")
            self.assertEqual(registered.schema, {"fields": {"sha256": "string", "uri": "string"}})
            self.assertEqual(read, entity)
            self.assertEqual(entity.address, "vera://entity-project/entity/dataset-001")
            self.assertEqual(entity.metadata, {"sha256": "abc", "uri": "file://corpus"})
            self.assertEqual(
                [event["action"] for event in store.audit_events()],
                ["STORE_INITIALIZED", "ENTITY_TYPE_REGISTERED", "ENTITY_CREATED"],
            )

    def test_rejects_duplicate_entity_type_without_new_audit(self) -> None:
        with self._open() as store:
            service = EntityService(store)
            self._register(service)
            with self.assertRaises(EntityError):
                self._register(service)
            self.assertEqual(
                [event["action"] for event in store.audit_events()],
                ["STORE_INITIALIZED", "ENTITY_TYPE_REGISTERED"],
            )

    def test_rejects_unknown_type_without_creating_entity(self) -> None:
        with self._open() as store:
            service = EntityService(store)
            with self.assertRaises(EntityError):
                service.create("unknown-001", "unknown", "Unknown type", actor="test-suite")
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM entity").fetchone()[0], 0)
            self.assertEqual([event["action"] for event in store.audit_events()], ["STORE_INITIALIZED"])

    def test_rejects_duplicate_entity_and_preserves_first_record(self) -> None:
        with self._open() as store:
            service = EntityService(store)
            self._register(service)
            first = service.create("dataset-001", "dataset", "First", actor="test-suite")
            with self.assertRaises(EntityError):
                service.create("dataset-001", "dataset", "Second", actor="test-suite")
            self.assertEqual(service.get("dataset-001"), first)
            self.assertEqual(
                [event["action"] for event in store.audit_events()],
                ["STORE_INITIALIZED", "ENTITY_TYPE_REGISTERED", "ENTITY_CREATED"],
            )

    def test_rejects_invalid_identifier_and_non_mapping_json(self) -> None:
        with self._open() as store:
            service = EntityService(store)
            self._register(service)
            with self.assertRaises(EntityError):
                service.create("../escape", "dataset", "Unsafe", actor="test-suite")
            with self.assertRaises(EntityError):
                service.create("dataset-001", "dataset", "Bad metadata", metadata=["not", "an", "object"], actor="test-suite")  # type: ignore[arg-type]
            with self.assertRaises(EntityError):
                service.register_type("bad_type", "Bad")

    def test_read_requires_exact_existing_identifier(self) -> None:
        with self._open() as store:
            service = EntityService(store)
            self._register(service)
            service.create("dataset-001", "dataset", "Baseline", actor="test-suite")
            with self.assertRaises(EntityNotFoundError):
                service.get("dataset-002")
            with self.assertRaises(EntityError):
                service.get("dataset-001/other")

    def test_entity_and_audit_rollback_together_when_audit_insert_fails(self) -> None:
        with self._open() as store:
            service = EntityService(store)
            self._register(service)
            store.connection.execute(
                "CREATE TRIGGER reject_entity_audit BEFORE INSERT ON store_audit "
                "WHEN NEW.action = 'ENTITY_CREATED' "
                "BEGIN SELECT RAISE(ABORT, 'audit rejected'); END"
            )
            with self.assertRaises(EntityError):
                service.create("dataset-001", "dataset", "Baseline", actor="test-suite")
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM entity").fetchone()[0], 0)
            self.assertEqual(
                [event["action"] for event in store.audit_events()],
                ["STORE_INITIALIZED", "ENTITY_TYPE_REGISTERED"],
            )


if __name__ == "__main__":
    unittest.main()
