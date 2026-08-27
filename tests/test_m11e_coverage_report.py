from __future__ import annotations

from contextlib import asynccontextmanager, redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_SERVER = ROOT / "tests" / "m11c_mcp_fixture_server.py"


PROFILE = '''
mmu:
  version: "2.0"
project:
  id: "m11e-coverage"
  name: "M11-E Coverage"
  domain: "research"
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


class CoverageReportTests(unittest.TestCase):
    def _store(self, root: Path) -> MemoryStore:
        runtime = root / ".vera-mmu"
        runtime.mkdir()
        profile = runtime / "project.yaml"
        profile.write_text(PROFILE, encoding="utf-8")
        return MemoryStore.open(load_profile(profile), profile)

    def test_i001_i007_i008_i011_report_is_deterministic_project_bound_and_non_sensitive(self) -> None:
        from vera_mmu.coverage_report import compile_coverage_report

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                audits = store.audit_events()
                first = compile_coverage_report(store)
                second = compile_coverage_report(store)
                self.assertEqual(first.as_dict(), second.as_dict())
                report = first.as_dict()
                self.assertEqual(report["format"], "vera-coverage-report/v1")
                self.assertEqual(report["project_identity"], store.identity.as_dict())
                self.assertIn("mmu_get_coverage_report", report["mcp_tools"])
                self.assertIn("symbol", report["readable_resources"])
                self.assertEqual(report["findable_resources"], ["entity", "knowledge", "work-item"])
                self.assertEqual(report["bounded_histories"], {"evidence": 100, "execution": 100})
                rendered = str(report)
                self.assertNotIn(str(store.workspace.project_root), rendered)
                self.assertNotIn("profile_path", rendered)
                self.assertEqual(store.audit_events(), audits)


class CoverageReportTransportTests(unittest.IsolatedAsyncioTestCase):
    @asynccontextmanager
    async def _session(self, profile: Path):
        from mcp.client.session import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client

        parameters = StdioServerParameters(
            command=sys.executable,
            args=[str(FIXTURE_SERVER), "--profile", str(profile)],
            env={**os.environ, "PYTHONPATH": str(ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"},
            cwd=str(ROOT),
        )
        async with stdio_client(parameters) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                yield session

    async def test_i001_i007_i008_cli_and_mcp_return_derived_report_without_client_selection(self) -> None:
        from vera_mmu.__main__ import main

        with TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / ".vera-mmu"
            runtime.mkdir()
            profile = runtime / "project.yaml"
            profile.write_text(PROFILE, encoding="utf-8")
            output = StringIO()
            with redirect_stdout(output):
                status = main(["coverage", str(profile)])
            cli = json.loads(output.getvalue())
            self.assertEqual(status, 0)
            self.assertEqual(cli["coverage"]["format"], "vera-coverage-report/v1")
            async with self._session(profile) as session:
                tools = {tool.name: tool for tool in (await session.list_tools()).tools}
                self.assertEqual(set(tools["mmu_get_coverage_report"].input_schema.get("properties", {})), set())
                response = await session.call_tool("mmu_get_coverage_report", {})
                payload = response.structured_content
                self.assertIsInstance(payload, dict)
                self.assertTrue(payload["ok"])
                self.assertEqual(payload["result"]["project_identity"]["project_id"], "m11e-coverage")
                self.assertNotIn("profile_path", str(payload["result"]))


if __name__ == "__main__":
    unittest.main()
