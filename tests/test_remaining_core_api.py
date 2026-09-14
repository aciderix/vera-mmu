"""Cover the last six tools of the specification's Core API (§24).

These were the remainder after the usability lot: the two resume reads that make a resume
contract inspectable before it is acknowledged, the bundle import preview and its confirmed
restore, the non-archive export projection, and attaching admitted evidence to a gate.

No tool here accepts a filesystem path: a bundle is named by its identifier and resolved inside
the project runtime. Invariants exercised: I009 (resume bound to a hashed contract), I010
(bundle integrity chain), I011 (project identity) and I013 (explicit decision on a write).
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.bundles import BundleService
from vera_mmu.identity import load_profile
from vera_mmu.profile_resume import compile_profile_resume_dossier, profile_resume_sections
from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization
from vera_mmu.read_api import ReadApiError, ReadService
from vera_mmu.session_lifecycle import ResumeGuardService
from vera_mmu.store import MemoryStore
from vera_mmu.write_api import WriteApiError, WriteService


SESSION = "session-alpha"
ADAPTER = "generic-mcp"


class RemainingCoreApiTests(unittest.TestCase):
    def _project(self, root: Path, project_id: str = "api-project") -> Path:
        preview = preview_project_initialization(root, template="software", project_id=project_id, project_name="API Project")
        apply_project_initialization(root, preview, confirm=True)
        return root / ".vera-mmu" / "project.yaml"

    def _front(self, writer: WriteService) -> None:
        writer.replace_front("front-1", {
            "active_goal": "Terminer le contrat", "current_work": "Livrer les outils restants",
            "validated_facts": "La chaîne complète est prouvée", "blockers": "Aucun",
            "risks": "Surface élargie", "next_action": "Rejouer la suite",
        }, actor="test", confirm=True)

    # --- resume ----------------------------------------------------------

    def test_resume_brief_states_what_the_agent_must_produce(self) -> None:
        with TemporaryDirectory() as tmp:
            profile = self._project(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                brief = ReadService(store).resume_brief()
                self.assertEqual(brief["format"], "vera-resume-brief/v1")
                section_ids = [section["id"] for section in brief["required_sections"]]
                self.assertEqual(section_ids, ["working-rules", "current-state", "validated-facts", "risks", "next-action"])
                for section in brief["required_sections"]:
                    self.assertGreater(section["maximum_characters"], section["minimum_characters"])
                self.assertGreater(brief["max_resume_bytes"], 0)
                self.assertIsNone(brief["current_front"])

    def test_resume_brief_points_at_the_current_front_once_one_exists(self) -> None:
        with TemporaryDirectory() as tmp:
            profile = self._project(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                self._front(WriteService(store))
                brief = ReadService(store).resume_brief()
                self.assertEqual(brief["current_front"]["id"], "front-1")

    def test_resume_status_is_not_armed_on_a_fresh_project(self) -> None:
        with TemporaryDirectory() as tmp:
            profile = self._project(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                status = ReadService(store).resume_status(SESSION, ADAPTER)
                self.assertEqual(status["status"], "NOT_ARMED")
                self.assertIsNone(status["resume_contract_hash"])

    def test_resume_status_reports_an_armed_contract_without_leaking_the_session_key(self) -> None:
        """I009: the armed contract hash is readable; the session state key is not."""
        with TemporaryDirectory() as tmp:
            profile = self._project(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                self._front(WriteService(store))
                dossier = compile_profile_resume_dossier(store, profile_resume_sections(store, "Reprise en cours de vérification."))
                ResumeGuardService(store).arm(SESSION, ADAPTER, "RESUME", dossier, mode="HARD")

                status = ReadService(store).resume_status(SESSION, ADAPTER)
                self.assertEqual(status["status"], "ARMED")
                self.assertEqual(status["mode"], "HARD")
                self.assertEqual(status["resume_contract_hash"], dossier.resume_contract_hash)
                self.assertNotIn("session_state_key", status)
                self.assertNotIn(SESSION, str(status))

    # --- export projection -----------------------------------------------

    def test_export_projection_describes_the_project_without_writing_an_archive(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._project(root)
            with MemoryStore.open(load_profile(profile), profile) as store:
                WriteService(store).sync_profile_capabilities(actor="test")
                projection = ReadService(store).export_projection()
                self.assertEqual(projection["format"], "vera-export-projection/v1")
                self.assertEqual(projection["project_identity"]["project_id"], "api-project")
                self.assertEqual(len(projection["schema_hash"]), 64)
                self.assertEqual(projection["counts"]["capability"], 3)
                self.assertEqual(projection["catalog_hashes"].keys(), {"capabilities", "gates", "policies"})
            self.assertFalse((root / ".vera-mmu" / "bundles").exists())

    def test_export_projection_is_deterministic(self) -> None:
        with TemporaryDirectory() as tmp:
            profile = self._project(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                reader = ReadService(store)
                self.assertEqual(reader.export_projection(), reader.export_projection())

    # --- bundle preview and restore --------------------------------------

    def test_bundle_preview_verifies_without_writing(self) -> None:
        with TemporaryDirectory() as tmp:
            profile = self._project(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                BundleService(store).export("bundle-one", confirm=True)
                preview = ReadService(store).preview_bundle_import("bundle-one")
                self.assertEqual(preview["format"], "vera-bundle-import-preview/v1")
                self.assertEqual(preview["bundle_id"], "bundle-one")
                self.assertEqual(preview["project_identity"], store.identity.as_dict())
                self.assertEqual(len(preview["memory_hash"]), 64)
                # The current memory is present, so a restore would not merge into it.
                self.assertEqual(preview["target_state"], "OCCUPIED")

    def test_bundle_preview_refuses_an_unknown_identifier(self) -> None:
        with TemporaryDirectory() as tmp:
            profile = self._project(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                with self.assertRaises(ReadApiError):
                    ReadService(store).preview_bundle_import("absent")

    def test_bundle_identifier_cannot_escape_the_runtime(self) -> None:
        """I008: a bundle is named, never pathed."""
        with TemporaryDirectory() as tmp:
            profile = self._project(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                for candidate in ("../escape", "nested/bundle", "/etc/passwd"):
                    with self.assertRaises(ReadApiError):
                        ReadService(store).preview_bundle_import(candidate)

    def test_restore_refuses_without_confirmation_and_refuses_to_merge(self) -> None:
        with TemporaryDirectory() as tmp:
            profile = self._project(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                BundleService(store).export("bundle-two", confirm=True)
                writer = WriteService(store)
                with self.assertRaises(Exception):
                    writer.restore_bundle_by_id("bundle-two", confirm=False)
                # The live memory differs from the snapshot, so a merge is refused (I010/I011).
                writer.sync_profile_knowledge_types(actor="test")
                with self.assertRaises(Exception):
                    writer.restore_bundle_by_id("bundle-two", confirm=True)

    def test_restore_into_the_exporting_project_is_refused_as_a_merge(self) -> None:
        """Exporting writes the archive into the runtime, so the runtime no longer matches it.

        A bundle is meant to travel to an empty target of the same identity. Restoring into the
        project that produced it is therefore a merge, and a merge is always refused (I010).
        """
        with TemporaryDirectory() as tmp:
            profile = self._project(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                BundleService(store).export("bundle-three", confirm=True)
                with self.assertRaises(Exception):
                    WriteService(store).restore_bundle_by_id("bundle-three", confirm=True)

    # --- attach proof ----------------------------------------------------

    def test_attach_proof_binds_admitted_evidence_to_a_declared_gate(self) -> None:
        with TemporaryDirectory() as tmp:
            profile = self._project(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                from vera_mmu.evidence import EvidenceService
                from vera_mmu.executions import ExecutionService

                writer = WriteService(store)
                writer.sync_profile_capabilities(actor="test")
                writer.create_work_item("wi-gate", item_type="SUBTASK", title="Gated", actor="test")
                ExecutionService(store).run_noop("run-a", "test-suite-report", {"suite": "s", "passed": "1", "failed": "0"}, actor="test")
                EvidenceService(store).record("ev-a", "run-a", "TEST_PROOF", "PASS", {"suite": "s", "passed": "1", "failed": "0"})
                ExecutionService(store).run_noop("run-b", "test-suite-report", {"suite": "t", "passed": "2", "failed": "0"}, actor="test")
                EvidenceService(store).record("ev-b", "run-b", "TEST_PROOF", "PASS", {"suite": "t", "passed": "2", "failed": "0"})
                writer.declare_gate("gate-1", work_item_id="wi-gate", evidence_id="ev-a", actor="test")

                attached = writer.attach_proof("gate-1", evidence_id="ev-b", actor="test")
                self.assertEqual(attached["gate_id"], "gate-1")
                self.assertEqual(attached["evidence_id"], "ev-b")
                count = store.connection.execute(
                    "SELECT COUNT(*) FROM admission_gate_requirement WHERE gate_id = ?", ("gate-1",)
                ).fetchone()[0]
                self.assertEqual(count, 1)

    def test_attach_proof_refuses_an_unknown_gate_or_evidence(self) -> None:
        with TemporaryDirectory() as tmp:
            profile = self._project(Path(tmp))
            with MemoryStore.open(load_profile(profile), profile) as store:
                with self.assertRaises(Exception):
                    WriteService(store).attach_proof("absent", evidence_id="absent", actor="test")


if __name__ == "__main__":
    unittest.main()
