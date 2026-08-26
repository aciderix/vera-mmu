from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
import unittest

from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore
from vera_mmu.work_items import WorkItemService
from vera_mmu.work_lifecycle import WorkLifecycleError, WorkLifecycleService


PROFILE = '''
mmu:
  version: "2.0"
project:
  id: "lifecycle-project"
  name: "Lifecycle Project"
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
'''


class WorkLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory(); self.addCleanup(self._directory.cleanup)
        runtime = Path(self._directory.name) / ".vera-mmu"; runtime.mkdir()
        self.profile_path = runtime / "project.yaml"; self.profile_path.write_text(PROFILE)

    def _open(self) -> MemoryStore:
        return MemoryStore.open(load_profile(self.profile_path), self.profile_path)

    def test_derives_state_from_append_only_events_without_rewriting_work_item(self) -> None:
        with self._open() as store:
            WorkItemService(store).create("work", "WORK_ITEM", "Work")
            service = WorkLifecycleService(store)
            self.assertEqual(service.get_state("work").status, "PLANNED")
            started = service.transition("start", "work", "START", "begin", actor="test")
            self.assertEqual(started.sequence, 1); self.assertEqual(service.get_state("work").status, "ACTIVE")
            completed = service.transition("complete", "work", "COMPLETE", "done", actor="test")
            self.assertEqual(completed.sequence, 2); self.assertEqual(service.get_state("work").status, "COMPLETED")
            self.assertEqual([event.event for event in service.history("work")], ["START", "COMPLETE"])
            self.assertEqual(WorkItemService(store).get("work").status, "PLANNED")
            self.assertEqual(store.audit_events()[-1]["action"], "WORK_LIFECYCLE_EVENT_RECORDED")
            with self.assertRaises(WorkLifecycleError): service.transition("restart", "work", "START", "again")
            with self.assertRaises(WorkLifecycleError): service.transition("cancel", "work", "CANCEL", "late")
            with self.assertRaises(sqlite3.IntegrityError): store.connection.execute("UPDATE work_lifecycle_event SET event='CANCEL' WHERE id='complete'")
            with self.assertRaises(sqlite3.IntegrityError): store.connection.execute("DELETE FROM work_lifecycle_event WHERE id='complete'")

    def test_only_allowed_transitions_produce_events(self) -> None:
        with self._open() as store:
            WorkItemService(store).create("planned", "SUBTASK", "Planned")
            WorkItemService(store).create("active", "SUBTASK", "Active")
            service = WorkLifecycleService(store)
            audits_before = len(store.audit_events())
            with self.assertRaises(WorkLifecycleError): service.transition("bad-complete", "planned", "COMPLETE", "invalid")
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM work_lifecycle_event").fetchone()[0], 0)
            self.assertEqual(len(store.audit_events()), audits_before)
            cancelled = service.transition("cancel-planned", "planned", "CANCEL", "stopped")
            self.assertEqual(cancelled.sequence, 1); self.assertEqual(service.get_state("planned").status, "CANCELLED")
            service.transition("start-active", "active", "START", "begin")
            service.transition("cancel-active", "active", "CANCEL", "stopped")
            self.assertEqual(service.get_state("active").status, "CANCELLED")


if __name__ == "__main__":
    unittest.main()
