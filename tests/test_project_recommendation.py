"""Cover the automatic profile recommendation the specification asks for (§31).

From a scan report, propose a template, a set of capabilities and a set of gates — and stop
there. The specification is explicit that «l'utilisateur peut modifier chaque élément», so a
recommendation is a proposal with its reasons attached, never a decision and never a write.

Three properties matter more than the proposals themselves, and each has its test here. It is
deterministic, so the same tree always argues the same way. It writes nothing, anywhere. And it
never proposes a command, a path or a runner: naming a `lint` capability is not the same act as
saying what lint runs, and only the second one is a decision the project owner makes (I008).
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.project_recommendation import RecommendationError, recommend_profile
from vera_mmu.project_scan import scan_project


def materialize(root: Path, *relatives: str) -> None:
    for relative in relatives:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("", encoding="utf-8")


def recommend(root: Path):
    return recommend_profile(scan_project(root))


class ProfileRecommendationTests(unittest.TestCase):
    # --- the specification's own example ---------------------------------

    def test_the_specification_example_is_recommended_as_written(self) -> None:
        """§31: TypeScript + Node + Vitest + Playwright + GitHub Actions → a software profile."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize(
                root, "package.json", "tsconfig.json", "src/app.tsx", "vitest.config.ts",
                "playwright.config.ts", ".eslintrc.json", ".github/workflows/ci.yml",
            )

            result = recommend(root)

            self.assertEqual(result.template, "software")
            proposed = {item.id for item in result.capabilities}
            self.assertLessEqual({"install", "test", "lint", "typecheck", "e2e"}, proposed)
            gates = {item.id for item in result.gates}
            self.assertLessEqual({"UNIT_TESTS_OK", "LINT_OK", "TYPECHECK_OK", "E2E_OK"}, gates)

    def test_every_proposal_carries_the_observations_that_support_it(self) -> None:
        """A recommendation that cannot say why it proposes something is an opinion."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize(root, "package.json", "src/app.ts", "ruff.toml")

            result = recommend(root)

            self.assertTrue(result.template_rationale)
            for proposal in result.capabilities + result.gates:
                self.assertTrue(proposal.rationale, f"`{proposal.id}` proposé sans justification")

    def test_a_gate_is_only_proposed_for_a_capability_that_is_proposed(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize(root, "pyproject.toml", "src/main.py", "tests/test_unit.py")

            result = recommend(root)

            capabilities = {item.id for item in result.capabilities}
            for gate in result.gates:
                self.assertIn(gate.capability_id, capabilities)

    # --- what a recommendation must never be -----------------------------

    def test_no_proposal_carries_a_command_a_path_or_a_runner(self) -> None:
        """I008: naming a capability is not saying what executes it."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize(root, "package.json", "src/app.ts", "Makefile", "Dockerfile")

            payload = recommend(root).as_dict()

            forbidden = ("command", "argv", "shell", "interpreter", "cwd", "executable", "runner", "path", "url")
            def walk(value: object, trail: str = "") -> None:
                if isinstance(value, dict):
                    for key, item in value.items():
                        self.assertNotIn(key, forbidden, f"clé interdite `{key}` sous {trail}")
                        walk(item, f"{trail}.{key}")
                elif isinstance(value, list):
                    for item in value:
                        walk(item, trail)
            walk(payload)

    def test_the_recommendation_is_deterministic(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize(root, "pyproject.toml", "src/main.py", "tests/test_unit.py", "Makefile", ".flake8")
            self.assertEqual(recommend(root), recommend(root))

    def test_the_recommendation_writes_nothing(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize(root, "pyproject.toml", "src/main.py")
            before = {path.relative_to(root).as_posix() for path in root.rglob("*")}

            result = recommend(root)

            self.assertEqual({path.relative_to(root).as_posix() for path in root.rglob("*")}, before)
            self.assertEqual(result.mutation, "NONE")
            self.assertEqual(result.status, "PROPOSED")

    def test_every_element_is_marked_editable(self) -> None:
        """§31: «l'utilisateur peut modifier chaque élément» — the payload says so itself."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize(root, "package.json", "src/app.ts")
            payload = recommend(root).as_dict()
            self.assertTrue(payload["editable"])

    # --- the templates -----------------------------------------------------

    def test_a_dataset_heavy_tree_is_recommended_the_data_template(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize(root, "pyproject.toml", "src/pipeline.py", "data/rows.csv", "data/events.parquet", "notebooks/explore.ipynb")
            self.assertEqual(recommend(root).template, "data")

    def test_a_documentation_only_tree_is_recommended_the_documentation_template(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize(root, "README.md", "docs/guide.md", "docs/reference.rst", "CONTRIBUTING.md")
            self.assertEqual(recommend(root).template, "documentation")

    def test_a_firmware_tree_is_recommended_the_hardware_template(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize(root, "platformio.ini", "src/main.ino")
            self.assertEqual(recommend(root).template, "hardware")

    def test_an_unreadable_tree_falls_back_to_software_and_says_so(self) -> None:
        """A fallback that presents itself as a deduction would be the fabrication to avoid."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize(root, "notes.txt")

            result = recommend(root)

            self.assertEqual(result.template, "software")
            self.assertTrue(any("défaut" in reason for reason in result.template_rationale))

    def test_an_empty_tree_proposes_nothing_rather_than_a_default_workflow(self) -> None:
        with TemporaryDirectory() as tmp:
            result = recommend(Path(tmp))
            self.assertEqual(result.capabilities, ())
            self.assertEqual(result.gates, ())

    def test_a_report_of_another_format_is_refused(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize(root, "pyproject.toml")
            report = scan_project(root)
            with self.assertRaises(RecommendationError):
                recommend_profile(object())
            with self.assertRaises(RecommendationError):
                recommend_profile(type(report)("vera-scan-report/v1", report.root, report.observations, report.categories, report.status, report.report_hash, report.json_text))

    def test_the_recommendation_is_bound_to_the_report_it_read(self) -> None:
        """A proposal that could not name its input could be shown next to another project."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize(root, "pyproject.toml", "src/main.py")
            report = scan_project(root)
            self.assertEqual(recommend_profile(report).report_hash, report.report_hash)


if __name__ == "__main__":
    unittest.main()
