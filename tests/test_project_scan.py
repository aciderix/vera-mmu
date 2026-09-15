"""Cover the fourteen observation categories the specification fixes for the scanner (§30).

The scanner produced six of them — version control, CI, languages inferred from a dependency
manifest, documentation, container and test-like paths — and conflated languages with dependency
managers. Frameworks, build scripts, linters, datasets, assets, sub-projects and configuration
files had no category at all.

Every category here is proven by a fixture rather than asserted from the table, and a single test
fails the moment a category the specification requires stops being observed.

The scanner stays an observer: it recognises names, never content. It opens no file, follows no
symlink, starts no process and reaches no network. `OBSERVED` is what it may say; a marker named
`pytest.ini` means a file of that name exists, not that tests pass.
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.project_scan import SPECIFIED_CATEGORIES, scan_project


# One fixture per category required by §30: the files a project of that shape actually carries.
FIXTURES: dict[str, dict[str, str]] = {
    "vcs": {".git/HEAD": "ref: refs/heads/main\n"},
    "language": {"src/main.py": "", "src/app.ts": "", "src/lib.rs": ""},
    "framework": {"next.config.mjs": "", "manage.py": ""},
    "dependency-manager": {"requirements.txt": "", "pnpm-lock.yaml": ""},
    "build-script": {"Makefile": "", "CMakeLists.txt": ""},
    "tests": {"tests/test_unit.py": "", "vitest.config.ts": ""},
    "linter": {".eslintrc.json": "", "ruff.toml": ""},
    "ci": {".github/workflows/ci.yml": "", ".gitlab-ci.yml": ""},
    "container": {"Dockerfile": "", "compose.yaml": ""},
    "documentation": {"README.md": "", "docs/guide.rst": ""},
    "dataset": {"data/rows.csv": "", "corpus/events.jsonl": ""},
    "asset": {"assets/logo.svg": "", "public/hero.png": ""},
    "subproject": {"packages/api/package.json": "", "services/worker/Cargo.toml": ""},
    "configuration": {"settings.ini": "", "config/app.yaml": ""},
}


def materialize(root: Path, files: dict[str, str]) -> None:
    for relative, content in files.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


class ScannerCategoryTests(unittest.TestCase):
    def test_the_specification_categories_are_all_declared(self) -> None:
        """A category the specification requires must exist, and have a fixture proving it."""
        self.assertEqual(sorted(FIXTURES), sorted(SPECIFIED_CATEGORIES))

    def test_every_specified_category_is_observed_on_its_own_fixture(self) -> None:
        for category, files in sorted(FIXTURES.items()):
            with self.subTest(category=category):
                with TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    materialize(root, files)
                    observed = {item.kind for item in scan_project(root).observations}
                    self.assertIn(category, observed, f"catégorie `{category}` non détectée sur sa propre fixture")

    def test_a_whole_project_is_observed_in_every_category_at_once(self) -> None:
        """The fixtures must not depend on being alone: a real project carries all of them."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for files in FIXTURES.values():
                materialize(root, files)
            observed = {item.kind for item in scan_project(root).observations}
            missing = sorted(set(SPECIFIED_CATEGORIES) - observed)
            self.assertEqual(missing, [], f"catégories absentes du rapport complet : {missing}")

    def test_languages_and_dependency_managers_are_distinct_categories(self) -> None:
        """§30 lists them separately; one manifest is not the same observation as one language."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize(root, {"pyproject.toml": "", "src/main.py": ""})
            observations = scan_project(root).observations
            languages = {item.marker for item in observations if item.kind == "language"}
            managers = {item.marker for item in observations if item.kind == "dependency-manager"}
            self.assertEqual(languages, {"python"})
            self.assertIn("python", managers)

    def test_a_manifest_alone_is_not_a_language(self) -> None:
        """A dependency manifest says how the project is built, not what it is written in."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize(root, {"package.json": ""})
            observations = scan_project(root).observations
            self.assertEqual({item.kind for item in observations} & {"language"}, set())
            self.assertIn("dependency-manager", {item.kind for item in observations})

    def test_a_nested_manifest_is_a_subproject_and_the_root_one_is_not(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize(root, {"package.json": "", "packages/api/package.json": ""})
            subprojects = {item.path for item in scan_project(root).observations if item.kind == "subproject"}
            self.assertEqual(subprojects, {"packages/api"})

    # --- what the scanner must never become ------------------------------

    def test_the_scan_reads_no_file_content(self) -> None:
        """The same tree observes identically whatever the files contain."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize(root, {"src/main.py": "print('one')\n", "Makefile": "all:\n\techo one\n"})
            first = scan_project(root)
            (root / "src" / "main.py").write_text("import os\nos.system('rm -rf /')\n", encoding="utf-8")
            (root / "Makefile").write_text("all:\n\techo something else entirely\n", encoding="utf-8")
            second = scan_project(root)
            self.assertEqual(
                [item.as_dict() for item in first.observations],
                [item.as_dict() for item in second.observations],
            )

    def test_every_observation_is_observed_and_never_proven(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for files in FIXTURES.values():
                materialize(root, files)
            report = scan_project(root)
            self.assertEqual({item.status for item in report.observations}, {"OBSERVED"})
            self.assertEqual(report.status, "OBSERVED")

    def test_the_scan_never_follows_a_symlink_out_of_the_root(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            root.mkdir()
            outside = Path(tmp) / "elsewhere"
            outside.mkdir()
            (outside / "secret.py").write_text("", encoding="utf-8")
            (root / "foreign").symlink_to(outside, target_is_directory=True)
            materialize(root, {"src/main.py": ""})

            paths = {item.path for item in scan_project(root).observations}
            self.assertNotIn("foreign/secret.py", paths)
            self.assertFalse(any(path.startswith("foreign") for path in paths))

    def test_the_report_is_deterministic(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for files in FIXTURES.values():
                materialize(root, files)
            self.assertEqual(scan_project(root), scan_project(root))

    def test_one_row_per_recognised_marker_rather_than_one_per_file(self) -> None:
        """A thousand Python files are one observation about Python, with its count."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize(root, {f"src/module_{index}.py": "" for index in range(40)})
            python = [item for item in scan_project(root).observations if item.kind == "language"]
            self.assertEqual(len(python), 1)
            self.assertEqual(python[0].marker, "python")
            self.assertEqual(python[0].occurrences, 40)

    def test_the_vera_runtime_is_not_observed_as_part_of_the_project(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize(root, {".vera-mmu/policies.yaml": "", "src/main.py": ""})
            paths = {item.path for item in scan_project(root).observations}
            self.assertFalse(any(path.startswith(".vera-mmu") for path in paths))


if __name__ == "__main__":
    unittest.main()
