from __future__ import annotations

from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest

from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore
from vera_mmu.work_items import WorkItemError, WorkItemNotFoundError, WorkItemService


PROFILE = """\
mmu:
  version: "2.0"
project:
  id: "work-item-project"
  name: "Work Item Project"
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


class WorkItemServiceTests(unittest.TestCase):
    """I001/I002/I003/I009/I011/I014/I015: work items are exact, append-only and non-operational."""

    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._directory.cleanup)
        self.runtime = Path(self._directory.name) / "project" / ".vera-mmu"
        self.runtime.mkdir(parents=True)
        self.profile_path = self.runtime / "project.yaml"
        self.profile_path.write_text(PROFILE, encoding="utf-8")

    def _open(self) -> MemoryStore:
        return MemoryStore.open(load_profile(self.profile_path), self.profile_path)

    def test_default_migrations_include_work_item_backbone(self) -> None:
        with self._open() as store:
            self.assertEqual(store.migration_checksums.keys(), {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35})
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 35})

    def test_existing_m2_12_store_migrates_to_work_item_backbone(self) -> None:
        schema = Path(self._directory.name) / "m2_12_schema"
        schema.mkdir()
        source_dir = Path(__file__).parents[1] / "src" / "vera_mmu" / "schema"
        for version in range(1, 13):
            source = next(source_dir.glob(f"{version:03d}_*.sql"))
            shutil.copyfile(source, schema / source.name)
        with MemoryStore.open(load_profile(self.profile_path), self.profile_path, schema_dir=schema) as m2_12_store:
            self.assertEqual(m2_12_store.metadata()["store_format"], {"schema_version": 12})
        source = next(source_dir.glob("013_*.sql"))
        shutil.copyfile(source, schema / source.name)
        with MemoryStore.open(load_profile(self.profile_path), self.profile_path, schema_dir=schema) as store:
            service = WorkItemService(store)
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 13})
            self.assertEqual(
                [event["action"] for event in store.audit_events()],
                ["STORE_INITIALIZED", "STORE_MIGRATED"],
            )
            self.assertEqual(service.create("goal-001", "GOAL", "Universal Core").status, "PLANNED")

    def test_create_and_read_exact_work_item(self) -> None:
        with self._open() as store:
            service = WorkItemService(store)
            created = service.create(
                "goal-001",
                "GOAL",
                "Universal Core",
                description="Complete the generic persistence substrate.",
                priority=10,
                assignee="planner",
                metadata={"track": "universalization", "risk": "controlled"},
                actor="test-suite",
            )
            child = service.create("epic-001", "EPIC", "Persistence", parent_id="goal-001", actor="test-suite")
            self.assertEqual(service.get("goal-001"), created)
            self.assertEqual(created.address, "vera://work-item-project/work-item/goal-001")
            self.assertEqual(created.status, "PLANNED")
            self.assertEqual(created.parent_id, None)
            self.assertEqual(created.created_at, created.updated_at)
            self.assertEqual(created.priority, 10)
            self.assertEqual(created.assignee, "planner")
            self.assertEqual(created.metadata, {"risk": "controlled", "track": "universalization"})
            self.assertEqual(child.parent_id, "goal-001")
            self.assertEqual(
                [event["action"] for event in store.audit_events()],
                ["STORE_INITIALIZED", "WORK_ITEM_CREATED", "WORK_ITEM_CREATED"],
            )

    def test_rejects_duplicate_identifier_and_preserves_first_record(self) -> None:
        with self._open() as store:
            service = WorkItemService(store)
            first = service.create("goal-001", "GOAL", "First")
            with self.assertRaises(WorkItemError):
                service.create("goal-001", "GOAL", "Second")
            self.assertEqual(service.get("goal-001"), first)
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM work_item").fetchone()[0], 1)

    def test_rejects_unknown_or_self_parent_without_side_effect(self) -> None:
        with self._open() as store:
            service = WorkItemService(store)
            with self.assertRaises(WorkItemError):
                service.create("epic-001", "EPIC", "Unknown parent", parent_id="goal-001")
            with self.assertRaises(WorkItemError):
                service.create("goal-001", "GOAL", "Self parent", parent_id="goal-001")
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM work_item").fetchone()[0], 0)
            self.assertEqual([event["action"] for event in store.audit_events()], ["STORE_INITIALIZED"])

    def test_rejects_invalid_inputs_without_side_effect(self) -> None:
        with self._open() as store:
            service = WorkItemService(store)
            invalid_calls = (
                lambda: service.create("../escape", "GOAL", "Unsafe"),
                lambda: service.create("goal-001", "goal", "Bad type"),
                lambda: service.create("goal-001", "GATE", "M3 type"),
                lambda: service.create("goal-001", "GOAL", " Bad title"),
                lambda: service.create("goal-001", "GOAL", "Bad priority", priority=True),
                lambda: service.create("goal-001", "GOAL", "Bad metadata", metadata=["bad"]),  # type: ignore[arg-type]
                lambda: service.create("goal-001", "GOAL", "Bad assignee", assignee=" planner"),
            )
            for call in invalid_calls:
                with self.assertRaises(WorkItemError):
                    call()
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM work_item").fetchone()[0], 0)
            self.assertEqual([event["action"] for event in store.audit_events()], ["STORE_INITIALIZED"])

    def test_read_requires_exact_existing_identifier(self) -> None:
        with self._open() as store:
            service = WorkItemService(store)
            service.create("goal-001", "GOAL", "Universal Core")
            with self.assertRaises(WorkItemNotFoundError):
                service.get("goal-002")
            with self.assertRaises(WorkItemError):
                service.get("goal-001/other")

    def test_work_item_and_audit_rollback_together_when_audit_insert_fails(self) -> None:
        with self._open() as store:
            service = WorkItemService(store)
            store.connection.execute(
                "CREATE TRIGGER reject_work_item_audit BEFORE INSERT ON store_audit "
                "WHEN NEW.action = 'WORK_ITEM_CREATED' "
                "BEGIN SELECT RAISE(ABORT, 'audit rejected'); END"
            )
            with self.assertRaises(WorkItemError):
                service.create("goal-001", "GOAL", "Universal Core")
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM work_item").fetchone()[0], 0)
            self.assertEqual([event["action"] for event in store.audit_events()], ["STORE_INITIALIZED"])

    def test_sqlite_rejects_work_item_update_and_delete(self) -> None:
        with self._open() as store:
            service = WorkItemService(store)
            service.create("goal-001", "GOAL", "Universal Core")
            with self.assertRaises(sqlite3.IntegrityError):
                store.connection.execute("UPDATE work_item SET status = 'DONE' WHERE id = 'goal-001'")
            with self.assertRaises(sqlite3.IntegrityError):
                store.connection.execute("DELETE FROM work_item WHERE id = 'goal-001'")
            self.assertEqual(service.get("goal-001").status, "PLANNED")


if __name__ == "__main__":
    unittest.main()
