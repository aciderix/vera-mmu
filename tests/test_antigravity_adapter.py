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
  id: "antigravity-mcp"
  name: "Antigravity MCP"
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

class AntigravityAdapterTests(unittest.IsolatedAsyncioTestCase):
    def _prepare(self, project: Path) -> Path:
        from vera_mmu.antigravity_adapter import compile_antigravity_plan, stage_antigravity_runtime
        profile = project / "project.yaml"; profile.write_text(PROFILE, encoding="utf-8")
        with MemoryStore.open(load_profile(profile), profile) as store:
            CapabilityService(store).create("alpha-check", "Alpha", "CHECK", "1.0.0", parameter_schema={"type":"object","additionalProperties":False}, metadata={}, actor="test")
            CapabilityContractService(store).declare("alpha-check", "OBSERVED_PROCESS", "DENY_NETWORK", 30, parameter_schema={"type":"object","additionalProperties":False}, actor="test")
            CapabilityPolicyService(store).declare("alpha-check", "ALLOW", "test", actor="test")
            manifest=compile_mcp_manifest(store,adapter_bindings={"alpha-check":"adapter-alpha-v1"}); ins=compile_mcp_instructions(store,manifest); integ=compile_mcp_integration(store,manifest,ins); hooks=compile_mcp_hook_plan(store,manifest,ins,integ); life=compile_lifecycle_adapter_plan(store,manifest,adapter_id="antigravity-v1",adapter_version="1.0.0",maximum_guard_mode="HARD"); plan=compile_antigravity_plan(store,manifest,ins,integ,hooks,life)
            self.assertEqual(stage_antigravity_runtime(store,manifest,ins,integ,hooks,life,plan,confirm=True).status,"STAGED")
        return profile
    def _hook(self, profile:Path,event:str,payload:dict[str,object])->dict[str,object]:
        done=subprocess.run([sys.executable,"-m","vera_mmu.antigravity_adapter","--profile",str(profile),"--event",event],cwd=ROOT,env={**os.environ,"PYTHONPATH":str(ROOT/"src"),"PYTHONDONTWRITEBYTECODE":"1"},input=json.dumps(payload),text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
        self.assertEqual(done.returncode,0,done.stderr); return json.loads(done.stdout)
    @asynccontextmanager
    async def _session(self,profile:Path):
        from mcp.client.session import ClientSession
        from mcp.client.stdio import StdioServerParameters,stdio_client
        params=StdioServerParameters(command=sys.executable,args=["-c","from vera_mmu.antigravity_adapter import antigravity_mcp_main; antigravity_mcp_main()","--profile",str(profile)],env={**os.environ,"PYTHONPATH":str(ROOT/"src"),"PYTHONDONTWRITEBYTECODE":"1"},cwd=str(ROOT))
        async with stdio_client(params) as (read,write):
            async with ClientSession(read,write) as session:
                await session.initialize();yield session
    async def test_i007_i011_antigravity_stage_and_project_config(self)->None:
        from vera_mmu.antigravity_adapter import AntigravityAdapterError,apply_antigravity_host_config,preview_antigravity_host_config
        with TemporaryDirectory() as directory:
            project=Path(directory);profile=self._prepare(project); settings={"extensions":{"third-party":{"enabled":True}}}
            (project/".antigravity").mkdir();(project/".antigravity"/"settings.json").write_text(json.dumps(settings),encoding="utf-8")
            with MemoryStore.open(load_profile(profile),profile) as store:
                preview=preview_antigravity_host_config(store,settings);self.assertIn("third-party",preview.settings_json_text);self.assertIn("vmmu-antigravity-hook",preview.settings_json_text);self.assertIn("vmmu-antigravity-mcp",preview.settings_json_text)
                with self.assertRaises(AntigravityAdapterError):apply_antigravity_host_config(store,preview,confirm=False)
                self.assertEqual(apply_antigravity_host_config(store,preview,confirm=True).status,"APPLIED_PROJECT_LOCAL")
    async def test_i007_i011_antigravity_turn_guard_ack_and_stop(self)->None:
        with TemporaryDirectory() as directory:
            project=Path(directory);profile=self._prepare(project);session="turn-1"
            opened=self._hook(profile,"PreInvocation",{"invocation_id":session,"cwd":str(project)})
            self.assertIn("Resume Dossier",opened["context"])
            denied=self._hook(profile,"PreToolUse",{"invocation_id":session,"cwd":str(project),"tool_name":"shell"});self.assertEqual(denied["decision"],"deny")
            async with self._session(profile) as client:
                result=await client.call_tool("mmu_acknowledge_resume",{"sections":{"working-rules":"Mesurer les faits avant toute conclusion.","current-state":"La garde Antigravity attend un acquittement."}});self.assertTrue(result.structured_content["ok"])
            allowed=self._hook(profile,"PreToolUse",{"invocation_id":session,"cwd":str(project),"tool_name":"shell"});self.assertNotIn("decision",allowed)
            stopped=self._hook(profile,"Stop",{"invocation_id":session,"cwd":str(project)});self.assertIn("status",stopped)
    async def test_i007_i011_antigravity_refuses_conflict_and_symlink(self)->None:
        from vera_mmu.antigravity_adapter import AntigravityAdapterError,preview_antigravity_host_config
        with TemporaryDirectory() as directory:
            project=Path(directory)/"project";project.mkdir();profile=self._prepare(project)
            with MemoryStore.open(load_profile(profile),profile) as store:
                with self.assertRaises(AntigravityAdapterError):preview_antigravity_host_config(store,{"hooks":{"PreInvocation":[{"command":"vmmu-antigravity-hook --profile foreign --event PreInvocation"}]}})
            foreign=Path(directory)/"foreign";foreign.mkdir();(project/".antigravity").symlink_to(foreign,target_is_directory=True)
            with MemoryStore.open(load_profile(profile),profile) as store:
                with self.assertRaises(AntigravityAdapterError):preview_antigravity_host_config(store,{})
if __name__=="__main__":unittest.main()
