from __future__ import annotations

from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest

from vera_mmu.admission import AdmissionService
from vera_mmu.admission_policies import AdmissionPolicyService
from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.evidence import EvidenceService
from vera_mmu.executions import ExecutionService
from vera_mmu.gates import GateService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore
from vera_mmu.work_items import WorkItemService
from vera_mmu.work_lifecycle import WorkLifecycleError, WorkLifecycleService
from vera_mmu.work_readiness import WorkReadinessService
from vera_mmu.work_start_policies import WorkStartPolicyError, WorkStartPolicyService

PROFILE = '''
mmu:
  version: "2.0"
project:
  id: "work-start-policy-project"
  name: "Work Start Policy"
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


class WorkStartPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory(); self.addCleanup(self._directory.cleanup)
        runtime = Path(self._directory.name) / ".vera-mmu"; runtime.mkdir()
        self.profile_path = runtime / "project.yaml"; self.profile_path.write_text(PROFILE, encoding="utf-8")

    def _open(self, schema_dir: Path | None = None) -> MemoryStore:
        return MemoryStore.open(load_profile(self.profile_path), self.profile_path, schema_dir=schema_dir)

    def _evidence(self, store: MemoryStore) -> None:
        CapabilityService(store).create("source", "Source", "CHECK", "1.0.0")
        CapabilityContractService(store).declare("source", "NOOP", "DENY_NETWORK", 30)
        CapabilityPolicyService(store).declare("source", "ALLOW", "test policy")
        ExecutionService(store).run_noop("execution", "source", {})
        for evidence_id in ("e1", "e2"):
            EvidenceService(store).record(evidence_id, "execution", "TEST_PROOF", "PASS", {"evidence": evidence_id})
        AdmissionPolicyService(store).declare("PASS_EVIDENCE")

    def _blocked_target(self, store: MemoryStore) -> None:
        work_items = WorkItemService(store)
        work_items.create("upstream", "SUBTASK", "Upstream")
        work_items.create("target", "SUBTASK", "Target")
        gates = GateService(store)
        gates.add_dependency("target", "upstream")
        gates.declare("target-gate", "target", "e1")
        gates.add_requirement("target-gate", "e2")
        gates.declare_policy("target-gate", "ALL")

    def test_open_default_preserves_unblocked_lifecycle_transition(self) -> None:
        with self._open() as store:
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 30})
            self._evidence(store); self._blocked_target(store)
            readiness = WorkReadinessService(store).evaluate("target")
            self.assertEqual((readiness.status, readiness.prerequisites_completed, readiness.prerequisites_total, readiness.gates_passed, readiness.gates_total), ("BLOCKED", 0, 1, 0, 1))
            WorkLifecycleService(store).transition("target-start", "target", "START", "open policy")
            self.assertEqual(WorkLifecycleService(store).get_state("target").status, "ACTIVE")

    def test_strict_policy_requires_existing_completed_prerequisites_and_gates(self) -> None:
        with self._open() as store:
            self._evidence(store); self._blocked_target(store)
            policy = WorkStartPolicyService(store).declare("REQUIRE_READY", actor="test")
            self.assertEqual(policy.mode, "REQUIRE_READY"); self.assertEqual(WorkStartPolicyService(store).get(), policy)
            lifecycle = WorkLifecycleService(store)
            audits = len(store.audit_events())
            with self.assertRaises(WorkLifecycleError): lifecycle.transition("target-start-blocked", "target", "START", "blocked")
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM work_lifecycle_event WHERE work_item_id='target'").fetchone()[0], 0)
            self.assertEqual(len(store.audit_events()), audits)
            lifecycle.transition("upstream-start", "upstream", "START", "start")
            lifecycle.transition("upstream-complete", "upstream", "COMPLETE", "complete")
            self.assertEqual(WorkReadinessService(store).evaluate("target").status, "BLOCKED")
            AdmissionService(store).decide("admit-e1", "e1", "ADMITTED", "test")
            self.assertEqual(WorkReadinessService(store).evaluate("target").status, "BLOCKED")
            AdmissionService(store).decide("admit-e2", "e2", "ADMITTED", "test")
            ready = WorkReadinessService(store).evaluate("target")
            self.assertEqual((ready.status, ready.prerequisites_completed, ready.prerequisites_total, ready.gates_passed, ready.gates_total), ("READY", 1, 1, 1, 1))
            lifecycle.transition("target-start", "target", "START", "ready")
            self.assertEqual(lifecycle.get_state("target").status, "ACTIVE")

    def test_policy_is_closed_immutable_and_refuses_invalid_declarations_atomically(self) -> None:
        with self._open() as store:
            WorkItemService(store).create("work", "SUBTASK", "Work")
            service = WorkStartPolicyService(store); audits = len(store.audit_events())
            for mode in ("UNKNOWN", "", None):
                with self.assertRaises(WorkStartPolicyError): service.declare(mode)  # type: ignore[arg-type]
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM work_start_policy").fetchone()[0], 0)
            self.assertEqual(len(store.audit_events()), audits)
            service.declare("OPEN")
            with self.assertRaises(WorkStartPolicyError): service.declare("REQUIRE_READY")
            with self.assertRaises(sqlite3.IntegrityError): store.connection.execute("UPDATE work_start_policy SET mode='REQUIRE_READY' WHERE id=1")
            with self.assertRaises(sqlite3.IntegrityError): store.connection.execute("DELETE FROM work_start_policy WHERE id=1")

    def test_existing_m3_15_store_upgrades_to_optional_work_start_policy(self) -> None:
        schema = Path(self._directory.name) / "m3-15-schema"; schema.mkdir()
        source_dir = Path(__file__).parents[1] / "src" / "vera_mmu" / "schema"
        for version in range(1, 28):
            source = next(source_dir.glob(f"{version:03d}_*.sql")); shutil.copyfile(source, schema / source.name)
        with self._open(schema) as legacy:
            self.assertEqual(legacy.metadata()["store_format"], {"schema_version": 27})
            WorkItemService(legacy).create("legacy", "SUBTASK", "Legacy")
        source = next(source_dir.glob("028_*.sql")); shutil.copyfile(source, schema / source.name)
        with self._open(schema) as store:
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 28})
            self.assertEqual(WorkReadinessService(store).evaluate("legacy").status, "READY")
            self.assertEqual(WorkStartPolicyService(store).declare("REQUIRE_READY").mode, "REQUIRE_READY")


if __name__ == "__main__":
    unittest.main()
