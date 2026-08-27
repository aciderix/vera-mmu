from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.__main__ import main

PROFILE = """
mmu:
  version: "2.0"
project:
  id: "operations-cli"
  name: "Operations CLI"
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

def invoke(arguments: list[str]) -> tuple[int, dict[str, object]]:
    stream=StringIO()
    with redirect_stdout(stream): code=main(arguments)
    return code,json.loads(stream.getvalue())

class OperationsCLITests(unittest.TestCase):
    def _profile(self,directory:Path)->Path:
        path=directory/"project.yaml";path.write_text(PROFILE,encoding="utf-8");return path
    def test_i007_i011_matrix_is_static_and_bounded(self)->None:
        code,payload=invoke(["adapter","matrix"])
        self.assertEqual(code,0);self.assertTrue(payload["ok"])
        adapters={item["adapter"]:item for item in payload["adapters"]}
        self.assertEqual(adapters["generic-mcp"]["coverage"],"MCP_ONLY")
        self.assertEqual(adapters["gemini"]["coverage"],"TOOL_GUARD_NO_POST_COMPACTION")
        self.assertNotIn("userScopeApply",adapters["claude-code-cloud"])
    def test_i007_i011_doctor_is_observational_and_reports_missing_runtime(self)->None:
        with TemporaryDirectory() as directory:
            profile=self._profile(Path(directory)); code,payload=invoke(["adapter","doctor","--profile",str(profile),"--adapter","codex"])
            self.assertEqual(code,0);self.assertTrue(payload["ok"]);self.assertEqual(payload["doctor"]["runtime"],"RUNTIME_MISSING")
            self.assertFalse((Path(directory)/".codex").exists())
    def test_i007_i011_stage_configure_route_is_confirmed_and_blocks_cloud_user_scope(self)->None:
        with TemporaryDirectory() as directory:
            project=Path(directory);profile=self._profile(project)
            code,payload=invoke(["adapter","stage","--profile",str(profile),"--adapter","generic-mcp"])
            self.assertEqual(code,2);self.assertFalse(payload["ok"])
            self.assertFalse((project/".mcp.json").exists())
            code,payload=invoke(["adapter","configure","--profile",str(profile),"--adapter","claude-code-cloud","--apply-user-scope","--confirm"])
            self.assertEqual(code,2);self.assertFalse(payload["ok"]);self.assertIn("user-scope",payload["error"])
            code,payload=invoke(["adapter","doctor","--profile",str(profile),"--adapter","unknown"])
            self.assertEqual(code,2);self.assertFalse(payload["ok"])
    def test_i001_i007_memory_sync_command_has_no_git_arguments_and_reports_policy_state(self)->None:
        with TemporaryDirectory() as directory:
            profile=self._profile(Path(directory));code,payload=invoke(["memory-sync",str(profile)])
            self.assertEqual(code,0);self.assertTrue(payload["ok"]);self.assertEqual(payload["memory_sync"]["status"],"DISABLED")
if __name__=="__main__":unittest.main()
