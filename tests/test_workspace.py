from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from vera_mmu.identity import ProfileError, load_profile, project_identity
from vera_mmu.workspace import WorkspaceError, WorkspaceResolver, resolve_workspace


class WorkspaceTests(unittest.TestCase):
    """I011/I012/I014/I015: project roots and local runtime stay explicit and confined."""

    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._directory.cleanup)
        self.project = Path(self._directory.name) / "project"
        self.project.mkdir()

    def _profile_path(
        self,
        *,
        root: str = ".",
        additional_roots: list[str] | None = None,
        memory_dir: str = ".vera-mmu",
        nested_runtime: bool = True,
    ) -> Path:
        profile_dir = self.project / ".vera-mmu" if nested_runtime else self.project
        profile_dir.mkdir(exist_ok=True)
        path = profile_dir / "project.yaml"
        additional = additional_roots or []
        yaml_items = "\n".join(f"    - {item!r}" for item in additional) or "    []"
        path.write_text(
            f"""mmu:
  version: \"2.0\"
project:
  id: \"demo-project\"
  name: \"Demo Project\"
  domain: \"generic\"
workspace:
  root: {root!r}
  additional_roots:
{yaml_items}
storage:
  memory_dir: {memory_dir!r}
  sqlite_file: \"memory.sqlite\"
  artifacts_dir: \"artifacts\"
identity:
  include_vcs_revision: false
  include_profile_hash: true
""",
            encoding="utf-8",
        )
        return path

    def test_no_git_single_root_is_valid(self) -> None:
        path = self._profile_path()
        workspace = WorkspaceResolver(load_profile(path), path).resolve()
        self.assertEqual(workspace.project_root, self.project.resolve())
        self.assertEqual(workspace.roots, (self.project.resolve(),))
        self.assertEqual(workspace.runtime_dir, (self.project / ".vera-mmu").resolve())
        self.assertEqual(workspace.vcs_roots, ())

    def test_local_git_marker_is_reported_without_running_git(self) -> None:
        (self.project / ".git").mkdir()
        path = self._profile_path()
        workspace = resolve_workspace(load_profile(path), path)
        self.assertEqual(workspace.vcs_roots, (self.project.resolve(),))

    def test_multi_root_workspace_is_explicit_and_deduplicated(self) -> None:
        (self.project / "src").mkdir()
        (self.project / "packages" / "alpha").mkdir(parents=True)
        (self.project / "services" / "beta").mkdir(parents=True)
        path = self._profile_path(root="src", additional_roots=["packages/alpha", "services/beta"])
        workspace = resolve_workspace(load_profile(path), path)
        self.assertEqual(
            workspace.roots,
            (
                (self.project / "src").resolve(),
                (self.project / "packages" / "alpha").resolve(),
                (self.project / "services" / "beta").resolve(),
            ),
        )

    def test_profile_rejects_root_escape_before_resolution(self) -> None:
        path = self._profile_path(additional_roots=["../outside"])
        with self.assertRaises(ProfileError):
            load_profile(path)

    def test_workspace_rejects_symlinked_root_escape(self) -> None:
        outside = Path(self._directory.name) / "outside"
        outside.mkdir()
        link = self.project / "linked-root"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"Symlink non disponible dans l’environnement de test : {exc}")
        path = self._profile_path(root="linked-root")
        with self.assertRaises(WorkspaceError):
            resolve_workspace(load_profile(path), path)

    def test_workspace_rejects_symlinked_runtime_escape(self) -> None:
        outside = Path(self._directory.name) / "outside-runtime"
        outside.mkdir()
        link = self.project / "runtime-link"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"Symlink non disponible dans l’environnement de test : {exc}")
        path = self._profile_path(memory_dir="runtime-link", nested_runtime=False)
        with self.assertRaises(WorkspaceError):
            resolve_workspace(load_profile(path), path)

    def test_project_identity_matches_resolved_workspace_topology(self) -> None:
        (self.project / "src").mkdir()
        path = self._profile_path(root="src")
        profile = load_profile(path)
        workspace = resolve_workspace(profile, path)
        self.assertEqual(project_identity(profile).workspace_hash, project_identity(profile, workspace).workspace_hash)

    def test_project_identity_is_portable_across_workspace_locations(self) -> None:
        first = load_profile(self._profile_path())
        clone = Path(self._directory.name) / "clone"
        clone.mkdir()
        clone_profile = clone / "project.yaml"
        clone_profile.write_text((self.project / ".vera-mmu" / "project.yaml").read_text(encoding="utf-8"), encoding="utf-8")
        second = load_profile(clone_profile)
        self.assertEqual(project_identity(first), project_identity(second))


if __name__ == "__main__":
    unittest.main()
