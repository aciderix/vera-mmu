"""Run one generic project from initialization to a signed `PROVEN` promotion.

Every earlier suite proves one surface. This one proves the product: a freshly initialized,
domain-agnostic project executes its own declared capability, produces evidence, gets that
evidence validated and admitted, and only then promotes a knowledge record to `PROVEN`.

It is also the regression guard for a defect the declarative path alone cannot catch: a
capability can pass generation and still be unexecutable if its parameter schema does not match
the runner its declaration names.

Invariants exercised: I004 (`PROVEN` requires an admissible `PASS`), I006 (a raw output is not
a proof), I007 (the executed capability comes from the declared catalog) and I012.
"""
from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

from vera_mmu.admission import AdmissionService
from vera_mmu.admission_policies import AdmissionPolicyService
from vera_mmu.evidence import EvidenceService
from vera_mmu.executions import ExecutionService
from vera_mmu.identity import load_profile
from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization
from vera_mmu.read_api import ReadService
from vera_mmu.store import MemoryStore
from vera_mmu.validators import ValidatorService
from vera_mmu.write_api import PROOF_HMAC_SECRET_VARIABLE, WriteService


class FullEpistemicChainTests(unittest.TestCase):
    def _project(self, root: Path, template: str = "software") -> Path:
        preview = preview_project_initialization(root, template=template, project_id="chain-project", project_name="Chain Project")
        apply_project_initialization(root, preview, confirm=True)
        return root / ".vera-mmu" / "project.yaml"

    def _prepare(self, store: MemoryStore) -> WriteService:
        writer = WriteService(store)
        writer.sync_profile_capabilities(actor="chain")
        writer.sync_profile_knowledge_types(actor="chain")
        return writer

    def test_declared_capability_is_actually_executable(self) -> None:
        """A declaration that generation accepts must also run; schema and runner must agree."""
        with TemporaryDirectory() as tmp:
            profile = self._project(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                self._prepare(store)
                validator = ValidatorService(store).get("vera-evidence-fields")
                self.assertEqual(validator.kind, "EVIDENCE_FIELDS")

                # The project produces its own evidence, carrying the fields its domain declares.
                ExecutionService(store).run_noop(
                    "collect-chain", "test-suite-report", {"suite": "pytest", "passed": "683", "failed": "0"}, actor="chain",
                )
                EvidenceService(store).record(
                    "evidence-chain", "collect-chain", "TEST_PROOF", "PASS",
                    {"suite": "pytest", "passed": "683", "failed": "0"},
                )
                execution = ExecutionService(store).run_evidence_fields(
                    "execution-chain", "software-fields-check",
                    {"validator_id": "vera-evidence-fields", "evidence_id": "evidence-chain"},
                    validation_id="validation-chain", actor="chain",
                )
                self.assertEqual(execution.status, "COMPLETED")
                self.assertEqual(ValidatorService(store).get_result("validation-chain").verdict, "PASS")

    def test_full_chain_reaches_proven_and_is_readable_back(self) -> None:
        with TemporaryDirectory() as tmp:
            profile = self._project(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                writer = self._prepare(store)
                writer.append_knowledge(
                    "kn-chain", type_id="MEASUREMENT", status="OBSERVED",
                    title="Résultat de la suite", content="La suite du projet est au vert.", actor="chain",
                )
                ExecutionService(store).run_noop(
                    "collect-chain", "test-suite-report", {"suite": "pytest", "passed": "683", "failed": "0"}, actor="chain",
                )
                EvidenceService(store).record(
                    "evidence-chain", "collect-chain", "TEST_PROOF", "PASS",
                    {"suite": "pytest", "passed": "683", "failed": "0"},
                )
                ExecutionService(store).run_evidence_fields(
                    "execution-chain", "software-fields-check",
                    {"validator_id": "vera-evidence-fields", "evidence_id": "evidence-chain"},
                    validation_id="validation-chain", actor="chain",
                )
                AdmissionPolicyService(store).declare("VALIDATED_PASS_EVIDENCE")
                AdmissionService(store).decide(
                    "admission-chain", "evidence-chain", "ADMITTED", "validée", validation_id="validation-chain",
                )
                writer.declare_proof_policy("HMAC_SHA256", hmac_required=True, actor="chain")

                with mock.patch.dict(os.environ, {PROOF_HMAC_SECRET_VARIABLE: "secret-de-chaine"}):
                    proof = writer.promote_knowledge(
                        "proof-chain", knowledge_id="kn-chain", evidence_id="evidence-chain",
                        admission_id="admission-chain", actor="chain",
                    )
                self.assertEqual(proof["status"], "PROVEN")

                read = ReadService(store).read("vera://chain-project/proof/proof-chain")
                self.assertEqual(read["record"]["status"], "PROVEN")
                self.assertTrue(read["record"]["signed"])
                self.assertNotIn("hmac_digest", read["record"])

    def test_promotion_refused_when_the_evidence_lacks_a_declared_field(self) -> None:
        """I004/I006: a field-incomplete evidence yields FAIL, so nothing can be promoted."""
        with TemporaryDirectory() as tmp:
            profile = self._project(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                writer = self._prepare(store)
                writer.append_knowledge(
                    "kn-weak", type_id="MEASUREMENT", status="OBSERVED", title="Partiel", content="Mesure incomplète.", actor="chain",
                )
                # `failed` is declared by the domain but missing here.
                ExecutionService(store).run_noop(
                    "collect-weak", "test-suite-report", {"suite": "pytest", "passed": "1", "failed": "0"}, actor="chain",
                )
                EvidenceService(store).record("evidence-weak", "collect-weak", "TEST_PROOF", "PASS", {"suite": "pytest", "passed": "1"})
                ExecutionService(store).run_evidence_fields(
                    "execution-weak", "software-fields-check",
                    {"validator_id": "vera-evidence-fields", "evidence_id": "evidence-weak"},
                    validation_id="validation-weak", actor="chain",
                )
                self.assertEqual(ValidatorService(store).get_result("validation-weak").verdict, "FAIL")
                AdmissionPolicyService(store).declare("VALIDATED_PASS_EVIDENCE")
                with self.assertRaises(Exception):
                    AdmissionService(store).decide(
                        "admission-weak", "evidence-weak", "ADMITTED", "forcée", validation_id="validation-weak",
                    )


if __name__ == "__main__":
    unittest.main()
