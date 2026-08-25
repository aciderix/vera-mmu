from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractError, CapabilityContractService
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

    def test_refuses_parameter_schemas_outside_the_closed_subset(self) -> None:
        invalid_schemas = (
            {"type": "string"},
            {"type": "object", "properties": {"scope": {"type": "array"}}},
            {"type": "object", "properties": {"scope": {"type": "string", "enum": ["core"]}}},
            {"type": "object", "properties": {"scope": {"type": "string"}}, "required": ["missing"]},
            {"type": "object", "additionalProperties": "false"},
            {"type": "object", "unknown": True},
        )
        with self._open() as store:
            CapabilityService(store).create("check", "Check", "CHECK", "1.0.0")
            contracts = CapabilityContractService(store)
            for schema in invalid_schemas:
                with self.assertRaises(CapabilityContractError):
                    contracts.declare("check", "NOOP", "DENY_NETWORK", 30, parameter_schema=schema)
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM capability_contract").fetchone()[0], 0)

    def test_noop_validates_parameters_before_execution_insertion(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "scope": {"type": "string"},
                "attempt": {"type": "integer"},
                "enabled": {"type": "boolean"},
                "ratio": {"type": "number"},
            },
            "required": ["scope", "attempt"],
            "additionalProperties": False,
        }
        with self._open() as store:
            CapabilityService(store).create("check", "Check", "CHECK", "1.0.0")
            CapabilityContractService(store).declare("check", "NOOP", "DENY_NETWORK", 30, parameter_schema=schema)
            service = ExecutionService(store)
            execution = service.run_noop("execution-valid", "check", {"scope": "core", "attempt": 2, "enabled": True, "ratio": 1.5})
            self.assertEqual(execution.parameters["scope"], "core")
            audits_before = len(store.audit_events())
            for identifier, parameters in (
                ("execution-missing", {"scope": "core"}),
                ("execution-extra", {"scope": "core", "attempt": 1, "other": "x"}),
                ("execution-integer", {"scope": "core", "attempt": True}),
                ("execution-boolean", {"scope": "core", "attempt": 1, "enabled": "yes"}),
            ):
                with self.assertRaises(ExecutionError):
                    service.run_noop(identifier, "check", parameters)
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM execution").fetchone()[0], 1)
            self.assertEqual(len(store.audit_events()), audits_before)

if __name__ == "__main__": unittest.main()
