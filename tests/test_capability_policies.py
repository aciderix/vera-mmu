from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
import unittest

from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyError, CapabilityPolicyService
from vera_mmu.executions import ExecutionError, ExecutionService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore


PROFILE = '''
mmu:
  version: "2.0"
project:
  id: "policy-project"
  name: "Policy Project"
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


class CapabilityPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory(); self.addCleanup(self._directory.cleanup)
        runtime = Path(self._directory.name) / ".vera-mmu"; runtime.mkdir()
        self.profile_path = runtime / "project.yaml"; self.profile_path.write_text(PROFILE)

    def _open(self) -> MemoryStore:
        return MemoryStore.open(load_profile(self.profile_path), self.profile_path)

    def _capability(self, store: MemoryStore, identifier: str) -> None:
        CapabilityService(store).create(identifier, identifier, "CHECK", "1.0.0")
        CapabilityContractService(store).declare(identifier, "NOOP", "DENY_NETWORK", 30)

    def test_policy_is_exact_immutable_and_audited(self) -> None:
        with self._open() as store:
            self._capability(store, "allow")
            service = CapabilityPolicyService(store)
            policy = service.declare("allow", "ALLOW", "approved", actor="test")
            self.assertEqual(policy.capability_id, "allow"); self.assertEqual(policy.decision, "ALLOW")
            self.assertEqual(service.get("allow"), policy)
            self.assertEqual(store.audit_events()[-1]["action"], "CAPABILITY_POLICY_DECLARED")
            with self.assertRaises(CapabilityPolicyError):
                service.declare("allow", "ALLOW", "again")
            with self.assertRaises(CapabilityPolicyError):
                service.declare("allow", "UNKNOWN", "bad")
            with self.assertRaises(sqlite3.IntegrityError):
                store.connection.execute("UPDATE capability_policy SET decision='DENY' WHERE capability_id='allow'")
            with self.assertRaises(sqlite3.IntegrityError):
                store.connection.execute("DELETE FROM capability_policy WHERE capability_id='allow'")

    def test_noop_requires_an_allow_policy_without_writes_on_refusal(self) -> None:
        with self._open() as store:
            runner = ExecutionService(store)
            policies = CapabilityPolicyService(store)
            self._capability(store, "missing")
            audits_before = len(store.audit_events())
            with self.assertRaises(ExecutionError):
                runner.run_noop("execution-missing", "missing", {})
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM execution").fetchone()[0], 0)
            self.assertEqual(len(store.audit_events()), audits_before)
            for identifier, decision in (("deny", "DENY"), ("confirm", "CONFIRM")):
                self._capability(store, identifier)
                policies.declare(identifier, decision, "not automatic")
                audits_before = len(store.audit_events())
                with self.assertRaises(ExecutionError):
                    runner.run_noop(f"execution-{identifier}", identifier, {})
                self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM execution").fetchone()[0], 0)
                self.assertEqual(len(store.audit_events()), audits_before)
            self._capability(store, "allow")
            policies.declare("allow", "ALLOW", "approved")
            execution = runner.run_noop("execution-allow", "allow", {})
            self.assertEqual(execution.capability_id, "allow")
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM execution").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
