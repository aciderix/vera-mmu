from __future__ import annotations

from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest

from vera_mmu.assets import AssetService
from vera_mmu.identity import load_profile
from vera_mmu.knowledge import KnowledgeService
from vera_mmu.knowledge_assets import (
    KnowledgeAssetLinkError,
    KnowledgeAssetLinkNotFoundError,
    KnowledgeAssetLinkService,
)
from vera_mmu.store import MemoryStore


PROFILE = """\
mmu:
  version: "2.0"
project:
  id: "knowledge-asset-project"
  name: "Knowledge Asset Project"
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


class KnowledgeAssetLinkServiceTests(unittest.TestCase):
    """I001/I002/I003/I004/I005/I011/I014/I015: immutable links are declarative, exact and non-probative."""

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
    def _seed(knowledge: KnowledgeService, assets: AssetService) -> None:
        knowledge.register_type("observation", "Observation", actor="test-suite")
        knowledge.append(
            "knowledge-001",
            "observation",
            "OBSERVED",
            "Observed source",
            "The content is associated declaratively only.",
            actor="test-suite",
        )
        knowledge.append(
            "knowledge-002",
            "observation",
            "OBSERVED",
            "Second observation",
            "Second assertion remains independent.",
            actor="test-suite",
        )
        assets.record("asset-001", b"asset-one", media_type="text/plain", actor="test-suite")
        assets.record("asset-002", b"asset-two", media_type="text/plain", actor="test-suite")

    def test_default_migrations_include_knowledge_asset_links(self) -> None:
        with self._open() as store:
            self.assertEqual(store.migration_checksums.keys(), {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20})
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 20})

    def test_existing_m2_7_store_migrates_to_knowledge_asset_links(self) -> None:
        schema = Path(self._directory.name) / "m2_7_schema"
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
        ):
            shutil.copyfile(source_dir / version, schema / version)
        with MemoryStore.open(self._profile(), self.profile_path, schema_dir=schema) as m2_7_store:
            self.assertEqual(m2_7_store.metadata()["store_format"], {"schema_version": 7})
        shutil.copyfile(source_dir / "008_knowledge_asset_links.sql", schema / "008_knowledge_asset_links.sql")
        with MemoryStore.open(self._profile(), self.profile_path, schema_dir=schema) as store:
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 8})
            self.assertEqual(
                [event["action"] for event in store.audit_events()],
                ["STORE_INITIALIZED", "STORE_MIGRATED"],
            )

    def test_link_and_read_exact_pair_without_mutating_knowledge_or_asset(self) -> None:
        with self._open() as store:
            knowledge = KnowledgeService(store)
            assets = AssetService(store)
            links = KnowledgeAssetLinkService(store)
            self._seed(knowledge, assets)
            before_knowledge = knowledge.get("knowledge-001")
            before_asset = assets.get("asset-001")
            linked = links.link("knowledge-001", "asset-001", actor="test-suite")
            self.assertEqual(links.get("knowledge-001", "asset-001"), linked)
            self.assertEqual(linked.knowledge_id, "knowledge-001")
            self.assertEqual(linked.asset_id, "asset-001")
            self.assertEqual(knowledge.get("knowledge-001"), before_knowledge)
            self.assertEqual(assets.get("asset-001"), before_asset)
            self.assertEqual(store.audit_events()[-1]["action"], "KNOWLEDGE_ASSET_LINK_RECORDED")

    def test_rejects_unknown_invalid_and_duplicate_endpoints(self) -> None:
        with self._open() as store:
            knowledge = KnowledgeService(store)
            assets = AssetService(store)
            links = KnowledgeAssetLinkService(store)
            self._seed(knowledge, assets)
            with self.assertRaises(KnowledgeAssetLinkError):
                links.link("missing", "asset-001")
            with self.assertRaises(KnowledgeAssetLinkError):
                links.link("knowledge-001", "missing")
            with self.assertRaises(KnowledgeAssetLinkError):
                links.link("../escape", "asset-001")
            with self.assertRaises(KnowledgeAssetLinkError):
                links.link("knowledge-001", "../escape")
            linked = links.link("knowledge-001", "asset-001")
            with self.assertRaises(KnowledgeAssetLinkError):
                links.link("knowledge-001", "asset-001")
            self.assertEqual(links.get("knowledge-001", "asset-001"), linked)
            with self.assertRaises(KnowledgeAssetLinkNotFoundError):
                links.get("knowledge-001", "asset-002")

    def test_database_rejects_link_rewrites_and_deletes(self) -> None:
        with self._open() as store:
            knowledge = KnowledgeService(store)
            assets = AssetService(store)
            links = KnowledgeAssetLinkService(store)
            self._seed(knowledge, assets)
            links.link("knowledge-001", "asset-001")
            with self.assertRaises(sqlite3.DatabaseError):
                store.connection.execute(
                    "UPDATE knowledge_asset_link SET asset_id = 'asset-002' WHERE knowledge_id = 'knowledge-001'"
                )
            with self.assertRaises(sqlite3.DatabaseError):
                store.connection.execute(
                    "DELETE FROM knowledge_asset_link WHERE knowledge_id = 'knowledge-001'"
                )
            self.assertEqual(links.get("knowledge-001", "asset-001").asset_id, "asset-001")

    def test_link_and_audit_rollback_together_when_audit_insert_fails(self) -> None:
        with self._open() as store:
            knowledge = KnowledgeService(store)
            assets = AssetService(store)
            links = KnowledgeAssetLinkService(store)
            self._seed(knowledge, assets)
            store.connection.execute(
                "CREATE TRIGGER reject_knowledge_asset_link_audit BEFORE INSERT ON store_audit "
                "WHEN NEW.action = 'KNOWLEDGE_ASSET_LINK_RECORDED' "
                "BEGIN SELECT RAISE(ABORT, 'audit rejected'); END"
            )
            with self.assertRaises(KnowledgeAssetLinkError):
                links.link("knowledge-001", "asset-001")
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM knowledge_asset_link").fetchone()[0], 0)
            self.assertNotIn("KNOWLEDGE_ASSET_LINK_RECORDED", [event["action"] for event in store.audit_events()])


if __name__ == "__main__":
    unittest.main()
