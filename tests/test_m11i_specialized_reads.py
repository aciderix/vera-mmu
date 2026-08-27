from __future__ import annotations

from contextlib import asynccontextmanager, redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.__main__ import main
from vera_mmu.entities import EntityCreateInput, EntityService
from vera_mmu.front import FrontService
from vera_mmu.handoff import HandoffService
from vera_mmu.identity import load_profile
from vera_mmu.profile_resume import compile_profile_resume_dossier, profile_resume_sections
from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization
from vera_mmu.relations import RelationService
from vera_mmu.store import MemoryStore


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_SERVER = ROOT / "tests" / "m11c_mcp_fixture_server.py"


def _initialize(root: Path) -> tuple[Path, dict[str, str]]:
    root.mkdir(parents=True, exist_ok=True)
    preview = preview_project_initialization(
        root,
        template="documentation",
        project_id="m11i-special",
        project_name="M11-I Specialized Reads",
    )
    apply_project_initialization(root, preview, confirm=True)
    profile = root / ".vera-mmu" / "project.yaml"
    with MemoryStore.open(load_profile(profile), profile) as store:
        fields = {field: f"Valeur persistée pour {field}." for field in load_profile(profile)["front"]["fields"]}
        front = FrontService(store).replace("front-special", fields, actor="test", confirm=True)
        dossier = compile_profile_resume_dossier(
            store,
            profile_resume_sections(store, "Le Front spécialisé est persistant et le handoff doit rester lié à son hash."),
        )
        handoff = HandoffService(store).prepare("handoff-special", dossier, actor="test", confirm=True)
        entities = EntityService(store)
        entities.register_type_and_create_batch(
            "component",
            "Component",
            [
                EntityCreateInput("source", "Source component"),
                EntityCreateInput("target", "Target component"),
            ],
        )
        relations = RelationService(store)
        relations.register_type("depends-on", "Depends on", from_types=["component"], to_types=["component"])
        relation = relations.create("relation-special", "depends-on", "source", "target", actor="test")
    return profile, {"front": front.id, "handoff": handoff.id, "relation": relation.id}


def _cli(arguments: list[str]) -> tuple[int, dict[str, object]]:
    output = StringIO()
    with redirect_stdout(output):
        status = main(arguments)
    return status, json.loads(output.getvalue())


class SpecializedReadCoreTests(unittest.TestCase):
    def test_i001_i002_i003_i009_i011_specialized_reads_are_exact_current_and_non_mutating(self) -> None:
        from vera_mmu.read_api import ReadApiError, ReadService

        with TemporaryDirectory() as directory:
            profile, identifiers = _initialize(Path(directory))
            with MemoryStore.open(load_profile(profile), profile) as store:
                service = ReadService(store)
                audit_before = store.audit_events()
                current = service.current_front()
                latest = service.latest_handoff()
                front = service.read(f"vera://m11i-special/front/{identifiers['front']}")
                handoff = service.read(f"vera://m11i-special/handoff/{identifiers['handoff']}")
                relation = service.read(f"vera://m11i-special/relation/{identifiers['relation']}")
                self.assertEqual(current["record"]["id"], identifiers["front"])
                self.assertEqual(latest["record"]["id"], identifiers["handoff"])
                self.assertEqual(front["record"]["fields"], current["record"]["fields"])
                self.assertEqual(handoff["record"]["payload"]["handoff"]["front"]["id"], identifiers["front"])
                self.assertEqual(relation["record"]["from_address"], "vera://m11i-special/entity/source")
                self.assertEqual(relation["record"]["to_address"], "vera://m11i-special/entity/target")
                self.assertEqual(store.audit_events(), audit_before)
                with self.assertRaises(ReadApiError):
                    service.read("vera://other-project/front/front-special")
                with self.assertRaises(ReadApiError):
                    service.read("vera://m11i-special/handoff/current")

    def test_cli_returns_current_front_and_handoff_without_identifiers(self) -> None:
        with TemporaryDirectory() as directory:
            profile, identifiers = _initialize(Path(directory))
            status, front = _cli(["get-front", str(profile)])
            self.assertEqual(status, 0)
            self.assertEqual(front["front"]["record"]["id"], identifiers["front"])
            status, handoff = _cli(["get-handoff", str(profile)])
            self.assertEqual(status, 0)
            self.assertEqual(handoff["handoff"]["record"]["id"], identifiers["handoff"])


class SpecializedReadMCPTests(unittest.IsolatedAsyncioTestCase):
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

    async def test_i001_i007_i008_i011_mcp_specialized_tools_are_closed_and_project_bound(self) -> None:
        with TemporaryDirectory() as directory:
            profile, identifiers = _initialize(Path(directory))
            async with self._session(profile) as session:
                tools = {tool.name: tool for tool in (await session.list_tools()).tools}
                self.assertTrue({"mmu_get_front", "mmu_get_handoff"}.issubset(tools))
                self.assertEqual(set(tools["mmu_get_front"].input_schema.get("properties", {})), set())
                self.assertEqual(set(tools["mmu_get_handoff"].input_schema.get("properties", {})), set())
                front = self._payload(await session.call_tool("mmu_get_front", {}))
                handoff = self._payload(await session.call_tool("mmu_get_handoff", {}))
                relation = self._payload(await session.call_tool("mmu_read", {"address": f"vera://m11i-special/relation/{identifiers['relation']}"}))
                self.assertTrue(front["ok"])
                self.assertTrue(handoff["ok"])
                self.assertTrue(relation["ok"])
                self.assertEqual(front["result"]["record"]["id"], identifiers["front"])
                self.assertEqual(handoff["result"]["record"]["id"], identifiers["handoff"])
                self.assertEqual(relation["result"]["record"]["id"], identifiers["relation"])


if __name__ == "__main__":
    unittest.main()
