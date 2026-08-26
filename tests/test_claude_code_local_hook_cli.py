from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.claude_code_integration import compile_claude_code_integration_plan
from vera_mmu.claude_code_local import compile_claude_code_local_plan, install_claude_code_local
from vera_mmu.identity import load_profile
from vera_mmu.lifecycle_adapters import compile_lifecycle_adapter_plan
from vera_mmu.mcp_hooks import compile_mcp_hook_plan
from vera_mmu.mcp_instructions import compile_mcp_instructions
from vera_mmu.mcp_integration import compile_mcp_integration
from vera_mmu.mcp_manifest import compile_mcp_manifest
from vera_mmu.store import MemoryStore


ROOT = Path(__file__).resolve().parents[1]
PROFILE = """
mmu:
  version: "2.0"
project:
  id: "claude-local-cli"
  name: "Claude Local CLI"
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


class ClaudeCodeLocalHookCLITests(unittest.TestCase):
    def _store(self, directory: Path) -> MemoryStore:
        profile = directory / "project.yaml"
        profile.write_text(PROFILE, encoding="utf-8")
        return MemoryStore.open(load_profile(profile), profile)

    @staticmethod
    def _declare(store: MemoryStore) -> None:
        CapabilityService(store).create(
            "alpha-check", "Alpha", "CHECK", "1.0.0", parameter_schema={"type": "object", "additionalProperties": False}, metadata={}, actor="test"
        )
        CapabilityContractService(store).declare(
            "alpha-check", "OBSERVED_PROCESS", "DENY_NETWORK", 30, parameter_schema={"type": "object", "additionalProperties": False}, actor="test"
        )
        CapabilityPolicyService(store).declare("alpha-check", "ALLOW", "test", actor="test")

    @staticmethod
    def _snapshots(store: MemoryStore):
        manifest = compile_mcp_manifest(store, adapter_bindings={"alpha-check": "adapter-alpha-v1"})
        instructions = compile_mcp_instructions(store, manifest)
        integration = compile_mcp_integration(store, manifest, instructions)
        hooks = compile_mcp_hook_plan(store, manifest, instructions, integration)
        review = compile_claude_code_integration_plan(store, manifest, instructions, integration, hooks)
        lifecycle = compile_lifecycle_adapter_plan(
            store, manifest, adapter_id="claude-code-local-v1", adapter_version="1.0.0", maximum_guard_mode="HARD"
        )
        plan = compile_claude_code_local_plan(store, manifest, instructions, integration, hooks, review, lifecycle)
        return manifest, instructions, integration, hooks, review, lifecycle, plan

    def _invoke(self, profile: Path, event: str, payload: dict[str, object]) -> tuple[int, dict[str, object]]:
        completed = subprocess.run(
            [sys.executable, "-m", "vera_mmu.claude_code_local", "--profile", str(profile), "--event", event],
            cwd=str(ROOT),
            env={**os.environ, "PYTHONPATH": str(ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"},
            input=json.dumps(payload),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        return completed.returncode, json.loads(completed.stdout)

    def test_installed_entrypoint_arms_and_blocks_before_acknowledgement(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory)
            profile = project / "project.yaml"
            with self._store(project) as store:
                self._declare(store)
                snapshots = self._snapshots(store)
                install_claude_code_local(store, *snapshots, confirm=True)
            code, started = self._invoke(profile, "SessionStart", {"session_id": "cli-session", "cwd": str(project), "source": "startup"})
            self.assertEqual(code, 0)
            self.assertIn("Resume Dossier", started["hookSpecificOutput"]["additionalContext"])
            code, denied = self._invoke(profile, "PreToolUse", {"session_id": "cli-session", "cwd": str(project), "tool_name": "Read", "tool_input": {}})
            self.assertEqual(code, 0)
            self.assertEqual(denied["hookSpecificOutput"]["permissionDecision"], "deny")


if __name__ == "__main__":
    unittest.main()
