"""M5-D — vrai client MCP face à l’adapter ARET de production du Pack."""

from __future__ import annotations

from contextlib import asynccontextmanager
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_SERVER = ROOT / "tests" / "aret_mcp_runtime_fixture_server.py"


class AretMCPStdioRuntimeTests(unittest.IsolatedAsyncioTestCase):
    """La surface stdio utilise l’adapter Pack, pas l’adapter de scénario M5-A."""

    @asynccontextmanager
    async def _session(self):
        from mcp.client.session import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client

        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        profile = Path(directory.name) / "project.yaml"
        profile.write_text(
            """
mmu:
  version: "2.0"
project:
  id: "aret-mcp-stdio-runtime"
  name: "ARET MCP Stdio Runtime"
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

    async def test_i007_real_stdio_uses_aret_pack_adapter_and_keeps_parameters_closed(self) -> None:
        async with self._session() as session:
            catalog = self._payload(await session.call_tool("mmu_get_capability_catalog", {}))
            self.assertTrue(catalog["ok"])
            self.assertEqual(
                {item["id"] for item in catalog["result"]["capabilities"]},
                {"aret-oracle-difftest"},
            )
            injected = self._payload(
                await session.call_tool(
                    "mmu_run_capability",
                    {"capability_id": "aret-oracle-difftest", "parameters": {"command": "id"}},
                )
            )
            self.assertFalse(injected["ok"])
            run = self._payload(
                await session.call_tool(
                    "mmu_run_capability", {"capability_id": "aret-oracle-difftest", "parameters": {}}
                )
            )
            self.assertTrue(run["ok"])
            result = run["result"]
            self.assertEqual(result["verdict"], "PASS")
            validation = self._payload(
                await session.call_tool("mmu_validate_evidence", {"evidence_id": result["evidence_id"]})
            )
            self.assertEqual(validation["result"]["verdict"], "PASS")
            admission = self._payload(
                await session.call_tool(
                    "mmu_decide_admission",
                    {"evidence_id": result["evidence_id"], "validation_id": validation["result"]["validation_id"]},
                )
            )
            self.assertTrue(admission["ok"])
            gate = self._payload(await session.call_tool("mmu_evaluate_gate", {"gate_id": result["gate_id"]}))
            self.assertEqual(gate["result"]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
