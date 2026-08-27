from __future__ import annotations

from contextlib import asynccontextmanager
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.evidence import EvidenceService
from vera_mmu.executions import ExecutionService
from vera_mmu.identity import load_profile
from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization
from vera_mmu.store import MemoryStore


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_SERVER = ROOT / "tests" / "m11c_mcp_fixture_server.py"


def _initialize(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    preview = preview_project_initialization(root, template="research", project_id="m11j-proof", project_name="M11-J Proof Reads")
    apply_project_initialization(root, preview, confirm=True)
    profile = root / ".vera-mmu" / "project.yaml"
    with MemoryStore.open(load_profile(profile), profile) as store:
        CapabilityService(store).create("inspect-state", "Inspect state", "QUERY", "1.0.0", description="Capability de lecture déclarative.")
        CapabilityContractService(store).declare("inspect-state", "NOOP", "DENY_NETWORK", 30)
        CapabilityPolicyService(store).declare("inspect-state", "ALLOW", "fixture policy", actor="test")
        ExecutionService(store).run_noop("execution-proof", "inspect-state", {"scope": "core"}, actor="test")
        EvidenceService(store).record(
            "evidence-proof", "execution-proof", "TEST_PROOF", "PASS", {"summary": "Evidence persistée pour lecture exacte."}, actor="test"
        )
    return profile


class ExecutionEvidenceReadCoreTests(unittest.TestCase):
    def test_i001_i004_i005_i007_i011_exact_reads_are_project_bound_and_non_mutating(self) -> None:
        from vera_mmu.read_api import ReadApiError, ReadService

        with TemporaryDirectory() as directory:
            profile = _initialize(Path(directory))
            with MemoryStore.open(load_profile(profile), profile) as store:
                audit_before = store.audit_events()
                service = ReadService(store)
                capability = service.read("vera://m11j-proof/capability/inspect-state")
                execution = service.read("vera://m11j-proof/execution/execution-proof")
                evidence = service.read("vera://m11j-proof/evidence/evidence-proof")
                self.assertEqual(capability["record"]["kind"], "QUERY")
                self.assertEqual(execution["record"]["parameters"], {"scope": "core"})
                self.assertEqual(execution["record"]["status"], "COMPLETED")
                self.assertEqual(evidence["record"]["verdict"], "PASS")
                self.assertEqual(evidence["record"]["content"]["summary"], "Evidence persistée pour lecture exacte.")
                self.assertEqual(store.audit_events(), audit_before)
                with self.assertRaises(ReadApiError):
                    service.read("vera://other-project/evidence/evidence-proof")
                with self.assertRaises(ReadApiError):
                    service.read("vera://m11j-proof/execution/absent")


class ExecutionEvidenceReadMCPTests(unittest.IsolatedAsyncioTestCase):
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

    @staticmethod
    def _payload(response):
        payload = response.structured_content
        if not isinstance(payload, dict):
            raise AssertionError(f"Réponse MCP structurée absente : {response}")
        return payload

    async def test_i004_i005_i007_i008_i011_mcp_read_is_exact_and_does_not_accept_records(self) -> None:
        with TemporaryDirectory() as directory:
            profile = _initialize(Path(directory))
            async with self._session(profile) as session:
                tools = {tool.name: tool for tool in (await session.list_tools()).tools}
                schema = tools["mmu_read"].input_schema
                self.assertEqual(set(schema.get("properties", {})), {"address"})
                self.assertNotIn("record", schema.get("properties", {}))
                evidence = self._payload(await session.call_tool("mmu_read", {"address": "vera://m11j-proof/evidence/evidence-proof"}))
                execution = self._payload(await session.call_tool("mmu_read", {"address": "vera://m11j-proof/execution/execution-proof"}))
                self.assertTrue(evidence["ok"])
                self.assertTrue(execution["ok"])
                self.assertEqual(evidence["result"]["record"]["content_hash"], evidence["result"]["record"]["content_hash"])
                self.assertEqual(execution["result"]["record"]["capability_id"], "inspect-state")


if __name__ == "__main__":
    unittest.main()
