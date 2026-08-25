from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from verichronicle.identity import ProfileError, load_profile, profile_identity


PROFILE = """\
mmu:
  version: "2.0"
project:
  id: "demo-project"
  name: "Demo Project"
  domain: "generic"
workspace:
  root: "."
storage:
  memory_dir: ".mmu"
  sqlite_file: "memory.sqlite"
  artifacts_dir: "artifacts"
"""


class ProfileIdentityTests(unittest.TestCase):
    """I011/I012: profile identity is stable, explicit, and bounded."""

    def _profile_file(self, text: str = PROFILE) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "project.yaml"
        path.write_text(text, encoding="utf-8")
        return path

    def test_same_profile_has_the_same_identity(self) -> None:
        profile = load_profile(self._profile_file())
        self.assertEqual(profile_identity(profile), profile_identity(profile))

    def test_yaml_key_order_does_not_change_identity(self) -> None:
        reordered = """\
storage:
  artifacts_dir: "artifacts"
  sqlite_file: "memory.sqlite"
  memory_dir: ".mmu"
workspace:
  root: "."
project:
  domain: "generic"
  name: "Demo Project"
  id: "demo-project"
mmu:
  version: "2.0"
"""
        original_identity = profile_identity(load_profile(self._profile_file(PROFILE)))
        reordered_identity = profile_identity(load_profile(self._profile_file(reordered)))
        self.assertEqual(original_identity.profile_hash, reordered_identity.profile_hash)

    def test_project_id_must_be_bounded_slug(self) -> None:
        invalid = PROFILE.replace('id: "demo-project"', 'id: "Demo Project"')
        with self.assertRaises(ProfileError):
            load_profile(self._profile_file(invalid))

    def test_workspace_cannot_escape_project_root(self) -> None:
        invalid = PROFILE.replace('root: "."', 'root: "../outside"')
        with self.assertRaises(ProfileError):
            load_profile(self._profile_file(invalid))


if __name__ == "__main__":
    unittest.main()
