from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest
from unittest.mock import patch
import yaml

import vera_mmu.profile_migration as profile_migration
from vera_mmu.identity import load_profile
from vera_mmu.profile_migration import ProfileMigrationError, _copy_tree_verified, execute_profile_physical_migration, inspect_profile_migration_journal, prepare_profile_migration_journal, preview_profile_physical_migration, record_copy_progress, recover_profile_physical_migration, transition_profile_migration_state
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
            self.assertEqual(first.migration_strategy, "RENAME_ATOMIC")
            self.assertEqual(len(first.workspace_moves), 1)
            self.assertEqual(first.workspace_moves[0]["kind"], "workspace-root[0]")
            self.assertTrue(any(item.kind == "runtime-file" and item.sha256 for item in first.inventory))
            self.assertTrue(profile_path.is_file())
            self.assertFalse((root / ".vera-mmu-next").exists())

    def test_copy_tree_verified_hashes_files_and_removes_partial_target(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            target = root / "target"
            source.mkdir()
            (source / "nested").mkdir()
            (source / "nested" / "file.txt").write_text("verified", encoding="utf-8")
            progress: list[tuple[str, str]] = []
            _copy_tree_verified(source, target, progress=lambda relative, state: progress.append((relative, state)))
            self.assertEqual((target / "nested" / "file.txt").read_text(encoding="utf-8"), "verified")
            self.assertEqual(progress, [("nested/file.txt", "COPYING"), ("nested/file.txt", "VERIFIED")])
            (source / "unsafe").symlink_to(source / "nested", target_is_directory=True)
            with self.assertRaises(ProfileMigrationError):
                _copy_tree_verified(source, root / "rejected")
            self.assertFalse((root / "rejected").exists())

    def test_copy_tree_verified_persists_copying_and_verified_in_journal(self) -> None:
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
            prepared = prepare_profile_migration_journal(profile_path, candidate, preview, confirm=True)
            journal = Path(str(prepared["journal_path"]))
            source = root / "copy-source"
            target = root / "copy-target"
            (source / "nested").mkdir(parents=True)
            (source / "nested" / "file.txt").write_text("journalled", encoding="utf-8")

            _copy_tree_verified(source, target, journal_path=journal)

            record = json.loads(journal.read_text(encoding="utf-8"))
            self.assertEqual(
                record["copy_progress"],
                [
                    {"path": "nested/file.txt", "state": "COPYING"},
                    {"path": "nested/file.txt", "state": "VERIFIED"},
                ],
            )
            self.assertEqual((target / "nested" / "file.txt").read_text(encoding="utf-8"), "journalled")

    def test_copy_tree_verified_keeps_copying_when_verified_persistence_fails(self) -> None:
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
            prepared = prepare_profile_migration_journal(profile_path, candidate, preview, confirm=True)
            journal = Path(str(prepared["journal_path"]))
            source = root / "copy-source"
            target = root / "copy-target"
            source.mkdir()
            (source / "file.txt").write_text("ambiguous", encoding="utf-8")

            original = profile_migration.record_copy_progress

            def fail_after_copying(journal_path: str | Path, relative_path: str, state: str) -> dict[str, object]:
                if state == "VERIFIED":
                    raise ProfileMigrationError("journal unavailable")
                return original(journal_path, relative_path, state)

            with patch.object(profile_migration, "record_copy_progress", side_effect=fail_after_copying):
                with self.assertRaises(ProfileMigrationError):
                    _copy_tree_verified(source, target, journal_path=journal)

            record = json.loads(journal.read_text(encoding="utf-8"))
            self.assertEqual(record["state"], "COPYING")
            self.assertEqual(record["copy_progress"], [{"path": "file.txt", "state": "COPYING"}])
            self.assertFalse(target.exists())

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
            self.assertEqual(json.loads(journal.read_text(encoding="utf-8"))["migration_strategy"], "RENAME_ATOMIC")
            self.assertEqual(record_copy_progress(journal, "nested/file.txt", "COPYING")["state"], "COPYING")
            self.assertEqual(record_copy_progress(journal, "nested/file.txt", "VERIFIED")["state"], "VERIFIED")
            with self.assertRaises(ProfileMigrationError):
                record_copy_progress(journal, "nested/file.txt", "VERIFIED")
            with self.assertRaises(ProfileMigrationError):
                prepare_profile_migration_journal(profile_path, candidate, preview, confirm=True)

    def test_global_migration_state_transitions_are_allowlisted(self) -> None:
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
            prepared = prepare_profile_migration_journal(profile_path, candidate, preview, confirm=True)
            journal = Path(str(prepared["journal_path"]))

            self.assertEqual(transition_profile_migration_state(journal, "COPYING")["state"], "COPYING")
            self.assertEqual(transition_profile_migration_state(journal, "VERIFIED")["state"], "VERIFIED")
            self.assertEqual(transition_profile_migration_state(journal, "SWITCHING")["state"], "SWITCHING")
            self.assertEqual(transition_profile_migration_state(journal, "COMMITTED")["state"], "COMMITTED")
            with self.assertRaises(ProfileMigrationError):
                transition_profile_migration_state(journal, "PLANNED")

    def test_global_migration_state_refuses_unknown_and_skipped_states(self) -> None:
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
            prepared = prepare_profile_migration_journal(profile_path, candidate, preview, confirm=True)
            journal = Path(str(prepared["journal_path"]))

            with self.assertRaises(ProfileMigrationError):
                transition_profile_migration_state(journal, "COMMITTED")
            with self.assertRaises(ProfileMigrationError):
                transition_profile_migration_state(journal, "SWITCHING")
            with self.assertRaises(ProfileMigrationError):
                transition_profile_migration_state(journal, "UNKNOWN")

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

    def test_execute_moves_an_isolated_additional_workspace_root(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            profile_path = self._project(root)
            (root / "src").mkdir()
            (root / "docs").mkdir()
            (root / "docs" / "note.md").write_text("note", encoding="utf-8")
            current = load_profile(profile_path)
            current["workspace"]["root"] = "src"
            current["workspace"]["additional_roots"] = ["docs"]
            profile_path.write_text(yaml.safe_dump(current, sort_keys=False), encoding="utf-8")
            candidate = load_profile(profile_path)
            candidate["workspace"]["root"] = "src-next"
            candidate["workspace"]["additional_roots"] = ["docs-next"]
            candidate["storage"]["memory_dir"] = ".vera-mmu-next"
            candidate["capabilities"]["catalog"] = ".vera-mmu-next/capabilities.yaml"
            candidate["gates"]["catalog"] = ".vera-mmu-next/gates.yaml"
            candidate["policies"]["file"] = ".vera-mmu-next/policies.yaml"
            candidate["integrations"]["agent_profiles"] = ".vera-mmu-next/agent-profiles.yaml"
            sqlite_path = root / ".vera-mmu" / "memory.sqlite"
            sqlite_path.unlink()
            with sqlite3.connect(sqlite_path) as connection:
                connection.execute("CREATE TABLE marker(value TEXT)")
                connection.execute("INSERT INTO marker VALUES ('root-move')")
            preview = preview_profile_physical_migration(profile_path, candidate)
            prepare_profile_migration_journal(profile_path, candidate, preview, confirm=True)
            result = execute_profile_physical_migration(profile_path, candidate, preview, confirm=True)
            self.assertEqual(result["status"], "COMMITTED")
            self.assertTrue((root / "src-next").is_dir())
            self.assertFalse((root / "docs").exists())
            self.assertEqual((root / "docs-next" / "note.md").read_text(encoding="utf-8"), "note")

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
