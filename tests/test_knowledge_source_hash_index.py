from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import unittest

from vera_mmu.knowledge import KnowledgeService
from vera_mmu.provenance import KnowledgeSourceError, KnowledgeSourceService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore


PROFILE = """\
mmu:
  version: "2.0"
project:
  id: "knowledge-source-index-project"
  name: "Knowledge Source Index Project"
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

SOURCE_HASH_SHARED = "a" * 64
SOURCE_HASH_OTHER = "b" * 64
SOURCE_HASH_UNKNOWN = "d" * 64


class KnowledgeSourceHashIndexTests(unittest.TestCase):
    """I001/I002/I004/I011/I014/I015: source-hash indexing returns declared metadata only, never knowledge content."""

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
    def _seed(knowledge: KnowledgeService, sources: KnowledgeSourceService) -> None:
        knowledge.register_type("note", "Note", actor="test-suite")
        knowledge.append("knowledge-002", "note", "ACTIVE", "Second", "second canonical knowledge", actor="test-suite")
        knowledge.append("knowledge-001", "note", "ACTIVE", "First", "first canonical knowledge", actor="test-suite")
        knowledge.append("knowledge-003", "note", "ACTIVE", "Third", "third canonical knowledge", actor="test-suite")
        sources.attach(
            "source-002",
            "knowledge-002",
            repository="documentation",
            revision="commit-001",
            path="docs/z.md",
            start_line=9,
            end_line=11,
            section="Shared source",
            source_hash=SOURCE_HASH_SHARED,
            actor="test-suite",
        )
        sources.attach(
            "source-001",
            "knowledge-001",
            repository="documentation",
            revision="commit-001",
            path="docs/a.md",
            start_line=2,
            end_line=4,
            section="Shared source",
            source_hash=SOURCE_HASH_SHARED,
            actor="test-suite",
        )
        sources.attach(
            "source-003",
            "knowledge-003",
            repository="documentation",
            revision="commit-001",
            path="docs/other.md",
            start_line=1,
            end_line=1,
            section="Other source",
            source_hash=SOURCE_HASH_OTHER,
            actor="test-suite",
        )

    def test_default_migrations_include_knowledge_source_hash_index(self) -> None:
        with self._open() as store:
            self.assertEqual(store.migration_checksums.keys(), {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17})
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 17})
            index_names = {row[1] for row in store.connection.execute("PRAGMA index_list('knowledge_source')").fetchall()}
            self.assertIn("idx_knowledge_source_hash_knowledge", index_names)

    def test_existing_m2_10_store_migrates_to_knowledge_source_hash_index(self) -> None:
        schema = Path(self._directory.name) / "m2_10_schema"
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
            "010_asset_sources.sql",
        ):
            shutil.copyfile(source_dir / version, schema / version)
        with MemoryStore.open(self._profile(), self.profile_path, schema_dir=schema) as m2_10_store:
            self.assertEqual(m2_10_store.metadata()["store_format"], {"schema_version": 10})
        shutil.copyfile(source_dir / "011_knowledge_source_hash_indexes.sql", schema / "011_knowledge_source_hash_indexes.sql")
        with MemoryStore.open(self._profile(), self.profile_path, schema_dir=schema) as store:
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 11})
            self.assertEqual([event["action"] for event in store.audit_events()], ["STORE_INITIALIZED", "STORE_MIGRATED"])

    def test_exact_hash_index_returns_ordered_sources_without_knowledge_content_or_audit(self) -> None:
        with self._open() as store:
            knowledge = KnowledgeService(store)
            sources = KnowledgeSourceService(store)
            self._seed(knowledge, sources)
            audit_before = store.audit_events()
            matches = sources.list_by_source_hash(SOURCE_HASH_SHARED)
            self.assertEqual(tuple(source.id for source in matches), ("source-001", "source-002"))
            self.assertEqual(tuple(source.knowledge_id for source in matches), ("knowledge-001", "knowledge-002"))
            self.assertTrue(all(source.source_hash == SOURCE_HASH_SHARED for source in matches))
            self.assertTrue(all(not hasattr(source, "content") for source in matches))
            self.assertEqual(sources.list_by_source_hash(SOURCE_HASH_OTHER), (sources.get("source-003"),))
            self.assertEqual(store.audit_events(), audit_before)

    def test_exact_hash_index_enforces_limit_and_empty_results(self) -> None:
        with self._open() as store:
            knowledge = KnowledgeService(store)
            sources = KnowledgeSourceService(store)
            self._seed(knowledge, sources)
            self.assertEqual(tuple(source.id for source in sources.list_by_source_hash(SOURCE_HASH_SHARED, limit=1)), ("source-001",))
            self.assertEqual(sources.list_by_source_hash(SOURCE_HASH_UNKNOWN), ())
            for invalid_hash in ("", "A" * 64, SOURCE_HASH_SHARED[:63], SOURCE_HASH_SHARED + "0", "prefix-" + SOURCE_HASH_SHARED[:57]):
                with self.assertRaises(KnowledgeSourceError):
                    sources.list_by_source_hash(invalid_hash)
            for invalid_limit in (0, 101, True, "1"):
                with self.assertRaises(KnowledgeSourceError):
                    sources.list_by_source_hash(SOURCE_HASH_SHARED, limit=invalid_limit)


if __name__ == "__main__":
    unittest.main()
