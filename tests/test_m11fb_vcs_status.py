from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore


PROFILE = '''
mmu:
  version: "2.0"
project:
  id: "m11fb-vcs"
  name: "M11-F-B VCS"
  domain: "research"
workspace:
  root: "."
storage:
  memory_dir: ".vera-mmu"
  sqlite_file: "memory.sqlite"
  artifacts_dir: "artifacts"
identity:
  include_vcs_revision: false
  include_profile_hash: true
'''


class VcsStatusTests(unittest.TestCase):
    def _store(self, root: Path) -> MemoryStore:
        runtime = root / ".vera-mmu"
        runtime.mkdir(exist_ok=True)
        profile = runtime / "project.yaml"
        profile.write_text(PROFILE, encoding="utf-8")
        return MemoryStore.open(load_profile(profile), profile)

    def test_i001_i007_i011_i014_vcs_status_is_local_non_mutating_and_fail_closed(self) -> None:
        from vera_mmu.vcs import VcsError, inspect_vcs

        with TemporaryDirectory() as directory:
            root = Path(directory)
            with self._store(root) as store:
                audits = store.audit_events()
                self.assertEqual(inspect_vcs(store).as_dict(), {"provider": "NONE", "status": "NO_VCS"})
                (root / ".git").mkdir()
                self.assertEqual(inspect_vcs(store).as_dict(), {"provider": "GIT", "status": "OBSERVED"})
                self.assertEqual(store.audit_events(), audits)
            (root / ".git").rmdir()
            (root / ".git").symlink_to(root / "foreign")
            with self._store(root) as store:
                with self.assertRaises(VcsError):
                    inspect_vcs(store)


if __name__ == "__main__":
    unittest.main()
