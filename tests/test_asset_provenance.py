from __future__ import annotations

from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest

from vera_mmu.assets import AssetService
from vera_mmu.asset_provenance import AssetSourceError, AssetSourceNotFoundError, AssetSourceService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore


PROFILE = """\
mmu:
  version: "2.0"
project:
  id: "asset-source-project"
  name: "Asset Source Project"
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
"""

SOURCE_HASH_A = "a" * 64
SOURCE_HASH_B = "b" * 64


class AssetSourceServiceTests(unittest.TestCase):
    """I001/I002/I004/I005/I011/I014/I015: asset provenance stays immutable, declarative and non-probative."""

    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._directory.cleanup)
        self.runtime = Path(self._directory.name) / "project" / ".vera-mmu"
        self.runtime.mkdir(parents=True)
        self.profile_path = self.runtime / "project.yaml"
        self.profile_path.write_text(PROFILE, encoding="utf-8")

    def _profile(self) -> dict[str, object]:
        return load_profile(self.profile_path)

    def _open(self) -> MemoryStore:
        return MemoryStore.open(self._profile(), self.profile_path)

    @staticmethod
    def _seed(assets: AssetService) -> None:
        assets.record("asset-001", b"asset one", media_type="text/plain", actor="test-suite")
        assets.record("asset-002", b"asset two", media_type="text/plain", actor="test-suite")

    @staticmethod
    def _attach(service: AssetSourceService, identifier: str, *, path: str = "docs/source.md", start_line: int = 1, source_hash: str = SOURCE_HASH_A):
        return service.attach(
            identifier,
            "asset-001",
            repository="documentation",
            revision="commit-001",
            path=path,
            start_line=start_line,
            end_line=start_line + 2,
            section="Declared source",
            source_hash=source_hash,
            actor="test-suite",
        )

    def test_default_migrations_include_asset_source_registry(self) -> None:
        with self._open() as store:
            self.assertEqual(store.migration_checksums.keys(), {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17})
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 17})

    def test_existing_m2_9_store_migrates_to_asset_source_registry(self) -> None:
        schema = Path(self._directory.name) / "m2_9_schema"
        schema.mkdir()
        source_dir = Path(__file__).parents[1] / "src" / "vera_mmu" / "schema"
        for version in (
            "001_core_store.sql",
            "002_entity_registry.sql",
            "003_relation_registry.sql",
            "004_knowledge_registry.sql",
            "005_knowledge_sources.sql",
            "006_knowledge_supersession.sql",
            "007_asset_registry.sql",
            "008_knowledge_asset_links.sql",
            "009_knowledge_asset_link_indexes.sql",
        ):
            shutil.copyfile(source_dir / version, schema / version)
        with MemoryStore.open(self._profile(), self.profile_path, schema_dir=schema) as m2_9_store:
            self.assertEqual(m2_9_store.metadata()["store_format"], {"schema_version": 9})
        shutil.copyfile(source_dir / "010_asset_sources.sql", schema / "010_asset_sources.sql")
        with MemoryStore.open(self._profile(), self.profile_path, schema_dir=schema) as store:
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 10})
            self.assertEqual([event["action"] for event in store.audit_events()], ["STORE_INITIALIZED", "STORE_MIGRATED"])

    def test_attach_get_and_list_declared_sources_without_reading_or_changing_asset(self) -> None:
        with self._open() as store:
            assets = AssetService(store)
            sources = AssetSourceService(store)
            self._seed(assets)
            before_asset = assets.get("asset-001")
            attached = self._attach(sources, "asset-source-002", path="docs/z.md", start_line=7)
            earlier = self._attach(sources, "asset-source-001", path="docs/a.md", start_line=2, source_hash=SOURCE_HASH_B)
            self.assertEqual(sources.get("asset-source-002"), attached)
            self.assertEqual(sources.list_for("asset-001"), (earlier, attached))
            self.assertTrue(all(not hasattr(source, "content") for source in sources.list_for("asset-001")))
            self.assertEqual(assets.get("asset-001"), before_asset)
            self.assertEqual(store.audit_events()[-1]["action"], "ASSET_SOURCE_ATTACHED")

    def test_rejects_unknown_asset_invalid_data_duplicate_identifier_and_duplicate_slice(self) -> None:
        with self._open() as store:
            assets = AssetService(store)
            sources = AssetSourceService(store)
            self._seed(assets)
            with self.assertRaises(AssetSourceError):
                sources.attach(
                    "asset-source-missing",
                    "missing",
                    repository="documentation",
                    revision="commit-001",
                    path="docs/source.md",
                    start_line=1,
                    end_line=3,
                    section="Declared source",
                    source_hash=SOURCE_HASH_A,
                )
            invalid_calls = (
                lambda: self._attach(sources, "../bad"),
                lambda: sources.attach("asset-source-absolute", "asset-001", repository="documentation", revision="commit-001", path="/absolute.md", start_line=1, end_line=3, section="Declared source", source_hash=SOURCE_HASH_A),
                lambda: sources.attach("asset-source-traversal", "asset-001", repository="documentation", revision="commit-001", path="docs/../source.md", start_line=1, end_line=3, section="Declared source", source_hash=SOURCE_HASH_A),
                lambda: sources.attach("asset-source-lines", "asset-001", repository="documentation", revision="commit-001", path="docs/source.md", start_line=4, end_line=3, section="Declared source", source_hash=SOURCE_HASH_A),
                lambda: sources.attach("asset-source-hash", "asset-001", repository="documentation", revision="commit-001", path="docs/source.md", start_line=1, end_line=3, section="Declared source", source_hash="not-a-hash"),
            )
            for call in invalid_calls:
                with self.assertRaises(AssetSourceError):
                    call()
            self._attach(sources, "asset-source-001")
            with self.assertRaises(AssetSourceError):
                self._attach(sources, "asset-source-001", path="docs/other.md", source_hash=SOURCE_HASH_B)
            with self.assertRaises(AssetSourceError):
                self._attach(sources, "asset-source-duplicate")
            with self.assertRaises(AssetSourceNotFoundError):
                sources.get("asset-source-missing")
            with self.assertRaises(AssetSourceError):
                sources.list_for("missing")

    def test_database_rejects_asset_source_rewrites_and_deletes(self) -> None:
        with self._open() as store:
            assets = AssetService(store)
            sources = AssetSourceService(store)
            self._seed(assets)
            self._attach(sources, "asset-source-001")
            with self.assertRaises(sqlite3.DatabaseError):
                store.connection.execute("UPDATE asset_source SET source_path = 'docs/changed.md' WHERE id = 'asset-source-001'")
            with self.assertRaises(sqlite3.DatabaseError):
                store.connection.execute("DELETE FROM asset_source WHERE id = 'asset-source-001'")
            self.assertEqual(sources.get("asset-source-001").source_path, "docs/source.md")

    def test_attach_and_audit_rollback_together_when_audit_insert_fails(self) -> None:
        with self._open() as store:
            assets = AssetService(store)
            sources = AssetSourceService(store)
            self._seed(assets)
            store.connection.execute(
                "CREATE TRIGGER reject_asset_source_audit BEFORE INSERT ON store_audit "
                "WHEN NEW.action = 'ASSET_SOURCE_ATTACHED' "
                "BEGIN SELECT RAISE(ABORT, 'audit rejected'); END"
            )
            with self.assertRaises(AssetSourceError):
                self._attach(sources, "asset-source-001")
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM asset_source").fetchone()[0], 0)
            self.assertNotIn("ASSET_SOURCE_ATTACHED", [event["action"] for event in store.audit_events()])


if __name__ == "__main__":
    unittest.main()
