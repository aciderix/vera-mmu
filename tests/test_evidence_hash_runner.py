from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.evidence import EvidenceService
from vera_mmu.executions import ExecutionError, ExecutionService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore
from vera_mmu.validators import ValidatorService


PROFILE = '''
mmu:
  version: "2.0"
project:
  id: "evidence-hash-runner-project"
  name: "Evidence Hash Runner Project"
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


class EvidenceHashRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory(); self.addCleanup(self._directory.cleanup)
        runtime = Path(self._directory.name) / ".vera-mmu"; runtime.mkdir()
        self.profile_path = runtime / "project.yaml"; self.profile_path.write_text(PROFILE)

    def _open(self) -> MemoryStore:
        return MemoryStore.open(load_profile(self.profile_path), self.profile_path)

    def _source_evidence(self, store: MemoryStore) -> None:
        CapabilityService(store).create("source", "Source", "CHECK", "1.0.0")
        CapabilityContractService(store).declare("source", "NOOP", "DENY_NETWORK", 30)
        CapabilityPolicyService(store).declare("source", "ALLOW", "source policy")
        ExecutionService(store).run_noop("source-execution", "source", {})
        EvidenceService(store).record("evidence", "source-execution", "TEST_PROOF", "PASS", {"assertion": "integrity"})

    def _runner_capability(self, store: MemoryStore, *, decision: str = "ALLOW") -> None:
        CapabilityService(store).create("hash-check", "Hash Check", "CHECK", "1.0.0")
        schema = {"type": "object", "properties": {"validator_id": {"type": "string"}, "evidence_id": {"type": "string"}}, "required": ["validator_id", "evidence_id"], "additionalProperties": False}
        CapabilityContractService(store).declare("hash-check", "EVIDENCE_HASH", "DENY_NETWORK", 30, parameter_schema=schema)
        CapabilityPolicyService(store).declare("hash-check", decision, "runner policy")

    def test_runner_records_execution_and_validation_together(self) -> None:
        with self._open() as store:
            self._source_evidence(store); self._runner_capability(store); ValidatorService(store).register("validator", "EVIDENCE_HASH")
            result = ExecutionService(store).run_evidence_hash("hash-execution", "hash-check", {"validator_id": "validator", "evidence_id": "evidence"}, validation_id="validation", actor="test")
            self.assertEqual(result.status, "COMPLETED"); self.assertEqual(result.exit_code, 0)
            execution = store.connection.execute("SELECT result_json FROM execution WHERE id='hash-execution'").fetchone()
            self.assertEqual(json.loads(execution["result_json"]), {"validation_id": "validation", "verdict": "PASS"})
            validation = ValidatorService(store).get_result("validation")
            self.assertEqual(validation.verdict, "PASS")
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM evidence_admission").fetchone()[0], 0)
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM knowledge_proof").fetchone()[0], 0)

    def test_refuses_policy_before_execution_or_validation(self) -> None:
        with self._open() as store:
            self._source_evidence(store); self._runner_capability(store, decision="DENY"); ValidatorService(store).register("validator", "EVIDENCE_HASH")
            audits_before = len(store.audit_events())
            with self.assertRaises(ExecutionError): ExecutionService(store).run_evidence_hash("denied", "hash-check", {"validator_id": "validator", "evidence_id": "evidence"}, validation_id="validation")
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM execution").fetchone()[0], 1)
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM validation_result").fetchone()[0], 0)
            self.assertEqual(len(store.audit_events()), audits_before)

    def test_refuses_parameters_and_duplicate_before_new_execution(self) -> None:
        with self._open() as store:
            self._source_evidence(store); self._runner_capability(store); ValidatorService(store).register("validator", "EVIDENCE_HASH")
            with self.assertRaises(ExecutionError): ExecutionService(store).run_evidence_hash("invalid", "hash-check", {"validator_id": "validator"}, validation_id="validation")
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM execution").fetchone()[0], 1)
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM validation_result").fetchone()[0], 0)
            ExecutionService(store).run_evidence_hash("valid", "hash-check", {"validator_id": "validator", "evidence_id": "evidence"}, validation_id="validation")
            with self.assertRaises(ExecutionError): ExecutionService(store).run_evidence_hash("duplicate", "hash-check", {"validator_id": "validator", "evidence_id": "evidence"}, validation_id="duplicate-validation")
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM execution").fetchone()[0], 2)
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM validation_result").fetchone()[0], 1)

    def test_hash_runner_records_fail_for_controlled_content_hash_mismatch(self) -> None:
        with self._open() as store:
            self._source_evidence(store); self._runner_capability(store); ValidatorService(store).register("validator", "EVIDENCE_HASH")
            store.connection.execute("DROP TRIGGER evidence_no_update")
            store.connection.execute("UPDATE evidence SET content_hash=? WHERE id='evidence'", ("0" * 64,))
            result = ExecutionService(store).run_evidence_hash("hash-fail-execution", "hash-check", {"validator_id": "validator", "evidence_id": "evidence"}, validation_id="validation-fail")
            self.assertEqual(result.status, "COMPLETED"); self.assertEqual(result.exit_code, 0)
            self.assertEqual(ValidatorService(store).get_result("validation-fail").verdict, "FAIL")
            execution = store.connection.execute("SELECT result_json FROM execution WHERE id='hash-fail-execution'").fetchone()
            self.assertEqual(json.loads(execution["result_json"]), {"validation_id": "validation-fail", "verdict": "FAIL"})
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM evidence_admission").fetchone()[0], 0)
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM knowledge_proof").fetchone()[0], 0)

    def test_existing_m3_13_store_upgrades_contract_catalog_to_evidence_hash(self) -> None:
        schema = Path(self._directory.name) / "m3-13-schema"; schema.mkdir()
        source_dir = Path(__file__).parents[1] / "src" / "vera_mmu" / "schema"
        for version in range(1, 26):
            source = next(source_dir.glob(f"{version:03d}_*.sql")); shutil.copyfile(source, schema / source.name)
        with MemoryStore.open(load_profile(self.profile_path), self.profile_path, schema_dir=schema) as legacy:
            self.assertEqual(legacy.metadata()["store_format"], {"schema_version": 25})
            CapabilityService(legacy).create("legacy", "Legacy", "CHECK", "1.0.0")
            CapabilityContractService(legacy).declare("legacy", "NOOP", "DENY_NETWORK", 30)
        source = next(source_dir.glob("026_*.sql")); shutil.copyfile(source, schema / source.name)
        with MemoryStore.open(load_profile(self.profile_path), self.profile_path, schema_dir=schema) as store:
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 26})
            self.assertEqual(store.connection.execute("SELECT runner_profile FROM capability_contract WHERE capability_id='legacy'").fetchone()[0], "NOOP")
            with self.assertRaises(Exception): store.connection.execute("UPDATE capability_contract SET runner_profile='EVIDENCE_HASH' WHERE capability_id='legacy'")
            CapabilityService(store).create("hash", "Hash", "CHECK", "1.0.0")
            CapabilityContractService(store).declare("hash", "EVIDENCE_HASH", "DENY_NETWORK", 30, parameter_schema={"type": "object", "properties": {"validator_id": {"type": "string"}, "evidence_id": {"type": "string"}}, "required": ["validator_id", "evidence_id"], "additionalProperties": False})


if __name__ == "__main__":
    unittest.main()
