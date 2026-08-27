"""Contrat M5 : vrai client MCP stdio pour le transport de verdicts VERA.

Le scénario est choisi au démarrage du serveur de fixture, jamais dans un argument MCP.
Le client ne peut donc pas injecter commande, stdout, exit_code, verdict ou artifact.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_SERVER = ROOT / "tests" / "mcp_verdict_fixture_server.py"


class MCPStdioVerdictTransportTests(unittest.IsolatedAsyncioTestCase):
    """La façade MCP doit transporter, non réinterpréter, les verdicts des services VERA."""

    _required_tools = {
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
        "mmu_get_documentation",
        "mmu_get_vcs_status",
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
    _forbidden_client_fields = {
        "verdict",
        "score",
        "stdout",
        "stderr",
        "exit_code",
        "command",
        "artifact",
        "artifact_bytes",
        "artifact_path",
    }

    @asynccontextmanager
    async def _session(self, scenario: str):
        try:
            from mcp.client.session import ClientSession
            from mcp.client.stdio import StdioServerParameters, stdio_client
        except ImportError as exc:  # Le rouge initial documente la dépendance MCP à porter d’ARET.
            self.fail(f"Le SDK MCP requis par le contrat M5 est absent : {exc}")

        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        runtime = Path(directory.name)
        profile = runtime / "project.yaml"
        profile.write_text(
            """
mmu:
  version: "2.0"
project:
  id: "mcp-verdict-transport"
  name: "MCP Verdict Transport"
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
            args=[str(FIXTURE_SERVER), "--profile", str(profile), "--scenario", scenario],
            env={
                **os.environ,
                "PYTHONPATH": str(ROOT / "src"),
                "PYTHONDONTWRITEBYTECODE": "1",
            },
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

    async def test_generated_documentation_has_no_client_input(self) -> None:
        async with self._session("pass") as session:
            response = self._payload(await session.call_tool("mmu_get_documentation", {}))
            self.assertTrue(response["ok"])
            self.assertEqual(set(response["result"]["documents"]), {"MMU_SETUP.md", "TOOLS.md", "GATES.md", "POLICIES.md", "ARCHITECTURE.md", "MAINTENANCE.md"})

    async def test_catalog_is_closed_and_execution_input_cannot_inject_results(self) -> None:
        async with self._session("pass") as session:
            tools = await session.list_tools()
            names = {tool.name for tool in tools.tools}
            self.assertEqual(names, self._required_tools)
            run_tool = next(tool for tool in tools.tools if tool.name == "mmu_run_capability")
            properties = set(run_tool.input_schema.get("properties", {}))
            self.assertEqual(properties, {"capability_id", "parameters"})
            self.assertFalse(properties & self._forbidden_client_fields)
            injected = self._payload(
                await session.call_tool(
                    "mmu_run_capability",
                    {"capability_id": "aret-oracle-difftest", "parameters": {"verdict": "PASS"}},
                )
            )
            self.assertFalse(injected["ok"])
            self.assertEqual(injected["error"]["code"], "VERA_ERROR")
            catalog = self._payload(await session.call_tool("mmu_get_capability_catalog", {}))
            self.assertTrue(catalog["ok"])
            self.assertEqual(
                {item["id"] for item in catalog["result"]["capabilities"]},
                {"aret-oracle-difftest", "aret-oracle-winehash"},
            )

    async def test_contractual_scenarios_reach_admission_and_gate_fail_closed(self) -> None:
        scenarios = (
            ("pass", "aret-oracle-difftest", "PASS", "PASS", True),
            ("fail", "aret-oracle-difftest", "FAIL", "PASS", False),
            ("skipped", "aret-oracle-difftest", "SKIPPED", "PASS", False),
            ("timeout", "aret-oracle-difftest", "ERROR", "PASS", False),
            ("unrecognized", "aret-oracle-difftest", "ERROR", "PASS", False),
            ("unknown", "aret-oracle-winehash", "UNKNOWN", "PASS", False),
            ("tampered", "aret-oracle-difftest", "PASS", "FAIL", False),
        )
        for scenario, capability_id, expected_verdict, expected_validation, admitted in scenarios:
            with self.subTest(scenario=scenario):
                async with self._session(scenario) as session:
                    run = self._payload(
                        await session.call_tool(
                            "mmu_run_capability",
                            {"capability_id": capability_id, "parameters": {}},
                        )
                    )
                    self.assertTrue(run["ok"])
                    result = run["result"]
                    self.assertEqual(result["verdict"], expected_verdict)
                    self.assertEqual(result["capability_id"], capability_id)
                    self.assertNotIn("stdout", result)
                    self.assertNotIn("stderr", result)
                    execution = self._payload(
                        await session.call_tool("mmu_get_execution", {"execution_id": result["execution_id"]})
                    )
                    self.assertTrue(execution["ok"])
                    self.assertEqual(execution["result"]["result"]["verdict"], expected_verdict)
                    artifact = self._payload(
                        await session.call_tool("mmu_read_artifact", {"asset_id": result["asset_id"]})
                    )
                    self.assertTrue(artifact["ok"])
                    self.assertEqual(artifact["result"]["asset_id"], result["asset_id"])
                    validation = self._payload(
                        await session.call_tool("mmu_validate_evidence", {"evidence_id": result["evidence_id"]})
                    )
                    self.assertTrue(validation["ok"])
                    self.assertEqual(validation["result"]["verdict"], expected_validation)
                    decision = self._payload(
                        await session.call_tool(
                            "mmu_decide_admission",
                            {
                                "evidence_id": result["evidence_id"],
                                "validation_id": validation["result"]["validation_id"],
                            },
                        )
                    )
                    self.assertEqual(decision["ok"], admitted)
                    if admitted:
                        self.assertEqual(decision["result"]["decision"], "ADMITTED")
                    else:
                        self.assertEqual(decision["error"]["code"], "VERA_ERROR")
                    gate = self._payload(
                        await session.call_tool("mmu_evaluate_gate", {"gate_id": result["gate_id"]})
                    )
                    self.assertTrue(gate["ok"])
                    self.assertEqual(gate["result"]["status"], "PASS" if admitted else "FAIL")


if __name__ == "__main__":
    unittest.main()
