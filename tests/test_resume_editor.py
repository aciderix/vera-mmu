"""The resume contract and the enabled integrations, editable at last — and what that breaks.

The exit criterion of this lot has two halves, and both are proven against the Core rather than a
screen: an edited contract produces exactly the requirements the guard then demands, and an edited
contract makes the resume already in flight visibly unusable.
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import yaml

from vera_mmu.identity import load_profile, profile_identity
from vera_mmu.profile_resume import compile_profile_resume_dossier, profile_resume_requirements, profile_resume_sections
from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization
from vera_mmu.session_lifecycle import ResumeGuardService
from vera_mmu.store import MemoryStore
from vera_mmu.write_api import WriteService


SESSION = "session-resume-editor"
ADAPTER = "generic-mcp"


class ResumeEditorTests(unittest.TestCase):
    def _project(self, root: Path, template: str = "software") -> Path:
        preview = preview_project_initialization(root, template=template, project_id="resume-app", project_name="Resume App")
        apply_project_initialization(root, preview, confirm=True)
        return root / ".vera-mmu" / "project.yaml"

    def _front(self, store: MemoryStore, identifier: str = "front-1") -> None:
        WriteService(store).replace_front(
            identifier,
            fields={
                "active_goal": "Prouver que le contrat de reprise est éditable et que la barrière suit.",
                "current_work": "Éditer les sections requises puis réarmer la garde de reprise.",
                "validated_facts": "La barrière lie une session au hash exact du dossier qui l’a armée.",
                "blockers": "Aucun.",
                "risks": "Une édition silencieuse casserait une reprise en cours sans le dire.",
                "next_action": "Éditer le contrat, puis réarmer et acquitter.",
            },
            actor="test",
            confirm=True,
        )

    def _dossier(self, store: MemoryStore):
        return compile_profile_resume_dossier(store, profile_resume_sections(store, "Reprise en cours de vérification."))

    def _sections(self, profile: Path) -> list[dict]:
        return yaml.safe_load(profile.read_text(encoding="utf-8"))["resume"]["sections"]

    # --- the editor, which did not exist ----------------------------------

    def test_i001_i009_preview_is_non_mutating_and_apply_is_confirmed_fresh_and_atomic(self) -> None:
        from vera_mmu.resume_editor import ResumeEditorError, apply_resume_edit, preview_resume_edit

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            before = profile.read_bytes()
            preview = preview_resume_edit(profile, integrations=["generic-mcp"])
            self.assertEqual(preview.status, "PREVIEW")
            self.assertEqual(profile.read_bytes(), before)
            with self.assertRaises(ResumeEditorError):
                apply_resume_edit(profile, preview, confirm=False)
            result = apply_resume_edit(profile, preview, confirm=True)
            self.assertEqual(result["status"], "APPLIED")
            self.assertEqual(load_profile(profile)["integrations"]["enabled"], ["generic-mcp"])

    def test_i009_step_thirteen_could_not_be_completed_before_and_can_be_now(self) -> None:
        """`integrations.enabled` gated the journey's step 13 and nothing could write it."""
        from vera_mmu.resume_editor import apply_resume_edit, preview_resume_edit
        from vera_mmu.wizard import wizard_state

        with TemporaryDirectory() as directory:
            root = Path(directory)
            profile = self._project(root)
            steps = {step.id: step.state for step in wizard_state(root).steps}
            self.assertNotEqual(steps["choose-integrations"], "COMPLETED")
            apply_resume_edit(profile, preview_resume_edit(profile, integrations=["generic-mcp"]), confirm=True)
            steps = {step.id: step.state for step in wizard_state(root).steps}
            self.assertEqual(steps["choose-integrations"], "COMPLETED")

    def test_i009_an_edit_that_changes_nothing_says_so_rather_than_rewriting_the_profile(self) -> None:
        from vera_mmu.resume_editor import apply_resume_edit, preview_resume_edit

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            before = profile.read_bytes()
            preview = preview_resume_edit(profile, template="engineering")
            self.assertEqual(preview.status, "NOTHING_TO_CHANGE")
            self.assertEqual(apply_resume_edit(profile, preview, confirm=True)["status"], "NOTHING_TO_CHANGE")
            self.assertEqual(profile.read_bytes(), before)

    def test_i009_a_preview_whose_profile_changed_since_review_is_refused(self) -> None:
        from vera_mmu.resume_editor import ResumeEditorError, apply_resume_edit, preview_resume_edit

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            stale = preview_resume_edit(profile, integrations=["generic-mcp"])
            other = preview_resume_edit(profile, max_resume_bytes=12_000)
            apply_resume_edit(profile, other, confirm=True)
            with self.assertRaises(ResumeEditorError):
                apply_resume_edit(profile, stale, confirm=True)

    # --- the exit criterion, first half -----------------------------------

    def test_i009_an_edited_contract_produces_exactly_the_requirements_the_guard_demands(self) -> None:
        """What the preview announces is what `profile_resume_requirements` then derives."""
        from vera_mmu.resume_editor import apply_resume_edit, preview_resume_edit

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            preview = preview_resume_edit(
                profile,
                sections=[
                    {"id": "working-rules", "required": True},
                    {"id": "next-action", "required": True},
                    {"id": "notes", "required": False},
                ],
            )
            announced = [dict(item) for item in preview.requirements]
            result = apply_resume_edit(profile, preview, confirm=True)
            self.assertEqual(result["requirements"], announced)
            with MemoryStore.open(load_profile(profile), profile) as store:
                derived = [
                    {"id": item.identifier, "minimum": item.minimum_characters, "maximum": item.maximum_characters}
                    for item in profile_resume_requirements(store)
                ]
            self.assertEqual(derived, announced)
            self.assertEqual([item["id"] for item in derived], ["working-rules", "next-action"])
            self.assertEqual(result["profile_hash"], profile_identity(load_profile(profile)).profile_hash)

    # --- the exit criterion, second half ----------------------------------

    def test_i009_an_edited_contract_visibly_invalidates_the_resume_in_flight(self) -> None:
        """The guard binds a session to one contract hash; editing the contract breaks that bond."""
        from vera_mmu.resume_editor import apply_resume_edit, preview_resume_edit

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            with MemoryStore.open(load_profile(profile), profile) as store:
                self._front(store)
                armed_dossier = self._dossier(store)
                ResumeGuardService(store).arm(SESSION, ADAPTER, "RESUME", armed_dossier, mode="HARD")
                sections = profile_resume_sections(store, "Reprise en cours de vérification.")
                # Before the edit the acknowledgement is possible; the test would prove nothing
                # otherwise.
                self.assertTrue(
                    ResumeGuardService(store).acknowledge(SESSION, ADAPTER, armed_dossier.resume_contract_hash, sections)
                )

            preview = preview_resume_edit(profile, sections=[{"id": "working-rules", "required": True}, {"id": "next-action", "required": True}])
            # The preview names what it will break, before anything is written.
            self.assertEqual([item["resume_contract_hash"] for item in preview.invalidates], [armed_dossier.resume_contract_hash])
            self.assertEqual([item["adapter_id"] for item in preview.invalidates], [ADAPTER])
            result = apply_resume_edit(profile, preview, confirm=True)
            self.assertEqual([item["resume_contract_hash"] for item in result["invalidated"]], [armed_dossier.resume_contract_hash])

            with MemoryStore.open(load_profile(profile), profile) as store:
                guard = ResumeGuardService(store)
                # Re-arming under the new contract yields a different hash…
                new_dossier = self._dossier(store)
                self.assertNotEqual(new_dossier.resume_contract_hash, armed_dossier.resume_contract_hash)
                guard.arm(SESSION, ADAPTER, "RESUME", new_dossier, mode="HARD")
                new_sections = profile_resume_sections(store, "Reprise en cours de vérification.")
                # …and the old hash no longer acknowledges anything.
                self.assertFalse(guard.acknowledge(SESSION, ADAPTER, armed_dossier.resume_contract_hash, new_sections))
                self.assertTrue(guard.acknowledge(SESSION, ADAPTER, new_dossier.resume_contract_hash, new_sections))

    def test_i009_a_handoff_prepared_under_the_old_contract_is_refused_after_the_edit(self) -> None:
        """The dossier carries its requirements; the Core refuses one the profile no longer declares."""
        from vera_mmu.handoff import HandoffError, HandoffService
        from vera_mmu.resume_editor import apply_resume_edit, preview_resume_edit

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            with MemoryStore.open(load_profile(profile), profile) as store:
                self._front(store)
                stale_dossier = self._dossier(store)
            apply_resume_edit(
                profile,
                preview_resume_edit(profile, sections=[{"id": "working-rules", "required": True}]),
                confirm=True,
            )
            with MemoryStore.open(load_profile(profile), profile) as store:
                # A Front is bound to the profile it was written under, so the project records a
                # new one after an edit. That is a separate consequence; what is proven here is
                # that the dossier compiled from the old contract is refused on its own merits.
                self._front(store, identifier="front-2")
                with self.assertRaises(HandoffError) as refused:
                    HandoffService(store).prepare("handoff-1", stale_dossier, actor="test", confirm=True)
                # The profile hash moved with the contract, so that binding refuses first; the
                # requirements comparison behind it can only fire on a hand-built dossier.
                self.assertIn("étranger", str(refused.exception))
                # The counterpart: a dossier compiled from the new contract is accepted.
                fresh = HandoffService(store).prepare("handoff-2", self._dossier(store), actor="test", confirm=True)
                self.assertEqual(fresh.id, "handoff-2")

    def test_i009_a_preview_that_changes_nothing_claims_to_invalidate_nothing(self) -> None:
        """Announcing a break that will not happen would train whoever reads it to ignore the notice."""
        from vera_mmu.resume_editor import preview_resume_edit

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            with MemoryStore.open(load_profile(profile), profile) as store:
                self._front(store)
                ResumeGuardService(store).arm(SESSION, ADAPTER, "RESUME", self._dossier(store), mode="HARD")
            self.assertEqual(preview_resume_edit(profile, template="engineering").invalidates, ())

    # --- what every profile edit used to break --------------------------

    def test_i011_i014_editing_a_profile_leaves_the_store_and_the_front_usable(self) -> None:
        """Two bricks, measured rather than supposed, and fixed for every profile editor.

        The store binds to `profile_hash`, so writing an edited profile without realigning it left
        the memory unopenable. And `current()` read the latest Front revision whatever profile it
        belonged to, so `_from_row` refused it and `replace` — which chains onto the current Front —
        could never record another: the Front was unreadable *and* unwritable, with no way back.
        """
        from vera_mmu.front import FrontError, FrontService
        from vera_mmu.profile_taxonomy import apply_taxonomy_edit, preview_taxonomy_edit
        from vera_mmu.resume_editor import apply_resume_edit, preview_resume_edit

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            with MemoryStore.open(load_profile(profile), profile) as store:
                self._front(store)
                self.assertIsNotNone(FrontService(store).current())
            apply_resume_edit(profile, preview_resume_edit(profile, integrations=["generic-mcp"]), confirm=True)
            apply_taxonomy_edit(
                profile,
                preview_taxonomy_edit(profile, entity_types=["COMPONENT", "MODULE", "SYMBOL", "TEST", "BUILD", "DEPLOY", "SERVICE"]),
                confirm=True,
            )
            # The store opens, so the identity moved with the profile.
            with MemoryStore.open(load_profile(profile), profile) as store:
                front = FrontService(store)
                # The previous profile's revision is history, not this profile's current Front…
                self.assertIsNone(front.current())
                with self.assertRaises(FrontError):
                    front.get("front-1")
                # …and a new one can be recorded, which was impossible before.
                self._front(store, identifier="front-2")
                current = front.current()
                self.assertIsNotNone(current)
                self.assertEqual(current.id, "front-2")
                self.assertIsNone(current.previous_front_id)
            self.assertEqual(sorted(p.name for p in profile.parent.glob(".profile-rebind-*")), [])

    # --- the contract's own feasibility ------------------------------------

    def test_i014_a_contract_the_guard_could_never_arm_is_refused(self) -> None:
        from vera_mmu.resume_editor import preview_resume_edit

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            empty = preview_resume_edit(profile, sections=[{"id": "notes", "required": False}])
            self.assertEqual([item.code for item in empty.blockers], ["NO_REQUIRED_SECTION"])
            for budget in (0, 10, 59):
                narrow = preview_resume_edit(profile, max_resume_bytes=budget)
                self.assertEqual([item.code for item in narrow.blockers], ["RESUME_BUDGET_TOO_SMALL"], budget)
            # The same budget is accepted once fewer sections share it, so the rule is about the
            # ratio rather than about refusing any small number.
            self.assertEqual(
                preview_resume_edit(profile, max_resume_bytes=59, sections=[{"id": "working-rules", "required": True}]).status,
                "PREVIEW",
            )

    def test_i009_an_integration_the_project_does_not_declare_is_refused(self) -> None:
        from vera_mmu.resume_editor import preview_resume_edit

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            refused = preview_resume_edit(profile, integrations=["not-a-profile"])
            self.assertEqual([item.code for item in refused.blockers], ["INTEGRATION_UNDECLARED"])
            self.assertEqual(preview_resume_edit(profile, integrations=["generic-mcp", "codex"]).status, "PREVIEW")

    def test_i014_a_malformed_section_is_refused_rather_than_written(self) -> None:
        from vera_mmu.resume_editor import ResumeEditorError, preview_resume_edit

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            before = profile.read_bytes()
            for sections in (
                [],
                [{"id": "", "required": True}],
                [{"id": "working-rules", "required": "yes"}],
                [{"id": "working-rules"}, {"id": "working_rules"}],
                [{"id": "working-rules", "required": True, "extra": 1}],
                "working-rules",
            ):
                with self.assertRaises(ResumeEditorError):
                    preview_resume_edit(profile, sections=sections)
            with self.assertRaises(ResumeEditorError):
                preview_resume_edit(profile)
            # A section id this module accepts but the Core's own profile contract does not: the
            # candidate is replayed through `validate_profile`, so the refusal comes from there.
            for invalid in ("Not A Section!", "x" * 200, "-leading"):
                refused = preview_resume_edit(profile, sections=[{"id": invalid, "required": True}])
                self.assertEqual([item.code for item in refused.blockers], ["RESUME_CONTRACT_INVALID"], invalid)
            self.assertEqual(profile.read_bytes(), before)

    def test_i011_a_preview_bound_to_another_project_is_refused(self) -> None:
        from vera_mmu.resume_editor import ResumeEditorError, apply_resume_edit, preview_resume_edit

        with TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first"
            first.mkdir()
            second = root / "second"
            second.mkdir()
            profile = self._project(first)
            other = self._project(second, template="data")
            preview = preview_resume_edit(profile, integrations=["generic-mcp"])
            with self.assertRaises(ResumeEditorError):
                apply_resume_edit(other, preview, confirm=True)


if __name__ == "__main__":
    unittest.main()
