"""Cover the conclusion of the eighteen-step journey (§29.2, steps 15 to 18).

The four closing actions all existed and all worked. Nothing joined them: `wizard_state` reports
`next_step: None` the moment every observable step carries its evidence and stops, and the Doctor
sat in the console as one button among six. A project could therefore finish its journey, be told
nothing remained, and be broken — which is the state this suite starts from, in
`test_the_journey_no_longer_ends_in_silence_on_a_broken_project`.

What is pinned here is the verdict and its four outcomes, that each one is reachable, that the two
closing rows are *refused* rather than guessed while a step is still open, and that concluding a
journey writes nothing at all.
"""
from __future__ import annotations

from contextlib import redirect_stdout
from hashlib import sha256
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import yaml

from vera_mmu.__main__ import main
from vera_mmu.doctor import diagnose_project
from vera_mmu.generic_mcp_adapter import compile_generic_mcp_plan, stage_generic_mcp_runtime
from vera_mmu.identity import load_profile
from vera_mmu.journey_outcome import (
    COMPLETE,
    FAILED,
    INCOMPLETE,
    JOURNEY_OUTCOME_FORMAT,
    JourneyOutcomeError,
    NOT_REACHED,
    OPEN_STATES,
    REFUSED,
    journey_outcome,
)
from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization
from vera_mmu.project_validation import validate_project
from vera_mmu.store import MemoryStore
from vera_mmu.wizard import NOT_OBSERVABLE, wizard_state


def _silent(argv: list[str]) -> int:
    output = StringIO()
    with redirect_stdout(output):
        return main(argv)


def _cli(argv: list[str]) -> tuple[int, dict[str, object]]:
    output = StringIO()
    with redirect_stdout(output):
        code = main(argv)
    return code, json.loads(output.getvalue())


def _fingerprint(root: Path) -> list[tuple[str, str]]:
    """Hash every file under the project, so an unwritten byte is provable.

    The `-wal` and `-shm` sidecars are excluded: SQLite rebuilds them on its own, and the test
    must open the memory once to read the audit baseline. Including them would measure that
    opening rather than the conclusion, which writes nothing.
    """
    return sorted(
        (str(path.relative_to(root)), sha256(path.read_bytes()).hexdigest())
        for path in root.rglob("*")
        if path.is_file() and not path.is_symlink() and not path.name.endswith(("-wal", "-shm"))
    )


class JourneyConclusionTests(unittest.TestCase):
    """Every project here is built by the real pipeline, never by hand-written stubs.

    An outcome assembled from a fabricated `.mcp.json` and an empty `generated/` file would say
    `COMPLETE` for a project that no adapter ever configured, and the suite would be proving the
    assembly rather than the conclusion.
    """

    @staticmethod
    def _initialize(root: Path) -> Path:
        preview = preview_project_initialization(root, template="software", project_id="journey-project", project_name="Journey Project")
        apply_project_initialization(root, preview, confirm=True)
        return root / ".vera-mmu" / "project.yaml"

    def _terminal(self, root: Path) -> Path:
        """Walk the journey to its end for real: declare, initialise, generate, install."""
        profile = self._initialize(root)
        document = yaml.safe_load(profile.read_text(encoding="utf-8"))
        document["integrations"]["enabled"] = ["generic-mcp"]
        profile.write_text(yaml.safe_dump(document, allow_unicode=True, sort_keys=False), encoding="utf-8")
        self.assertEqual(_silent(["init", str(profile)]), 0)
        self.assertEqual(_silent(["sync-capabilities", str(profile)]), 0)
        with MemoryStore.open(load_profile(profile), profile) as store:
            stage_generic_mcp_runtime(store, compile_generic_mcp_plan(store), confirm=True)
        self.assertEqual(_silent(["install", str(profile), "--adapter", "generic-mcp", "--apply-project", "--confirm"]), 0)
        self.assertIsNone(wizard_state(root).next_step)
        return profile

    # --- the hole this lot closes ------------------------------------------

    def test_the_journey_no_longer_ends_in_silence_on_a_broken_project(self) -> None:
        """The state that had no name: every observable step done, and a project that fails."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._terminal(root)
            (root / ".vera-mmu" / "memory.sqlite").unlink()

            state = wizard_state(root)
            self.assertIsNone(state.next_step)  # the journey says nothing remains
            self.assertEqual(diagnose_project(profile).status, "FAIL")  # and the project is broken

            outcome = journey_outcome(root)
            self.assertEqual(outcome["status"], FAILED)
            self.assertIn("non sain", str(outcome["verdict"]))
            self.assertTrue(outcome["doctor"]["failing"])

    # --- the four outcomes, each reachable ---------------------------------

    def test_a_finished_and_healthy_project_concludes_complete(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._terminal(root)
            outcome = journey_outcome(root)
            self.assertEqual(outcome["status"], COMPLETE)
            self.assertEqual(outcome["format"], JOURNEY_OUTCOME_FORMAT)
            self.assertEqual(outcome["validation"]["status"], "VALID")
            self.assertEqual(outcome["doctor"]["status"], "PASS")
            self.assertEqual(outcome["doctor"]["failing"], [])
            self.assertEqual(outcome["project_id"], "journey-project")

    def test_an_unfinished_journey_concludes_incomplete_and_names_the_first_open_step(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._initialize(root)
            outcome = journey_outcome(root)
            self.assertEqual(outcome["status"], INCOMPLETE)
            first = outcome["steps"]["remaining"][0]
            self.assertEqual(first["id"], "choose-integrations")
            self.assertIn(first["label"], str(outcome["verdict"]))

    def test_a_refused_declarative_surface_concludes_refused(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._terminal(root)
            document = yaml.safe_load(profile.read_text(encoding="utf-8"))
            for section in document["resume"]["sections"]:
                section["required"] = False
            profile.write_text(yaml.safe_dump(document, allow_unicode=True, sort_keys=False), encoding="utf-8")

            outcome = journey_outcome(root)
            self.assertEqual(outcome["status"], REFUSED)
            self.assertEqual(outcome["validation"]["status"], REFUSED)
            self.assertIn("n’exige aucune section", str(outcome["validation"]["detail"]))

    def test_the_four_outcomes_are_distinct_and_all_observed(self) -> None:
        """Pin that no branch is dead: a status nobody can produce is a status nobody maintains."""
        observed = set()
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._initialize(root)
            observed.add(journey_outcome(root)["status"])
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._terminal(root)
            observed.add(journey_outcome(root)["status"])
            (root / ".vera-mmu" / "memory.sqlite").unlink()
            observed.add(journey_outcome(root)["status"])
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._terminal(root)
            (root / ".vera-mmu" / "playbook.md").unlink()
            observed.add(journey_outcome(root)["status"])
            del profile
        self.assertEqual(observed, {INCOMPLETE, COMPLETE, FAILED, REFUSED})

    # --- what the conclusion refuses to guess ------------------------------

    def test_both_closing_rows_are_not_reached_while_a_step_is_still_open(self) -> None:
        """A Doctor rendered mid-journey would only say « pas encore » — and teach the operator
        to scroll past the one check that must never be scrolled past."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._initialize(root)
            self.assertEqual(diagnose_project(profile).status, "FAIL")  # it would fail, for nothing

            outcome = journey_outcome(root)
            for key in ("validation", "doctor"):
                self.assertEqual(outcome[key]["status"], NOT_REACHED, key)
                self.assertIn("Choisir les intégrations", str(outcome[key]["detail"]), key)
            self.assertEqual(outcome["doctor"]["failing"], [])
            self.assertEqual(outcome["doctor"]["checks"], 0)

    def test_a_refused_surface_stops_before_the_doctor(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._terminal(root)
            (root / ".vera-mmu" / "playbook.md").unlink()
            outcome = journey_outcome(root)
            self.assertEqual(outcome["status"], REFUSED)
            self.assertEqual(outcome["doctor"]["status"], NOT_REACHED)
            self.assertIn("Valider", str(outcome["doctor"]["detail"]))
            del profile

    def test_an_ambiguous_root_refuses_loudly(self) -> None:
        with TemporaryDirectory() as tmp:
            with self.assertRaises(JourneyOutcomeError):
                journey_outcome(Path(tmp) / "absent")

    # --- what the conclusion never invents ---------------------------------

    def test_concluding_the_journey_writes_nothing(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._terminal(root)
            with MemoryStore.open(load_profile(profile), profile) as store:
                audit_before = store.audit_events()
            before = _fingerprint(root)

            self.assertEqual(journey_outcome(root)["mutation"], "NONE")

            self.assertEqual(_fingerprint(root), before)
            with MemoryStore.open(load_profile(profile), profile) as store:
                self.assertEqual(store.audit_events(), audit_before)

    def test_the_steps_are_the_wizard_s_own_and_partition_the_journey(self) -> None:
        """The conclusion renders the journey; it never recounts it."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._initialize(root)
            state = wizard_state(root)
            outcome = journey_outcome(root)
            steps = outcome["steps"]

            self.assertEqual(
                [item["id"] for item in steps["remaining"]],
                [step.id for step in state.steps if step.state in OPEN_STATES],
            )
            self.assertEqual(steps["next_step"], state.next_step)
            self.assertEqual(steps["total"], len(state.steps))
            self.assertEqual(steps["completed"] + steps["not_observable"] + len(steps["remaining"]), steps["total"])
            self.assertNotIn(NOT_OBSERVABLE, {item["state"] for item in steps["remaining"]})

    def test_the_hashes_are_the_validator_s_own(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._terminal(root)
            validation = validate_project(profile)
            hashes = journey_outcome(root)["validation"]["hashes"]
            self.assertEqual(hashes["profile_hash"], validation.profile_hash)
            self.assertEqual(hashes["playbook_hash"], validation.playbook_hash)
            for name, value in validation.catalog_hashes.items():
                self.assertEqual(hashes[name], value, name)

    def test_only_failing_checks_are_reported_as_failures(self) -> None:
        """A healthy project carries `INFO` rows; reporting them as failures would cry wolf."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._terminal(root)
            (root / ".vera-mmu" / "memory.sqlite").unlink()
            report = diagnose_project(profile)
            self.assertTrue(any(check.status == "INFO" for check in report.checks))

            doctor = journey_outcome(root)["doctor"]
            self.assertEqual(
                {item["name"] for item in doctor["failing"]},
                {check.name for check in report.checks if check.status == "FAIL"},
            )
            self.assertEqual(doctor["checks"], len(report.checks))

    def test_every_reported_failure_carries_its_repair(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._terminal(root)
            (root / ".vera-mmu" / "memory.sqlite").unlink()
            failing = journey_outcome(root)["doctor"]["failing"]
            self.assertTrue(failing)
            for check in failing:
                self.assertTrue(str(check["remediation"]).strip(), check["name"])
                self.assertNotEqual(check["remediation"], "Aucune action requise.")

    # --- the command line --------------------------------------------------

    def test_conclude_exits_zero_only_on_a_complete_journey(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            code, payload = _cli(["conclude", str(root)])
            self.assertEqual(code, 2)
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["outcome"]["status"], INCOMPLETE)

            self._terminal(root)
            code, payload = _cli(["conclude", str(root)])
            self.assertEqual(code, 0)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["outcome"]["status"], COMPLETE)

            (root / ".vera-mmu" / "memory.sqlite").unlink()
            code, payload = _cli(["conclude", str(root)])
            self.assertEqual(code, 2)
            self.assertEqual(payload["outcome"]["status"], FAILED)


if __name__ == "__main__":
    unittest.main()
