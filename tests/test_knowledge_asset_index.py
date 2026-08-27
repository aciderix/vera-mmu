from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import unittest

from vera_mmu.assets import AssetService
from vera_mmu.identity import load_profile
from vera_mmu.knowledge import KnowledgeService
from vera_mmu.knowledge_assets import (
    KnowledgeAssetLinkError,
    KnowledgeAssetLinkService,
    MAX_KNOWLEDGE_ASSET_LINK_INDEX_LIMIT,
)
from vera_mmu.store import MemoryStore


PROFILE = """\
mmu:
  version: "2.0"
project:
  id: "knowledge-asset-index-project"
  name: "Knowledge Asset Index Project"
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


class KnowledgeAssetIndexTests(unittest.TestCase):
    """I001/I002/I003/I004/I005/I011/I014/I015: association discovery is exact, bounded and content-free."""

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
    def _seed(knowledge: KnowledgeService, assets: AssetService, links: KnowledgeAssetLinkService) -> None:
        knowledge.register_type("observation", "Observation", actor="test-suite")
        for index in range(1, 4):
            knowledge.append(
                f"knowledge-{index:03d}",
                "observation",
                "OBSERVED",
                f"Observation {index}",
                f"Assertion content {index} remains unread by the index.",
                actor="test-suite",
            )
            assets.record(
                f"asset-{index:03d}",
                f"asset bytes {index}".encode("utf-8"),
                media_type="text/plain",
                actor="test-suite",
            )
        links.link("knowledge-001", "asset-003", actor="test-suite")
        links.link("knowledge-001", "asset-001", actor="test-suite")
        links.link("knowledge-001", "asset-002", actor="test-suite")
        assets.record("asset-004", b"unlinked asset bytes", media_type="text/plain", actor="test-suite")
        links.link("knowledge-003", "asset-001", actor="test-suite")
        links.link("knowledge-002", "asset-001", actor="test-suite")

    def test_default_migrations_include_knowledge_asset_index(self) -> None:
        with self._open() as store:
            self.assertEqual(store.migration_checksums.keys(), set(range(1, 40)))
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 39})
            index_names = {row[1] for row in store.connection.execute("PRAGMA index_list('knowledge_asset_link')").fetchall()}
            self.assertIn("idx_knowledge_asset_link_asset_knowledge", index_names)

    def test_existing_m2_8_store_migrates_to_knowledge_asset_index(self) -> None:
        schema = Path(self._directory.name) / "m2_8_schema"
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
        ):
            shutil.copyfile(source_dir / version, schema / version)
        with MemoryStore.open(self._profile(), self.profile_path, schema_dir=schema) as m2_8_store:
            self.assertEqual(m2_8_store.metadata()["store_format"], {"schema_version": 8})
        shutil.copyfile(source_dir / "009_knowledge_asset_link_indexes.sql", schema / "009_knowledge_asset_link_indexes.sql")
        with MemoryStore.open(self._profile(), self.profile_path, schema_dir=schema) as store:
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 9})
            self.assertEqual(
                [event["action"] for event in store.audit_events()],
                ["STORE_INITIALIZED", "STORE_MIGRATED"],
            )

    def test_lists_exact_endpoint_links_in_deterministic_order_without_endpoint_content(self) -> None:
        with self._open() as store:
            knowledge = KnowledgeService(store)
            assets = AssetService(store)
            links = KnowledgeAssetLinkService(store)
            self._seed(knowledge, assets, links)
            knowledge_before = knowledge.get("knowledge-001")
            asset_before = assets.get("asset-001")
            by_knowledge = links.list_for_knowledge("knowledge-001")
            by_asset = links.list_for_asset("asset-001")
            self.assertEqual([link.asset_id for link in by_knowledge], ["asset-001", "asset-002", "asset-003"])
            self.assertEqual([link.knowledge_id for link in by_asset], ["knowledge-001", "knowledge-002", "knowledge-003"])
            self.assertTrue(all(not hasattr(link, "content") for link in by_knowledge + by_asset))
            self.assertEqual(knowledge.get("knowledge-001"), knowledge_before)
            self.assertEqual(assets.get("asset-001"), asset_before)

    def test_lists_are_bounded_and_existing_unlinked_endpoint_returns_empty(self) -> None:
        with self._open() as store:
            knowledge = KnowledgeService(store)
            assets = AssetService(store)
            links = KnowledgeAssetLinkService(store)
            self._seed(knowledge, assets, links)
            self.assertEqual([link.asset_id for link in links.list_for_knowledge("knowledge-001", limit=2)], ["asset-001", "asset-002"])
            self.assertEqual([link.knowledge_id for link in links.list_for_asset("asset-001", limit=1)], ["knowledge-001"])
            self.assertEqual(links.list_for_asset("asset-004"), ())
            self.assertEqual(links.list_for_asset("asset-002"), (links.get("knowledge-001", "asset-002"),))

    def test_rejects_unknown_or_invalid_endpoint_and_invalid_limit(self) -> None:
        with self._open() as store:
            knowledge = KnowledgeService(store)
            assets = AssetService(store)
            links = KnowledgeAssetLinkService(store)
            self._seed(knowledge, assets, links)
            for invalid in (0, -1, True, "1", MAX_KNOWLEDGE_ASSET_LINK_INDEX_LIMIT + 1):
                with self.assertRaises(KnowledgeAssetLinkError):
                    links.list_for_knowledge("knowledge-001", limit=invalid)  # type: ignore[arg-type]
            with self.assertRaises(KnowledgeAssetLinkError):
                links.list_for_knowledge("missing")
            with self.assertRaises(KnowledgeAssetLinkError):
                links.list_for_asset("missing")
            with self.assertRaises(KnowledgeAssetLinkError):
                links.list_for_knowledge("knowledge-001/escape")
            with self.assertRaises(KnowledgeAssetLinkError):
                links.list_for_asset("asset-001/escape")


if __name__ == "__main__":
    unittest.main()
