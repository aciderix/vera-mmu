"""Cover the work graph and proof promotion half of the VERA write facade.

Until this lot `ProofService.promote` had no production caller at all: invariant I004, the
rule the whole product exists to enforce, was reachable only from the test suite. These tests
exercise it through the facade, together with the work items and gates it depends on.

Invariants exercised: I004 (`PROVEN` requires an admissible `PASS`), I006 (a raw output is not
a proof), I007 (closed lifecycle event catalog) and I014 (loud refusal on missing secret).
"""
from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

from vera_mmu.admission import AdmissionService
from vera_mmu.admission_policies import AdmissionPolicyService
from vera_mmu.agent_profiles import builtin_agent_profiles_json
from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.evidence import EvidenceService
from vera_mmu.executions import ExecutionService
from vera_mmu.identity import load_profile
from vera_mmu.knowledge import KnowledgeService
from vera_mmu.read_api import ReadService
from vera_mmu.store import MemoryStore
from vera_mmu.validators import ValidatorService
from vera_mmu.work_lifecycle import WorkLifecycleService
from vera_mmu.write_api import PROOF_HMAC_SECRET_VARIABLE, WriteApiError, WriteService


PROFILE = """
mmu:
  version: "2.0"
project:
  id: "work-project"
  name: "Work Project"
  domain: "software"
workspace:
  root: "."
storage:
  memory_dir: ".vera-mmu"
  sqlite_file: "memory.sqlite"
  artifacts_dir: "artifacts"
  max_resume_bytes: 4096
work:
  enabled: true
"""
HASH_SCHEMA = {
    "type": "object",
    "properties": {"validator_id": {"type": "string"}, "evidence_id": {"type": "string"}},
    "required": ["validator_id", "evidence_id"],
    "additionalProperties": False,
}


class WriteApiWorkTests(unittest.TestCase):
    def _store(self, directory: Path) -> MemoryStore:
        runtime = directory / ".vera-mmu"
        runtime.mkdir(exist_ok=True)
        profile_path = runtime / "project.yaml"
        profile_path.write_text(PROFILE, encoding="utf-8")
        (runtime / "capabilities.yaml").write_text("format: vera-capability-catalog/v1\ncapabilities: []\n", encoding="utf-8")
        (runtime / "gates.yaml").write_text("format: vera-gate-catalog/v1\ngates: []\n", encoding="utf-8")
        (runtime / "agent-profiles.yaml").write_text(builtin_agent_profiles_json(), encoding="utf-8")
        (runtime / "policies.yaml").write_text(
            "format: vera-policy-catalog/v1\n"
            "filesystem: {read: allow, write: allow}\n"
            "network: {default: deny}\n"
            "process: {allowed_runners: []}\n"
            "git: {commit: confirm, push: confirm}\n"
            "destructive: {default: confirm}\n"
            "promotion: {proven_requires: [admissible_pass, technical_validation]}\n",
            encoding="utf-8",
        )
        return MemoryStore.open(load_profile(profile_path), profile_path)

    def _admissible_evidence(self, store: MemoryStore) -> None:
        """Build one genuinely admitted PASS evidence through the closed Core chain."""
        knowledge = KnowledgeService(store)
        knowledge.register_type("fact", "Fact")
        knowledge.append("knowledge-1", "fact", "OBSERVED", "Fait mesuré", "Un fait observé du projet.")
        CapabilityService(store).create("source", "Source", "CHECK", "1.0.0")
        CapabilityContractService(store).declare("source", "NOOP", "DENY_NETWORK", 30)
        CapabilityPolicyService(store).declare("source", "ALLOW", "test")
        ExecutionService(store).run_noop("source-run", "source", {})
        EvidenceService(store).record("evidence-1", "source-run", "TEST_PROOF", "PASS", {"claim": "terminal"})
        ValidatorService(store).register("hash", "EVIDENCE_HASH")
        CapabilityService(store).create("hash-cap", "Hash", "CHECK", "1.0.0")
        CapabilityContractService(store).declare("hash-cap", "EVIDENCE_HASH", "DENY_NETWORK", 30, parameter_schema=HASH_SCHEMA)
        CapabilityPolicyService(store).declare("hash-cap", "ALLOW", "test")
        ExecutionService(store).run_evidence_hash(
            "hash-run", "hash-cap", {"validator_id": "hash", "evidence_id": "evidence-1"}, validation_id="validation-1",
        )
        AdmissionPolicyService(store).declare("VALIDATED_PASS_EVIDENCE")
        AdmissionService(store).decide("admission-1", "evidence-1", "ADMITTED", "validated", validation_id="validation-1")

    # --- work items ------------------------------------------------------

    def test_create_work_item_and_read_graph(self) -> None:
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                writer = WriteService(store)
                parent = writer.create_work_item("wi-parent", item_type="EPIC", title="Chantier", actor="test")
                self.assertEqual(parent["status"], "PLANNED")
                self.assertEqual(parent["address"], "vera://work-project/work-item/wi-parent")
                writer.create_work_item("wi-child", item_type="SUBTASK", title="Sous-tâche", parent_id="wi-parent", actor="test")

                graph = ReadService(store).work_graph()
                self.assertEqual(graph["format"], "vera-work-graph/v1")
                identifiers = [item["id"] for item in graph["items"]]
                self.assertEqual(identifiers, ["wi-child", "wi-parent"])
                child = next(item for item in graph["items"] if item["id"] == "wi-child")
                self.assertEqual(child["parent_id"], "wi-parent")

    def test_create_work_item_refuses_unknown_parent(self) -> None:
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                with self.assertRaises(Exception):
                    WriteService(store).create_work_item("wi-orphan", item_type="SUBTASK", title="T", parent_id="absent", actor="test")

    def test_lifecycle_transition_is_a_closed_catalog(self) -> None:
        """I007: a client cannot invent a lifecycle event or a target state."""
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                writer = WriteService(store)
                writer.create_work_item("wi-1", item_type="SUBTASK", title="Tâche", actor="test")
                event = writer.transition_work_item("ev-1", work_item_id="wi-1", event="START", reason="prêt", actor="test")
                self.assertEqual(event["event"], "START")
                self.assertEqual(WorkLifecycleService(store).get_state("wi-1").status, "ACTIVE")
                with self.assertRaises(Exception):
                    writer.transition_work_item("ev-2", work_item_id="wi-1", event="TELEPORT", reason="x", actor="test")

    def test_work_graph_reports_lifecycle_state_not_creation_status(self) -> None:
        """The status column keeps its creation value; the state lives in the event log."""
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                writer = WriteService(store)
                writer.create_work_item("wi-live", item_type="SUBTASK", title="Vivant", actor="test")
                writer.transition_work_item("ev-live", work_item_id="wi-live", event="START", reason="demarrage", actor="test")

                item = next(row for row in ReadService(store).work_graph()["items"] if row["id"] == "wi-live")
                self.assertEqual(item["status"], "ACTIVE")
                self.assertEqual(WorkLifecycleService(store).get_state("wi-live").status, "ACTIVE")

    def test_dependency_refuses_cycle(self) -> None:
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                writer = WriteService(store)
                writer.create_work_item("wi-a", item_type="SUBTASK", title="A", actor="test")
                writer.create_work_item("wi-b", item_type="SUBTASK", title="B", actor="test")
                writer.add_work_dependency("wi-b", "wi-a", actor="test")
                with self.assertRaises(Exception):
                    writer.add_work_dependency("wi-a", "wi-b", actor="test")

    # --- gates -----------------------------------------------------------

    def test_declare_gate_binds_work_item_and_evidence(self) -> None:
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                self._admissible_evidence(store)
                writer = WriteService(store)
                writer.create_work_item("wi-gate", item_type="SUBTASK", title="Gated", actor="test")
                gate = writer.declare_gate("gate-1", work_item_id="wi-gate", evidence_id="evidence-1", actor="test")
                self.assertEqual(gate["gate_id"], "gate-1")
                self.assertEqual(gate["work_item_id"], "wi-gate")

    def test_declare_gate_refuses_unknown_evidence(self) -> None:
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                writer = WriteService(store)
                writer.create_work_item("wi-gate", item_type="SUBTASK", title="Gated", actor="test")
                with self.assertRaises(Exception):
                    writer.declare_gate("gate-x", work_item_id="wi-gate", evidence_id="absent", actor="test")

    # --- promotion -------------------------------------------------------

    def test_promotion_requires_admissible_pass(self) -> None:
        """I004: this is the rule the product exists to enforce."""
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                self._admissible_evidence(store)
                writer = WriteService(store)
                writer.declare_proof_policy("HMAC_SHA256", hmac_required=False, actor="test")
                proof = writer.promote_knowledge(
                    "proof-1", knowledge_id="knowledge-1", evidence_id="evidence-1", admission_id="admission-1", actor="test",
                )
                self.assertEqual(proof["status"], "PROVEN")
                self.assertEqual(ReadService(store).list_proofs()["proofs"][0]["id"], "proof-1")

    def test_promotion_refused_without_admission(self) -> None:
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                self._admissible_evidence(store)
                writer = WriteService(store)
                writer.declare_proof_policy("HMAC_SHA256", hmac_required=False, actor="test")
                with self.assertRaises(Exception):
                    writer.promote_knowledge(
                        "proof-x", knowledge_id="knowledge-1", evidence_id="evidence-1", admission_id="absent", actor="test",
                    )

    def test_promotion_refused_without_declared_policy(self) -> None:
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                self._admissible_evidence(store)
                with self.assertRaises(Exception):
                    WriteService(store).promote_knowledge(
                        "proof-np", knowledge_id="knowledge-1", evidence_id="evidence-1", admission_id="admission-1", actor="test",
                    )

    def test_hmac_secret_comes_from_environment_not_from_the_caller(self) -> None:
        """I014: a policy requiring HMAC fails loudly rather than promoting unsigned."""
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                self._admissible_evidence(store)
                writer = WriteService(store)
                writer.declare_proof_policy("HMAC_SHA256", hmac_required=True, actor="test")
                with mock.patch.dict(os.environ, {}, clear=False):
                    os.environ.pop(PROOF_HMAC_SECRET_VARIABLE, None)
                    with self.assertRaises(WriteApiError):
                        writer.promote_knowledge(
                            "proof-nosecret", knowledge_id="knowledge-1", evidence_id="evidence-1", admission_id="admission-1", actor="test",
                        )
                with mock.patch.dict(os.environ, {PROOF_HMAC_SECRET_VARIABLE: "secret-de-projet"}):
                    proof = writer.promote_knowledge(
                        "proof-signed", knowledge_id="knowledge-1", evidence_id="evidence-1", admission_id="admission-1", actor="test",
                    )
                self.assertEqual(proof["status"], "PROVEN")
                self.assertNotIn("hmac_secret", proof)

    def test_promotion_signature_is_not_returned_as_client_input(self) -> None:
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                self._admissible_evidence(store)
                writer = WriteService(store)
                writer.declare_proof_policy("HMAC_SHA256", hmac_required=False, actor="test")
                proof = writer.promote_knowledge(
                    "proof-2", knowledge_id="knowledge-1", evidence_id="evidence-1", admission_id="admission-1", actor="test",
                )
                self.assertEqual(proof["knowledge_id"], "knowledge-1")
                self.assertEqual(proof["evidence_id"], "evidence-1")


if __name__ == "__main__":
    unittest.main()
