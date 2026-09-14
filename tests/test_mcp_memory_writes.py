"""Prove the memory write surface is reachable through a real MCP stdio session.

Before this lot the Core could append knowledge, snapshot a Front and prepare a handoff, but
no transport exposed those operations. These tests exercise the tools over a genuine stdio
client so the write path is proven end to end, not only at the facade.

Invariants exercised: I003 (append-only), I004 (`PROVEN` unreachable by append), I007/I015
(closed, profile-declared taxonomy) and I013 (explicit decision on a controlled write).
"""
from __future__ import annotations

from contextlib import asynccontextmanager
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_SERVER = ROOT / "tests" / "m11c_mcp_fixture_server.py"

WRITE_TOOLS = {
    "mmu_sync_knowledge_types",
    "mmu_append_knowledge",
    "mmu_replace_front",
    "mmu_update_front",
    "mmu_prepare_handoff",
}
FRONT_FIELDS = {
    "active_goal": "Rendre la memoire inscriptible",
    "current_work": "Exposer les ecritures par MCP",
    "validated_facts": "La facade Core est couverte par des tests",
    "blockers": "Aucun blocage identifie",
    "risks": "Surface MCP elargie a surveiller",
    "next_action": "Etendre au work graph",
}
RESUME_SECTIONS = {
    "working-rules": "Mesurer les faits et refuser toute conclusion non prouvee.",
    "current-state": "Les ecritures memoire sont exposees par le transport MCP.",
    "validated-facts": "La suite Core reste verte apres ouverture des ecritures.",
    "risks": "La surface MCP s elargit et doit rester fermee par manifeste.",
    "next-action": "Exposer le work graph et la promotion de preuve.",
}


def _initialize(root: Path, project_id: str = "mcp-write") -> Path:
    root.mkdir(parents=True, exist_ok=True)
    preview = preview_project_initialization(root, template="software", project_id=project_id, project_name="MCP Write Contract")
    apply_project_initialization(root, preview, confirm=True)
    return root / ".vera-mmu" / "project.yaml"


class MCPMemoryWriteTests(unittest.IsolatedAsyncioTestCase):
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

    async def test_write_tools_are_exposed_without_dangerous_inputs(self) -> None:
        with TemporaryDirectory() as directory:
            profile = _initialize(Path(directory))
            async with self._session(profile) as session:
                tools = {tool.name: tool for tool in (await session.list_tools()).tools}
                self.assertTrue(WRITE_TOOLS.issubset(tools))
                for name in WRITE_TOOLS:
                    properties = set(tools[name].input_schema.get("properties", {}))
                    self.assertNotIn("profile_path", properties)
                    self.assertNotIn("project_id", properties)
                    self.assertNotIn("command", properties)
                # A client never supplies the resume contract hash; the Core computes it.
                self.assertNotIn("resume_contract_hash", set(tools["mmu_prepare_handoff"].input_schema.get("properties", {})))

    async def test_append_knowledge_round_trips_through_mcp(self) -> None:
        with TemporaryDirectory() as directory:
            profile = _initialize(Path(directory))
            async with self._session(profile) as session:
                synced = self._payload(await session.call_tool("mmu_sync_knowledge_types", {}))
                self.assertTrue(synced["ok"])
                self.assertIn("decision", synced["result"]["knowledge_types"])

                appended = self._payload(await session.call_tool("mmu_append_knowledge", {
                    "identifier": "kn-mcp-1", "type_id": "DECISION", "status": "OBSERVED",
                    "title": "Decision de transport", "content": "La memoire est inscriptible par MCP.",
                }))
                self.assertTrue(appended["ok"])
                self.assertEqual(appended["result"]["type_id"], "decision")

                read = self._payload(await session.call_tool("mmu_read", {"address": "vera://mcp-write/knowledge/kn-mcp-1"}))
                self.assertTrue(read["ok"])
                self.assertEqual(read["result"]["record"]["content"], "La memoire est inscriptible par MCP.")

    async def test_append_refuses_proven_and_undeclared_type(self) -> None:
        with TemporaryDirectory() as directory:
            profile = _initialize(Path(directory))
            async with self._session(profile) as session:
                await session.call_tool("mmu_sync_knowledge_types", {})
                proven = self._payload(await session.call_tool("mmu_append_knowledge", {
                    "identifier": "kn-proven", "type_id": "DECISION", "status": "PROVEN", "title": "T", "content": "C",
                }))
                self.assertFalse(proven["ok"])
                smuggled = self._payload(await session.call_tool("mmu_append_knowledge", {
                    "identifier": "kn-smuggled", "type_id": "SMUGGLED", "status": "OBSERVED", "title": "T", "content": "C",
                }))
                self.assertFalse(smuggled["ok"])

    async def test_front_and_handoff_round_trip_through_mcp(self) -> None:
        with TemporaryDirectory() as directory:
            profile = _initialize(Path(directory))
            async with self._session(profile) as session:
                refused = self._payload(await session.call_tool("mmu_replace_front", {"identifier": "front-1", "fields": FRONT_FIELDS}))
                self.assertFalse(refused["ok"])

                replaced = self._payload(await session.call_tool("mmu_replace_front", {
                    "identifier": "front-1", "fields": FRONT_FIELDS, "confirm": True,
                }))
                self.assertTrue(replaced["ok"])
                self.assertEqual(replaced["result"]["fields"]["active_goal"], "Rendre la memoire inscriptible")

                updated = self._payload(await session.call_tool("mmu_update_front", {
                    "identifier": "front-2", "fields": {"risks": "Risque revu a la hausse"}, "confirm": True,
                }))
                self.assertTrue(updated["ok"])
                self.assertEqual(updated["result"]["fields"]["risks"], "Risque revu a la hausse")
                self.assertEqual(updated["result"]["fields"]["active_goal"], "Rendre la memoire inscriptible")

                handoff = self._payload(await session.call_tool("mmu_prepare_handoff", {
                    "identifier": "handoff-1", "sections": RESUME_SECTIONS, "confirm": True,
                }))
                self.assertTrue(handoff["ok"])
                self.assertEqual(handoff["result"]["front_revision_id"], "front-2")

                boot = self._payload(await session.call_tool("mmu_boot", {}))
                self.assertEqual(boot["result"]["current_front"]["id"], "front-2")
                self.assertEqual(boot["result"]["latest_handoff"]["id"], "handoff-1")


    async def test_work_graph_and_promotion_guards_through_mcp(self) -> None:
        with TemporaryDirectory() as directory:
            profile = _initialize(Path(directory))
            async with self._session(profile) as session:
                created = self._payload(await session.call_tool("mmu_create_work_item", {
                    "identifier": "wi-mcp", "item_type": "EPIC", "title": "Chantier MCP",
                }))
                self.assertTrue(created["ok"])
                self.assertEqual(created["result"]["status"], "PLANNED")

                started = self._payload(await session.call_tool("mmu_update_work_item", {
                    "identifier": "ev-mcp", "work_item_id": "wi-mcp", "event": "START", "reason": "demarrage",
                }))
                self.assertTrue(started["ok"])

                graph = self._payload(await session.call_tool("mmu_get_work_graph", {}))
                self.assertTrue(graph["ok"])
                self.assertEqual(graph["result"]["items"][0]["status"], "ACTIVE")

                # I007: the lifecycle catalog is closed, so an invented event is refused.
                invented = self._payload(await session.call_tool("mmu_update_work_item", {
                    "identifier": "ev-bad", "work_item_id": "wi-mcp", "event": "TELEPORT", "reason": "x",
                }))
                self.assertFalse(invented["ok"])

                # I004: promotion is refused before any policy is declared...
                unpoliced = self._payload(await session.call_tool("mmu_record_proof", {
                    "identifier": "p-1", "knowledge_id": "k", "evidence_id": "e", "admission_id": "a",
                }))
                self.assertFalse(unpoliced["ok"])

                declared = self._payload(await session.call_tool("mmu_declare_proof_policy", {"algorithm": "HMAC_SHA256"}))
                self.assertTrue(declared["ok"])

                # ...and still refused without an admitted PASS evidence.
                unproven = self._payload(await session.call_tool("mmu_record_proof", {
                    "identifier": "p-2", "knowledge_id": "k", "evidence_id": "e", "admission_id": "a",
                }))
                self.assertFalse(unproven["ok"])
                self.assertEqual(self._payload(await session.call_tool("mmu_get_proofs", {}))["result"]["proofs"], [])


if __name__ == "__main__":
    unittest.main()
