from __future__ import annotations

from contextlib import asynccontextmanager, redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.__main__ import main
from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_SERVER = ROOT / "tests" / "m11c_mcp_fixture_server.py"


def _initialize(root: Path, project_id: str = "m11c-project") -> Path:
    root.mkdir(parents=True, exist_ok=True)
    preview = preview_project_initialization(
        root,
        template="documentation",
        project_id=project_id,
        project_name="M11-C Project",
    )
    apply_project_initialization(root, preview, confirm=True)
    return root / ".vera-mmu" / "project.yaml"


def _cli(arguments: list[str]) -> tuple[int, dict[str, object]]:
    output = StringIO()
    with redirect_stdout(output):
        status = main(arguments)
    return status, json.loads(output.getvalue())


class M11CPublicCliTests(unittest.TestCase):
    def test_i007_i010_i011_cli_exports_restores_and_imports_only_after_confirmation(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source_profile = _initialize(root / "source")
            (source_profile.parent.parent / "README.md").write_text("# M11-C source\n", encoding="utf-8")

            denied_status, denied = _cli(["bundle-export", str(source_profile), "--bundle-id", "snapshot-001"])
            self.assertEqual(denied_status, 2)
            self.assertFalse(denied["ok"])
            self.assertFalse((source_profile.parent / "bundles" / "snapshot-001.zip").exists())

            exported_status, exported = _cli(
                ["bundle-export", str(source_profile), "--bundle-id", "snapshot-001", "--confirm"]
            )
            self.assertEqual(exported_status, 0)
            self.assertTrue(exported["ok"])
            bundle = Path(str(exported["bundle"]["path"]))
            self.assertTrue(bundle.is_file())
            self.assertEqual(exported["bundle"]["bundle_id"], "snapshot-001")

            preview_status, preview = _cli(
                [
                    "project-import",
                    str(source_profile),
                    "--document",
                    "README.md",
                    "--batch-id",
                    "documents-001",
                    "--knowledge-type-id",
                    "project-document",
                    "--knowledge-type-label",
                    "Project document",
                ]
            )
            self.assertEqual(preview_status, 0)
            self.assertTrue(preview["ok"])
            self.assertEqual(preview["preview"]["documents"][0]["path"], "README.md")
            self.assertNotIn("content", preview["preview"]["documents"][0])

            imported_status, imported = _cli(
                [
                    "project-import",
                    str(source_profile),
                    "--document",
                    "README.md",
                    "--batch-id",
                    "documents-001",
                    "--knowledge-type-id",
                    "project-document",
                    "--knowledge-type-label",
                    "Project document",
                    "--apply",
                    "--confirm",
                ]
            )
            self.assertEqual(imported_status, 0)
            self.assertTrue(imported["ok"])
            self.assertEqual(imported["project_import"]["status"], "IMPORTED")
            self.assertEqual(imported["project_import"]["knowledge"][0]["status"], "OBSERVED")

            target_root = root / "target"
            shutil.copytree(
                source_profile.parent,
                target_root / ".vera-mmu",
                ignore=shutil.ignore_patterns("memory.sqlite", "memory.sqlite-wal", "memory.sqlite-shm", "artifacts", "bundles"),
            )
            target_profile = target_root / ".vera-mmu" / "project.yaml"
            restored_status, restored = _cli(
                ["bundle-restore", str(target_profile), "--bundle", str(bundle), "--confirm"]
            )
            self.assertEqual(restored_status, 0)
            self.assertTrue(restored["ok"])
            self.assertEqual(restored["bundle_restore"]["status"], "RESTORED")


class M11CPublicMCPTests(unittest.IsolatedAsyncioTestCase):
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

    async def test_i007_i008_i010_i011_mcp_exposes_bounded_bundle_and_project_import_contracts(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            profile = _initialize(root)
            (root / "README.md").write_text("# M11-C MCP\n", encoding="utf-8")
            async with self._session(profile) as session:
                tools = {tool.name: tool for tool in (await session.list_tools()).tools}
                self.assertTrue(
                    {
                        "mmu_export_bundle",
                        "mmu_preview_project_documents",
                        "mmu_import_project_documents",
                        "mmu_sync_memory",
                    }
                    <= set(tools)
                )
                self.assertEqual(set(tools["mmu_export_bundle"].input_schema.get("properties", {})), {"bundle_id", "confirm"})
                self.assertNotIn("path", tools["mmu_export_bundle"].input_schema.get("properties", {}))
                self.assertEqual(
                    set(tools["mmu_preview_project_documents"].input_schema.get("properties", {})),
                    {"batch_id", "documents", "knowledge_type_id", "knowledge_type_label"},
                )
                denied = self._payload(await session.call_tool("mmu_export_bundle", {"bundle_id": "snapshot-001", "confirm": False}))
                self.assertFalse(denied["ok"])
                exported = self._payload(await session.call_tool("mmu_export_bundle", {"bundle_id": "snapshot-001", "confirm": True}))
                self.assertTrue(exported["ok"])
                self.assertEqual(exported["result"]["bundle_id"], "snapshot-001")

                preview = self._payload(
                    await session.call_tool(
                        "mmu_preview_project_documents",
                        {
                            "documents": ["README.md"],
                            "batch_id": "documents-001",
                            "knowledge_type_id": "project-document",
                            "knowledge_type_label": "Project document",
                        },
                    )
                )
                self.assertTrue(preview["ok"])
                self.assertNotIn("content", preview["result"]["documents"][0])
                imported = self._payload(
                    await session.call_tool(
                        "mmu_import_project_documents",
                        {
                            "documents": ["README.md"],
                            "batch_id": "documents-001",
                            "knowledge_type_id": "project-document",
                            "knowledge_type_label": "Project document",
                            "preview_hash": preview["result"]["preview_hash"],
                            "confirm": True,
                        },
                    )
                )
                self.assertTrue(imported["ok"])
                self.assertEqual(imported["result"]["status"], "IMPORTED")
                self.assertEqual(imported["result"]["knowledge"][0]["status"], "OBSERVED")


if __name__ == "__main__":
    unittest.main()
