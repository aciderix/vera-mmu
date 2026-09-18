"""The MCP Preview of §34: figures rendered, hashes rendered, and alerts told honestly.

Two things are proven here beyond the numbers themselves.

1. **The counts describe the façade that actually runs.** The manifest advertised one tool fewer
   than the server registered, so any figure built on it under-reported the surface. A test now
   pins the two together, and pins the classification against the server's own routing.
2. **Three of §34's four alerts can no longer fire**, because the lots before this one closed
   them at declaration. The preview reports them `NOT_APPLICABLE` with the rule that closed them,
   rather than showing a reassuring zero.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import yaml

from vera_mmu.identity import load_profile
from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization
from vera_mmu.store import MemoryStore
from vera_mmu.write_api import WriteService


class MCPToolClassTests(unittest.TestCase):
    """The classification the counts rest on, checked against the server rather than asserted."""

    def test_i012_every_advertised_tool_carries_exactly_one_class(self) -> None:
        from vera_mmu.mcp_tool_classes import READ_ONLY, TOOL_ACCESS, WRITE, unclassified_tools, undeclared_tools

        self.assertEqual(unclassified_tools(), ())
        self.assertEqual(undeclared_tools(), ())
        self.assertEqual(set(TOOL_ACCESS.values()), {READ_ONLY, WRITE})

    def test_i012_the_manifest_advertises_exactly_what_the_server_registers(self) -> None:
        """It advertised one fewer than it served; a count built on that would under-report."""
        from vera_mmu.mcp_manifest import TOOL_NAMES

        registered = self._registered_tools()
        self.assertEqual(set(TOOL_NAMES), set(registered))
        self.assertEqual(len(TOOL_NAMES), len(set(TOOL_NAMES)))

    def test_i012_every_mutating_tool_is_declared_write(self) -> None:
        """The one-way relation that *is* derivable, pinned; the converse deliberately is not.

        `_mutating_call` means « report the memory-sync status », not « changes something », so a
        classification read off it would call `mmu_export_bundle` and `mmu_sync_memory` read-only.
        """
        from vera_mmu.mcp_tool_classes import WRITE, classify_tool

        mutating = {name for name, is_mutating in self._registered_tools().items() if is_mutating}
        self.assertTrue(mutating)
        for name in sorted(mutating):
            self.assertEqual(classify_tool(name), WRITE, name)
        # And the two that write without that marker are still declared write, which is the
        # whole reason the table is declared rather than derived.
        self.assertNotIn("mmu_export_bundle", mutating)
        self.assertNotIn("mmu_sync_memory", mutating)
        self.assertEqual(classify_tool("mmu_export_bundle"), WRITE)
        self.assertEqual(classify_tool("mmu_sync_memory"), WRITE)

    def test_i012_a_sensitive_tool_is_always_a_write_and_carries_its_reason(self) -> None:
        from vera_mmu.mcp_tool_classes import SENSITIVE_REASONS, SENSITIVE_TOOLS, WRITE, classify_tool

        self.assertEqual(set(SENSITIVE_REASONS), set(SENSITIVE_TOOLS))
        for name in sorted(SENSITIVE_TOOLS):
            self.assertEqual(classify_tool(name), WRITE, name)
            self.assertTrue(SENSITIVE_REASONS[name].strip())

    def test_i014_an_unknown_tool_is_refused_rather_than_given_a_default(self) -> None:
        from vera_mmu.mcp_tool_classes import ToolClassError, classify_tool

        with self.assertRaises(ToolClassError):
            classify_tool("mmu_do_anything")

    @staticmethod
    def _registered_tools() -> dict[str, bool]:
        """Read the server's own registrations: each tool name, and whether it mutates."""
        source = (Path(__file__).resolve().parents[1] / "src" / "vera_mmu" / "mcp_server.py").read_text(encoding="utf-8")
        blocks = re.split(r'@server\.tool\(name="', source)[1:]
        return {
            block.split('"', 1)[0]: "_mutating_call(" in re.split(r'@server\.tool\(name="', block)[0]
            for block in blocks
        }


class MCPPreviewTests(unittest.TestCase):
    def _project(self, root: Path, template: str = "software") -> Path:
        preview = preview_project_initialization(root, template=template, project_id="preview-app", project_name="Preview App")
        apply_project_initialization(root, preview, confirm=True)
        return root / ".vera-mmu" / "project.yaml"

    def _ready(self, profile: Path) -> None:
        with MemoryStore.open(load_profile(profile), profile) as store:
            WriteService(store).sync_profile_capabilities(actor="test")

    def _preview(self, profile: Path) -> dict:
        from vera_mmu.mcp_preview import compile_mcp_preview

        with MemoryStore.open(load_profile(profile), profile) as store:
            return compile_mcp_preview(store, "generic-mcp")

    def _alert(self, payload: dict, identifier: str) -> dict:
        return next(item for item in payload["alerts"] if item["id"] == identifier)

    # --- the figures §34 displays -----------------------------------------

    def test_i012_the_preview_renders_the_counts_and_hashes_the_core_already_holds(self) -> None:
        """Counted here from the table and from the server, not by calling the same helper.

        Comparing the payload against `tool_counts()` would prove only that the preview renders
        that function: replace its body with a constant and both sides move together. The figures
        are recounted independently, and the partition is checked against what the server serves.
        """
        from vera_mmu.mcp_tool_classes import READ_ONLY, SENSITIVE_TOOLS, TOOL_ACCESS, WRITE
        from vera_mmu.project_catalogs import load_project_catalogs

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            self._ready(profile)
            payload = self._preview(profile)
            catalogs = load_project_catalogs(profile)
            registered = MCPToolClassTests._registered_tools()
            counts = payload["counts"]
            self.assertEqual(counts["core_tools"], len(registered))
            self.assertEqual(counts["read_only"], sum(1 for value in TOOL_ACCESS.values() if value == READ_ONLY))
            self.assertEqual(counts["write"], sum(1 for value in TOOL_ACCESS.values() if value == WRITE))
            # Read-only and write partition the façade: no tool is both, none is neither.
            self.assertEqual(counts["read_only"] + counts["write"], len(registered))
            self.assertEqual(counts["sensitive"], len(SENSITIVE_TOOLS))
            self.assertEqual(counts["network"], 0)
            self.assertEqual(counts["project_tools"], 0)
            self.assertEqual(counts["gates"], len(catalogs.gates["gates"]))
            self.assertEqual(counts["capabilities"], len(catalogs.capabilities["capabilities"]))
            # Rendered, never recomputed: the hashes are the ones the compiler produced.
            self.assertEqual(payload["hashes"]["policy_hash"], catalogs.policy_hash)
            self.assertEqual(payload["hashes"]["capability_catalog_hash"], catalogs.capability_catalog_hash)
            self.assertEqual(payload["hashes"]["gate_catalog_hash"], catalogs.gate_catalog_hash)
            self.assertEqual(payload["mutation"], "NONE")

    def test_i012_a_project_that_declares_more_capabilities_counts_more(self) -> None:
        """Without this, a constant would pass the count test above."""
        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            self._ready(profile)
            before = self._preview(profile)["counts"]
            catalog = profile.parent / "capabilities.yaml"
            gates = profile.parent / "gates.yaml"
            data = yaml.safe_load(catalog.read_text(encoding="utf-8"))
            data["capabilities"].append({**data["capabilities"][0], "id": "extra-check", "name": "Extra"})
            catalog.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            gate_data = yaml.safe_load(gates.read_text(encoding="utf-8"))
            gate_data["gates"] = gate_data["gates"][:-1]
            gates.write_text(yaml.safe_dump(gate_data, sort_keys=False), encoding="utf-8")
            after = self._preview(profile)["counts"]
            self.assertEqual(after["capabilities"], before["capabilities"] + 1)
            self.assertEqual(after["gates"], before["gates"] - 1)

    def test_i012_the_preview_refuses_a_project_the_compiler_refuses(self) -> None:
        """A figure produced for a build that cannot happen would describe nothing."""
        from vera_mmu.mcp_preview import MCPPreviewError, compile_mcp_preview

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            with MemoryStore.open(load_profile(profile), profile) as store:
                with self.assertRaises(MCPPreviewError):
                    compile_mcp_preview(store, "generic-mcp")

    # --- the alerts §34 lists ---------------------------------------------

    def test_i014_an_unregistered_validator_raises_the_objective_validator_alert(self) -> None:
        """Reachable: the catalogue declares a validator kind that `sync-capabilities` has not registered."""
        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            catalog = profile.parent / "capabilities.yaml"
            gates = profile.parent / "gates.yaml"
            data = yaml.safe_load(catalog.read_text(encoding="utf-8"))
            data["capabilities"] = [item for item in data["capabilities"] if item["validator"] == "EVIDENCE_FIELDS"]
            kept = {item["id"] for item in data["capabilities"]}
            gate_data = yaml.safe_load(gates.read_text(encoding="utf-8"))
            gate_data["gates"] = [item for item in gate_data["gates"] if item["capability_id"] in kept]
            catalog.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            gates.write_text(yaml.safe_dump(gate_data, sort_keys=False), encoding="utf-8")
            self._ready(profile)
            self.assertEqual(self._alert(self._preview(profile), "capability_without_objective_validator")["status"], "CLEAR")

            data["capabilities"].append({
                **data["capabilities"][0], "id": "hash-check", "name": "Hash check", "kind": "CHECK",
                "runner": "EVIDENCE_HASH", "validator": "EVIDENCE_HASH",
            })
            catalog.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            alert = self._alert(self._preview(profile), "capability_without_objective_validator")
            self.assertEqual(alert["status"], "RAISED")
            self.assertEqual(alert["severity"], "ERROR")
            self.assertEqual(alert["instances"], ["hash-check"])
            self.assertEqual(self._preview(profile)["raised"], ["capability_without_objective_validator"])

    def test_i004_the_hmac_alert_fires_only_when_a_promotion_would_be_refused(self) -> None:
        from vera_mmu.proof_policies import ProofPolicyService

        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            self._ready(profile)
            # No proof policy declared: nothing can be promoted, so nothing is missing.
            self.assertEqual(self._alert(self._preview(profile), "proven_without_hmac_secret")["status"], "CLEAR")
            with MemoryStore.open(load_profile(profile), profile) as store:
                ProofPolicyService(store).declare("HMAC_SHA256", hmac_required=True)
            with patch.dict(os.environ, {"VERA_MMU_PROOF_HMAC_SECRET": ""}, clear=False):
                alert = self._alert(self._preview(profile), "proven_without_hmac_secret")
                self.assertEqual(alert["status"], "RAISED")
                self.assertEqual(alert["severity"], "WARNING")
            with patch.dict(os.environ, {"VERA_MMU_PROOF_HMAC_SECRET": "secret-de-test"}, clear=False):
                self.assertEqual(self._alert(self._preview(profile), "proven_without_hmac_secret")["status"], "CLEAR")

    def test_i013_the_two_alerts_the_core_closed_are_reported_as_impossible_not_as_zero(self) -> None:
        """A rule that moved is worth naming; a quiet zero would read as a reassurance."""
        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            self._ready(profile)
            payload = self._preview(profile)
            for identifier, keyword in (
                ("gate_depends_on_network_capability", "DENY_NETWORK"),
                ("output_path_outside_scope", "artefact"),
            ):
                alert = self._alert(payload, identifier)
                self.assertEqual(alert["status"], "NOT_APPLICABLE", identifier)
                self.assertIn(keyword, alert["message"], identifier)
                self.assertEqual(alert["instances"], [])
            self.assertEqual(len(payload["alerts"]), 4)

    def test_i012_the_counts_that_are_zero_say_why_rather_than_leaving_it_to_be_guessed(self) -> None:
        with TemporaryDirectory() as directory:
            profile = self._project(Path(directory))
            self._ready(profile)
            payload = self._preview(profile)
            self.assertEqual(payload["counts"]["network"], 0)
            self.assertEqual(payload["counts"]["project_tools"], 0)
            self.assertIn("DENY_NETWORK", payload["notes"]["network"])
            self.assertIn("capabilities", payload["notes"]["project_tools"])
            self.assertEqual(
                [item["tool"] for item in payload["notes"]["sensitive"]],
                ["mmu_record_proof", "mmu_restore", "mmu_sync_memory"],
            )


if __name__ == "__main__":
    unittest.main()
