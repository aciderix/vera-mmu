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
from vera_mmu.identity import load_profile
from vera_mmu.knowledge import KnowledgeService
from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization
from vera_mmu.store import MemoryStore
from vera_mmu.work_items import WorkItemService


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_SERVER = ROOT / "tests" / "m11c_mcp_fixture_server.py"


def _initialize(root: Path, project_id: str = "m11h-read") -> Path:
    root.mkdir(parents=True, exist_ok=True)
    preview = preview_project_initialization(
        root,
        template="documentation",
        project_id=project_id,
        project_name="M11-H Read Contract",
    )
    apply_project_initialization(root, preview, confirm=True)
    profile = root / ".vera-mmu" / "project.yaml"
    with MemoryStore.open(load_profile(profile), profile) as store:
        knowledge = KnowledgeService(store)
        knowledge.register_type("observation", "Observation")
        knowledge.append(
            "read-alpha",
            "observation",
            "OBSERVED",
            "Alpha title",
            "Le contenu secret de recherche alpha reste réservé à READ.",
            metadata={"source": "fixture"},
        )
        entity = EntityService(store)
        entity.register_type_and_create_batch(
            "component",
            "Component",
            [EntityCreateInput("entity-alpha", "Alpha component", "Entity description")],
        )
        WorkItemService(store).create("task-alpha", "WORK_ITEM", "Alpha task", description="Work item description")
    return profile


def _cli(arguments: list[str]) -> tuple[int, dict[str, object]]:
    output = StringIO()
    with redirect_stdout(output):
        status = main(arguments)
    return status, json.loads(output.getvalue())


class BootFindReadCoreTests(unittest.TestCase):
    def test_i001_i002_i011_boot_find_read_and_batch_are_project_bound_and_non_mutating(self) -> None:
        from vera_mmu.read_api import ReadApiError, ReadService

        with TemporaryDirectory() as directory:
            profile = _initialize(Path(directory))
            with MemoryStore.open(load_profile(profile), profile) as store:
                audit_before = store.audit_events()
                service = ReadService(store)
                boot = service.boot()
                self.assertEqual(boot["project_identity"]["project_id"], "m11h-read")
                self.assertEqual(boot["resume_status"], "NOT_ARMED")
                self.assertIsNone(boot["current_front"])
                self.assertIsNone(boot["latest_handoff"])

                findings = service.find("alpha", resource_types=["knowledge", "entity", "work-item"])
                self.assertEqual([item["address"] for item in findings], [
                    "vera://m11h-read/entity/entity-alpha",
                    "vera://m11h-read/knowledge/read-alpha",
                    "vera://m11h-read/work-item/task-alpha",
                ])
                self.assertTrue(all("content" not in item and "description" not in item for item in findings))
                self.assertEqual(findings[1]["title"], "Alpha title")

                knowledge = service.read("vera://m11h-read/knowledge/read-alpha")
                self.assertEqual(knowledge["resource_type"], "knowledge")
                self.assertEqual(knowledge["record"]["content"], "Le contenu secret de recherche alpha reste réservé à READ.")
                batch = service.read_batch([
                    "vera://m11h-read/knowledge/read-alpha",
                    "vera://m11h-read/entity/entity-alpha",
                ])
                self.assertEqual([item["resource_type"] for item in batch], ["knowledge", "entity"])
                self.assertEqual(store.audit_events(), audit_before)

                with self.assertRaises(ReadApiError):
                    service.read("vera://other-project/knowledge/read-alpha")
                with self.assertRaises(ReadApiError):
                    service.find("a")
                with self.assertRaises(ReadApiError):
                    service.read_batch(["vera://m11h-read/knowledge/read-alpha"] * 33)

    def test_i002_cli_keeps_find_and_read_separate(self) -> None:
        with TemporaryDirectory() as directory:
            profile = _initialize(Path(directory))
            status, boot = _cli(["boot", str(profile)])
            self.assertEqual(status, 0)
            self.assertTrue(boot["ok"])
            self.assertEqual(boot["boot"]["project_identity"]["project_id"], "m11h-read")

            status, found = _cli(["find", str(profile), "--query", "alpha", "--resource", "knowledge"])
            self.assertEqual(status, 0)
            self.assertEqual(found["find"][0]["address"], "vera://m11h-read/knowledge/read-alpha")
            self.assertNotIn("content", found["find"][0])

            status, read = _cli(["read", str(profile), "vera://m11h-read/knowledge/read-alpha"])

            self.assertEqual(status, 0)
            self.assertEqual(read["read"]["record"]["content"], "Le contenu secret de recherche alpha reste réservé à READ.")


class BootFindReadMCPTests(unittest.IsolatedAsyncioTestCase):
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

    async def test_i001_i002_i007_i008_i011_mcp_exposes_closed_boot_find_read_tools(self) -> None:
        with TemporaryDirectory() as directory:
            profile = _initialize(Path(directory))
            async with self._session(profile) as session:
                tools = {tool.name: tool for tool in (await session.list_tools()).tools}
                self.assertTrue({"mmu_boot", "mmu_find", "mmu_read", "mmu_read_batch"}.issubset(tools))
                self.assertEqual(set(tools["mmu_boot"].input_schema.get("properties", {})), set())
                self.assertNotIn("profile_path", tools["mmu_find"].input_schema.get("properties", {}))
                self.assertNotIn("project_id", tools["mmu_read"].input_schema.get("properties", {}))

                boot = self._payload(await session.call_tool("mmu_boot", {}))
                self.assertTrue(boot["ok"])
                self.assertEqual(boot["result"]["project_identity"]["project_id"], "m11h-read")
                found = self._payload(await session.call_tool("mmu_find", {"query": "alpha", "resource_types": ["knowledge"]}))
                self.assertTrue(found["ok"])
                self.assertEqual(found["result"]["findings"][0]["address"], "vera://m11h-read/knowledge/read-alpha")
                self.assertNotIn("content", found["result"]["findings"][0])
                read = self._payload(await session.call_tool("mmu_read", {"address": "vera://m11h-read/knowledge/read-alpha"}))
                self.assertTrue(read["ok"])
                self.assertEqual(read["result"]["record"]["content"], "Le contenu secret de recherche alpha reste réservé à READ.")


if __name__ == "__main__":
    unittest.main()
