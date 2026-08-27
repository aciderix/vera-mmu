from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.__main__ import main
from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore

PROFILE = '''
mmu:
  version: "2.0"
project:
  id: "operations-scan"
  name: "Operations Scan"
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
'''

def invoke(argv:list[str])->tuple[int,dict[str,object]]:
    output=StringIO()
    with redirect_stdout(output):code=main(argv)
    return code,json.loads(output.getvalue())

class ProjectOperationsTests(unittest.TestCase):
    def _profile(self,root:Path,seed:bool=False)->Path:
        profile=root/"project.yaml";profile.write_text(PROFILE,encoding="utf-8")
        if seed:
            with MemoryStore.open(load_profile(profile),profile) as store:
                CapabilityService(store).create("check","Check","CHECK","1.0.0",parameter_schema={"type":"object","additionalProperties":False},metadata={},actor="test")
                CapabilityContractService(store).declare("check","OBSERVED_PROCESS","DENY_NETWORK",30,parameter_schema={"type":"object","additionalProperties":False},actor="test")
                CapabilityPolicyService(store).declare("check","ALLOW","test",actor="test")
        return profile
    def test_i007_i011_scan_is_observational_deterministic_and_never_follows_symlink(self)->None:
        from vera_mmu.project_operations import ProjectOperationError,scan_project
        with TemporaryDirectory() as directory:
            root=Path(directory);(root/"pyproject.toml").write_text("[project]\n",encoding="utf-8");(root/"README.md").write_text("x",encoding="utf-8");(root/"tests").mkdir();(root/"tests"/"test_x.py").write_text("",encoding="utf-8");outside=root.parent/"outside-vera-scan";outside.mkdir(exist_ok=True);(outside/"secret.py").write_text("",encoding="utf-8");(root/"foreign").symlink_to(outside,target_is_directory=True)
            first=scan_project(root);second=scan_project(root)
            self.assertEqual(first,second);self.assertEqual(first.status,"OBSERVED");self.assertIn("python",{item.kind for item in first.observations});self.assertIn("tests",{item.kind for item in first.observations});self.assertNotIn("foreign/secret.py",{item.path for item in first.observations})
            with self.assertRaises(ProjectOperationError):scan_project(root/"foreign")
            code,payload=invoke(["scan",str(root)])
            self.assertEqual(code,0);self.assertTrue(payload["ok"]);self.assertEqual(payload["scan"]["status"],"OBSERVED")
            self.assertFalse((root/".vera-mmu").exists())
    def test_i007_i011_generation_preview_is_deterministic_and_has_no_host_write(self)->None:
        from vera_mmu.project_operations import compile_generation_preview
        with TemporaryDirectory() as directory:
            root=Path(directory);profile=self._profile(root,seed=True)
            with MemoryStore.open(load_profile(profile),profile) as store:
                first=compile_generation_preview(store,"generic-mcp");second=compile_generation_preview(store,"generic-mcp")
                self.assertEqual(first,second);self.assertEqual(first.status,"PREVIEW");self.assertEqual(first.adapter,"generic-mcp");self.assertIn("mcpServers",first.integration_json_text);self.assertTrue(first.preview_hash)
            self.assertFalse((root/".mcp.json").exists())
            code,payload=invoke(["generate",str(profile),"--adapter","generic-mcp"]);self.assertEqual(code,0);self.assertTrue(payload["ok"]);self.assertEqual(payload["generation"]["status"],"PREVIEW")
    def test_i007_i011_install_routes_only_allowlisted_adapter_with_preview_and_confirmation(self)->None:
        from vera_mmu.generic_mcp_adapter import compile_generic_mcp_plan,stage_generic_mcp_runtime
        with TemporaryDirectory() as directory:
            root=Path(directory);profile=self._profile(root,seed=True)
            with MemoryStore.open(load_profile(profile),profile) as store:stage_generic_mcp_runtime(store,compile_generic_mcp_plan(store),confirm=True)
            code,payload=invoke(["install",str(profile),"--adapter","generic-mcp"]);self.assertEqual(code,0);self.assertEqual(payload["installation"]["status"],"PREVIEW");self.assertFalse((root/".mcp.json").exists())
            code,payload=invoke(["install",str(profile),"--adapter","generic-mcp","--apply-project"]);self.assertEqual(code,2);self.assertFalse(payload["ok"]);self.assertFalse((root/".mcp.json").exists())
            code,payload=invoke(["install",str(profile),"--adapter","generic-mcp","--apply-project","--confirm"]);self.assertEqual(code,0);self.assertEqual(payload["installation"]["status"],"APPLIED_PROJECT_LOCAL");self.assertTrue((root/".mcp.json").is_file())
            code,payload=invoke(["install",str(profile),"--adapter","unknown"]);self.assertEqual(code,2);self.assertFalse(payload["ok"])
if __name__=="__main__":unittest.main()
