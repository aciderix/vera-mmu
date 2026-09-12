from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest

from vera_mmu.identity import load_profile
from vera_mmu.profile_migration import ProfileMigrationError, execute_profile_physical_migration, inspect_profile_migration_journal, prepare_profile_migration_journal, preview_profile_physical_migration, recover_profile_physical_migration
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
            self.assertEqual(len(first.workspace_moves), 1)
            self.assertEqual(first.workspace_moves[0]["kind"], "workspace-root[0]")
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

    def test_journal_preparation_is_confirmed_atomic_and_refuses_stale_preview(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            profile_path = self._project(root)
            profile = load_profile(profile_path)
            candidate = deepcopy(profile)
            candidate["storage"]["memory_dir"] = ".vera-mmu-next"
            candidate["capabilities"]["catalog"] = ".vera-mmu-next/capabilities.yaml"
            candidate["gates"]["catalog"] = ".vera-mmu-next/gates.yaml"
            candidate["policies"]["file"] = ".vera-mmu-next/policies.yaml"
            candidate["integrations"]["agent_profiles"] = ".vera-mmu-next/agent-profiles.yaml"
            preview = preview_profile_physical_migration(profile_path, candidate)
            with self.assertRaises(ProfileMigrationError):
                prepare_profile_migration_journal(profile_path, candidate, preview, confirm=False)
            result = prepare_profile_migration_journal(profile_path, candidate, preview, confirm=True)
            journal = Path(str(result["journal_path"]))
            self.assertEqual(result["status"], "PLANNED")
            self.assertEqual(result["mutation"], "JOURNAL_ONLY")
            self.assertTrue(journal.is_file())
            self.assertTrue(profile_path.is_file())
            inspected = inspect_profile_migration_journal(profile_path)
            self.assertEqual(inspected["status"], "READY_FOR_EXECUTOR")
            self.assertEqual(inspected["mutation"], "NONE")
            self.assertIn("workspace_moves", json.loads(journal.read_text(encoding="utf-8")))
            with self.assertRaises(ProfileMigrationError):
                prepare_profile_migration_journal(profile_path, candidate, preview, confirm=True)

    def test_journal_inspection_refuses_source_divergence_and_target_collision(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            profile_path = self._project(root)
            profile = load_profile(profile_path)
            candidate = deepcopy(profile)
            candidate["storage"]["memory_dir"] = ".vera-mmu-next"
            candidate["capabilities"]["catalog"] = ".vera-mmu-next/capabilities.yaml"
            candidate["gates"]["catalog"] = ".vera-mmu-next/gates.yaml"
            candidate["policies"]["file"] = ".vera-mmu-next/policies.yaml"
            candidate["integrations"]["agent_profiles"] = ".vera-mmu-next/agent-profiles.yaml"
            preview = preview_profile_physical_migration(profile_path, candidate)
            prepare_profile_migration_journal(profile_path, candidate, preview, confirm=True)
            (root / ".vera-mmu" / "artifacts" / "proof.bin").write_bytes(b"altered")
            report = inspect_profile_migration_journal(profile_path)
            self.assertEqual(report["status"], "DIVERGED")
            self.assertTrue(any(issue["code"] == "SOURCE_DIVERGED" for issue in report["issues"]))

    def test_execute_moves_only_runtime_and_profile_after_wal_checkpoint(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            profile_path = self._project(root)
            sqlite_path = root / ".vera-mmu" / "memory.sqlite"
            sqlite_path.unlink()
            with sqlite3.connect(sqlite_path) as connection:
                connection.execute("CREATE TABLE marker(value TEXT)")
                connection.execute("INSERT INTO marker VALUES ('ok')")
                connection.commit()
            profile = load_profile(profile_path)
            candidate = deepcopy(profile)
            candidate["storage"]["memory_dir"] = ".vera-mmu-next"
            candidate["capabilities"]["catalog"] = ".vera-mmu-next/capabilities.yaml"
            candidate["gates"]["catalog"] = ".vera-mmu-next/gates.yaml"
            candidate["policies"]["file"] = ".vera-mmu-next/policies.yaml"
            candidate["integrations"]["agent_profiles"] = ".vera-mmu-next/agent-profiles.yaml"
            preview = preview_profile_physical_migration(profile_path, candidate)
            prepare_profile_migration_journal(profile_path, candidate, preview, confirm=True)
            result = execute_profile_physical_migration(profile_path, candidate, preview, confirm=True)
            self.assertEqual(result["status"], "COMMITTED")
            self.assertFalse((root / ".vera-mmu").exists())
            self.assertTrue((root / ".vera-mmu-next" / "memory.sqlite").is_file())
            migrated_profile = Path(str(result["profile_path"]))
            self.assertEqual(load_profile(migrated_profile)["storage"]["memory_dir"], ".vera-mmu-next")

    def test_recovery_rolls_back_interruption_before_move(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            profile_path = self._project(root)
            profile = load_profile(profile_path)
            candidate = deepcopy(profile)
            candidate["storage"]["memory_dir"] = ".vera-mmu-next"
            candidate["capabilities"]["catalog"] = ".vera-mmu-next/capabilities.yaml"
            candidate["gates"]["catalog"] = ".vera-mmu-next/gates.yaml"
            candidate["policies"]["file"] = ".vera-mmu-next/policies.yaml"
            candidate["integrations"]["agent_profiles"] = ".vera-mmu-next/agent-profiles.yaml"
            preview = preview_profile_physical_migration(profile_path, candidate)
            result = prepare_profile_migration_journal(profile_path, candidate, preview, confirm=True)
            journal = Path(str(result["journal_path"]))
            backup = root / ".vera-profile-migration-backup"
            backup.write_text(profile_path.read_text(encoding="utf-8"), encoding="utf-8")
            import json
            record = json.loads(journal.read_text(encoding="utf-8"))
            record["state"] = "EXECUTING"
            record["backup_path"] = str(backup)
            journal.write_text(json.dumps(record) + "\n", encoding="utf-8")
            recovered = recover_profile_physical_migration(journal, confirm=True)
            self.assertEqual(recovered["status"], "ROLLED_BACK_TO_PLANNED")
            self.assertTrue(journal.is_file())
            self.assertFalse(backup.exists())


if __name__ == "__main__":
    unittest.main()
