from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
import unittest

from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.executions import ExecutionError, ExecutionService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore


PROFILE = '''
mmu:
  version: "2.0"
project:
  id: "observed-process-project"
  name: "Observed Process Project"
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


class ObservedProcessRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._directory.cleanup)
        runtime = Path(self._directory.name) / ".vera-mmu"
        runtime.mkdir()
        self.profile_path = runtime / "project.yaml"
        self.profile_path.write_text(PROFILE, encoding="utf-8")

    def _open(self) -> MemoryStore:
        return MemoryStore.open(load_profile(self.profile_path), self.profile_path)

    def _declare(
        self,
        store: MemoryStore,
        *,
        capability_id: str = "external-check",
        profile: str = "OBSERVED_PROCESS",
        decision: str = "ALLOW",
    ) -> None:
        CapabilityService(store).create(capability_id, f"External check {capability_id}", "CHECK", "1.0.0")
        CapabilityContractService(store).declare(
            capability_id,
            profile,
            "DENY_NETWORK",
            30,
            parameter_schema={"type": "object"},
            yields_proof=False,
            actor="test-suite",
        )
        CapabilityPolicyService(store).declare(capability_id, decision, "test policy", actor="test-suite")

    def test_records_hash_bound_observed_process_without_admission_or_proof(self) -> None:
        with self._open() as store:
            self._declare(store)
            execution = ExecutionService(store).record_observed_process(
                "external-run-1",
                "external-check",
                {"oracle": "fixed-name"},
                environment={"adapter": "domain-pack/1", "network": "DENY_NETWORK"},
                exit_code=1,
                artifact_hash="a" * 64,
                result={"verdict": "FAIL", "timed_out": False},
                actor="test-suite",
            )
            self.assertEqual(execution.id, "external-run-1")
            self.assertEqual(execution.status, "COMPLETED")
            self.assertEqual(execution.exit_code, 1)
            self.assertEqual(execution.parameters, {"oracle": "fixed-name"})
            self.assertEqual(execution.artifact_hash, "a" * 64)
            row = store.connection.execute(
                "SELECT environment_json, result_json FROM execution WHERE id = ?", ("external-run-1",)
            ).fetchone()
            self.assertEqual(str(row["environment_json"]), '{"adapter":"domain-pack/1","network":"DENY_NETWORK"}')
            self.assertEqual(str(row["result_json"]), '{"timed_out":false,"verdict":"FAIL"}')
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM evidence_admission").fetchone()[0], 0)
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM knowledge_proof").fetchone()[0], 0)

    def test_refuses_wrong_contract_policy_or_artifact_without_writing(self) -> None:
        for index, (profile, decision, artifact_hash) in enumerate((
            ("NOOP", "ALLOW", "b" * 64),
            ("OBSERVED_PROCESS", "DENY", "b" * 64),
            ("OBSERVED_PROCESS", "ALLOW", "not-a-sha256"),
        )):
            with self.subTest(profile=profile, decision=decision, artifact_hash=artifact_hash):
                with self._open() as store:
                    capability_id = f"external-check-{index}"
                    self._declare(store, capability_id=capability_id, profile=profile, decision=decision)
                    with self.assertRaises(ExecutionError):
                        ExecutionService(store).record_observed_process(
                            "external-run-1",
                            capability_id,
                            {},
                            environment={},
                            exit_code=0,
                            artifact_hash=artifact_hash,
                            result={"verdict": "PASS"},
                            actor="test-suite",
                        )
                    self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM execution").fetchone()[0], 0)

    def test_append_only_execution_survives_audit_rejection_atomically(self) -> None:
        with self._open() as store:
            self._declare(store)
            store.connection.execute(
                "CREATE TRIGGER reject_observed_execution_audit BEFORE INSERT ON store_audit "
                "WHEN NEW.action = 'OBSERVED_PROCESS_RECORDED' "
                "BEGIN SELECT RAISE(ABORT, 'reject'); END"
            )
            with self.assertRaises(ExecutionError):
                ExecutionService(store).record_observed_process(
                    "external-run-1",
                    "external-check",
                    {},
                    environment={},
                    exit_code=None,
                    artifact_hash="c" * 64,
                    result={"verdict": "ERROR", "timed_out": True},
                    actor="test-suite",
                )
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM execution").fetchone()[0], 0)
            store.connection.execute("DROP TRIGGER reject_observed_execution_audit")
            ExecutionService(store).record_observed_process(
                "external-run-1",
                "external-check",
                {},
                environment={},
                exit_code=None,
                artifact_hash="c" * 64,
                result={"verdict": "ERROR", "timed_out": True},
                actor="test-suite",
            )
            with self.assertRaises(sqlite3.IntegrityError):
                store.connection.execute("UPDATE execution SET status = 'changed'")


if __name__ == "__main__":
    unittest.main()
