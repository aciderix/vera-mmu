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
  id: "gemini-mcp"
  name: "Gemini MCP"
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


class GeminiAdapterTests(unittest.IsolatedAsyncioTestCase):
    def _prepare(self, project: Path) -> Path:
        from vera_mmu.gemini_adapter import compile_gemini_plan, stage_gemini_runtime
        profile = project / "project.yaml"
        profile.write_text(PROFILE, encoding="utf-8")
        with MemoryStore.open(load_profile(profile), profile) as store:
            CapabilityService(store).create("alpha-check", "Alpha", "CHECK", "1.0.0", parameter_schema={"type":"object","additionalProperties":False}, metadata={}, actor="test")
            CapabilityContractService(store).declare("alpha-check", "OBSERVED_PROCESS", "DENY_NETWORK", 30, parameter_schema={"type":"object","additionalProperties":False}, actor="test")
            CapabilityPolicyService(store).declare("alpha-check", "ALLOW", "test", actor="test")
            manifest = compile_mcp_manifest(store, adapter_bindings={"alpha-check":"adapter-alpha-v1"})
            instructions = compile_mcp_instructions(store, manifest)
            integration = compile_mcp_integration(store, manifest, instructions)
            hooks = compile_mcp_hook_plan(store, manifest, instructions, integration)
            lifecycle = compile_lifecycle_adapter_plan(store, manifest, adapter_id="gemini-cli-v1", adapter_version="1.0.0", maximum_guard_mode="HARD")
            plan = compile_gemini_plan(store, manifest, instructions, integration, hooks, lifecycle)
            self.assertEqual(stage_gemini_runtime(store, manifest, instructions, integration, hooks, lifecycle, plan, confirm=True).status, "STAGED")
        return profile

    def _hook(self, profile: Path, event: str, payload: dict[str, object]) -> dict[str, object]:
        completed = subprocess.run([sys.executable, "-m", "vera_mmu.gemini_adapter", "--profile", str(profile), "--event", event], cwd=ROOT, env={**os.environ,"PYTHONPATH":str(ROOT / "src"),"PYTHONDONTWRITEBYTECODE":"1"}, input=json.dumps(payload), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(completed.stdout)

    @asynccontextmanager
    async def _session(self, profile: Path):
        from mcp.client.session import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client
        parameters = StdioServerParameters(command=sys.executable, args=["-c", "from vera_mmu.gemini_adapter import gemini_mcp_main; gemini_mcp_main()", "--profile", str(profile)], env={**os.environ,"PYTHONPATH":str(ROOT / "src"),"PYTHONDONTWRITEBYTECODE":"1"}, cwd=str(ROOT))
        async with stdio_client(parameters) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session

    async def test_i007_i011_gemini_stage_and_config_are_confirmed_project_local(self) -> None:
        from vera_mmu.gemini_adapter import GeminiAdapterError, apply_gemini_host_config, preview_gemini_host_config
        with TemporaryDirectory() as directory:
            project = Path(directory)
            profile = self._prepare(project)
            settings = {"ui": {"theme": "dark"}, "hooks": {"Notification": [{"hooks":[{"type":"command","command":"third-party"}]}]}}
            (project / ".gemini").mkdir()
            (project / ".gemini" / "settings.json").write_text(json.dumps(settings), encoding="utf-8")
            with MemoryStore.open(load_profile(profile), profile) as store:
                preview = preview_gemini_host_config(store, settings)
                self.assertIn("third-party", preview.settings_json_text)
                self.assertIn("vmmu-gemini-hook", preview.settings_json_text)
                self.assertIn("vmmu-gemini-mcp", preview.settings_json_text)
                with self.assertRaises(GeminiAdapterError):
                    apply_gemini_host_config(store, preview, confirm=False)
                self.assertEqual(apply_gemini_host_config(store, preview, confirm=True).status, "APPLIED_PROJECT_LOCAL")
            self.assertTrue((project / ".gemini" / "settings.json").is_file())

    async def test_i007_i011_gemini_before_tool_ack_and_precompress_limit(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory)
            profile = self._prepare(project)
            session_id = "gemini-session"
            started = self._hook(profile, "SessionStart", {"session_id":session_id,"cwd":str(project),"source":"startup"})
            self.assertIn("Resume Dossier", started["hookSpecificOutput"]["additionalContext"])
            denied = self._hook(profile, "BeforeTool", {"session_id":session_id,"cwd":str(project),"tool_name":"run_shell_command","tool_input":{}})
            self.assertEqual(denied["decision"], "deny")
            async with self._session(profile) as client:
                answer = await client.call_tool("mmu_acknowledge_resume", {"sections":{"working-rules":"Mesurer les faits avant toute conclusion.","current-state":"La garde Gemini attend un acquittement."}})
                self.assertIsInstance(answer.structured_content, dict)
                self.assertTrue(answer.structured_content["ok"])
            allowed = self._hook(profile, "BeforeTool", {"session_id":session_id,"cwd":str(project),"tool_name":"run_shell_command","tool_input":{}})
            self.assertNotIn("decision", allowed)
            preparing = self._hook(profile, "PreCompress", {"session_id":session_id,"cwd":str(project)})
            self.assertIn("ne peut pas réarmer", preparing["systemMessage"])
            still_allowed = self._hook(profile, "BeforeTool", {"session_id":session_id,"cwd":str(project),"tool_name":"run_shell_command","tool_input":{}})
            self.assertNotIn("decision", still_allowed)

    async def test_i007_i011_gemini_refuses_conflict_and_symlink(self) -> None:
        from vera_mmu.gemini_adapter import GeminiAdapterError, preview_gemini_host_config
        with TemporaryDirectory() as directory:
            project = Path(directory) / "project"; project.mkdir()
            profile = self._prepare(project)
            with MemoryStore.open(load_profile(profile), profile) as store:
                with self.assertRaises(GeminiAdapterError):
                    preview_gemini_host_config(store, {"hooks":{"SessionStart":[{"hooks":[{"command":"vmmu-gemini-hook --profile foreign --event SessionStart"}]}]}})
            foreign = Path(directory) / "foreign"; foreign.mkdir()
            (project / ".gemini").symlink_to(foreign, target_is_directory=True)
            with MemoryStore.open(load_profile(profile), profile) as store:
                with self.assertRaises(GeminiAdapterError):
                    preview_gemini_host_config(store, {})

if __name__ == "__main__":
    unittest.main()
