"""Cover the eighteen-step configuration journey the specification lays out (§29.2).

The desktop console was a single page of independent buttons: nothing said what had to exist
before what, and nothing could say where a half-configured project stood. This pins the journey
itself — its order, its entry criteria, and the evidence that makes a step done.

The state is **derived from the project**, never from a flag the interface keeps. Reopening the
application on a project someone left half-configured must land on the same step, and asking
where the journey stands must write nothing.

Five of the eighteen steps leave no trace at all — scanning, detecting, proposing, previewing,
validating and running the Doctor change nothing on disk. They are reported `NOT_OBSERVABLE`
rather than guessed at: a wizard that claimed a scan had happened would be inventing the one
thing it cannot see.
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import yaml

from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization
from vera_mmu.wizard import WIZARD_STEPS, WizardError, wizard_state


SPECIFIED_ORDER = (
    "scan-project", "detect-structure", "propose-profile", "choose-domain", "edit-taxonomy",
    "define-entities", "define-relations", "configure-work-graph", "declare-capabilities",
    "build-gates", "define-policies", "configure-resume", "choose-integrations", "preview-mcp",
    "validate", "generate", "install", "run-doctor",
)


class WizardJourneyTests(unittest.TestCase):
    def _initialize(self, root: Path) -> Path:
        preview = preview_project_initialization(root, template="software", project_id="wizard-project", project_name="Wizard Project")
        apply_project_initialization(root, preview, confirm=True)
        return root / ".vera-mmu" / "project.yaml"

    @staticmethod
    def _by_id(root: Path) -> dict:
        return {step.id: step for step in wizard_state(root).steps}

    # --- the journey itself ------------------------------------------------

    def test_the_eighteen_steps_are_declared_in_the_specification_order(self) -> None:
        self.assertEqual(tuple(step.id for step in WIZARD_STEPS), SPECIFIED_ORDER)
        self.assertEqual(tuple(step.index for step in WIZARD_STEPS), tuple(range(1, 19)))

    def test_the_state_reports_every_step_once(self) -> None:
        with TemporaryDirectory() as tmp:
            steps = wizard_state(Path(tmp)).steps
            self.assertEqual(tuple(step.id for step in steps), SPECIFIED_ORDER)

    # --- an untouched directory -------------------------------------------

    def test_an_untouched_directory_can_only_be_observed_and_initialized(self) -> None:
        with TemporaryDirectory() as tmp:
            steps = self._by_id(Path(tmp))
            for identifier in ("scan-project", "detect-structure", "propose-profile"):
                self.assertEqual(steps[identifier].state, "NOT_OBSERVABLE")
            self.assertEqual(steps["choose-domain"].state, "AVAILABLE")
            for identifier in ("edit-taxonomy", "declare-capabilities", "generate", "install"):
                self.assertEqual(steps[identifier].state, "BLOCKED", identifier)

    def test_every_step_that_is_not_completed_says_why(self) -> None:
        with TemporaryDirectory() as tmp:
            for step in wizard_state(Path(tmp)).steps:
                if step.state != "COMPLETED":
                    self.assertTrue(step.reason, f"`{step.id}` sans raison")

    def test_the_next_step_of_an_untouched_directory_is_the_domain(self) -> None:
        with TemporaryDirectory() as tmp:
            self.assertEqual(wizard_state(Path(tmp)).next_step, "choose-domain")

    # --- after initialization ---------------------------------------------

    def test_initialization_completes_the_steps_whose_evidence_it_writes(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile_path = self._initialize(root)
            profile = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
            steps = self._by_id(root)

            for identifier in ("choose-domain", "edit-taxonomy", "define-entities", "define-relations",
                               "declare-capabilities", "build-gates", "define-policies", "configure-resume"):
                self.assertEqual(steps[identifier].state, "COMPLETED", identifier)
            # The work graph is completed only if the profile actually enables it.
            expected = "COMPLETED" if profile["work"]["enabled"] is True else "AVAILABLE"
            self.assertEqual(steps["configure-work-graph"].state, expected)

    def test_integrations_stay_open_until_one_is_enabled(self) -> None:
        """Initialization declares the agent profiles; enabling one is the owner's decision."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile_path = self._initialize(root)
            self.assertEqual(self._by_id(root)["choose-integrations"].state, "AVAILABLE")

            profile = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
            profile["integrations"]["enabled"] = ["generic-mcp"]
            profile_path.write_text(yaml.safe_dump(profile, sort_keys=True), encoding="utf-8")

            self.assertEqual(self._by_id(root)["choose-integrations"].state, "COMPLETED")

    def test_install_stays_blocked_until_something_has_been_generated(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._initialize(root)
            self.assertEqual(self._by_id(root)["install"].state, "BLOCKED")

            generated = root / ".vera-mmu" / "generated"
            generated.mkdir()
            (generated / "generic-mcp-runtime.json").write_text("{}", encoding="utf-8")

            self.assertEqual(self._by_id(root)["install"].state, "AVAILABLE")

    def test_install_is_completed_once_a_declared_host_configuration_exists(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._initialize(root)
            generated = root / ".vera-mmu" / "generated"
            generated.mkdir()
            (generated / "generic-mcp-runtime.json").write_text("{}", encoding="utf-8")
            (root / ".mcp.json").write_text("{}", encoding="utf-8")

            self.assertEqual(self._by_id(root)["install"].state, "COMPLETED")

    # --- what the state must never become ----------------------------------

    def test_asking_where_the_journey_stands_writes_nothing(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._initialize(root)
            before = {path.relative_to(root).as_posix() for path in root.rglob("*")}

            result = wizard_state(root)

            self.assertEqual({path.relative_to(root).as_posix() for path in root.rglob("*")}, before)
            self.assertEqual(result.mutation, "NONE")

    def test_the_state_is_derived_and_not_remembered(self) -> None:
        """Removing the evidence returns the journey to its start, with no memory of the past."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            initial = wizard_state(root).as_dict()
            self._initialize(root)
            self.assertNotEqual(wizard_state(root).as_dict(), initial)

            for path in sorted((root / ".vera-mmu").rglob("*"), reverse=True):
                path.unlink() if path.is_file() else path.rmdir()
            (root / ".vera-mmu").rmdir()

            self.assertEqual(wizard_state(root).as_dict(), initial)

    def test_the_state_is_deterministic(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._initialize(root)
            self.assertEqual(wizard_state(root), wizard_state(root))

    def test_a_broken_catalog_blocks_its_step_rather_than_crashing_the_journey(self) -> None:
        """A half-configured project is exactly what this must survive describing."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._initialize(root)
            (root / ".vera-mmu" / "capabilities.yaml").write_text(":\n  not: [valid", encoding="utf-8")

            steps = self._by_id(root)

            self.assertNotEqual(steps["declare-capabilities"].state, "COMPLETED")
            self.assertTrue(steps["declare-capabilities"].reason)

    def test_a_broken_profile_blocks_everything_after_the_domain_rather_than_crashing(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile_path = self._initialize(root)
            profile_path.write_text("mmu:\n  version: \"2.0\"\n", encoding="utf-8")

            steps = self._by_id(root)

            self.assertEqual(steps["choose-domain"].state, "AVAILABLE")
            self.assertEqual(steps["edit-taxonomy"].state, "BLOCKED")
            self.assertTrue(steps["edit-taxonomy"].reason)

    def test_a_root_that_is_not_a_directory_is_refused(self) -> None:
        with TemporaryDirectory() as tmp:
            target = Path(tmp) / "file.txt"
            target.write_text("", encoding="utf-8")
            with self.assertRaises(WizardError):
                wizard_state(target)

    def test_a_symlinked_root_is_refused(self) -> None:
        with TemporaryDirectory() as tmp:
            real = Path(tmp) / "real"
            real.mkdir()
            link = Path(tmp) / "link"
            link.symlink_to(real, target_is_directory=True)
            with self.assertRaises(WizardError):
                wizard_state(link)


if __name__ == "__main__":
    unittest.main()
