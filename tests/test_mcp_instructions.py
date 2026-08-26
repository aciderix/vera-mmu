"""M5-E — instructions MCP déterministes et liées au manifeste attesté."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.identity import load_profile
from vera_mmu.mcp_manifest import compile_mcp_manifest
from vera_mmu.store import MemoryStore


PROFILE = """
mmu:
  version: "2.0"
project:
  id: "instruction-project"
  name: "Instruction Project"
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


class MCPInstructionsTests(unittest.TestCase):
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

    def test_i007_i012_compiles_stable_universal_instructions_from_manifest(self) -> None:
        from vera_mmu.mcp_instructions import compile_mcp_instructions

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                self._declare(store, "alpha-check")
                manifest = compile_mcp_manifest(store, adapter_bindings={"alpha-check": "adapter-alpha-v1"})
                first = compile_mcp_instructions(store, manifest)
                second = compile_mcp_instructions(store, manifest)
                self.assertEqual(first, second)
                self.assertEqual(first.mcp_build_hash, manifest.mcp_build_hash)
                self.assertEqual(len(first.instructions_hash), 64)
                self.assertIn("Project: instruction-project", first.text)
                self.assertIn(f"Manifest SHA-256: {manifest.mcp_build_hash}", first.text)
                self.assertIn("alpha-check | CHECK | OBSERVED_PROCESS | DENY_NETWORK | 30 | adapter-alpha-v1", first.text)
                self.assertIn("Never accept a client-supplied command", first.text)
                self.assertNotIn("ARET", first.text)

    def test_i012_facade_refuses_instructions_bound_to_another_manifest(self) -> None:
        from dataclasses import replace
        from vera_mmu.mcp_instructions import compile_mcp_instructions
        from vera_mmu.mcp_server import create_server

        class Adapter:
            adapter_id = "adapter-alpha-v1"

            def run(self, *args: object, **kwargs: object) -> dict[str, object]:
                raise AssertionError("Aucune exécution requise pour ce test de démarrage.")

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                self._declare(store, "alpha-check")
                manifest = compile_mcp_manifest(store, adapter_bindings={"alpha-check": "adapter-alpha-v1"})
                instructions = compile_mcp_instructions(store, manifest)
                with self.assertRaises(ValueError):
                    create_server(
                        store,
                        runtime_adapter=Adapter(),
                        manifest=manifest,
                        instructions=replace(instructions, mcp_build_hash="0" * 64),
                    )

    def test_i011_refuses_instructions_from_a_stale_manifest(self) -> None:
        from vera_mmu.mcp_instructions import MCPInstructionsError, compile_mcp_instructions

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                self._declare(store, "alpha-check")
                manifest = compile_mcp_manifest(store, adapter_bindings={"alpha-check": "adapter-alpha-v1"})
                self._declare(store, "beta-check")
                with self.assertRaises(MCPInstructionsError):
                    compile_mcp_instructions(store, manifest)


if __name__ == "__main__":
    unittest.main()
