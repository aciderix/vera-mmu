"""The three classes of §33, and the one rule that gives them teeth.

The exit criterion of this lot is a single sentence: a gate whose requirement is a semantic
appreciation cannot create a proof. It is proven here **against the Core** — `ProofService.promote`
refuses it — rather than against a screen, because a rule an interface holds stops existing the
moment the CLI, the MCP server or another agent writes.
"""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from vera_mmu.admission import AdmissionService
from vera_mmu.admission_policies import AdmissionPolicyService
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
from vera_mmu.work_items import WorkItemService


PROFILE = '''
mmu:
  version: "2.0"
project:
  id: "gate-classes"
  name: "Gate classes"
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


class _ProjectFixture:
    """The shared chain builder; not a test case, so it is never collected twice."""

    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        runtime = Path(self.directory.name) / ".vera-mmu"
        runtime.mkdir()
        self.profile = runtime / "project.yaml"
        self.profile.write_text(PROFILE, encoding="utf-8")

    def _store(self) -> MemoryStore:
        return MemoryStore.open(load_profile(self.profile), self.profile)

    def _chain(self, store: MemoryStore, evidence_type: str, *, suffix: str = "") -> tuple[str, str]:
        """Build one genuinely admitted PASS evidence of the requested type, through the Core."""
        capability = f"capability{suffix}"
        CapabilityService(store).create(capability, f"Capability{suffix}", "CHECK", "1.0.0")
        CapabilityContractService(store).declare(capability, "NOOP", "DENY_NETWORK", 30)
        CapabilityPolicyService(store).declare(capability, "ALLOW", "test")
        ExecutionService(store).run_noop(f"execution{suffix}", capability, {})
        evidence_id = f"evidence{suffix}"
        EvidenceService(store).record(evidence_id, f"execution{suffix}", evidence_type, "PASS", {"claim": "x"})
        admission_id = f"admission{suffix}"
        AdmissionService(store).decide(admission_id, evidence_id, "ADMITTED", "revue")
        return evidence_id, admission_id

    def _ready(self, store: MemoryStore) -> None:
        knowledge = KnowledgeService(store)
        knowledge.register_type("fact", "Fact")
        knowledge.append("knowledge-1", "fact", "OBSERVED", "Titre", "Contenu")
        AdmissionPolicyService(store).declare("PASS_EVIDENCE")
        ProofPolicyService(store).declare("HMAC_SHA256", hmac_required=False)


class EvidenceClassTests(_ProjectFixture, unittest.TestCase):
    """The classification, and the one rule that gives it teeth."""

    def test_i004_every_evidence_type_the_core_admits_carries_exactly_one_class(self) -> None:
        """An unclassified type would silently decide whether an opinion counts as a proof."""
        from vera_mmu.evidence import TYPES
        from vera_mmu.evidence_classes import CLASS_BY_EVIDENCE_TYPE, EVIDENCE_CLASSES, unclassified_types

        self.assertEqual(unclassified_types(), ())
        self.assertEqual(set(CLASS_BY_EVIDENCE_TYPE), set(TYPES))
        self.assertEqual(set(CLASS_BY_EVIDENCE_TYPE.values()), set(EVIDENCE_CLASSES))

    def test_i004_the_three_classes_are_reported_with_what_each_may_found(self) -> None:
        from vera_mmu.evidence_classes import EvidenceClassError, classify, describe, may_create_proof

        self.assertEqual(classify("TEST_PROOF"), "TECHNICAL_VALIDATION")
        self.assertEqual(classify("METRIC_PROOF"), "SIMPLE_OBSERVATION")
        self.assertEqual(classify("HUMAN_ASSERTION"), "SEMANTIC_APPRECIATION")
        self.assertTrue(may_create_proof("HASH_PROOF"))
        self.assertFalse(may_create_proof("MODEL_EVALUATION"))
        self.assertFalse(may_create_proof("EXTERNAL_ATTESTATION"))
        described = describe("HUMAN_ASSERTION")
        self.assertEqual(described["evidence_class"], "SEMANTIC_APPRECIATION")
        self.assertIn("jugement", described["reason"])
        # An unknown type is refused rather than given a default that would decide for the project.
        with self.assertRaises(EvidenceClassError):
            classify("VIBES")

    def test_i004_each_class_carries_its_own_reason_and_no_type_borrows_another(self) -> None:
        """Sharing a consequence does not make them one class: the fix differs, so the reason must.

        Checked structurally rather than by keyword: every type's reported reason must be exactly
        the one its own class maps to, and the three must be pairwise distinct. A keyword check
        alone would survive two classes swapping their explanations.
        """
        from vera_mmu.evidence_classes import CLASS_BY_EVIDENCE_TYPE, EVIDENCE_CLASSES, classify, describe, reason

        reasons = [reason(name) for name in EVIDENCE_CLASSES]
        self.assertEqual(len(set(reasons)), len(EVIDENCE_CLASSES))
        for evidence_type in CLASS_BY_EVIDENCE_TYPE:
            self.assertEqual(describe(evidence_type)["reason"], reason(classify(evidence_type)), evidence_type)

    # --- the exit criterion of the lot -------------------------------------

    def test_i004_i006_a_semantic_appreciation_cannot_create_a_proof(self) -> None:
        """The whole point of §33: an admitted PASS opinion still cannot promote."""
        with self._store() as store:
            self._ready(store)
            evidence_id, admission_id = self._chain(store, "HUMAN_ASSERTION")
            with self.assertRaises(ProofError) as refused:
                ProofService(store).promote("proof-1", "knowledge-1", evidence_id, admission_id)
            self.assertIn("SEMANTIC_APPRECIATION", str(refused.exception))

    def test_i004_a_simple_observation_cannot_create_a_proof_either(self) -> None:
        with self._store() as store:
            self._ready(store)
            evidence_id, admission_id = self._chain(store, "METRIC_PROOF")
            with self.assertRaises(ProofError) as refused:
                ProofService(store).promote("proof-1", "knowledge-1", evidence_id, admission_id)
            self.assertIn("SIMPLE_OBSERVATION", str(refused.exception))

    def test_i004_a_technical_validation_still_promotes(self) -> None:
        """The counterpart, without which the refusals could be a blanket ban proving nothing."""
        with self._store() as store:
            self._ready(store)
            evidence_id, admission_id = self._chain(store, "TEST_PROOF")
            proof = ProofService(store).promote("proof-1", "knowledge-1", evidence_id, admission_id)
            self.assertEqual(proof.status, "PROVEN")

    def test_i004_the_refusal_survives_a_gate_that_admits_the_opinion(self) -> None:
        """A gate may be satisfied by an appreciation; the promotion behind it is still refused."""
        with self._store() as store:
            self._ready(store)
            WorkItemService(store).create("work-1", item_type="WORK_ITEM", title="Revue")
            evidence_id, admission_id = self._chain(store, "MODEL_EVALUATION")
            GateService(store).declare("gate-1", "work-1", evidence_id)
            self.assertEqual(GateService(store).evaluate("gate-1").status, "PASS")
            with self.assertRaises(ProofError):
                ProofService(store).promote("proof-1", "knowledge-1", evidence_id, admission_id)


class GateReportTests(_ProjectFixture, unittest.TestCase):
    """The §33 screen itself, derived from what the Core holds."""

    def test_i004_a_gate_report_shows_each_requirement_with_its_class(self) -> None:
        from vera_mmu.gate_reports import report_gate

        with self._store() as store:
            self._ready(store)
            WorkItemService(store).create("work-1", item_type="WORK_ITEM", title="Livraison")
            primary, _ = self._chain(store, "TEST_PROOF", suffix="-1")
            opinion, _ = self._chain(store, "HUMAN_ASSERTION", suffix="-2")
            GateService(store).declare_with_requirements("gate-1", "work-1", primary, (opinion,))
            report = report_gate(store, "gate-1")
            self.assertEqual(report["gate_id"], "gate-1")
            self.assertEqual(report["capability"], {"status": "DERIVED", "capability_id": "capability-1"})
            classes = {item["evidence_id"]: item["evidence_class"] for item in report["requirements"]}
            self.assertEqual(classes, {primary: "TECHNICAL_VALIDATION", opinion: "SEMANTIC_APPRECIATION"})
            self.assertEqual(report["policy"]["status"], "NOT_DECLARED")
            self.assertTrue(report["promotion"]["can_create_proof"])
            self.assertTrue(report["promotion"]["can_satisfy_gate"])

    def test_i004_a_gate_made_only_of_appreciations_is_reported_unable_to_found_a_proof(self) -> None:
        """Not refused — a sign-off gate is legitimate — but never able to promote, and it says so."""
        from vera_mmu.gate_reports import report_gate

        with self._store() as store:
            self._ready(store)
            WorkItemService(store).create("work-1", item_type="WORK_ITEM", title="Revue")
            first, _ = self._chain(store, "HUMAN_ASSERTION", suffix="-1")
            second, _ = self._chain(store, "MODEL_EVALUATION", suffix="-2")
            GateService(store).declare_with_requirements("gate-1", "work-1", first, (second,))
            report = report_gate(store, "gate-1")
            self.assertFalse(report["promotion"]["can_create_proof"])
            self.assertIn("opinion", report["promotion"]["proof_reason"].lower())
            self.assertEqual(report["classes"]["TECHNICAL_VALIDATION"], [])
            self.assertEqual(len(report["classes"]["SEMANTIC_APPRECIATION"]), 2)

    def test_i014_a_gate_the_core_does_not_hold_is_refused_rather_than_reported_empty(self) -> None:
        from vera_mmu.gate_reports import GateReportError, report_gate

        with self._store() as store:
            self._ready(store)
            with self.assertRaises(GateReportError):
                report_gate(store, "absent")
            with self.assertRaises(GateReportError):
                report_gate(store, "bad/id")

    def test_i004_the_builder_shows_the_classes_before_the_gate_exists(self) -> None:
        """§33 is a builder screen: the classes are shown while declaring, not discovered later."""
        from vera_mmu.gate_structure_builder import apply_gate_structure_draft, preview_gate_structure_draft

        with self._store() as store:
            self._ready(store)
            WorkItemService(store).create("work-1", item_type="WORK_ITEM", title="Livraison")
            opinion, _ = self._chain(store, "HUMAN_ASSERTION", suffix="-1")
            observation, _ = self._chain(store, "METRIC_PROOF", suffix="-2")
            preview = preview_gate_structure_draft(
                store, gate_id="gate-1", work_item_id="work-1", primary_evidence_id=opinion,
                requirement_evidence_ids=(observation,),
            )
            payload = preview.as_dict()
            self.assertFalse(payload["promotion"]["can_create_proof"])
            self.assertEqual(
                [item["evidence_class"] for item in payload["endpoints"]],
                ["SEMANTIC_APPRECIATION", "SIMPLE_OBSERVATION"],
            )
            # It is reported, not refused: the gate is declarable and simply cannot promote.
            self.assertEqual(apply_gate_structure_draft(store, preview, confirm=True)["status"], "DECLARED")

    def test_i004_the_builder_reports_a_provable_gate_as_provable(self) -> None:
        from vera_mmu.gate_structure_builder import preview_gate_structure_draft

        with self._store() as store:
            self._ready(store)
            WorkItemService(store).create("work-1", item_type="WORK_ITEM", title="Livraison")
            technical, _ = self._chain(store, "CI_PROOF", suffix="-1")
            opinion, _ = self._chain(store, "HUMAN_ASSERTION", suffix="-2")
            preview = preview_gate_structure_draft(
                store, gate_id="gate-1", work_item_id="work-1", primary_evidence_id=technical,
                requirement_evidence_ids=(opinion,),
            )
            self.assertTrue(preview.can_create_proof)
            self.assertIn(technical, preview.proof_reason)


if __name__ == "__main__":
    unittest.main()
