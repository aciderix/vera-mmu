from __future__ import annotations

from contextlib import asynccontextmanager
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
from vera_mmu.claude_code_cloud import compile_claude_code_cloud_plan
from vera_mmu.claude_code_integration import compile_claude_code_integration_plan
from vera_mmu.claude_code_local import compile_claude_code_local_plan
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
  id: "claude-cloud-mcp"
  name: "Claude Cloud MCP"
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


class ClaudeCodeCloudRuntimeTests(unittest.IsolatedAsyncioTestCase):
    def _prepare(self, project: Path) -> Path:
        from vera_mmu.claude_code_cloud import stage_claude_code_cloud_runtime

        profile = project / "project.yaml"
        profile.write_text(PROFILE, encoding="utf-8")
        with MemoryStore.open(load_profile(profile), profile) as store:
            CapabilityService(store).create(
                "alpha-check", "Alpha", "CHECK", "1.0.0", parameter_schema={"type": "object", "additionalProperties": False}, metadata={}, actor="test"
            )
            CapabilityContractService(store).declare(
                "alpha-check", "OBSERVED_PROCESS", "DENY_NETWORK", 30, parameter_schema={"type": "object", "additionalProperties": False}, actor="test"
            )
            CapabilityPolicyService(store).declare("alpha-check", "ALLOW", "test", actor="test")
            manifest = compile_mcp_manifest(store, adapter_bindings={"alpha-check": "adapter-alpha-v1"})
            instructions = compile_mcp_instructions(store, manifest)
            integration = compile_mcp_integration(store, manifest, instructions)
            hooks = compile_mcp_hook_plan(store, manifest, instructions, integration)
            review = compile_claude_code_integration_plan(store, manifest, instructions, integration, hooks)
            local_lifecycle = compile_lifecycle_adapter_plan(
                store, manifest, adapter_id="claude-code-local-v1", adapter_version="1.0.0", maximum_guard_mode="HARD"
            )
            local = compile_claude_code_local_plan(store, manifest, instructions, integration, hooks, review, local_lifecycle)
            cloud = compile_claude_code_cloud_plan(store, manifest, instructions, integration, hooks, review, local_lifecycle, local)
            result = stage_claude_code_cloud_runtime(
                store, manifest, instructions, integration, hooks, review, local_lifecycle, local, cloud, confirm=True
            )
            self.assertEqual(result.status, "STAGED")
        return profile

    def _hook(self, profile: Path, event: str, payload: dict[str, object]) -> dict[str, object]:
        completed = subprocess.run(
            [sys.executable, "-m", "vera_mmu.claude_code_cloud", "--profile", str(profile), "--event", event],
            cwd=str(ROOT),
            env={**os.environ, "PYTHONPATH": str(ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"},
            input=json.dumps(payload),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(completed.stdout)

    @asynccontextmanager
    async def _session(self, profile: Path):
        from mcp.client.session import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client

        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-c", "from vera_mmu.claude_code_cloud import claude_code_cloud_mcp_main; claude_code_cloud_mcp_main()", "--profile", str(profile)],
            env={**os.environ, "PYTHONPATH": str(ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"},
            cwd=str(ROOT),
        )
        async with stdio_client(parameters) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                yield session

    @staticmethod
    def _payload(response):
        if not isinstance(response.structured_content, dict):
            raise AssertionError(f"Réponse MCP structurée absente : {response}")
        return response.structured_content

    async def test_i007_i011_stage_refuses_unconfirmed_and_writes_only_runtime(self) -> None:
        from vera_mmu.claude_code_cloud import ClaudeCodeCloudError, stage_claude_code_cloud_runtime

        with TemporaryDirectory() as directory:
            project = Path(directory)
            profile = project / "project.yaml"
            profile.write_text(PROFILE, encoding="utf-8")
            with MemoryStore.open(load_profile(profile), profile) as store:
                CapabilityService(store).create(
                    "alpha-check", "Alpha", "CHECK", "1.0.0", parameter_schema={"type": "object", "additionalProperties": False}, metadata={}, actor="test"
                )
                CapabilityContractService(store).declare(
                    "alpha-check", "OBSERVED_PROCESS", "DENY_NETWORK", 30, parameter_schema={"type": "object", "additionalProperties": False}, actor="test"
                )
                CapabilityPolicyService(store).declare("alpha-check", "ALLOW", "test", actor="test")
                manifest = compile_mcp_manifest(store, adapter_bindings={"alpha-check": "adapter-alpha-v1"})
                instructions = compile_mcp_instructions(store, manifest)
                integration = compile_mcp_integration(store, manifest, instructions)
                hooks = compile_mcp_hook_plan(store, manifest, instructions, integration)
                review = compile_claude_code_integration_plan(store, manifest, instructions, integration, hooks)
                lifecycle = compile_lifecycle_adapter_plan(
                    store, manifest, adapter_id="claude-code-local-v1", adapter_version="1.0.0", maximum_guard_mode="HARD"
                )
                local = compile_claude_code_local_plan(store, manifest, instructions, integration, hooks, review, lifecycle)
                cloud = compile_claude_code_cloud_plan(store, manifest, instructions, integration, hooks, review, lifecycle, local)
                with self.assertRaises(ClaudeCodeCloudError):
                    stage_claude_code_cloud_runtime(store, manifest, instructions, integration, hooks, review, lifecycle, local, cloud, confirm=False)
                result = stage_claude_code_cloud_runtime(store, manifest, instructions, integration, hooks, review, lifecycle, local, cloud, confirm=True)
                self.assertEqual(result.status, "STAGED")
                self.assertTrue(result.state_path.is_file())
                self.assertFalse((project / ".claude").exists())
                self.assertFalse((project / ".mcp.json").exists())
                unchanged = stage_claude_code_cloud_runtime(store, manifest, instructions, integration, hooks, review, lifecycle, local, cloud, confirm=True)
                self.assertEqual(unchanged.status, "UNCHANGED")

    async def test_hook_to_cloud_mcp_acknowledgement_to_pretool_allow(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory)
            profile = self._prepare(project)
            session_id = "cloud-mcp-session"
            started = self._hook(profile, "SessionStart", {"session_id": session_id, "cwd": str(project), "source": "startup"})
            self.assertIn("Resume Dossier", started["hookSpecificOutput"]["additionalContext"])
            denied = self._hook(profile, "PreToolUse", {"session_id": session_id, "cwd": str(project), "tool_name": "Read", "tool_input": {}})
            self.assertEqual(denied["hookSpecificOutput"]["permissionDecision"], "deny")
            async with self._session(profile) as session:
                tools = await session.list_tools()
                acknowledgement = next(tool for tool in tools.tools if tool.name == "mmu_acknowledge_resume")
                self.assertEqual(set(acknowledgement.input_schema.get("properties", {})), {"sections"})
                result = self._payload(
                    await session.call_tool(
                        "mmu_acknowledge_resume",
                        {
                            "sections": {
                                "working-rules": "Mesurer les faits avant toute conclusion.",
                                "current-state": "La garde Claude cloud attend un acquittement.",
                            }
                        },
                    )
                )
                self.assertTrue(result["ok"])
                self.assertEqual(result["result"], {"acknowledged": True})
            allowed = self._hook(profile, "PreToolUse", {"session_id": session_id, "cwd": str(project), "tool_name": "Read", "tool_input": {}})
            self.assertNotIn("permissionDecision", allowed["hookSpecificOutput"])
            compacted = self._hook(profile, "PostCompact", {"session_id": session_id, "cwd": str(project)})
            self.assertIn("Resume Dossier", compacted["hookSpecificOutput"]["additionalContext"])
            rearmed = self._hook(profile, "PreToolUse", {"session_id": session_id, "cwd": str(project), "tool_name": "Read", "tool_input": {}})
            self.assertEqual(rearmed["hookSpecificOutput"]["permissionDecision"], "deny")


if __name__ == "__main__":
    unittest.main()
