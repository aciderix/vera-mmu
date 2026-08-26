from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from vera_mmu.admission import AdmissionError, AdmissionService
from vera_mmu.admission_policies import AdmissionPolicyService
from vera_mmu.assets import AssetService
from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.evidence import EvidenceService
from vera_mmu.executions import ExecutionService
from vera_mmu.gates import GateService
from vera_mmu.identity import load_profile
from vera_mmu.knowledge import KnowledgeService
from vera_mmu.proof_policies import ProofPolicyService
from vera_mmu.proofs import ProofError, ProofService
from vera_mmu.store import MemoryStore
from vera_mmu.validators import ValidatorService
from vera_mmu.work_items import WorkItemService


PROFILE = '''
mmu:
  version: "2.0"
project:
  id: "universal-verdict-project"
  name: "Universal Verdict Project"
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


class EvidenceAssetValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._directory.cleanup)
        runtime = Path(self._directory.name) / ".vera-mmu"
        runtime.mkdir()
        self.profile_path = runtime / "project.yaml"
        self.profile_path.write_text(PROFILE, encoding="utf-8")

    def _open(self) -> MemoryStore:
        return MemoryStore.open(load_profile(self.profile_path), self.profile_path)

    def _declare_source(self, store: MemoryStore) -> None:
        CapabilityService(store).create("source", "Observed source", "CHECK", "1.0.0")
        CapabilityContractService(store).declare("source", "OBSERVED_PROCESS", "DENY_NETWORK", 30, parameter_schema={"type": "object"})
        CapabilityPolicyService(store).declare("source", "ALLOW", "test policy")

    def _evidence(self, store: MemoryStore, identifier: str, verdict: str, *, declared_hash: str | None = None) -> None:
        asset = AssetService(store).record(f"asset-{identifier}", f"artifact:{identifier}".encode(), media_type="text/plain")
        ExecutionService(store).record_observed_process(
            f"execution-{identifier}",
            "source",
            {},
            environment={"runner": "test"},
            exit_code=0 if verdict == "PASS" else 1,
            artifact_hash=asset.content_hash,
            result={"verdict": verdict},
        )
        EvidenceService(store).record(
            f"evidence-{identifier}",
            f"execution-{identifier}",
            "TEST_PROOF",
            verdict,
            {"asset_id": asset.id, "asset_hash": asset.content_hash if declared_hash is None else declared_hash},
        )

    def test_only_asset_bound_validated_pass_can_progress_to_admission_proof_and_gate(self) -> None:
        with self._open() as store:
            self._declare_source(store)
            for verdict in ("PASS", "FAIL", "ERROR", "SKIPPED", "UNKNOWN"):
                self._evidence(store, verdict.lower(), verdict)
            self._evidence(store, "tampered", "PASS", declared_hash="0" * 64)

            validators = ValidatorService(store)
            validators.register("asset-binding", "EVIDENCE_ASSET")
            validations = {
                verdict: validators.validate(
                    f"validation-{verdict.lower()}", "asset-binding", f"evidence-{verdict.lower()}"
                )
                for verdict in ("PASS", "FAIL", "ERROR", "SKIPPED", "UNKNOWN")
            }
            tampered = validators.validate("validation-tampered", "asset-binding", "evidence-tampered")
            self.assertTrue(all(result.verdict == "PASS" for result in validations.values()))
            self.assertEqual(tampered.verdict, "FAIL")

            AdmissionPolicyService(store).declare("VALIDATED_PASS_EVIDENCE")
            admitted = AdmissionService(store).decide(
                "admission-pass",
                "evidence-pass",
                "ADMITTED",
                "asset and evidence validated",
                validation_id="validation-pass",
            )
            self.assertEqual(admitted.decision, "ADMITTED")
            for verdict in ("FAIL", "ERROR", "SKIPPED", "UNKNOWN"):
                with self.subTest(verdict=verdict):
                    with self.assertRaises(AdmissionError):
                        AdmissionService(store).decide(
                            f"admission-{verdict.lower()}",
                            f"evidence-{verdict.lower()}",
                            "ADMITTED",
                            "must remain non-promotable",
                            validation_id=f"validation-{verdict.lower()}",
                        )
            with self.assertRaises(AdmissionError):
                AdmissionService(store).decide(
                    "admission-tampered",
                    "evidence-tampered",
                    "ADMITTED",
                    "asset binding failed",
                    validation_id="validation-tampered",
                )
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM evidence_admission").fetchone()[0], 1)

            WorkItemService(store).create("gate-pass", "SUBTASK", "Gate pass")
            WorkItemService(store).create("gate-fail", "SUBTASK", "Gate fail")
            gates = GateService(store)
            gates.declare("gate-pass", "gate-pass", "evidence-pass")
            gates.declare("gate-fail", "gate-fail", "evidence-fail")
            self.assertEqual(gates.evaluate("gate-pass").status, "PASS")
            self.assertEqual(gates.evaluate("gate-fail").status, "FAIL")

            knowledge = KnowledgeService(store)
            knowledge.register_type("fact", "Fact")
            knowledge.append("knowledge", "fact", "OBSERVED", "Observed", "content")
            ProofPolicyService(store).declare("HMAC_SHA256", hmac_required=True)
            proof = ProofService(store, hmac_secret=b"universal-verdict-secret").promote(
                "proof-pass", "knowledge", "evidence-pass", "admission-pass"
            )
            self.assertEqual(proof.status, "PROVEN")
            with self.assertRaises(ProofError):
                ProofService(store, hmac_secret=b"universal-verdict-secret").promote(
                    "proof-fail", "knowledge", "evidence-fail", "admission-fail"
                )
            self.assertEqual(KnowledgeService(store).get("knowledge").status, "OBSERVED")


if __name__ == "__main__":
    unittest.main()
