"""Cover the Work Graph configuration of the journey (§29.2, step 8).

Two facts shape this lot, and both are stated rather than smoothed over.

The lifecycle is **closed in the Core**: four states, three events, fixed transitions. A project
does not invent its own. Letting one declare a state machine the Core does not enforce would
produce a graph that lies about what will actually happen — the screen would show a transition
the engine refuses. So the graph is *reported*, and what a project configures is how strict the
gate on each transition is.

And a transition policy is **declared once and never changed**: one row, with triggers refusing
`UPDATE` and `DELETE`. A wizard that let someone click through that without saying so would hide
an irreversible decision behind an ordinary-looking form.
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.identity import load_profile
from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization
from vera_mmu.store import MemoryStore
from vera_mmu.work_graph_config import (
    WorkGraphConfigError,
    apply_work_graph_configuration,
    preview_work_graph_configuration,
    read_work_graph_configuration,
)
from vera_mmu.work_lifecycle import WorkLifecycleError, WorkLifecycleService
from vera_mmu.write_api import WriteService


class WorkGraphConfigurationTests(unittest.TestCase):
    def _store(self, root: Path) -> MemoryStore:
        preview = preview_project_initialization(root, template="software", project_id="work-project", project_name="Work Project")
        apply_project_initialization(root, preview, confirm=True)
        profile = root / ".vera-mmu" / "project.yaml"
        return MemoryStore.open(load_profile(profile), profile)

    # --- what the configuration reports ------------------------------------

    def test_the_reported_graph_is_the_one_the_core_enforces(self) -> None:
        """The whole point: a displayed transition must be a transition that actually happens."""
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                graph = read_work_graph_configuration(store)
                declared = {(item["from"], item["event"], item["to"]) for item in graph["transitions"]}

                service = WorkLifecycleService(store)
                WriteService(store).create_work_item("wi-1", item_type="WORK_ITEM", title="Élément", actor="test")

                # A transition the graph declares is accepted.
                self.assertIn(("PLANNED", "START", "ACTIVE"), declared)
                service.transition("ev-1", "wi-1", "START", "démarrage", actor="test")
                self.assertEqual(service.get_state("wi-1").status, "ACTIVE")

                # One it does not declare is refused by the Core, not merely absent from a screen.
                self.assertNotIn(("ACTIVE", "START", "ACTIVE"), declared)
                with self.assertRaises(WorkLifecycleError):
                    service.transition("ev-2", "wi-1", "START", "second démarrage", actor="test")

    def test_reading_the_configuration_writes_nothing(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self._store(root) as store:
                before = read_work_graph_configuration(store)
                self.assertEqual(before["mutation"], "NONE")
                self.assertEqual(read_work_graph_configuration(store), before)

    def test_an_undeclared_policy_is_reported_as_undeclared_not_as_a_default(self) -> None:
        """Reporting a default the store does not hold would be inventing a decision."""
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                graph = read_work_graph_configuration(store)
                self.assertEqual(graph["start_policy"]["status"], "NOT_DECLARED")
                self.assertEqual(graph["completion_policy"]["status"], "NOT_DECLARED")

    def test_the_configuration_states_whether_the_work_graph_is_enabled(self) -> None:
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                self.assertIn("enabled", read_work_graph_configuration(store))

    # --- declaring a policy ------------------------------------------------

    def test_the_preview_says_the_declaration_is_irreversible(self) -> None:
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                preview = preview_work_graph_configuration(store, start_mode="REQUIRE_READY")
                self.assertEqual(preview.status, "PREVIEW")
                self.assertEqual(preview.mutation, "NONE")
                self.assertTrue(preview.irreversible)
                self.assertTrue(any("définitive" in note for note in preview.notes), preview.notes)

    def test_a_confirmed_declaration_is_readable_afterwards(self) -> None:
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                preview = preview_work_graph_configuration(store, start_mode="REQUIRE_READY", completion_mode="OPEN")
                result = apply_work_graph_configuration(store, preview, confirm=True)

                self.assertEqual(result["status"], "APPLIED")
                graph = read_work_graph_configuration(store)
                self.assertEqual(graph["start_policy"]["status"], "DECLARED")
                self.assertEqual(graph["start_policy"]["mode"], "REQUIRE_READY")
                self.assertEqual(graph["completion_policy"]["mode"], "OPEN")

    def test_a_declared_policy_is_actually_enforced(self) -> None:
        """A policy that changed no behaviour would be a setting pretending to be a rule.

        Readiness is about unmet prerequisites, so the proof needs one: an item with no
        dependency is ready, and `REQUIRE_READY` would let it start whether it was declared or
        not. That would have passed by accident rather than by enforcement.
        """
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                apply_work_graph_configuration(
                    store, preview_work_graph_configuration(store, start_mode="REQUIRE_READY"), confirm=True,
                )
                service = WriteService(store)
                service.create_work_item("wi-1", item_type="WORK_ITEM", title="Élément", actor="test")
                service.create_work_item("wi-0", item_type="WORK_ITEM", title="Prérequis", actor="test")
                service.add_work_dependency("wi-1", "wi-0", actor="test")

                with self.assertRaises(WorkLifecycleError):
                    WorkLifecycleService(store).transition("ev-1", "wi-1", "START", "démarrage", actor="test")

    def test_an_item_without_prerequisite_starts_even_under_the_strict_policy(self) -> None:
        """The counterpart: the policy blocks what is not ready, not everything."""
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                apply_work_graph_configuration(
                    store, preview_work_graph_configuration(store, start_mode="REQUIRE_READY"), confirm=True,
                )
                WriteService(store).create_work_item("wi-1", item_type="WORK_ITEM", title="Élément", actor="test")
                WorkLifecycleService(store).transition("ev-1", "wi-1", "START", "démarrage", actor="test")
                self.assertEqual(WorkLifecycleService(store).get_state("wi-1").status, "ACTIVE")

    # --- the refusals ------------------------------------------------------

    def test_redeclaring_a_policy_is_refused_and_changes_nothing(self) -> None:
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                apply_work_graph_configuration(
                    store, preview_work_graph_configuration(store, start_mode="OPEN"), confirm=True,
                )

                preview = preview_work_graph_configuration(store, start_mode="REQUIRE_READY")

                self.assertEqual(preview.status, "REFUSED")
                self.assertTrue(preview.blockers)
                with self.assertRaises(WorkGraphConfigError):
                    apply_work_graph_configuration(store, preview, confirm=True)
                self.assertEqual(read_work_graph_configuration(store)["start_policy"]["mode"], "OPEN")

    def test_an_unknown_mode_is_refused(self) -> None:
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                with self.assertRaises(WorkGraphConfigError):
                    preview_work_graph_configuration(store, start_mode="WHENEVER")

    def test_a_declaration_requires_an_explicit_confirmation(self) -> None:
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                preview = preview_work_graph_configuration(store, start_mode="REQUIRE_READY")
                with self.assertRaises(WorkGraphConfigError):
                    apply_work_graph_configuration(store, preview, confirm=False)
                self.assertEqual(read_work_graph_configuration(store)["start_policy"]["status"], "NOT_DECLARED")

    def test_a_stale_preview_is_refused(self) -> None:
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                preview = preview_work_graph_configuration(store, start_mode="REQUIRE_READY")
                apply_work_graph_configuration(
                    store, preview_work_graph_configuration(store, start_mode="OPEN"), confirm=True,
                )
                with self.assertRaises(WorkGraphConfigError):
                    apply_work_graph_configuration(store, preview, confirm=True)

    def test_naming_no_policy_is_refused(self) -> None:
        with TemporaryDirectory() as tmp:
            with self._store(Path(tmp)) as store:
                with self.assertRaises(WorkGraphConfigError):
                    preview_work_graph_configuration(store)

    def test_the_lifecycle_itself_cannot_be_redefined_through_this_surface(self) -> None:
        """No parameter of this module accepts a state or a transition: the graph is the Core's."""
        import inspect

        signature = inspect.signature(preview_work_graph_configuration)
        self.assertEqual(sorted(signature.parameters), ["completion_mode", "start_mode", "store"])


if __name__ == "__main__":
    unittest.main()
