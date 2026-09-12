from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.identity import load_profile
from vera_mmu.profile_migration import ProfileMigrationError, preview_profile_physical_migration
from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization


class ProfileMigrationPreviewTests(unittest.TestCase):
    def _project(self, root: Path) -> Path:
        preview = preview_project_initialization(root, template="software", project_id="migration-app", project_name="Migration App")
        apply_project_initialization(root, preview, confirm=True)
        runtime = root / ".vera-mmu"
        (runtime / "memory.sqlite").write_bytes(b"sqlite-placeholder")
        (runtime / "artifacts").mkdir(exist_ok=True)
        (runtime / "artifacts" / "proof.bin").write_bytes(b"proof")
        return runtime / "project.yaml"

    def test_preview_is_deterministic_read_only_and_inventories_runtime(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            profile_path = self._project(root)
            profile = load_profile(profile_path)
            candidate = deepcopy(profile)
            candidate["workspace"]["root"] = "src"
            (root / "src").mkdir()
            candidate["storage"]["memory_dir"] = ".vera-mmu-next"
            candidate["capabilities"]["catalog"] = ".vera-mmu-next/capabilities.yaml"
            candidate["gates"]["catalog"] = ".vera-mmu-next/gates.yaml"
            candidate["policies"]["file"] = ".vera-mmu-next/policies.yaml"
            candidate["integrations"]["agent_profiles"] = ".vera-mmu-next/agent-profiles.yaml"
            first = preview_profile_physical_migration(profile_path, candidate)
            second = preview_profile_physical_migration(profile_path, candidate)
            self.assertEqual(first, second)
            self.assertEqual(first.as_dict()["mutation"], "NONE")
            self.assertEqual(first.as_dict()["status"], "PREVIEW")
            self.assertTrue(any(item.kind == "runtime-file" and item.sha256 for item in first.inventory))
            self.assertTrue(profile_path.is_file())
            self.assertFalse((root / ".vera-mmu-next").exists())

    def test_preview_rejects_symlinked_source_and_overlapping_targets(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            profile_path = self._project(root)
            profile = load_profile(profile_path)
            candidate = deepcopy(profile)
            candidate["storage"]["memory_dir"] = "target"
            candidate["workspace"]["root"] = "target"
            candidate["capabilities"]["catalog"] = "target/capabilities.yaml"
            candidate["gates"]["catalog"] = "target/gates.yaml"
            candidate["policies"]["file"] = "target/policies.yaml"
            candidate["integrations"]["agent_profiles"] = "target/agent-profiles.yaml"
            with self.assertRaises(ProfileMigrationError):
                preview_profile_physical_migration(profile_path, candidate)

            alias = root / ".vera-mmu" / "runtime-alias"
            alias.symlink_to(root / ".vera-mmu" / "artifacts", target_is_directory=True)
            with self.assertRaises(ProfileMigrationError):
                preview_profile_physical_migration(profile_path, profile)


if __name__ == "__main__":
    unittest.main()
