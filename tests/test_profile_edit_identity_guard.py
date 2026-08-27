from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore, StoreIdentityError


BASE = '''
mmu:
  version: "2.0"
project:
  id: "profile-guard"
  name: "Profile guard"
  description: "Initial description"
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


class ProfileEditIdentityGuardTests(unittest.TestCase):
    def test_i011_semantic_profile_change_is_refused_without_explicit_rebind_protocol(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / ".vera-mmu"
            runtime.mkdir()
            profile_path = runtime / "project.yaml"
            profile_path.write_text(BASE, encoding="utf-8")
            with MemoryStore.open(load_profile(profile_path), profile_path):
                pass
            profile_path.write_text(BASE.replace("Initial description", "Changed description"), encoding="utf-8")
            with self.assertRaises(StoreIdentityError):
                MemoryStore.open(load_profile(profile_path), profile_path)


if __name__ == "__main__":
    unittest.main()
