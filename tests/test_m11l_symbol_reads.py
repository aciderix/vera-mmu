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
from vera_mmu.store import MemoryStore
from vera_mmu.symbols import SymbolService


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_SERVER = ROOT / "tests" / "m11c_mcp_fixture_server.py"


PROFILE = '''
mmu:
  version: "2.0"
project:
  id: "m11l-symbol"
  name: "M11-L Symbol"
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


class SymbolReadTests(unittest.TestCase):
    def _store(self, root: Path) -> MemoryStore:
        runtime = root / ".vera-mmu"
        runtime.mkdir()
        profile = runtime / "project.yaml"
        profile.write_text(PROFILE, encoding="utf-8")
        return MemoryStore.open(load_profile(profile), profile)

    def test_i001_i002_i011_read_exact_symbol_is_project_bound_non_mutating_and_preserves_metadata(self) -> None:
        from vera_mmu.read_api import ReadApiError, ReadService

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                EntityService(store).register_type_and_create_batch(
                    "module", "Module", [EntityCreateInput("owner", "Owner")]
                )
                SymbolService(store).create(
                    "symbol-1", "owner", "FUNCTION", "src/module.py", "entry",
                    signature="() -> int", metadata={"language": "python", "public": True}, actor="author",
                )
                audits = store.audit_events()
                result = ReadService(store).read("vera://m11l-symbol/symbol/symbol-1")
                self.assertEqual(result["address"], "vera://m11l-symbol/symbol/symbol-1")
                self.assertEqual(result["resource_type"], "symbol")
                self.assertEqual(result["record"], {
                    "id": "symbol-1", "entity_id": "owner", "kind": "FUNCTION", "path": "src/module.py",
                    "identifier": "entry", "signature": "() -> int", "metadata": {"language": "python", "public": True},
                    "created_at": result["record"]["created_at"], "created_by": "author",
                    "address": "vera://m11l-symbol/symbol/symbol-1",
                })
                self.assertEqual(store.audit_events(), audits)
                self.assertEqual(ReadService(store).find("entry"), [])
                with self.assertRaises(ReadApiError):
                    ReadService(store).read("vera://other/symbol/symbol-1")
                with self.assertRaises(ReadApiError):
                    ReadService(store).read("vera://m11l-symbol/symbol/missing")

    def test_i001_i002_cli_reads_an_exact_symbol_only_by_address(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / ".vera-mmu"
            runtime.mkdir()
            profile = runtime / "project.yaml"
            profile.write_text(PROFILE, encoding="utf-8")
            with MemoryStore.open(load_profile(profile), profile) as store:
                EntityService(store).register_type_and_create_batch("module", "Module", [EntityCreateInput("owner", "Owner")])
                SymbolService(store).create("symbol-cli", "owner", "FUNCTION", "src/cli.py", "main")
            output = StringIO()
            with redirect_stdout(output):
                status = main(["read", str(profile), "vera://m11l-symbol/symbol/symbol-cli"])
            payload = json.loads(output.getvalue())
            self.assertEqual(status, 0)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["read"]["resource_type"], "symbol")
            self.assertEqual(payload["read"]["record"]["identifier"], "main")


class SymbolReadMCPTests(unittest.IsolatedAsyncioTestCase):
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

    async def test_i001_i002_i007_i011_mcp_read_returns_exact_symbol_with_closed_input(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / ".vera-mmu"
            runtime.mkdir()
            profile = runtime / "project.yaml"
            profile.write_text(PROFILE, encoding="utf-8")
            with MemoryStore.open(load_profile(profile), profile) as store:
                EntityService(store).register_type_and_create_batch("module", "Module", [EntityCreateInput("owner", "Owner")])
                SymbolService(store).create("symbol-mcp", "owner", "FUNCTION", "src/mcp.py", "mcp_main")
            async with self._session(profile) as session:
                tools = {tool.name: tool for tool in (await session.list_tools()).tools}
                self.assertEqual(set(tools["mmu_read"].input_schema.get("properties", {})), {"address"})
                response = await session.call_tool("mmu_read", {"address": "vera://m11l-symbol/symbol/symbol-mcp"})
                payload = response.structured_content
                self.assertIsInstance(payload, dict)
                self.assertTrue(payload["ok"])
                self.assertEqual(payload["result"]["resource_type"], "symbol")
                self.assertEqual(payload["result"]["record"]["identifier"], "mcp_main")


if __name__ == "__main__":
    unittest.main()
