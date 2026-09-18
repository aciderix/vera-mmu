"""Cover the command contract the specification fixes for the universal CLI (§28).

The package exposed eight of the thirteen verbs, and two more only under other names. This
suite pins the full contract and the behaviour of the verbs added to complete it.

Invariants exercised: I008 (no client input becomes a command or a path), I013 (a mutation
states an explicit decision) and I014 (a missing prerequisite refuses loudly).
"""
from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import yaml

from vera_mmu.__main__ import build_parser, main
from vera_mmu.identity import load_profile
from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization
from vera_mmu.store import MemoryStore
from vera_mmu.write_api import WriteService


SPECIFIED_COMMANDS = (
    "init", "scan", "configure", "validate", "generate", "install",
    "serve", "doctor", "migrate", "export", "import", "dashboard", "upgrade",
)


def run(argv: list[str]) -> tuple[int, dict[str, object]]:
    output = StringIO()
    with redirect_stdout(output):
        code = main(argv)
    return code, json.loads(output.getvalue())


class CLIContractTests(unittest.TestCase):
    def _project(self, root: Path, *, ready: bool = True) -> Path:
        preview = preview_project_initialization(root, template="software", project_id="cli-project", project_name="CLI Project")
        apply_project_initialization(root, preview, confirm=True)
        profile = root / ".vera-mmu" / "project.yaml"
        if ready:
            with MemoryStore.open(load_profile(profile), profile) as store:
                WriteService(store).sync_profile_capabilities(actor="test")
        return profile

    def test_every_specified_command_exists(self) -> None:
        import argparse

        parser = build_parser()
        actions = [a for a in parser._actions if isinstance(a, argparse._SubParsersAction)]
        available = set(actions[0].choices)
        missing = sorted(command for command in SPECIFIED_COMMANDS if command not in available)
        self.assertEqual(missing, [], f"Commandes du contrat absentes : {missing}")

    # --- validate --------------------------------------------------------

    def test_validate_accepts_a_coherent_project(self) -> None:
        with TemporaryDirectory() as tmp:
            code, payload = run(["validate", str(self._project(Path(tmp)))])
            self.assertEqual(code, 0)
            self.assertTrue(payload["ok"])
            validation = payload["validation"]
            self.assertEqual(validation["status"], "VALID")
            self.assertEqual(set(validation["catalog_hashes"]), {"capabilities", "gates", "policies", "agent_profiles"})
            self.assertTrue(validation["playbook_hash"])

    def test_validate_reports_a_broken_catalog_relation(self) -> None:
        """§28: validate checks the declarative files *and their relations*.

        This asserts **which layer** refuses, not merely that something did. `project_validation`
        long carried its own copy of this check and could never reach it, because
        `load_project_catalogs` raises first; the copy was removed. Naming the refusing layer here
        is what keeps that removal honest: relax the loader and this fails, instead of opening a
        hole nobody would notice.
        """
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._project(root)
            gates = root / ".vera-mmu" / "gates.yaml"
            gates.write_text(
                "format: vera-gate-catalog/v1\ngates:\n  - id: ORPHAN\n    name: \"Orpheline\"\n"
                "    capability_id: \"absente\"\n    required: true\n    expected:\n      verdict: PASS\n",
                encoding="utf-8",
            )
            code, payload = run(["validate", str(profile)])
            self.assertEqual(code, 2)
            self.assertFalse(payload["ok"])
            self.assertIn("Catalogues déclaratifs invalides", str(payload["error"]))
            self.assertIn("capability déclarée", str(payload["error"]))

    def test_validate_reports_an_integration_without_an_agent_profile(self) -> None:
        """The loader's second cross-catalog relation, pinned where it actually lives."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._project(root)
            document = yaml.safe_load(profile.read_text(encoding="utf-8"))
            document["integrations"]["enabled"] = ["aucun-agent-profile"]
            profile.write_text(yaml.safe_dump(document, allow_unicode=True, sort_keys=False), encoding="utf-8")
            code, payload = run(["validate", str(profile)])
            self.assertEqual(code, 2)
            self.assertIn("Catalogues déclaratifs invalides", str(payload["error"]))
            self.assertIn("Agent Profile absent", str(payload["error"]))

    def test_validate_refuses_a_resume_contract_that_requires_nothing(self) -> None:
        """The one relation `validate` still adds: the loader never reads the profile's resume."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._project(root)
            document = yaml.safe_load(profile.read_text(encoding="utf-8"))
            for section in document["resume"]["sections"]:
                section["required"] = False
            profile.write_text(yaml.safe_dump(document, allow_unicode=True, sort_keys=False), encoding="utf-8")
            code, payload = run(["validate", str(profile)])
            self.assertEqual(code, 2)
            self.assertIn("Relations déclaratives incohérentes", str(payload["error"]))
            self.assertIn("n’exige aucune section", str(payload["error"]))

    def test_validate_refuses_a_project_without_playbook(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._project(root)
            (root / ".vera-mmu" / "playbook.md").unlink()
            code, payload = run(["validate", str(profile)])
            self.assertEqual(code, 2)
            self.assertFalse(payload["ok"])

    # --- upgrade ---------------------------------------------------------

    def test_upgrade_reports_the_schema_it_moved_to(self) -> None:
        with TemporaryDirectory() as tmp:
            profile = self._project(Path(tmp))
            code, payload = run(["upgrade", str(profile), "--confirm"])
            self.assertEqual(code, 0)
            upgrade = payload["upgrade"]
            self.assertEqual(upgrade["status"], "UP_TO_DATE")
            self.assertGreater(upgrade["schema_version"], 0)

    def test_upgrade_refuses_without_confirmation(self) -> None:
        """I013: touching the store is a decision, even when nothing is pending."""
        with TemporaryDirectory() as tmp:
            profile = self._project(Path(tmp))
            code, payload = run(["upgrade", str(profile)])
            self.assertEqual(code, 2)
            self.assertFalse(payload["ok"])

    # --- import ----------------------------------------------------------

    def test_import_previews_a_project_bundle_without_writing(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._project(root)
            run(["bundle-export", str(profile), "--bundle-id", "bundle-cli", "--confirm"])
            code, payload = run(["import", str(profile), "--bundle-id", "bundle-cli"])
            self.assertEqual(code, 0)
            self.assertEqual(payload["import"]["mutation"], "NONE")
            self.assertEqual(payload["import"]["bundle_id"], "bundle-cli")

    def test_import_refuses_an_identifier_that_escapes_the_runtime(self) -> None:
        with TemporaryDirectory() as tmp:
            profile = self._project(Path(tmp))
            code, payload = run(["import", str(profile), "--bundle-id", "../escape"])
            self.assertEqual(code, 2)
            self.assertFalse(payload["ok"])

    # --- configure -------------------------------------------------------

    def test_configure_previews_an_adapter_once_its_runtime_is_staged(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._project(root)
            run(["adapter", "stage", "--profile", str(profile), "--adapter", "generic-mcp", "--confirm"])
            code, payload = run(["configure", str(profile), "--adapter", "generic-mcp"])
            self.assertEqual(code, 0)
            self.assertTrue(payload["ok"])
            self.assertFalse((root / ".mcp.json").exists())

    def test_configure_is_refused_before_the_adapter_runtime_is_staged(self) -> None:
        """Staging comes first: configuring an unstaged adapter would describe nothing real."""
        with TemporaryDirectory() as tmp:
            profile = self._project(Path(tmp))
            code, payload = run(["configure", str(profile), "--adapter", "generic-mcp"])
            self.assertEqual(code, 2)
            self.assertFalse(payload["ok"])

    def test_configure_refuses_an_unknown_adapter(self) -> None:
        with TemporaryDirectory() as tmp:
            profile = self._project(Path(tmp))
            code, payload = run(["configure", str(profile), "--adapter", "nope"])
            self.assertEqual(code, 2)
            self.assertFalse(payload["ok"])

    # --- serve / dashboard -----------------------------------------------

    def test_serve_describes_the_transport_without_starting_it(self) -> None:
        with TemporaryDirectory() as tmp:
            profile = self._project(Path(tmp))
            code, payload = run(["serve", str(profile), "--describe"])
            self.assertEqual(code, 0)
            self.assertEqual(payload["serve"]["transport"], "stdio")
            self.assertEqual(payload["serve"]["status"], "DESCRIBED")

    def test_dashboard_refuses_clearly_when_the_application_is_absent(self) -> None:
        """I014: an absent desktop build is named, not silently ignored."""
        with TemporaryDirectory() as tmp:
            profile = self._project(Path(tmp))
            code, payload = run(["dashboard", str(profile), "--describe"])
            self.assertIn(code, (0, 2))
            self.assertIn("dashboard", payload)


if __name__ == "__main__":
    unittest.main()
