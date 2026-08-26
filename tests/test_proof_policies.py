from __future__ import annotations

from pathlib import Path
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
from vera_mmu.identity import load_profile
from vera_mmu.knowledge import KnowledgeService
from vera_mmu.proof_policies import ProofPolicyError, ProofPolicyService
from vera_mmu.proofs import ProofError, ProofService
from vera_mmu.store import MemoryStore


PROFILE = '''
mmu:
  version: "2.0"
project:
  id: "proof-policy-project"
  name: "Proof Policy Project"
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


class ProofPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory(); self.addCleanup(self._directory.cleanup)
        runtime = Path(self._directory.name) / ".vera-mmu"; runtime.mkdir()
        self.profile_path = runtime / "project.yaml"; self.profile_path.write_text(PROFILE)

    def _open(self) -> MemoryStore:
        return MemoryStore.open(load_profile(self.profile_path), self.profile_path)

    def _ready(self, store: MemoryStore) -> None:
        knowledge = KnowledgeService(store); knowledge.register_type("fact", "Fact"); knowledge.append("knowledge", "fact", "OBSERVED", "Fact", "content")
        CapabilityService(store).create("check", "Check", "CHECK", "1.0.0")
        CapabilityContractService(store).declare("check", "NOOP", "DENY_NETWORK", 30)
        CapabilityPolicyService(store).declare("check", "ALLOW", "test policy")
        ExecutionService(store).run_noop("execution", "check", {})
        EvidenceService(store).record("evidence", "execution", "TEST_PROOF", "PASS", {})
        AdmissionPolicyService(store).declare("PASS_EVIDENCE")
        AdmissionService(store).decide("admission", "evidence", "ADMITTED", "verified")

    def test_policy_is_singleton_immutable_and_audited(self) -> None:
        with self._open() as store:
            service = ProofPolicyService(store)
            policy = service.declare("HMAC_SHA256", hmac_required=True, actor="test")
            self.assertEqual(policy.algorithm, "HMAC_SHA256"); self.assertTrue(policy.hmac_required)
            self.assertEqual(service.get(), policy)
            self.assertEqual(store.audit_events()[-1]["action"], "PROOF_POLICY_DECLARED")
            self.assertEqual({row[1] for row in store.connection.execute("PRAGMA table_info('proof_policy')").fetchall()}, {"singleton", "algorithm", "hmac_required", "created_at", "created_by"})
            with self.assertRaises(ProofPolicyError): service.declare("HMAC_SHA256", hmac_required=False)
            with self.assertRaises(ProofPolicyError): service.declare("PLAINTEXT", hmac_required=True)
            with self.assertRaises(sqlite3.IntegrityError): store.connection.execute("UPDATE proof_policy SET hmac_required=0")
            with self.assertRaises(sqlite3.IntegrityError): store.connection.execute("DELETE FROM proof_policy")

    def test_proof_requires_project_policy_and_memory_only_hmac_secret(self) -> None:
        with self._open() as store:
            self._ready(store)
            with self.assertRaises(ProofError): ProofService(store).promote("proof-no-policy", "knowledge", "evidence", "admission")
            ProofPolicyService(store).declare("HMAC_SHA256", hmac_required=True)
            with self.assertRaises(ProofError): ProofService(store).promote("proof-no-secret", "knowledge", "evidence", "admission")
            secret = b"proof-policy-test-secret"
            proof = ProofService(store, hmac_secret=secret).promote("proof-hmac", "knowledge", "evidence", "admission")
            self.assertTrue(proof.hmac_required); self.assertEqual(len(proof.hmac_digest or ""), 64)
            stored_digest = store.connection.execute("SELECT hmac_digest FROM knowledge_proof WHERE id='proof-hmac'").fetchone()[0]
            self.assertEqual(stored_digest, proof.hmac_digest)
            self.assertNotIn(secret.decode(), str(stored_digest) + str(store.audit_events()))
            self.assertEqual(KnowledgeService(store).get("knowledge").status, "OBSERVED")

    def test_non_hmac_policy_rejects_a_secret(self) -> None:
        with self._open() as store:
            self._ready(store)
            ProofPolicyService(store).declare("HMAC_SHA256", hmac_required=False)
            proof = ProofService(store).promote("proof-no-hmac", "knowledge", "evidence", "admission")
            self.assertFalse(proof.hmac_required); self.assertIsNone(proof.hmac_digest)
            with self.assertRaises(ProofError):
                ProofService(store, hmac_secret=b"not-needed").promote("proof-with-secret", "knowledge", "evidence", "admission")


if __name__ == "__main__":
    unittest.main()
