"""M5-G — plan de hook MCP déclaratif, attesté et non exécutable."""

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
from vera_mmu.mcp_integration import compile_mcp_integration
from vera_mmu.mcp_manifest import compile_mcp_manifest
from vera_mmu.store import MemoryStore


PROFILE = """
mmu:
  version: "2.0"
project:
  id: "hook-project"
  name: "Hook Project"
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


class MCPHookPlanTests(unittest.TestCase):
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

    def test_i007_i011_i012_compiles_stable_non_executable_session_start_plan(self) -> None:
        from vera_mmu.mcp_hooks import compile_mcp_hook_plan

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                self._declare(store, "alpha-check")
                manifest = compile_mcp_manifest(store, adapter_bindings={"alpha-check": "adapter-alpha-v1"})
                instructions = compile_mcp_instructions(store, manifest)
                integration = compile_mcp_integration(store, manifest, instructions)
                first = compile_mcp_hook_plan(store, manifest, instructions, integration)
                second = compile_mcp_hook_plan(store, manifest, instructions, integration)
                self.assertEqual(first, second)
                self.assertEqual(first.mcp_build_hash, manifest.mcp_build_hash)
                self.assertEqual(first.instructions_hash, instructions.instructions_hash)
                self.assertEqual(first.config_hash, integration.config_hash)
                self.assertEqual(len(first.hook_plan_hash), 64)
                payload = json.loads(first.json_text)
                self.assertEqual(set(payload), {"hookPlan"})
                self.assertEqual(payload["hookPlan"]["SessionStart"], {
                    "delivery": "HOST_ADAPTER_REQUIRED",
                    "instruction_source": "ATTESTED_MCP_INSTRUCTIONS",
                    "mode": "DECLARATIVE_ONLY",
                })
                self.assertNotIn("command", first.json_text)
                self.assertNotIn("ARET", first.json_text)

    def test_i011_refuses_plan_when_integration_is_stale(self) -> None:
        from vera_mmu.mcp_hooks import MCPHookPlanError, compile_mcp_hook_plan

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                self._declare(store, "alpha-check")
                manifest = compile_mcp_manifest(store, adapter_bindings={"alpha-check": "adapter-alpha-v1"})
                instructions = compile_mcp_instructions(store, manifest)
                integration = compile_mcp_integration(store, manifest, instructions)
                self._declare(store, "beta-check")
                with self.assertRaises(MCPHookPlanError):
                    compile_mcp_hook_plan(store, manifest, instructions, integration)

    def test_i008_preview_is_runtime_confined_and_non_overwriting(self) -> None:
        from vera_mmu.mcp_hooks import compile_mcp_hook_plan, write_mcp_hook_plan_preview

        with TemporaryDirectory() as directory:
            project = Path(directory)
            with self._store(project) as store:
                self._declare(store, "alpha-check")
                manifest = compile_mcp_manifest(store, adapter_bindings={"alpha-check": "adapter-alpha-v1"})
                instructions = compile_mcp_instructions(store, manifest)
                integration = compile_mcp_integration(store, manifest, instructions)
                plan = compile_mcp_hook_plan(store, manifest, instructions, integration)
                target = write_mcp_hook_plan_preview(store, plan)
                self.assertEqual(target, project.resolve() / ".vera-mmu" / "generated" / "hooks.json")
                self.assertEqual(target.read_text(encoding="utf-8"), plan.json_text)
                with self.assertRaises(FileExistsError):
                    write_mcp_hook_plan_preview(store, plan)
                self.assertFalse((project / ".claude" / "settings.json").exists())


if __name__ == "__main__":
    unittest.main()
