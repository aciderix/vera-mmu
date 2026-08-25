from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
import unittest

from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.evidence import EvidenceService
from vera_mmu.executions import ExecutionService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore
from vera_mmu.validators import ValidatorError, ValidatorService


PROFILE = '''
mmu:
  version: "2.0"
project:
  id: "validator-project"
  name: "Validator Project"
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


class ValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory(); self.addCleanup(self._directory.cleanup)
        runtime = Path(self._directory.name) / ".vera-mmu"; runtime.mkdir()
        self.profile_path = runtime / "project.yaml"; self.profile_path.write_text(PROFILE)

    def _open(self) -> MemoryStore:
        return MemoryStore.open(load_profile(self.profile_path), self.profile_path)

    def _evidence(self, store: MemoryStore) -> None:
        CapabilityService(store).create("check", "Check", "CHECK", "1.0.0")
        CapabilityContractService(store).declare("check", "NOOP", "DENY_NETWORK", 30)
        CapabilityPolicyService(store).declare("check", "ALLOW", "test policy")
        ExecutionService(store).run_noop("execution", "check", {})
        EvidenceService(store).record("evidence", "execution", "TEST_PROOF", "PASS", {"assertion": "integrity"})

    def test_validator_registry_and_result_are_immutable_and_audited(self) -> None:
        with self._open() as store:
            self._evidence(store)
            service = ValidatorService(store)
            validator = service.register("evidence-hash", "EVIDENCE_HASH", actor="test")
            self.assertEqual(validator.kind, "EVIDENCE_HASH")
            self.assertEqual(service.get("evidence-hash"), validator)
            result = service.validate("validation", "evidence-hash", "evidence", actor="test")
            self.assertEqual(result.verdict, "PASS")
            self.assertEqual(service.get_result("validation"), result)
            self.assertEqual(result.expected_hash, result.observed_hash)
            self.assertEqual(EvidenceService(store).get("evidence").admission_status, "PENDING")
            self.assertEqual(store.audit_events()[-1]["action"], "VALIDATION_RECORDED")
            with self.assertRaises(ValidatorError): service.register("evidence-hash", "EVIDENCE_HASH")
            with self.assertRaises(ValidatorError): service.register("unknown", "EXTERNAL_ORACLE")
            with self.assertRaises(sqlite3.IntegrityError): store.connection.execute("UPDATE validator SET kind='OTHER' WHERE id='evidence-hash'")
            with self.assertRaises(sqlite3.IntegrityError): store.connection.execute("DELETE FROM validation_result WHERE id='validation'")

    def test_hash_mismatch_is_fail_and_never_admits_or_runs(self) -> None:
        with self._open() as store:
            self._evidence(store)
            service = ValidatorService(store)
            service.register("evidence-hash", "EVIDENCE_HASH")
            store.connection.execute("DROP TRIGGER evidence_no_update")
            store.connection.execute("UPDATE evidence SET content_hash=? WHERE id='evidence'", ("0" * 64,))
            audits_before = len(store.audit_events())
            result = service.validate("validation-fail", "evidence-hash", "evidence")
            self.assertEqual(result.verdict, "FAIL")
            self.assertNotEqual(result.expected_hash, result.observed_hash)
            self.assertEqual(EvidenceService(store).get("evidence").admission_status, "PENDING")
            self.assertEqual(len(store.audit_events()), audits_before + 1)
            with self.assertRaises(ValidatorError): service.validate("unknown-validator", "missing", "evidence")
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM execution").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
