from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.executions import ExecutionError, ExecutionService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore

PROFILE = '''
mmu:
  version: "2.0"
project:
  id: "noop-runner-project"
  name: "NOOP Runner Project"
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

class NoopExecutionRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory(); self.addCleanup(self._directory.cleanup)
        runtime = Path(self._directory.name) / ".vera-mmu"; runtime.mkdir()
        self.profile_path = runtime / "project.yaml"; self.profile_path.write_text(PROFILE)
    def _open(self) -> MemoryStore: return MemoryStore.open(load_profile(self.profile_path), self.profile_path)
    def test_noop_writes_audited_non_proof_execution(self) -> None:
        with self._open() as store:
            CapabilityService(store).create("check", "Check", "CHECK", "1.0.0")
            CapabilityContractService(store).declare("check", "NOOP", "DENY_NETWORK", 30)
            execution = ExecutionService(store).run_noop("execution-001", "check", {"scope": "core"}, actor="test")
            self.assertEqual(execution.status, "COMPLETED"); self.assertEqual(execution.exit_code, 0)
            self.assertEqual(execution.parameters, {"scope": "core"}); self.assertIsNone(execution.artifact_hash)
            self.assertEqual([e["action"] for e in store.audit_events()][-1], "EXECUTION_RECORDED")
    def test_refuses_missing_contract_non_object_and_yields_proof(self) -> None:
        with self._open() as store:
            CapabilityService(store).create("check", "Check", "CHECK", "1.0.0")
            service = ExecutionService(store)
            with self.assertRaises(ExecutionError): service.run_noop("e-1", "check", {})
            CapabilityContractService(store).declare("check", "NOOP", "DENY_NETWORK", 30, yields_proof=False)
            with self.assertRaises(ExecutionError): service.run_noop("e-1", "check", [])  # type: ignore[arg-type]

if __name__ == "__main__": unittest.main()
