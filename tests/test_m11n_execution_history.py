from __future__ import annotations

from contextlib import asynccontextmanager, redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.executions import ExecutionService
from vera_mmu.identity import load_profile
from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization
from vera_mmu.store import MemoryStore


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_SERVER = ROOT / "tests" / "m11c_mcp_fixture_server.py"


def _initialize(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    preview = preview_project_initialization(root, template="research", project_id="m11n-history", project_name="M11-N Execution History")
    apply_project_initialization(root, preview, confirm=True)
    profile = root / ".vera-mmu" / "project.yaml"
    with MemoryStore.open(load_profile(profile), profile) as store:
        CapabilityService(store).create("inspect-state", "Inspect state", "QUERY", "1.0.0", description="Capability de lecture déclarative.")
        CapabilityContractService(store).declare("inspect-state", "NOOP", "DENY_NETWORK", 30)
        CapabilityPolicyService(store).declare("inspect-state", "ALLOW", "fixture policy", actor="test")
        executions = ExecutionService(store)
        for identifier in ("execution-1", "execution-2", "execution-3"):
            executions.run_noop(identifier, "inspect-state", {"scope": "core"}, actor="test")
    return profile


class ExecutionHistoryCoreTests(unittest.TestCase):
    def test_i001_i002_i005_i011_history_is_bounded_deterministic_compact_and_non_mutating(self) -> None:
        from vera_mmu.read_api import ReadApiError, ReadService

        with TemporaryDirectory() as directory:
            profile = _initialize(Path(directory))
            with MemoryStore.open(load_profile(profile), profile) as store:
                audits = store.audit_events()
                history = ReadService(store).execution_history(max_items=2)
                self.assertEqual(history["max_items"], 2)
                self.assertEqual([item["id"] for item in history["executions"]], ["execution-3", "execution-2"])
                self.assertEqual(set(history["executions"][0]), {
                    "address", "id", "capability_id", "status", "started_at", "finished_at", "artifact_hash",
                })
                self.assertTrue(all(item["address"].startswith("vera://m11n-history/execution/") for item in history["executions"]))
                self.assertTrue(all("parameters" not in item and "environment" not in item and "result" not in item for item in history["executions"]))
                self.assertEqual(store.audit_events(), audits)
                for value in (0, 101, True, "2"):
                    with self.assertRaises(ReadApiError):
                        ReadService(store).execution_history(max_items=value)


class ExecutionHistoryTransportTests(unittest.IsolatedAsyncioTestCase):
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

    async def test_i001_i002_i007_i008_cli_and_mcp_expose_only_bounded_compact_history(self) -> None:
        from vera_mmu.__main__ import main

        with TemporaryDirectory() as directory:
            profile = _initialize(Path(directory))
            output = StringIO()
            with redirect_stdout(output):
                status = main(["list-executions", str(profile), "--max-items", "2"])
            cli = json.loads(output.getvalue())
            self.assertEqual(status, 0)
            self.assertEqual([item["id"] for item in cli["executions"]["executions"]], ["execution-3", "execution-2"])
            async with self._session(profile) as session:
                tools = {tool.name: tool for tool in (await session.list_tools()).tools}
                self.assertEqual(set(tools["mmu_list_executions"].input_schema.get("properties", {})), {"max_items"})
                response = await session.call_tool("mmu_list_executions", {"max_items": 1})
                payload = response.structured_content
                self.assertIsInstance(payload, dict)
                self.assertTrue(payload["ok"])
                self.assertEqual([item["id"] for item in payload["result"]["executions"]], ["execution-3"])
                self.assertTrue(all("parameters" not in item and "result" not in item for item in payload["result"]["executions"]))
                invalid = await session.call_tool("mmu_list_executions", {"max_items": 101})
                invalid_payload = invalid.structured_content
                self.assertIsInstance(invalid_payload, dict)
                self.assertFalse(invalid_payload["ok"])


if __name__ == "__main__":
    unittest.main()
