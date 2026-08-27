from __future__ import annotations

from contextlib import asynccontextmanager
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_SERVER = ROOT / "tests" / "mcp_lifecycle_fixture_server.py"


class MCPLifecycleAcknowledgementTests(unittest.IsolatedAsyncioTestCase):
    _expected_tools = {
        "mmu_get_capability_catalog",
        "mmu_run_capability",
        "mmu_get_execution",
        "mmu_read_artifact",
        "mmu_validate_evidence",
        "mmu_decide_admission",
        "mmu_evaluate_gate",
        "mmu_acknowledge_resume",
        "mmu_sync_memory",
        "mmu_export_bundle",
        "mmu_preview_project_documents",
        "mmu_import_project_documents",
        "mmu_doctor",
        "mmu_get_coverage_report",
        "mmu_boot",
        "mmu_get_front",
        "mmu_get_handoff",
        "mmu_find",
        "mmu_get_related",
        "mmu_list_executions",
        "mmu_list_evidence",
        "mmu_read",
        "mmu_read_batch",
    }
    _forbidden_fields = {
        "session_id",
        "session_identity",
        "adapter_id",
        "adapter_version",
        "resume_contract_hash",
        "verdict",
        "status",
        "command",
        "path",
    }

    @asynccontextmanager
    async def _session(self, context: str, *, sync: bool = False):
        from mcp.client.session import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client

        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        runtime = Path(directory.name)
        profile = runtime / "project.yaml"
        profile.write_text(
            """
mmu:
  version: "2.0"
project:
  id: "mcp-lifecycle-transport"
  name: "MCP Lifecycle Transport"
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
""".strip()
            + "\n",
            encoding="utf-8",
        )
        remote = None
        if sync:
            memory = runtime / ".vera-mmu"
            memory.mkdir()
            (memory / "sync-policy.json").write_text(
                '{"auto_commit":true,"auto_push":true,"branch":"CURRENT","format":"vera-memory-sync-policy/v1","remote":"origin"}\n',
                encoding="utf-8",
            )
            remote = runtime.parent / f"mcp-memory-remote-{runtime.name}.git"
            for command in (("init", "-b", "main"), ("config", "user.name", "VERA MCP tests"), ("config", "user.email", "vera-mcp@example.invalid")):
                subprocess.run(["git", "-C", str(runtime), *command], check=True, text=True, capture_output=True)
            subprocess.run(["git", "init", "--bare", str(remote)], check=True, text=True, capture_output=True)
            subprocess.run(["git", "-C", str(runtime), "remote", "add", "origin", str(remote)], check=True, text=True, capture_output=True)
            subprocess.run(["git", "-C", str(runtime), "add", "--", "project.yaml", ".vera-mmu/sync-policy.json"], check=True, text=True, capture_output=True)
            subprocess.run(["git", "-C", str(runtime), "commit", "-m", "MCP sync baseline"], check=True, text=True, capture_output=True)
            subprocess.run(["git", "-C", str(runtime), "push", "-u", "origin", "main"], check=True, text=True, capture_output=True)
        parameters = StdioServerParameters(
            command=sys.executable,
            args=[str(FIXTURE_SERVER), "--profile", str(profile), "--context", context],
            env={**os.environ, "PYTHONPATH": str(ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"},
            cwd=str(ROOT),
        )
        async with stdio_client(parameters) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                yield session

    @staticmethod
    def _payload(response):
        payload = response.structured_content
        if not isinstance(payload, dict):
            raise AssertionError(f"Réponse MCP structurée absente : {response}")
        return payload

    @staticmethod
    def _sections() -> dict[str, str]:
        return {
            "working-rules": "Mesurer les faits avant toute conclusion.",
            "current-state": "La garde de reprise attend un acquittement.",
        }

    async def test_i007_i008_i009_acknowledges_only_host_contextualized_armed_state(self) -> None:
        async with self._session("ready") as session:
            tools = await session.list_tools()
            self.assertEqual({tool.name for tool in tools.tools}, self._expected_tools)
            tool = next(item for item in tools.tools if item.name == "mmu_acknowledge_resume")
            properties = set(tool.input_schema.get("properties", {}))
            self.assertEqual(properties, {"sections"})
            self.assertFalse(properties & self._forbidden_fields)
            invalid_sections = self._sections()
            invalid_sections["resume_contract_hash"] = "f" * 64
            embedded = self._payload(await session.call_tool("mmu_acknowledge_resume", {"sections": invalid_sections}))
            self.assertFalse(embedded["ok"])
            injected = self._payload(
                await session.call_tool(
                    "mmu_acknowledge_resume",
                    {
                        "sections": self._sections(),
                        "session_identity": "client-selected",
                        "adapter_id": "client-selected-v1",
                        "resume_contract_hash": "f" * 64,
                    },
                )
            )
            self.assertTrue(injected["ok"])
            self.assertEqual(injected["result"], {"acknowledged": True})
            repeated = self._payload(await session.call_tool("mmu_acknowledge_resume", {"sections": self._sections()}))
            self.assertFalse(repeated["ok"])

    async def test_i014_refuses_when_host_cannot_supply_session_context(self) -> None:
        async with self._session("missing") as session:
            result = self._payload(await session.call_tool("mmu_acknowledge_resume", {"sections": self._sections()}))
            self.assertFalse(result["ok"])
            self.assertEqual(result["error"]["code"], "VERA_ERROR")

    async def test_i001_i007_memory_sync_exposes_no_git_input(self) -> None:
        async with self._session("ready") as session:
            tools = await session.list_tools()
            tool = next(item for item in tools.tools if item.name == "mmu_sync_memory")
            self.assertEqual(set(tool.input_schema.get("properties", {})), set())
            result = self._payload(await session.call_tool("mmu_sync_memory", {}))
            self.assertTrue(result["ok"])
            self.assertEqual(result["result"]["status"], "DISABLED")

    async def test_i001_i007_acknowledgement_auto_syncs_memory_when_project_policy_allows_it(self) -> None:
        async with self._session("ready", sync=True) as session:
            result = self._payload(await session.call_tool("mmu_acknowledge_resume", {"sections": self._sections()}))
            self.assertTrue(result["ok"])
            self.assertEqual(result["result"], {"acknowledged": True})
            self.assertEqual(result["memory_sync"]["status"], "SYNCED")
            self.assertTrue(result["memory_sync"]["pushed"])


if __name__ == "__main__":
    unittest.main()
