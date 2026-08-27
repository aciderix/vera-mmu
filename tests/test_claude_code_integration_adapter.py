"""M5-H — adapter Claude Code de planification, sans installation implicite."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.identity import load_profile
from vera_mmu.mcp_hooks import compile_mcp_hook_plan
from vera_mmu.mcp_instructions import compile_mcp_instructions
from vera_mmu.mcp_integration import compile_mcp_integration
from vera_mmu.mcp_manifest import compile_mcp_manifest
from vera_mmu.store import MemoryStore


PROFILE = """
mmu:
  version: "2.0"
project:
  id: "claude-plan-project"
  name: "Claude Plan Project"
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


class ClaudeCodeIntegrationAdapterTests(unittest.TestCase):
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

    def _snapshots(self, store: MemoryStore):
        manifest = compile_mcp_manifest(store, adapter_bindings={"alpha-check": "adapter-alpha-v1"})
        instructions = compile_mcp_instructions(store, manifest)
        integration = compile_mcp_integration(store, manifest, instructions)
        hooks = compile_mcp_hook_plan(store, manifest, instructions, integration)
        return manifest, instructions, integration, hooks

    def test_i007_i011_i012_compiles_stable_review_required_claude_plan(self) -> None:
        from vera_mmu.claude_code_integration import compile_claude_code_integration_plan

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                self._declare(store, "alpha-check")
                manifest, instructions, integration, hooks = self._snapshots(store)
                first = compile_claude_code_integration_plan(store, manifest, instructions, integration, hooks)
                second = compile_claude_code_integration_plan(store, manifest, instructions, integration, hooks)
                self.assertEqual(first, second)
                self.assertEqual(first.mcp_build_hash, manifest.mcp_build_hash)
                self.assertEqual(first.instructions_hash, instructions.instructions_hash)
                self.assertEqual(first.config_hash, integration.config_hash)
                self.assertEqual(first.hook_plan_hash, hooks.hook_plan_hash)
                self.assertEqual(len(first.plan_hash), 64)
                payload = json.loads(first.json_text)
                self.assertEqual(set(payload), {"claudeCodeIntegration"})
                plan = payload["claudeCodeIntegration"]
                self.assertEqual(plan["installation"], {"mode": "REVIEW_REQUIRED", "writes": []})
                self.assertEqual(plan["mcpConfig"], {
                    "content_sha256": integration.config_hash,
                    "target": ".mcp.json",
                })
                self.assertEqual(plan["hooks"]["SessionStart"], {
                    "reason": "DECLARATIVE_HOOK_REQUIRES_EXECUTABLE_ADAPTER",
                    "status": "UNTRANSLATED",
                })
                self.assertNotIn("command", first.json_text)
                self.assertNotIn("ARET", first.json_text)

    def test_i011_refuses_any_stale_snapshot(self) -> None:
        from vera_mmu.claude_code_integration import ClaudeCodeIntegrationError, compile_claude_code_integration_plan

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                self._declare(store, "alpha-check")
                manifest, instructions, integration, hooks = self._snapshots(store)
                self._declare(store, "beta-check")
                with self.assertRaises(ClaudeCodeIntegrationError):
                    compile_claude_code_integration_plan(store, manifest, instructions, integration, hooks)

    def test_i008_preview_is_runtime_confined_and_non_overwriting(self) -> None:
        from vera_mmu.claude_code_integration import (
            compile_claude_code_integration_plan,
            write_claude_code_integration_preview,
        )

        with TemporaryDirectory() as directory:
            project = Path(directory)
            with self._store(project) as store:
                self._declare(store, "alpha-check")
                manifest, instructions, integration, hooks = self._snapshots(store)
                plan = compile_claude_code_integration_plan(store, manifest, instructions, integration, hooks)
                target = write_claude_code_integration_preview(store, plan)
                self.assertEqual(target, project.resolve() / ".vera-mmu" / "generated" / "claude-code-integration.json")
                self.assertEqual(target.read_text(encoding="utf-8"), plan.json_text)
                with self.assertRaises(FileExistsError):
                    write_claude_code_integration_preview(store, plan)
                self.assertFalse((project / ".mcp.json").exists())
                self.assertFalse((project / ".claude").exists())


if __name__ == "__main__":
    unittest.main()
