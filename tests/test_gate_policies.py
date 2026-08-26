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
from vera_mmu.gates import GateError, GateService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore
from vera_mmu.work_items import WorkItemService

PROFILE = '''
mmu:
  version: "2.0"
project:
  id: "gate-policy-project"
  name: "Gate Policy"
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


class GatePolicyTests(unittest.TestCase):
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
        for evidence_id in ("e1", "e2", "e3"):
            EvidenceService(store).record(evidence_id, "execution", "TEST_PROOF", "PASS", {"evidence": evidence_id})
        AdmissionPolicyService(store).declare("PASS_EVIDENCE")

    def _gate(self, store: MemoryStore, gate_id: str) -> GateService:
        WorkItemService(store).create(gate_id, "SUBTASK", gate_id)
        gates = GateService(store)
        gates.declare(gate_id, gate_id, "e1")
        gates.add_requirement(gate_id, "e2")
        gates.add_requirement(gate_id, "e3")
        return gates

    def _admit(self, store: MemoryStore, evidence_id: str) -> None:
        AdmissionService(store).decide(f"admit-{evidence_id}", evidence_id, "ADMITTED", "test")

    def test_default_and_explicit_all_are_conjunctive_and_pure(self) -> None:
        with self._open() as store:
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 32})
            self._evidence(store); gates = self._gate(store, "default")
            audits = len(store.audit_events())
            default = gates.evaluate("default")
            self.assertEqual(default.status, "FAIL"); self.assertEqual(default.mode, "ALL")
            self.assertEqual((default.admitted_count, default.required_count), (0, 3)); self.assertEqual(len(store.audit_events()), audits)
            self._admit(store, "e1"); self._admit(store, "e2")
            self.assertEqual(gates.evaluate("default").status, "FAIL")
            self._admit(store, "e3"); self.assertEqual(gates.evaluate("default").status, "PASS")
            gates = self._gate(store, "all")
            policy = gates.declare_policy("all", "ALL", actor="test")
            self.assertEqual((policy.mode, policy.minimum_admissions), ("ALL", None))
            self.assertEqual(gates.evaluate("all").status, "PASS")

    def test_any_is_a_closed_counted_policy(self) -> None:
        with self._open() as store:
            self._evidence(store); any_gate = self._gate(store, "any")
            any_policy = any_gate.declare_policy("any", "ANY")
            self.assertEqual(any_policy.mode, "ANY")
            self.assertEqual(any_gate.evaluate("any").status, "FAIL")
            self._admit(store, "e2")
            any_result = any_gate.evaluate("any")
            self.assertEqual((any_result.status, any_result.mode, any_result.admitted_count, any_result.required_count), ("PASS", "ANY", 1, 3))

    def test_at_least_is_a_closed_counted_policy(self) -> None:
        with self._open() as store:
            self._evidence(store); quota_gate = self._gate(store, "quota")
            quota_policy = quota_gate.declare_policy("quota", "AT_LEAST", minimum_admissions=2)
            self.assertEqual((quota_policy.mode, quota_policy.minimum_admissions), ("AT_LEAST", 2))
            self._admit(store, "e1")
            self.assertEqual(quota_gate.evaluate("quota").status, "FAIL")
            self._admit(store, "e3")
            quota_result = quota_gate.evaluate("quota")
            self.assertEqual((quota_result.status, quota_result.mode, quota_result.admitted_count, quota_result.required_count, quota_result.minimum_admissions), ("PASS", "AT_LEAST", 2, 3, 2))

    def test_policy_refusals_are_atomic_and_policy_is_immutable(self) -> None:
        with self._open() as store:
            self._evidence(store); gates = self._gate(store, "gate")
            audits = len(store.audit_events())
            invalid = (
                lambda: gates.declare_policy("missing", "ANY"),
                lambda: gates.declare_policy("gate", "UNKNOWN"),
                lambda: gates.declare_policy("gate", "ALL", minimum_admissions=1),
                lambda: gates.declare_policy("gate", "AT_LEAST"),
                lambda: gates.declare_policy("gate", "AT_LEAST", minimum_admissions=4),
            )
            for call in invalid:
                with self.assertRaises(GateError): call()
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM admission_gate_policy").fetchone()[0], 0)
            self.assertEqual(len(store.audit_events()), audits)
            gates.declare_policy("gate", "AT_LEAST", minimum_admissions=2)
            frozen_audits = len(store.audit_events())
            with self.assertRaises(GateError): gates.add_requirement("gate", "e3")
            self.assertEqual(len(store.audit_events()), frozen_audits)
            with self.assertRaises(GateError): gates.declare_policy("gate", "ANY")
            with self.assertRaises(sqlite3.IntegrityError): store.connection.execute("UPDATE admission_gate_policy SET mode='ANY' WHERE gate_id='gate'")
            with self.assertRaises(sqlite3.IntegrityError): store.connection.execute("DELETE FROM admission_gate_policy WHERE gate_id='gate'")

    def test_existing_m3_14_store_upgrades_with_default_all_and_new_policy_table(self) -> None:
        schema = Path(self._directory.name) / "m3-14-schema"; schema.mkdir()
        source_dir = Path(__file__).parents[1] / "src" / "vera_mmu" / "schema"
        for version in range(1, 27):
            source = next(source_dir.glob(f"{version:03d}_*.sql")); shutil.copyfile(source, schema / source.name)
        with self._open(schema) as legacy:
            self.assertEqual(legacy.metadata()["store_format"], {"schema_version": 26})
            self._evidence(legacy)
            WorkItemService(legacy).create("legacy", "SUBTASK", "legacy")
            GateService(legacy).declare("legacy", "legacy", "e1")
            legacy.connection.execute("INSERT INTO admission_gate_requirement(gate_id,evidence_id,created_at,created_by) VALUES('legacy','e2',strftime('%Y-%m-%dT%H:%M:%fZ','now'),'test')")
            legacy.connection.execute("INSERT INTO admission_gate_requirement(gate_id,evidence_id,created_at,created_by) VALUES('legacy','e3',strftime('%Y-%m-%dT%H:%M:%fZ','now'),'test')")
        source = next(source_dir.glob("027_*.sql")); shutil.copyfile(source, schema / source.name)
        with self._open(schema) as store:
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 27})
            result = GateService(store).evaluate("legacy")
            self.assertEqual((result.status, result.mode, result.required_count), ("FAIL", "ALL", 3))
            GateService(store).declare_policy("legacy", "ANY")
            self.assertEqual(GateService(store).evaluate("legacy").mode, "ANY")


if __name__ == "__main__":
    unittest.main()
