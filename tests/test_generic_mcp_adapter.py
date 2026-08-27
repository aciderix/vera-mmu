from __future__ import annotations

from contextlib import asynccontextmanager
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore

ROOT = Path(__file__).resolve().parents[1]
PROFILE = """
mmu:
  version: "2.0"
project:
  id: "generic-mcp"
  name: "Generic MCP"
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

class GenericMCPAdapterTests(unittest.IsolatedAsyncioTestCase):
    def _prepare(self, project: Path) -> Path:
        from vera_mmu.generic_mcp_adapter import compile_generic_mcp_plan, stage_generic_mcp_runtime
        profile = project / "project.yaml"; profile.write_text(PROFILE, encoding="utf-8")
        with MemoryStore.open(load_profile(profile), profile) as store:
            CapabilityService(store).create("alpha-check", "Alpha", "CHECK", "1.0.0", parameter_schema={"type":"object","additionalProperties":False}, metadata={}, actor="test")
            CapabilityContractService(store).declare("alpha-check", "OBSERVED_PROCESS", "DENY_NETWORK", 30, parameter_schema={"type":"object","additionalProperties":False}, actor="test")
            CapabilityPolicyService(store).declare("alpha-check", "ALLOW", "test", actor="test")
            plan=compile_generic_mcp_plan(store)
            with self.assertRaises(Exception): stage_generic_mcp_runtime(store,plan,confirm=False)
            self.assertEqual(stage_generic_mcp_runtime(store,plan,confirm=True).status,"STAGED")
        return profile
    @asynccontextmanager
    async def _session(self, profile:Path):
        from mcp.client.session import ClientSession
        from mcp.client.stdio import StdioServerParameters,stdio_client
        params=StdioServerParameters(command=sys.executable,args=["-c","from vera_mmu.generic_mcp_adapter import generic_mcp_main; generic_mcp_main()","--profile",str(profile)],env={"PYTHONPATH":str(ROOT/"src"),"PYTHONDONTWRITEBYTECODE":"1"},cwd=str(ROOT))
        async with stdio_client(params) as (read,write):
            async with ClientSession(read,write) as session:
                await session.initialize();yield session
    async def test_i007_i011_generic_stage_and_config_are_project_local(self)->None:
        from vera_mmu.generic_mcp_adapter import GenericMCPAdapterError,apply_generic_mcp_config,preview_generic_mcp_config
        with TemporaryDirectory() as directory:
            project=Path(directory);profile=self._prepare(project);existing={"mcpServers":{"third-party":{"command":"third","args":[]}}}
            (project/".mcp.json").write_text(json.dumps(existing),encoding="utf-8")
            with MemoryStore.open(load_profile(profile),profile) as store:
                preview=preview_generic_mcp_config(store,existing);self.assertIn("third-party",preview.json_text);self.assertIn("vmmu-generic-mcp",preview.json_text)
                with self.assertRaises(GenericMCPAdapterError):apply_generic_mcp_config(store,preview,confirm=False)
                self.assertEqual(apply_generic_mcp_config(store,preview,confirm=True).status,"APPLIED_PROJECT_LOCAL")
            self.assertTrue((project/".mcp.json").is_file())
    async def test_i007_i011_generic_mcp_catalog_without_lifecycle_automation(self)->None:
        with TemporaryDirectory() as directory:
            profile=self._prepare(Path(directory))
            async with self._session(profile) as client:
                tools=await client.list_tools();names={x.name for x in tools.tools};self.assertIn("mmu_get_capability_catalog",names);self.assertIn("mmu_acknowledge_resume",names)
                catalog=await client.call_tool("mmu_get_capability_catalog",{});self.assertTrue(catalog.structured_content["ok"])
                ack=await client.call_tool("mmu_acknowledge_resume",{"sections":{"working-rules":"x","current-state":"x"}});self.assertFalse(ack.structured_content["ok"])
                denied=await client.call_tool("mmu_run_capability",{"capability_id":"alpha-check","parameters":{}});self.assertFalse(denied.structured_content["ok"])
    async def test_i007_i011_generic_refuses_conflict_symlink_and_stale(self)->None:
        from vera_mmu.generic_mcp_adapter import GenericMCPAdapterError,compile_generic_mcp_plan,preview_generic_mcp_config,stage_generic_mcp_runtime
        with TemporaryDirectory() as directory:
            project=Path(directory)/"project";project.mkdir();profile=self._prepare(project)
            with MemoryStore.open(load_profile(profile),profile) as store:
                with self.assertRaises(GenericMCPAdapterError):preview_generic_mcp_config(store,{"mcpServers":{"vera-mmu-generic-mcp":{"command":"foreign","args":[]}}})
                plan=compile_generic_mcp_plan(store);project2=Path(directory)/"foreign";project2.mkdir();(store.locator.runtime_dir/"generated"/"generic-mcp-runtime.json").unlink();(store.locator.runtime_dir/"generated"/"generic-mcp-runtime.json").symlink_to(project2)
                with self.assertRaises(GenericMCPAdapterError):stage_generic_mcp_runtime(store,plan,confirm=True)

if __name__=="__main__":unittest.main()
