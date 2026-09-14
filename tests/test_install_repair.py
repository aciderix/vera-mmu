"""Cover the guided repair the Definition of Done asks for (§54).

The Doctor names what is broken; nothing acted on it. This closes the loop for the failures a
repair can honestly fix: a declarative file the initialization owns and that has gone missing.

Repair never invents project content it cannot derive, never overwrites a file that is present,
and never runs without an explicit confirmation — a preview always comes first.

Invariants exercised: I008 (writes stay inside the runtime, no symlink is followed), I013 (a
write states an explicit decision) and I014 (what cannot be repaired is named, not guessed).
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.doctor import diagnose_project
from vera_mmu.install_repair import (
    InstallRepairError,
    apply_install_repair,
    preview_install_repair,
)
from vera_mmu.identity import load_profile
from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization
from vera_mmu.store import MemoryStore


class InstallRepairTests(unittest.TestCase):
    def _project(self, root: Path) -> Path:
        preview = preview_project_initialization(root, template="software", project_id="repair-project", project_name="Repair Project")
        apply_project_initialization(root, preview, confirm=True)
        profile = root / ".vera-mmu" / "project.yaml"
        with MemoryStore.open(load_profile(profile), profile):
            pass
        return profile

    # --- preview ---------------------------------------------------------

    def test_healthy_project_needs_no_repair(self) -> None:
        with TemporaryDirectory() as tmp:
            preview = preview_install_repair(self._project(Path(tmp)))
            self.assertEqual(preview.status, "NOTHING_TO_REPAIR")
            self.assertEqual(preview.actions, ())

    def test_preview_names_each_missing_declarative_file(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._project(root)
            (root / ".vera-mmu" / "playbook.md").unlink()
            (root / ".vera-mmu" / "gates.yaml").unlink()
            preview = preview_install_repair(profile)
            self.assertEqual(preview.status, "REPAIRABLE")
            self.assertEqual({action.target for action in preview.actions}, {"playbook.md", "gates.yaml"})
            self.assertTrue(all(action.operation == "RESTORE_DECLARATIVE_FILE" for action in preview.actions))

    def test_preview_writes_nothing(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._project(root)
            (root / ".vera-mmu" / "playbook.md").unlink()
            preview_install_repair(profile)
            self.assertFalse((root / ".vera-mmu" / "playbook.md").exists())

    # --- apply -----------------------------------------------------------

    def test_repair_requires_confirmation(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._project(root)
            (root / ".vera-mmu" / "playbook.md").unlink()
            preview = preview_install_repair(profile)
            with self.assertRaises(InstallRepairError):
                apply_install_repair(profile, preview, confirm=False)
            self.assertFalse((root / ".vera-mmu" / "playbook.md").exists())

    def test_repair_restores_the_files_and_the_doctor_passes_again(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._project(root)
            (root / ".vera-mmu" / "playbook.md").unlink()
            (root / ".vera-mmu" / "capabilities.yaml").unlink()
            self.assertEqual(diagnose_project(profile).status, "FAIL")

            result = apply_install_repair(profile, preview_install_repair(profile), confirm=True)
            self.assertEqual(result.status, "REPAIRED")
            self.assertEqual(set(result.repaired), {"playbook.md", "capabilities.yaml"})
            self.assertEqual(diagnose_project(profile).status, "PASS")

    def test_repair_never_recreates_an_absent_memory(self) -> None:
        """A lost SQLite is named by the Doctor, never silently replaced by an empty one."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._project(root)
            (root / ".vera-mmu" / "memory.sqlite").unlink()
            preview = preview_install_repair(profile)
            self.assertNotIn("memory.sqlite", {action.target for action in preview.actions})
            self.assertEqual(diagnose_project(profile).status, "FAIL")

    def test_repair_never_overwrites_a_present_file(self) -> None:
        """A file that exists is the project's; repair restores absences only."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._project(root)
            book = root / ".vera-mmu" / "playbook.md"
            authored = book.read_text(encoding="utf-8") + "\n## Règle du projet\n\nÀ conserver.\n"
            book.write_text(authored, encoding="utf-8")
            (root / ".vera-mmu" / "gates.yaml").unlink()

            apply_install_repair(profile, preview_install_repair(profile), confirm=True)
            self.assertEqual(book.read_text(encoding="utf-8"), authored)

    def test_stale_preview_is_refused(self) -> None:
        """I013: the state must still be the one the operator reviewed."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._project(root)
            (root / ".vera-mmu" / "playbook.md").unlink()
            preview = preview_install_repair(profile)
            (root / ".vera-mmu" / "gates.yaml").unlink()
            with self.assertRaises(InstallRepairError):
                apply_install_repair(profile, preview, confirm=True)

    def test_symlinked_target_is_refused(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._project(root)
            book = root / ".vera-mmu" / "playbook.md"
            book.unlink()
            elsewhere = root / "elsewhere.md"
            elsewhere.write_text("# Ailleurs\n", encoding="utf-8")
            book.symlink_to(elsewhere)
            preview = preview_install_repair(profile)
            self.assertEqual(preview.status, "NOT_REPAIRABLE")
            self.assertTrue(preview.blockers)

    def test_unrepairable_failure_is_named_rather_than_guessed(self) -> None:
        """A broken profile is not something repair may rewrite on the project's behalf."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._project(root)
            profile.write_text("mmu:\n  version: \"2.0\"\n", encoding="utf-8")
            with self.assertRaises(InstallRepairError):
                preview_install_repair(profile)


if __name__ == "__main__":
    unittest.main()
