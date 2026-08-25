from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from vera_mmu.identity import ProfileError, load_profile
from vera_mmu.runtime import RuntimeLocator, RuntimeLocatorError


class RuntimeLocatorTests(unittest.TestCase):
    """I009/I014/I015: local runtime paths remain relative, explicit, and confined."""

    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._directory.cleanup)
        self.project = Path(self._directory.name) / "project"
        self.project.mkdir()
        self.runtime = self.project / ".vera-mmu"
        self.runtime.mkdir()
        self.profile_path = self.runtime / "project.yaml"
        self.profile_path.write_text(
            """mmu:
  version: "2.0"
project:
  id: "demo-project"
  name: "Demo Project"
  domain: "generic"
workspace:
  root: "."
storage:
  memory_dir: ".vera-mmu"
  sqlite_file: "memory.sqlite"
  artifacts_dir: "artifacts"
""",
            encoding="utf-8",
        )

    def test_default_runtime_is_bounded_under_project(self) -> None:
        runtime = RuntimeLocator.from_profile(load_profile(self.profile_path), self.profile_path)
        self.assertEqual(runtime.runtime_dir, self.runtime.resolve())
        self.assertEqual(runtime.sqlite_path, (self.runtime / "memory.sqlite").resolve())
        self.assertEqual(runtime.artifacts_dir, (self.runtime / "artifacts").resolve())

    def test_profile_rejects_runtime_child_traversal(self) -> None:
        invalid_path = self.runtime / "invalid.yaml"
        invalid_path.write_text(
            self.profile_path.read_text(encoding="utf-8").replace('sqlite_file: "memory.sqlite"', 'sqlite_file: "../escape.sqlite"'),
            encoding="utf-8",
        )
        with self.assertRaises(ProfileError):
            load_profile(invalid_path)

    def test_rejects_existing_artifact_symlink_escape(self) -> None:
        outside = Path(self._directory.name) / "outside-artifacts"
        outside.mkdir()
        link = self.runtime / "artifacts"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"Symlink non disponible dans l’environnement de test : {exc}")
        with self.assertRaises(RuntimeLocatorError):
            RuntimeLocator.from_profile(load_profile(self.profile_path), self.profile_path)


if __name__ == "__main__":
    unittest.main()
