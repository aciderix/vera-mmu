"""M5-F — configuration d’intégration MCP déterministe et confinée."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.identity import load_profile
from vera_mmu.mcp_instructions import compile_mcp_instructions
from vera_mmu.mcp_manifest import compile_mcp_manifest
from vera_mmu.store import MemoryStore


PROFILE = """
mmu:
  version: "2.0"
project:
  id: "integration-project"
  name: "Integration Project"
  domain: "generic"
workspace:
  root: "."
storage:
  memory_dir: ".vera-mmu"
  sqlite_file: "memory.sqlite"
  artifacts_dir: "artifacts"
identity:
  include_vcs_revision: false
  include_profile_hash: true
"""


class MCPIntegrationConfigTests(unittest.TestCase):
    def _store(self, directory: Path) -> MemoryStore:
        profile_path = directory / "project.yaml"
        profile_path.write_text(PROFILE, encoding="utf-8")
        return MemoryStore.open(load_profile(profile_path), profile_path)

    @staticmethod
    def _declare(store: MemoryStore, identifier: str) -> None:
        CapabilityService(store).create(
            identifier,
            f"Check {identifier}",
            "CHECK",
            "1.0.0",
            parameter_schema={"type": "object", "additionalProperties": False},
            metadata={},
            actor="test",
        )
        CapabilityContractService(store).declare(
            identifier,
            "OBSERVED_PROCESS",
            "DENY_NETWORK",
            30,
            parameter_schema={"type": "object", "additionalProperties": False},
            actor="test",
        )
        CapabilityPolicyService(store).declare(identifier, "ALLOW", "test", actor="test")

    def test_i007_i011_i012_compiles_stable_project_local_mcp_config(self) -> None:
        from vera_mmu.mcp_integration import compile_mcp_integration

        with TemporaryDirectory() as directory:
            project = Path(directory)
            with self._store(project) as store:
                self._declare(store, "alpha-check")
                manifest = compile_mcp_manifest(store, adapter_bindings={"alpha-check": "adapter-alpha-v1"})
                instructions = compile_mcp_instructions(store, manifest)
                first = compile_mcp_integration(store, manifest, instructions)
                second = compile_mcp_integration(store, manifest, instructions)
                self.assertEqual(first, second)
                self.assertEqual(first.mcp_build_hash, manifest.mcp_build_hash)
                self.assertEqual(first.instructions_hash, instructions.instructions_hash)
                self.assertEqual(len(first.config_hash), 64)
                payload = json.loads(first.json_text)
                self.assertEqual(set(payload), {"mcpServers"})
                self.assertEqual(set(payload["mcpServers"]), {"vera-mmu-integration-project"})
                server = payload["mcpServers"]["vera-mmu-integration-project"]
                self.assertEqual(server["command"], "vmmu-mcp")
                self.assertEqual(server["args"], ["--profile", "${CLAUDE_PROJECT_DIR:-.}/project.yaml"])
                self.assertEqual(server["env"], {
                    "VERA_MCP_BUILD_HASH": manifest.mcp_build_hash,
                    "VERA_MCP_INSTRUCTIONS_HASH": instructions.instructions_hash,
                    "VERA_PROJECT_ID": "integration-project",
                })
                self.assertNotIn("ARET", first.json_text)

    def test_i011_refuses_stale_instruction_or_manifest(self) -> None:
        from vera_mmu.mcp_integration import MCPIntegrationError, compile_mcp_integration

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                self._declare(store, "alpha-check")
                manifest = compile_mcp_manifest(store, adapter_bindings={"alpha-check": "adapter-alpha-v1"})
                instructions = compile_mcp_instructions(store, manifest)
                self._declare(store, "beta-check")
                with self.assertRaises(MCPIntegrationError):
                    compile_mcp_integration(store, manifest, instructions)

    def test_i008_preview_write_is_confined_and_non_overwriting(self) -> None:
        from vera_mmu.mcp_integration import compile_mcp_integration, write_mcp_integration_preview

        with TemporaryDirectory() as directory:
            project = Path(directory)
            with self._store(project) as store:
                self._declare(store, "alpha-check")
                manifest = compile_mcp_manifest(store, adapter_bindings={"alpha-check": "adapter-alpha-v1"})
                instructions = compile_mcp_instructions(store, manifest)
                integration = compile_mcp_integration(store, manifest, instructions)
                preview = write_mcp_integration_preview(store, integration)
                self.assertEqual(preview, project.resolve() / ".vera-mmu" / "generated" / "mcp.json")
                self.assertEqual(preview.read_text(encoding="utf-8"), integration.json_text)
                with self.assertRaises(FileExistsError):
                    write_mcp_integration_preview(store, integration)
                self.assertFalse((project / ".mcp.json").exists())


if __name__ == "__main__":
    unittest.main()
