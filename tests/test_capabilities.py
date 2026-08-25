from __future__ import annotations

from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest

import vera_mmu
from vera_mmu.capabilities import CapabilityError, CapabilityNotFoundError, CapabilityService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore


PROFILE = """\
mmu:
  version: "2.0"
project:
  id: "capability-project"
  name: "Capability Project"
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


class CapabilityServiceTests(unittest.TestCase):
    """I001/I002/I003/I004/I006/I007/I008/I011/I014/I015: capabilities are declarations, not runners."""

    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._directory.cleanup)
        self.runtime = Path(self._directory.name) / "project" / ".vera-mmu"
        self.runtime.mkdir(parents=True)
        self.profile_path = self.runtime / "project.yaml"
        self.profile_path.write_text(PROFILE, encoding="utf-8")

    def _open(self) -> MemoryStore:
        return MemoryStore.open(load_profile(self.profile_path), self.profile_path)

    def test_default_migrations_include_capability_and_execution_schemas(self) -> None:
        with self._open() as store:
            self.assertEqual(store.migration_checksums.keys(), {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22})
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 22})
            columns = {row[1] for row in store.connection.execute("PRAGMA table_info('execution')").fetchall()}
            self.assertEqual(
                columns,
                {
                    "id",
                    "capability_id",
                    "status",
                    "exit_code",
                    "parameters_json",
                    "environment_json",
                    "started_at",
                    "finished_at",
                    "artifact_hash",
                    "result_json",
                    "created_by",
                },
            )

    def test_existing_m2_13_store_migrates_to_capability_and_execution_schemas(self) -> None:
        schema = Path(self._directory.name) / "m2_13_schema"
        schema.mkdir()
        source_dir = Path(__file__).parents[1] / "src" / "vera_mmu" / "schema"
        for version in range(1, 14):
            source = next(source_dir.glob(f"{version:03d}_*.sql"))
            shutil.copyfile(source, schema / source.name)
        with MemoryStore.open(load_profile(self.profile_path), self.profile_path, schema_dir=schema) as m2_13_store:
            self.assertEqual(m2_13_store.metadata()["store_format"], {"schema_version": 13})
        source = next(source_dir.glob("014_*.sql"))
        shutil.copyfile(source, schema / source.name)
        with MemoryStore.open(load_profile(self.profile_path), self.profile_path, schema_dir=schema) as store:
            service = CapabilityService(store)
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 14})
            self.assertEqual(
                [event["action"] for event in store.audit_events()],
                ["STORE_INITIALIZED", "STORE_MIGRATED"],
            )
            self.assertEqual(service.create("unit-tests", "Unit tests", "CHECK", "1.0.0").id, "unit-tests")

    def test_create_and_read_exact_capability(self) -> None:
        with self._open() as store:
            service = CapabilityService(store)
            created = service.create(
                "unit-tests",
                "Unit tests",
                "CHECK",
                "1.0.0",
                description="A declarative project check.",
                input_schema={"type": "object"},
                parameter_schema={"properties": {"scope": {"type": "string"}}, "type": "object"},
                output_schema={"type": "object"},
                metadata={"category": "quality"},
                actor="test-suite",
            )
            self.assertEqual(service.get("unit-tests"), created)
            self.assertEqual(created.address, "vera://capability-project/capability/unit-tests")
            self.assertEqual(created.kind, "CHECK")
            self.assertEqual(created.version, "1.0.0")
            self.assertEqual(created.parameter_schema, {"properties": {"scope": {"type": "string"}}, "type": "object"})
            self.assertEqual(
                [event["action"] for event in store.audit_events()],
                ["STORE_INITIALIZED", "CAPABILITY_DECLARED"],
            )

    def test_rejects_duplicate_and_invalid_capability_inputs_without_side_effect(self) -> None:
        with self._open() as store:
            service = CapabilityService(store)
            first = service.create("unit-tests", "Unit tests", "CHECK", "1.0.0")
            with self.assertRaises(CapabilityError):
                service.create("unit-tests", "Duplicate", "CHECK", "1.0.1")
            invalid_calls = (
                lambda: service.create("../escape", "Bad", "CHECK", "1.0.0"),
                lambda: service.create("bad-kind", "Bad", "check", "1.0.0"),
                lambda: service.create("bad-version", "Bad", "CHECK", "latest"),
                lambda: service.create("bad-schema", "Bad", "CHECK", "1.0.0", input_schema=["bad"]),  # type: ignore[arg-type]
            )
            for call in invalid_calls:
                with self.assertRaises(CapabilityError):
                    call()
            self.assertEqual(service.get("unit-tests"), first)
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM capability").fetchone()[0], 1)
            self.assertEqual(
                [event["action"] for event in store.audit_events()],
                ["STORE_INITIALIZED", "CAPABILITY_DECLARED"],
            )

    def test_read_requires_exact_existing_identifier(self) -> None:
        with self._open() as store:
            service = CapabilityService(store)
            service.create("unit-tests", "Unit tests", "CHECK", "1.0.0")
            with self.assertRaises(CapabilityNotFoundError):
                service.get("other-check")
            with self.assertRaises(CapabilityError):
                service.get("unit-tests/other")

    def test_capability_and_audit_rollback_together_when_audit_insert_fails(self) -> None:
        with self._open() as store:
            service = CapabilityService(store)
            store.connection.execute(
                "CREATE TRIGGER reject_capability_audit BEFORE INSERT ON store_audit "
                "WHEN NEW.action = 'CAPABILITY_DECLARED' "
                "BEGIN SELECT RAISE(ABORT, 'audit rejected'); END"
            )
            with self.assertRaises(CapabilityError):
                service.create("unit-tests", "Unit tests", "CHECK", "1.0.0")
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM capability").fetchone()[0], 0)
            self.assertEqual([event["action"] for event in store.audit_events()], ["STORE_INITIALIZED"])

    def test_sqlite_rejects_capability_and_execution_updates_or_deletes(self) -> None:
        with self._open() as store:
            service = CapabilityService(store)
            service.create("unit-tests", "Unit tests", "CHECK", "1.0.0")
            with self.assertRaises(sqlite3.IntegrityError):
                store.connection.execute("UPDATE capability SET name = 'Changed' WHERE id = 'unit-tests'")
            with self.assertRaises(sqlite3.IntegrityError):
                store.connection.execute("DELETE FROM capability WHERE id = 'unit-tests'")
            with self.assertRaises(sqlite3.IntegrityError):
                store.connection.execute(
                    "INSERT INTO execution(id, capability_id, status, parameters_json, environment_json, created_by) "
                    "VALUES('execution-unknown', 'unknown', 'RECORDED', '{}', '{}', 'test-suite')"
                )
            store.connection.execute(
                "INSERT INTO execution(id, capability_id, status, parameters_json, environment_json, created_by) "
                "VALUES('execution-001', 'unit-tests', 'RECORDED', '{}', '{}', 'test-suite')"
            )
            with self.assertRaises(sqlite3.IntegrityError):
                store.connection.execute("UPDATE execution SET status = 'CHANGED' WHERE id = 'execution-001'")
            with self.assertRaises(sqlite3.IntegrityError):
                store.connection.execute("DELETE FROM execution WHERE id = 'execution-001'")
            self.assertEqual(store.connection.execute("SELECT status FROM execution WHERE id = 'execution-001'").fetchone()[0], "RECORDED")

    def test_no_execution_service_or_runner_is_exposed_by_m2(self) -> None:
        self.assertFalse(hasattr(vera_mmu, "ExecutionService"))
        self.assertFalse(hasattr(CapabilityService, "run"))


if __name__ == "__main__":
    unittest.main()
