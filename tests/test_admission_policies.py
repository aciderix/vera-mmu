from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
import unittest

from vera_mmu.admission import AdmissionError, AdmissionService
from vera_mmu.admission_policies import AdmissionPolicyError, AdmissionPolicyService
from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.evidence import EvidenceService
from vera_mmu.executions import ExecutionService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore
from vera_mmu.validators import ValidatorService


PROFILE = '''
mmu:
  version: "2.0"
project:
  id: "admission-policy-project"
  name: "Admission Policy Project"
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


class AdmissionPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory(); self.addCleanup(self._directory.cleanup)
        runtime = Path(self._directory.name) / ".vera-mmu"; runtime.mkdir()
        self.profile_path = runtime / "project.yaml"; self.profile_path.write_text(PROFILE)

    def _open(self) -> MemoryStore:
        return MemoryStore.open(load_profile(self.profile_path), self.profile_path)

    def _pass_evidence(self, store: MemoryStore) -> None:
        CapabilityService(store).create("check", "Check", "CHECK", "1.0.0")
        CapabilityContractService(store).declare("check", "NOOP", "DENY_NETWORK", 30)
        CapabilityPolicyService(store).declare("check", "ALLOW", "test policy")
        ExecutionService(store).run_noop("execution", "check", {})
        EvidenceService(store).record("evidence", "execution", "TEST_PROOF", "PASS", {})

    def test_policy_is_singleton_immutable_and_pass_mode_preserves_explicit_admission(self) -> None:
        with self._open() as store:
            self._pass_evidence(store)
            policy = AdmissionPolicyService(store).declare("PASS_EVIDENCE", actor="test")
            self.assertEqual(policy.mode, "PASS_EVIDENCE")
            self.assertEqual(AdmissionService(store).decide("admission", "evidence", "ADMITTED", "manual", actor="test").decision, "ADMITTED")
            with self.assertRaises(AdmissionPolicyError): AdmissionPolicyService(store).declare("PASS_EVIDENCE")
            with self.assertRaises(sqlite3.IntegrityError): store.connection.execute("UPDATE admission_policy SET mode='VALIDATED_PASS_EVIDENCE' WHERE id=1")

    def test_strict_mode_requires_existing_validation_pass_without_triggering_one(self) -> None:
        with self._open() as store:
            self._pass_evidence(store)
            AdmissionPolicyService(store).declare("VALIDATED_PASS_EVIDENCE")
            audits_before = len(store.audit_events())
            with self.assertRaises(AdmissionError): AdmissionService(store).decide("admission", "evidence", "ADMITTED", "strict")
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM evidence_admission").fetchone()[0], 0)
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM validation_result").fetchone()[0], 0)
            self.assertEqual(len(store.audit_events()), audits_before)
            validators = ValidatorService(store); validators.register("validator", "EVIDENCE_HASH"); self.assertEqual(validators.validate("validation", "validator", "evidence").verdict, "PASS")
            self.assertEqual(AdmissionService(store).decide("admission", "evidence", "ADMITTED", "strict", validation_id="validation").decision, "ADMITTED")

    def test_absent_policy_refuses_admitted_but_allows_rejected_diagnostic(self) -> None:
        with self._open() as store:
            self._pass_evidence(store)
            with self.assertRaises(AdmissionError): AdmissionService(store).decide("admission", "evidence", "ADMITTED", "missing")
            self.assertEqual(AdmissionService(store).decide("rejection", "evidence", "REJECTED", "diagnostic").decision, "REJECTED")


if __name__ == "__main__":
    unittest.main()
