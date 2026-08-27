"""M5-I — installateur MCP Claude Code opt-in et idempotent."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.claude_code_integration import compile_claude_code_integration_plan
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
  id: "install-project"
  name: "Install Project"
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


class ClaudeCodeMCPInstallerTests(unittest.TestCase):
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
        plan = compile_claude_code_integration_plan(store, manifest, instructions, integration, hooks)
        return manifest, instructions, integration, hooks, plan

    def test_i008_requires_explicit_confirmation_before_any_project_write(self) -> None:
        from vera_mmu.claude_code_installer import ClaudeCodeInstallError, install_claude_code_mcp

        with TemporaryDirectory() as directory:
            project = Path(directory)
            with self._store(project) as store:
                self._declare(store, "alpha-check")
                snapshots = self._snapshots(store)
                with self.assertRaises(ClaudeCodeInstallError):
                    install_claude_code_mcp(store, *snapshots, confirm=False)
                self.assertFalse((project / ".mcp.json").exists())
                self.assertFalse((project / ".claude").exists())

    def test_i007_i011_merges_only_attested_server_and_preserves_existing_entries(self) -> None:
        from vera_mmu.claude_code_installer import install_claude_code_mcp

        with TemporaryDirectory() as directory:
            project = Path(directory)
            target = project / ".mcp.json"
            target.write_text(
                json.dumps({"mcpServers": {"other": {"command": "other-mcp"}}, "retained": {"x": 1}}),
                encoding="utf-8",
            )
            with self._store(project) as store:
                self._declare(store, "alpha-check")
                manifest, instructions, integration, hooks, plan = self._snapshots(store)
                result = install_claude_code_mcp(store, manifest, instructions, integration, hooks, plan, confirm=True)
                self.assertEqual(result.status, "INSTALLED")
                self.assertEqual(result.path, target.resolve())
                merged = json.loads(target.read_text(encoding="utf-8"))
                generated = json.loads(integration.json_text)
                self.assertEqual(merged["retained"], {"x": 1})
                self.assertEqual(merged["mcpServers"]["other"], {"command": "other-mcp"})
                self.assertEqual(merged["mcpServers"], {**merged["mcpServers"], **generated["mcpServers"]})
                self.assertFalse((project / ".claude").exists())

    def test_i008_is_idempotent_and_never_rewrites_equivalent_target(self) -> None:
        from vera_mmu.claude_code_installer import install_claude_code_mcp

        with TemporaryDirectory() as directory:
            project = Path(directory)
            with self._store(project) as store:
                self._declare(store, "alpha-check")
                snapshots = self._snapshots(store)
                first = install_claude_code_mcp(store, *snapshots, confirm=True)
                before = first.path.read_bytes()
                second = install_claude_code_mcp(store, *snapshots, confirm=True)
                self.assertEqual(first.status, "INSTALLED")
                self.assertEqual(second.status, "UNCHANGED")
                self.assertEqual(before, second.path.read_bytes())

    def test_i008_i011_refuses_conflicting_or_symlinked_target_without_write(self) -> None:
        from vera_mmu.claude_code_installer import ClaudeCodeInstallError, install_claude_code_mcp

        with TemporaryDirectory() as directory:
            project = Path(directory)
            target = project / ".mcp.json"
            with self._store(project) as store:
                self._declare(store, "alpha-check")
                snapshots = self._snapshots(store)
                server_id = "vera-mmu-install-project"
                conflict = {"mcpServers": {server_id: {"command": "not-vera"}}}
                target.write_text(json.dumps(conflict), encoding="utf-8")
                before = target.read_bytes()
                with self.assertRaises(ClaudeCodeInstallError):
                    install_claude_code_mcp(store, *snapshots, confirm=True)
                self.assertEqual(target.read_bytes(), before)
            target.unlink()
            outside = project / "outside.json"
            outside.write_text("{}", encoding="utf-8")
            target.symlink_to(outside)
            with self._store(project) as store:
                # Le store existant conserve la capability déclarée dans la première sous-partie.
                snapshots = self._snapshots(store)
                with self.assertRaises(ClaudeCodeInstallError):
                    install_claude_code_mcp(store, *snapshots, confirm=True)
            self.assertEqual(outside.read_text(encoding="utf-8"), "{}")


if __name__ == "__main__":
    unittest.main()
