from __future__ import annotations

import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.memory_sync import automatic_memory_sync
from vera_mmu.store import MemoryStore


PROFILE = """
mmu:
  version: "2.0"
project:
  id: "memory-sync"
  name: "Memory Sync"
  domain: "generic"
workspace:
  root: "."
storage:
  memory_dir: ".vera-mmu"
  sqlite_file: "memory.sqlite"
  artifacts_dir: "artifacts"
identity:
  include_vcs_revision: false
  include_profile_hash: true
""".strip() + "\n"


def git(root: Path, *args: str) -> str:
    completed = subprocess.run(["git", "-C", str(root), *args], check=False, text=True, capture_output=True)
    if completed.returncode != 0:
        raise AssertionError(completed.stderr or completed.stdout)
    return completed.stdout.strip()


class MemorySyncTests(unittest.TestCase):
    def _store(self, directory: Path, *, policy: dict[str, object] | None, remote: bool = True) -> tuple[MemoryStore, Path | None]:
        git(directory, "init", "-b", "main")
        git(directory, "config", "user.name", "VERA tests")
        git(directory, "config", "user.email", "vera-tests@example.invalid")
        memory = directory / ".vera-mmu"
        memory.mkdir()
        profile = memory / "project.yaml"
        profile.write_text(PROFILE, encoding="utf-8")
        store = MemoryStore.open(__import__("vera_mmu.identity", fromlist=["load_profile"]).load_profile(profile), profile)
        store.connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
        if policy is not None:
            (memory / "sync-policy.json").write_text(json.dumps(policy, sort_keys=True) + "\n", encoding="utf-8")
        git(directory, "add", "--", ".vera-mmu")
        git(directory, "commit", "-m", "VERA memory baseline")
        if not remote:
            return store, None
        remote_path = directory.parent / f"{directory.name}-remote.git"
        subprocess.run(["git", "init", "--bare", str(remote_path)], check=True, text=True, capture_output=True)
        git(directory, "remote", "add", "origin", str(remote_path))
        git(directory, "push", "-u", "origin", "main")
        return store, remote_path

    @staticmethod
    def _mutate(store: MemoryStore) -> None:
        with store.transaction() as connection:
            store.append_audit(connection, "TEST_MEMORY_MUTATION", {"source": "test"})

    def test_i001_i007_i011_sync_commits_and_pushes_only_memory_policy_scope(self) -> None:
        policy = {"format": "vera-memory-sync-policy/v1", "auto_commit": True, "auto_push": True, "remote": "origin", "branch": "CURRENT"}
        with TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            root.mkdir()
            store, remote = self._store(root, policy=policy)
            self.addCleanup(store.close)
            (root / "work-in-progress.txt").write_text("do not stage\n", encoding="utf-8")
            self._mutate(store)
            result = store.last_sync_status
            self.assertEqual(result["status"], "SYNCED")
            self.assertTrue(result["committed"])
            self.assertTrue(result["pushed"])
            self.assertEqual(git(root, "status", "--porcelain=v1"), "?? work-in-progress.txt")
            committed_paths = git(root, "show", "--format=", "--name-only", "HEAD").splitlines()
            self.assertTrue(committed_paths)
            self.assertTrue(all(path == ".vera-mmu" or path.startswith(".vera-mmu/") for path in committed_paths))
            self.assertEqual(git(remote, "rev-parse", "main"), git(root, "rev-parse", "HEAD"))

    def test_i001_i007_policy_disabled_never_commits_or_pushes(self) -> None:
        policy = {"format": "vera-memory-sync-policy/v1", "auto_commit": False, "auto_push": False, "remote": "origin", "branch": "CURRENT"}
        with TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            root.mkdir()
            store, _ = self._store(root, policy=policy)
            self.addCleanup(store.close)
            baseline = git(root, "rev-parse", "HEAD")
            self._mutate(store)
            result = store.last_sync_status
            self.assertEqual(result["status"], "DISABLED")
            self.assertEqual(git(root, "rev-parse", "HEAD"), baseline)
            self.assertTrue((root / ".vera-mmu" / "memory.sqlite-wal").exists() or (root / ".vera-mmu" / "memory.sqlite").exists())

    def test_i007_i011_rejects_invalid_policy_symlink_and_missing_remote_without_claiming_push(self) -> None:
        policy = {"format": "vera-memory-sync-policy/v1", "auto_commit": True, "auto_push": True, "remote": "origin", "branch": "CURRENT"}
        with TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            root.mkdir()
            store, _ = self._store(root, policy=policy, remote=False)
            self.addCleanup(store.close)
            self._mutate(store)
            missing_remote = store.last_sync_status
            self.assertEqual(missing_remote["status"], "REFUSED")
            self.assertFalse(missing_remote["pushed"])

            (root / ".vera-mmu" / "sync-policy.json").unlink()
            (root / ".vera-mmu" / "sync-policy.json").symlink_to(root / "outside.json")
            self._mutate(store)
            symlink = store.last_sync_status
            self.assertEqual(symlink["status"], "REFUSED")
            self.assertFalse(symlink["committed"])

    def test_i007_i014_rejects_unknown_policy_fields_and_operation_identifier(self) -> None:
        policy = {"format": "vera-memory-sync-policy/v1", "auto_commit": True, "auto_push": True, "remote": "origin", "branch": "CURRENT", "command": "git push elsewhere"}
        with TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            root.mkdir()
            store, _ = self._store(root, policy=policy)
            self.addCleanup(store.close)
            self._mutate(store)
            bad_policy = store.last_sync_status
            self.assertEqual(bad_policy["status"], "REFUSED")
            valid_policy = {"format": "vera-memory-sync-policy/v1", "auto_commit": True, "auto_push": False, "remote": "origin", "branch": "CURRENT"}
            (root / ".vera-mmu" / "sync-policy.json").write_text(json.dumps(valid_policy) + "\n", encoding="utf-8")
            invalid_operation = automatic_memory_sync(store, "mcp mutation; push")
            self.assertEqual(invalid_operation["status"], "REFUSED")


if __name__ == "__main__":
    unittest.main()
