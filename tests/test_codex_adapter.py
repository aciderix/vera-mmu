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
  id: "codex-mcp"
  name: "Codex MCP"
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


class CodexAdapterTests(unittest.IsolatedAsyncioTestCase):
    def _prepare(self, project: Path) -> Path:
        from vera_mmu.codex_adapter import compile_codex_plan, stage_codex_runtime

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
            lifecycle = compile_lifecycle_adapter_plan(store, manifest, adapter_id="codex-v1", adapter_version="1.0.0", maximum_guard_mode="HARD")
            plan = compile_codex_plan(store, manifest, instructions, integration, hooks, lifecycle)
            result = stage_codex_runtime(store, manifest, instructions, integration, hooks, lifecycle, plan, confirm=True)
            self.assertEqual(result.status, "STAGED")
        return profile

    def _hook(self, profile: Path, event: str, payload: dict[str, object]) -> dict[str, object]:
        completed = subprocess.run(
            [sys.executable, "-m", "vera_mmu.codex_adapter", "--profile", str(profile), "--event", event],
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
            args=["-c", "from vera_mmu.codex_adapter import codex_mcp_main; codex_mcp_main()", "--profile", str(profile)],
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

    async def test_i007_i011_codex_stage_refuses_unconfirmed_and_is_runtime_confined(self) -> None:
        from vera_mmu.codex_adapter import CodexAdapterError, compile_codex_plan, stage_codex_runtime

        with TemporaryDirectory() as directory:
            project = Path(directory)
            profile = project / "project.yaml"
            profile.write_text(PROFILE, encoding="utf-8")
            with MemoryStore.open(load_profile(profile), profile) as store:
                CapabilityService(store).create("alpha-check", "Alpha", "CHECK", "1.0.0", parameter_schema={"type": "object", "additionalProperties": False}, metadata={}, actor="test")
                CapabilityContractService(store).declare("alpha-check", "OBSERVED_PROCESS", "DENY_NETWORK", 30, parameter_schema={"type": "object", "additionalProperties": False}, actor="test")
                CapabilityPolicyService(store).declare("alpha-check", "ALLOW", "test", actor="test")
                manifest = compile_mcp_manifest(store, adapter_bindings={"alpha-check": "adapter-alpha-v1"})
                instructions = compile_mcp_instructions(store, manifest)
                integration = compile_mcp_integration(store, manifest, instructions)
                hooks = compile_mcp_hook_plan(store, manifest, instructions, integration)
                lifecycle = compile_lifecycle_adapter_plan(store, manifest, adapter_id="codex-v1", adapter_version="1.0.0", maximum_guard_mode="HARD")
                plan = compile_codex_plan(store, manifest, instructions, integration, hooks, lifecycle)
                with self.assertRaises(CodexAdapterError):
                    stage_codex_runtime(store, manifest, instructions, integration, hooks, lifecycle, plan, confirm=False)
                staged = stage_codex_runtime(store, manifest, instructions, integration, hooks, lifecycle, plan, confirm=True)
            self.assertTrue(staged.state_path.is_file())
            self.assertFalse((project / ".codex").exists())

    async def test_i007_i011_codex_config_preview_preserves_third_party_and_refuses_conflict(self) -> None:
        from vera_mmu.codex_adapter import CodexAdapterError, preview_codex_host_config

        with TemporaryDirectory() as directory:
            project = Path(directory)
            profile = self._prepare(project)
            existing_hooks = {"description": "third party", "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "third-party-stop"}]}]}}
            existing_toml = 'model = "gpt-5"\n\n[mcp_servers.third_party]\ncommand = "third-party-mcp"\n'
            with MemoryStore.open(load_profile(profile), profile) as store:
                first = preview_codex_host_config(store, existing_hooks, existing_toml)
                second = preview_codex_host_config(store, existing_hooks, existing_toml)
                self.assertEqual(first, second)
                self.assertIn("third-party-stop", first.hooks_json_text)
                self.assertIn("third-party-mcp", first.config_toml_text)
                self.assertIn("vmmu-codex-hook", first.hooks_json_text)
                self.assertIn("vmmu-codex-mcp", first.config_toml_text)
                with self.assertRaises(CodexAdapterError):
                    preview_codex_host_config(store, {"hooks": {"SessionStart": [{"hooks": [{"command": "vmmu-codex-hook --profile foreign --event SessionStart"}]}]}}, existing_toml)
            self.assertFalse((project / ".codex").exists())

    async def test_i007_i011_codex_config_refuses_symlinked_project_target(self) -> None:
        from vera_mmu.codex_adapter import CodexAdapterError, preview_codex_host_config

        with TemporaryDirectory() as directory:
            project = Path(directory) / "project"
            project.mkdir()
            profile = self._prepare(project)
            foreign = Path(directory) / "foreign"
            foreign.mkdir()
            (project / ".codex").symlink_to(foreign, target_is_directory=True)
            with MemoryStore.open(load_profile(profile), profile) as store:
                with self.assertRaises(CodexAdapterError):
                    preview_codex_host_config(store, {}, "")

    async def test_i007_i011_codex_apply_confirmed_and_lifecycle_ack_chain(self) -> None:
        from vera_mmu.codex_adapter import CodexAdapterError, apply_codex_host_config, preview_codex_host_config

        with TemporaryDirectory() as directory:
            project = Path(directory)
            profile = self._prepare(project)
            with MemoryStore.open(load_profile(profile), profile) as store:
                preview = preview_codex_host_config(store, {}, "")
                with self.assertRaises(CodexAdapterError):
                    apply_codex_host_config(store, preview, confirm=False)
                result = apply_codex_host_config(store, preview, confirm=True)
            self.assertEqual(result.status, "APPLIED_PROJECT_LOCAL")
            self.assertTrue((project / ".codex" / "hooks.json").is_file())
            self.assertTrue((project / ".codex" / "config.toml").is_file())
            session_id = "codex-session"
            started = self._hook(profile, "SessionStart", {"session_id": session_id, "cwd": str(project), "source": "startup"})
            self.assertIn("Resume Dossier", started["additionalContext"])
            denied = self._hook(profile, "PreToolUse", {"session_id": session_id, "cwd": str(project), "tool_name": "Bash", "tool_input": {}})
            self.assertEqual(denied["decision"], "block")
            async with self._session(profile) as session:
                result = self._payload(await session.call_tool("mmu_acknowledge_resume", {"sections": {"working-rules": "Mesurer les faits avant toute conclusion.", "current-state": "La garde Codex attend un acquittement."}}))
                self.assertTrue(result["ok"])
            allowed = self._hook(profile, "PreToolUse", {"session_id": session_id, "cwd": str(project), "tool_name": "Bash", "tool_input": {}})
            self.assertNotIn("decision", allowed)
            compacted = self._hook(profile, "PostCompact", {"session_id": session_id, "cwd": str(project)})
            self.assertIn("Resume Dossier", compacted["additionalContext"])
            rearmed = self._hook(profile, "PreToolUse", {"session_id": session_id, "cwd": str(project), "tool_name": "Bash", "tool_input": {}})
            self.assertEqual(rearmed["decision"], "block")


if __name__ == "__main__":
    unittest.main()
