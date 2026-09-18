"""The policy catalogue: closed values, honest enforcement, and an editor that can reach it.

Three things are proven here, and the second is the one that mattered most before this lot.

1. `policies.yaml` can be edited at all. It shipped with every project, fed `policy_hash`, and no
   CLI, bridge or write API could change it.
2. Its **values** are closed, by the Core, on the file itself — so writing `network: {default:
   allow}` by hand is refused exactly as the editor refuses it.
3. The lines that claim to be enforced are enforced, and the ones that are not say so.
"""
from __future__ import annotations

from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

import yaml

from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization


class PolicyEditorTests(unittest.TestCase):
    def _project(self, root: Path, template: str = "software") -> Path:
        preview = preview_project_initialization(root, template=template, project_id="policy-app", project_name="Policy App")
        apply_project_initialization(root, preview, confirm=True)
        return root / ".vera-mmu" / "project.yaml"

    def _repository(self, root: Path) -> None:
        """Make the project a Git repository with a remote and a committed VERA baseline."""
        def git(*args: str) -> None:
            completed = subprocess.run(["git", "-C", str(root), *args], check=False, text=True, capture_output=True)
            if completed.returncode != 0:
                raise AssertionError(completed.stderr or completed.stdout)

        git("init", "-b", "main")
        git("config", "user.name", "VERA tests")
        git("config", "user.email", "vera-tests@example.invalid")
        git("add", "--", ".vera-mmu")
        git("commit", "-m", "VERA memory baseline")
        remote = root.parent / "remote.git"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, text=True, capture_output=True)
        git("remote", "add", "origin", str(remote))
        git("push", "-u", "origin", "main")

    def _policies(self, profile: Path) -> dict:
        return yaml.safe_load((profile.parent / "policies.yaml").read_text(encoding="utf-8"))

    def _write_policies(self, profile: Path, catalog: dict) -> None:
        (profile.parent / "policies.yaml").write_text(yaml.safe_dump(catalog, sort_keys=False), encoding="utf-8")

    def _assert_catalog_refused(self, profile: Path, section: str, key: str, value: object) -> None:
        """Set one line by hand and require the Core's loader to refuse it."""
        from vera_mmu.project_catalogs import ProjectCatalogError, load_project_catalogs

        path = profile.parent / "policies.yaml"
        original = path.read_bytes()
        try:
            catalog = self._policies(profile)
            catalog[section][key] = value
            self._write_policies(profile, catalog)
            with self.assertRaises(ProjectCatalogError):
                load_project_catalogs(profile)
        finally:
            path.write_bytes(original)

    # --- the editor, which did not exist ----------------------------------

    def test_i001_i013_preview_is_non_mutating_and_apply_is_confirmed_fresh_and_atomic(self) -> None:
        from vera_mmu.policy_editor import PolicyEditorError, apply_policy_edit, preview_policy_edit

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            before = (profile.parent / "policies.yaml").read_bytes()
            preview = preview_policy_edit(profile, {"filesystem.write": "deny"})
            self.assertEqual(preview.status, "PREVIEW")
            self.assertEqual((profile.parent / "policies.yaml").read_bytes(), before)
            with self.assertRaises(PolicyEditorError):
                apply_policy_edit(profile, preview, confirm=False)
            result = apply_policy_edit(profile, preview, confirm=True)
            self.assertEqual(result["status"], "APPLIED")
            self.assertEqual(self._policies(profile)["filesystem"]["write"], "deny")
            self.assertEqual(
                result["changes"], [{"section": "filesystem", "key": "write", "before": "confirm", "after": "deny"}]
            )

    def test_i013_an_edit_that_changes_nothing_says_so_rather_than_rewriting_the_file(self) -> None:
        from vera_mmu.policy_editor import apply_policy_edit, preview_policy_edit

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            before = (profile.parent / "policies.yaml").read_bytes()
            preview = preview_policy_edit(profile, {"filesystem.write": "confirm"})
            self.assertEqual(preview.status, "NOTHING_TO_CHANGE")
            self.assertEqual(apply_policy_edit(profile, preview, confirm=True)["status"], "NOTHING_TO_CHANGE")
            self.assertEqual((profile.parent / "policies.yaml").read_bytes(), before)

    def test_i013_a_preview_whose_catalog_changed_since_review_is_refused(self) -> None:
        from vera_mmu.policy_editor import PolicyEditorError, apply_policy_edit, preview_policy_edit

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            stale = preview_policy_edit(profile, {"filesystem.write": "deny"})
            other = preview_policy_edit(profile, {"git.push": "deny"})
            apply_policy_edit(profile, other, confirm=True)
            with self.assertRaises(PolicyEditorError):
                apply_policy_edit(profile, stale, confirm=True)

    def test_i013_an_unknown_line_is_refused_rather_than_added_to_the_catalog(self) -> None:
        from vera_mmu.policy_editor import PolicyEditorError, preview_policy_edit

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            for unknown in ("filesystem.execute", "sorcery.default", "filesystem", ""):
                with self.assertRaises(PolicyEditorError):
                    preview_policy_edit(profile, {unknown: "allow"})
            with self.assertRaises(PolicyEditorError):
                preview_policy_edit(profile, {})

    # --- the closed values, refused by the Core on the file itself ---------

    def test_i013_a_network_policy_the_core_cannot_honour_is_refused(self) -> None:
        """Fail-closed: the only network policy the Core admits is `deny`."""
        from vera_mmu.policy_editor import preview_policy_edit

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            for value in ("allow", "confirm"):
                self.assertEqual(preview_policy_edit(profile, {"network.default": value}).status, "REFUSED")
                self._assert_catalog_refused(profile, "network", "default", value)

    def test_i013_a_silently_permitted_destructive_default_is_not_declarable(self) -> None:
        from vera_mmu.policy_editor import preview_policy_edit

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            self.assertEqual(preview_policy_edit(profile, {"destructive.default": "allow"}).status, "REFUSED")
            self._assert_catalog_refused(profile, "destructive", "default", "allow")
            # `deny` stays declarable, so the rule is not simply refusing every change.
            self.assertEqual(preview_policy_edit(profile, {"destructive.default": "deny"}).status, "PREVIEW")

    def test_i004_proven_requires_cannot_declare_a_looser_engine_than_the_one_that_runs(self) -> None:
        """It records what promotion checks; declaring less would describe an engine that is not there."""
        from vera_mmu.policy_editor import preview_policy_edit

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            # The last one carries both required conditions, so only the unknown can refuse it.
            for value in ([], ["admissible_pass"], ["technical_validation"], ["admissible_pass", "technical_validation", "vibes"]):
                self.assertEqual(preview_policy_edit(profile, {"promotion.proven_requires": value}).status, "REFUSED", value)
                self._assert_catalog_refused(profile, "promotion", "proven_requires", value)

    def test_i007_a_runner_the_core_does_not_have_is_refused(self) -> None:
        from vera_mmu.policy_editor import preview_policy_edit

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            declared = list(self._policies(profile)["process"]["allowed_runners"])
            # Keeping every runner the catalogue uses, so only the unknown one can refuse this.
            for value in ([*declared, "SHELL"], ["SHELL"]):
                self.assertEqual(preview_policy_edit(profile, {"process.allowed_runners": value}).status, "REFUSED", value)
                self._assert_catalog_refused(profile, "process", "allowed_runners", value)

    def test_i007_the_runner_policy_is_cross_checked_against_the_capability_catalog(self) -> None:
        """It was decoration: every project shipped it empty while declaring capabilities that run."""
        from vera_mmu.policy_editor import preview_policy_edit

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            used = {str(item["runner"]) for item in yaml.safe_load((profile.parent / "capabilities.yaml").read_text(encoding="utf-8"))["capabilities"]}
            self.assertTrue(used)
            # The template now declares exactly the runners its own capabilities use.
            self.assertEqual(set(self._policies(profile)["process"]["allowed_runners"]), used)
            # Dropping one of them is refused, because a declared capability would use it.
            self.assertEqual(preview_policy_edit(profile, {"process.allowed_runners": []}).status, "REFUSED")
            self._assert_catalog_refused(profile, "process", "allowed_runners", [])

    def test_i007_a_capability_whose_runner_the_project_forbids_is_refused_before_it_is_written(self) -> None:
        """The refusal is in the preview, so no file is left for the loader to reject."""
        from vera_mmu.capability_builder import preview_capability_contract

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            declaration = {
                "id": "observed-run", "name": "Observed", "description": "Enregistre un processus observé.",
                "kind": "COLLECTOR", "version": "1.0.0", "runner": "OBSERVED_PROCESS", "policy": "READ_ONLY",
                "timeout_seconds": 60, "inputs": ["tool"], "outputs": ["verdict"], "artifacts": [],
                "validator": "EVIDENCE_FIELDS", "confirmation_required": False, "gate_backed": True,
            }
            refused = preview_capability_contract(profile, declaration)
            self.assertEqual(refused.status, "REFUSED")
            self.assertEqual([item.code for item in refused.refusals], ["DECLARATION_INVALID"])
            self.assertEqual((profile.parent / "capabilities.yaml").read_text(encoding="utf-8").count("observed-run"), 0)

    # --- enforcement reported honestly -------------------------------------

    def test_i013_each_line_names_what_enforces_it_or_says_that_nothing_does(self) -> None:
        from vera_mmu.policy_catalog import DECLARED_ONLY, ENFORCED
        from vera_mmu.policy_editor import policy_options

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            lines = {f"{item['section']}.{item['key']}": item for item in policy_options(profile)["lines"]}
            self.assertEqual(
                {name: item["enforcement"] for name, item in lines.items()},
                {
                    "filesystem.read": DECLARED_ONLY,
                    "filesystem.write": ENFORCED,
                    "network.default": ENFORCED,
                    "process.allowed_runners": ENFORCED,
                    "git.commit": ENFORCED,
                    "git.push": ENFORCED,
                    "destructive.default": DECLARED_ONLY,
                    "promotion.proven_requires": ENFORCED,
                },
            )
            self.assertTrue(all(item["reason"] for item in lines.values()))

    def test_i013_filesystem_write_deny_is_honoured_by_the_core(self) -> None:
        """The line reported ENFORCED is enforced, not merely labelled."""
        from vera_mmu.policy_editor import apply_policy_edit, preview_policy_edit
        from vera_mmu.project_policy import ProjectPolicyError, require_project_write_for_profile

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            require_project_write_for_profile(profile, confirm=True)
            apply_policy_edit(profile, preview_policy_edit(profile, {"filesystem.write": "deny"}), confirm=True)
            with self.assertRaises(ProjectPolicyError):
                require_project_write_for_profile(profile, confirm=True)

    def test_i013_git_deny_vetoes_the_automatic_memory_sync_without_ever_widening_it(self) -> None:
        """Two files declared Git behaviour; only one was read. The declared one is now a veto."""
        from vera_mmu.identity import load_profile
        from vera_mmu.memory_sync import automatic_memory_sync
        from vera_mmu.policy_editor import apply_policy_edit, preview_policy_edit
        from vera_mmu.store import MemoryStore

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            apply_policy_edit(profile, preview_policy_edit(profile, {"git.commit": "deny"}), confirm=True)
            with MemoryStore.open(load_profile(profile), profile) as store:
                result = automatic_memory_sync(store, "TEST_SYNC")
            self.assertEqual(result["status"], "DISABLED")
            self.assertEqual(result["reason"], "policies.yaml git.commit=deny")
            self.assertFalse(result["committed"])

    def test_i013_git_push_deny_stops_at_the_commit_instead_of_pushing(self) -> None:
        """The second veto, on its own branch: a commit is allowed and the push is not."""
        from vera_mmu.identity import load_profile
        from vera_mmu.memory_sync import automatic_memory_sync
        from vera_mmu.policy_editor import apply_policy_edit, preview_policy_edit
        from vera_mmu.store import MemoryStore

        with TemporaryDirectory() as directory:
            root = Path(directory) / "project"
            root.mkdir()
            profile = self._project(root)
            self._repository(root)
            apply_policy_edit(profile, preview_policy_edit(profile, {"git.push": "deny"}), confirm=True)
            with MemoryStore.open(load_profile(profile), profile) as store:
                # Opening the store synchronises the memory itself, so a second edit is what the
                # explicit sync below has left to commit.
                apply_policy_edit(profile, preview_policy_edit(profile, {"filesystem.read": "confirm"}), confirm=True)
                result = automatic_memory_sync(store, "TEST_SYNC")
            self.assertEqual(result["status"], "COMMITTED")
            self.assertEqual(result["reason"], "policies.yaml git.push=deny")
            self.assertTrue(result["committed"])
            self.assertFalse(result["pushed"])

    def test_i013_an_unreadable_policy_catalog_vetoes_nothing_it_did_not_say(self) -> None:
        """A veto nobody declared is not one: an unrelated failure must not stop the sync silently."""
        from vera_mmu.identity import load_profile
        from vera_mmu.memory_sync import _declared_git_policy
        from vera_mmu.store import MemoryStore

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            (profile.parent / "policies.yaml").write_text("format: broken\n", encoding="utf-8")
            with MemoryStore.open(load_profile(profile), profile) as store:
                self.assertEqual(_declared_git_policy(store), {"commit": "confirm", "push": "confirm"})

    def test_i011_a_symlinked_or_foreign_policy_file_is_refused(self) -> None:
        from vera_mmu.policy_editor import PolicyEditorError, apply_policy_edit, preview_policy_edit

        with TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first"
            first.mkdir()
            second = root / "second"
            second.mkdir()
            profile = self._project(first)
            other = self._project(second, template="data")
            preview = preview_policy_edit(profile, {"filesystem.write": "deny"})
            with self.assertRaises(PolicyEditorError):
                apply_policy_edit(other, preview, confirm=True)
            policies = profile.parent / "policies.yaml"
            policies.unlink()
            policies.symlink_to(profile.parent / "gates.yaml")
            with self.assertRaises(PolicyEditorError):
                preview_policy_edit(profile, {"filesystem.write": "deny"})


if __name__ == "__main__":
    unittest.main()
