"""Pin the Zero Pollution promise as an invariant rather than a README sentence (§36).

The specification states three things about a VERA installation: it requires no change to the
business code, its footprint is the VERA directory plus the host configuration, and the volatile
SQLite sidecars stay ignored — while the canonical memory and the profile remain versionable.

The behaviour was believed correct and never guarded. It was not: the automatic memory sync
staged `.vera-mmu/` wholesale, so `memory.sqlite-wal` and `memory.sqlite-shm` were committed into
the user's own repository. These tests measure the footprint on a witness project rather than
reading the code, so a regression shows up as a failure and not as a promise quietly broken.
"""
from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import json
import subprocess
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.__main__ import main
from vera_mmu.doctor import diagnose_project
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore
from vera_mmu.write_api import WriteService


HOST_CONFIGURATION = {".mcp.json"}
VOLATILE_SUFFIXES = ("-wal", "-shm")


def cli(argv: list[str]) -> int:
    """Run one CLI command the way an installing user would, without its output."""
    with redirect_stdout(StringIO()):
        return main(argv)


def git(repository: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments], cwd=repository, capture_output=True, text=True, check=True, timeout=30,
    )
    return result.stdout


class ZeroPollutionTests(unittest.TestCase):
    def _witness(self, root: Path) -> dict[str, bytes]:
        """Create a project with business code under Git, and return that code verbatim."""
        git(root, "init", "-q", "-b", "main")
        git(root, "config", "user.email", "conformance@vera.invalid")
        git(root, "config", "user.name", "VERA Conformance")
        (root / "src").mkdir()
        business = {
            "src/app.py": b"print('business code')\n",
            "README.md": b"# Witness project\n",
            "pyproject.toml": b"[project]\nname = 'witness'\n",
        }
        for relative, payload in business.items():
            (root / relative).write_bytes(payload)
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "business code")
        return business

    def _install(self, root: Path) -> Path:
        """Run the full installation path: initialize, declare, generate, stage, install."""
        self.assertEqual(cli([
            "init-project", str(root), "--template", "software",
            "--project-id", "witness", "--project-name", "Witness", "--apply", "--confirm",
        ]), 0)
        profile = root / ".vera-mmu" / "project.yaml"
        # auto_push would reach for a remote this witness project has not got.
        policy_file = root / ".vera-mmu" / "sync-policy.json"
        policy = json.loads(policy_file.read_text(encoding="utf-8"))
        policy["auto_push"] = False
        policy_file.write_text(json.dumps(policy), encoding="utf-8")
        with MemoryStore.open(load_profile(profile), profile) as store:
            WriteService(store).sync_profile_capabilities(actor="conformance")
        self.assertEqual(cli(["generate", str(profile), "--adapter", "generic-mcp"]), 0)
        self.assertEqual(cli(["adapter", "stage", "--profile", str(profile), "--adapter", "generic-mcp", "--confirm"]), 0)
        self.assertEqual(cli(["install", str(profile), "--adapter", "generic-mcp", "--apply-project", "--confirm"]), 0)
        return profile

    @staticmethod
    def _files(root: Path) -> set[str]:
        return {
            item.relative_to(root).as_posix()
            for item in root.rglob("*")
            if item.is_file() and not item.relative_to(root).as_posix().startswith(".git/")
        }

    def test_installation_stays_inside_the_vera_directory_and_the_host_configuration(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            business = self._witness(root)
            before = self._files(root)

            self._install(root)

            created = self._files(root) - before
            outside = {path for path in created if not path.startswith(".vera-mmu/")}
            self.assertEqual(outside, HOST_CONFIGURATION, f"empreinte hors périmètre : {sorted(outside)}")

    def test_installation_never_touches_the_business_code(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            business = self._witness(root)

            self._install(root)

            for relative, payload in business.items():
                self.assertEqual((root / relative).read_bytes(), payload, f"{relative} a été modifié")

    def test_the_volatile_sqlite_sidecars_are_never_versioned(self) -> None:
        """§36: `*.sqlite-wal` and `*.sqlite-shm` stay ignored, whoever stages the directory."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._witness(root)
            self._install(root)

            tracked = git(root, "ls-files").splitlines()
            volatile = [path for path in tracked if path.endswith(VOLATILE_SUFFIXES)]
            self.assertEqual(volatile, [], f"sidecars volatils versionnés : {volatile}")

            # And they stay out even when the user stages the whole project themselves.
            git(root, "add", "-A")
            staged = git(root, "diff", "--cached", "--name-only").splitlines()
            self.assertEqual([path for path in staged if path.endswith(VOLATILE_SUFFIXES)], [])

    def test_the_doctor_names_an_installation_that_already_versions_its_sidecars(self) -> None:
        """Adding an ignore rule does not untrack a file: an upgraded project must be told.

        This is the case the new rules cannot fix on their own. Repair would restore the rules
        and Git would keep the sidecars, so a report that only checked the rules would answer
        `PASS` over a project that still versions them.
        """
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._witness(root)
            profile = self._install(root)
            self.assertEqual(diagnose_project(profile).status, "PASS")

            # Reproduce an installation made before the rules existed.
            (root / ".vera-mmu" / ".gitignore").unlink()
            (root / ".vera-mmu" / "memory.sqlite-wal").write_bytes(b"")
            git(root, "add", "--force", "--", ".vera-mmu/memory.sqlite-wal")
            git(root, "commit", "-q", "-m", "legacy install")

            report = diagnose_project(profile)
            row = next(check for check in report.checks if check.name == "zero_pollution")
            self.assertEqual(report.status, "FAIL")
            self.assertEqual(row.status, "FAIL")
            self.assertIn("memory.sqlite-wal", row.detail)
            self.assertIn("git rm --cached", row.remediation)

    def test_the_doctor_never_answers_pass_when_it_could_not_ask_git(self) -> None:
        """A project outside any repository is `INFO`, never a `PASS` it did not verify."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._install(root)
            row = next(check for check in diagnose_project(profile).checks if check.name == "zero_pollution")
            self.assertEqual(row.status, "INFO")

    def test_the_canonical_memory_and_the_profile_remain_versionable(self) -> None:
        """The counterpart of the rule above: what must persist is not ignored along with it."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._witness(root)
            self._install(root)

            git(root, "add", "-A")
            staged = set(git(root, "diff", "--cached", "--name-only").splitlines()) | set(git(root, "ls-files").splitlines())
            for required in (".vera-mmu/memory.sqlite", ".vera-mmu/project.yaml", ".vera-mmu/playbook.md"):
                self.assertIn(required, staged, f"{required} doit rester versionnable")


if __name__ == "__main__":
    unittest.main()
