from __future__ import annotations

from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest

from vera_mmu.identity import load_profile
from vera_mmu.knowledge import KnowledgeService
from vera_mmu.provenance import KnowledgeSourceError, KnowledgeSourceNotFoundError, KnowledgeSourceService
from vera_mmu.store import MemoryStore


PROFILE = """\
mmu:
  version: "2.0"
project:
  id: "provenance-project"
  name: "Provenance Project"
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
SOURCE_HASH = "a" * 64


class KnowledgeSourceServiceTests(unittest.TestCase):
    """I001/I002/I003/I004/I011/I014/I015: provenance is declared, bounded, immutable and non-executing."""

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
    def _seed(knowledge: KnowledgeService) -> None:
        knowledge.register_type("observation", "Observation", actor="test-suite")
        knowledge.append("knowledge-001", "observation", "OBSERVED", "Observed", "The source records a fact.", actor="test-suite")

    def test_default_migrations_include_knowledge_sources(self) -> None:
        with self._open() as store:
            self.assertEqual(store.migration_checksums.keys(), {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22})
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 22})

    def test_existing_m2_4_store_migrates_to_knowledge_sources(self) -> None:
        schema = Path(self._directory.name) / "m2_4_schema"
        schema.mkdir()
        source_dir = Path(__file__).parents[1] / "src" / "vera_mmu" / "schema"
        for version in (
            "001_core_store.sql",
            "002_entity_registry.sql",
            "003_relation_registry.sql",
            "004_knowledge_registry.sql",
        ):
            shutil.copyfile(source_dir / version, schema / version)
        with MemoryStore.open(self._profile(), self.profile_path, schema_dir=schema) as m2_4_store:
            self.assertEqual(m2_4_store.metadata()["store_format"], {"schema_version": 4})
        shutil.copyfile(source_dir / "005_knowledge_sources.sql", schema / "005_knowledge_sources.sql")
        with MemoryStore.open(self._profile(), self.profile_path, schema_dir=schema) as store:
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 5})
            self.assertEqual(
                [event["action"] for event in store.audit_events()],
                ["STORE_INITIALIZED", "STORE_MIGRATED"],
            )

    def test_attach_and_read_exact_bounded_source(self) -> None:
        with self._open() as store:
            knowledge = KnowledgeService(store)
            sources = KnowledgeSourceService(store)
            self._seed(knowledge)
            attached = sources.attach(
                "source-001",
                "knowledge-001",
                repository="example/repository",
                revision="abc123",
                path="docs/guide.md",
                start_line=10,
                end_line=16,
                section="Introduction",
                source_hash=SOURCE_HASH,
                actor="test-suite",
            )
            self.assertEqual(sources.get("source-001"), attached)
            self.assertEqual(sources.list_for("knowledge-001"), (attached,))
            self.assertEqual(sources.list_for("knowledge-001", limit=1), (attached,))
            self.assertEqual(attached.source_path, "docs/guide.md")
            self.assertEqual(attached.source_start_line, 10)
            self.assertEqual(
                [event["action"] for event in store.audit_events()][-1],
                "KNOWLEDGE_SOURCE_ATTACHED",
            )

    def test_source_list_is_ordered_and_bounded(self) -> None:
        with self._open() as store:
            knowledge = KnowledgeService(store)
            sources = KnowledgeSourceService(store)
            self._seed(knowledge)
            sources.attach("source-b", "knowledge-001", repository="repo", revision="rev", path="docs/z.md", start_line=1, end_line=1, section="Z", source_hash="b" * 64)
            sources.attach("source-a", "knowledge-001", repository="repo", revision="rev", path="docs/a.md", start_line=3, end_line=3, section="A", source_hash="c" * 64)
            self.assertEqual([source.id for source in sources.list_for("knowledge-001", limit=1)], ["source-a"])
            self.assertEqual([source.id for source in sources.list_for("knowledge-001")], ["source-a", "source-b"])
            with self.assertRaises(KnowledgeSourceError):
                sources.list_for("knowledge-001", limit=0)

    def test_rejects_unknown_duplicate_and_unsafe_source_inputs(self) -> None:
        with self._open() as store:
            knowledge = KnowledgeService(store)
            sources = KnowledgeSourceService(store)
            self._seed(knowledge)
            arguments = dict(
                repository="repo",
                revision="rev",
                path="docs/file.md",
                start_line=1,
                end_line=2,
                section="Section",
                source_hash=SOURCE_HASH,
            )
            with self.assertRaises(KnowledgeSourceError):
                sources.attach("source-unknown", "missing", **arguments)
            attached = sources.attach("source-001", "knowledge-001", **arguments)
            with self.assertRaises(KnowledgeSourceError):
                sources.attach("source-002", "knowledge-001", **arguments)
            for unsafe_path in ("/etc/passwd", "../escape.md", "docs/../escape.md", "C:\\source.md", "docs\\source.md"):
                with self.assertRaises(KnowledgeSourceError):
                    sources.attach(f"source-{len(unsafe_path)}", "knowledge-001", **{**arguments, "path": unsafe_path})
            with self.assertRaises(KnowledgeSourceError):
                sources.attach("source-lines", "knowledge-001", **{**arguments, "start_line": 0})
            with self.assertRaises(KnowledgeSourceError):
                sources.attach("source-hash", "knowledge-001", **{**arguments, "source_hash": "not-a-hash"})
            self.assertEqual(sources.get("source-001"), attached)
            with self.assertRaises(KnowledgeSourceNotFoundError):
                sources.get("source-missing")

    def test_exact_read_rejects_inconsistent_source_reference(self) -> None:
        with self._open() as store:
            knowledge = KnowledgeService(store)
            sources = KnowledgeSourceService(store)
            self._seed(knowledge)
            store.connection.execute(
                "INSERT INTO knowledge_source(id, knowledge_id, source_repository, source_revision, source_path, source_start_line, source_end_line, source_section, source_hash, created_at, created_by) "
                "VALUES('source-tampered', 'knowledge-001', 'repo', 'rev', 'docs/file.md', 1, 2, 'Section', ?, '2026-01-01T00:00:00Z', 'test-suite')",
                ("z" * 64,),
            )
            with self.assertRaises(KnowledgeSourceError):
                sources.get("source-tampered")

    def test_database_rejects_source_rewrites_and_deletes(self) -> None:
        with self._open() as store:
            knowledge = KnowledgeService(store)
            sources = KnowledgeSourceService(store)
            self._seed(knowledge)
            sources.attach("source-001", "knowledge-001", repository="repo", revision="rev", path="docs/file.md", start_line=1, end_line=2, section="Section", source_hash=SOURCE_HASH)
            with self.assertRaises(sqlite3.DatabaseError):
                store.connection.execute("UPDATE knowledge_source SET source_path = 'docs/rewritten.md' WHERE id = 'source-001'")
            with self.assertRaises(sqlite3.DatabaseError):
                store.connection.execute("DELETE FROM knowledge_source WHERE id = 'source-001'")
            self.assertEqual(sources.get("source-001").source_path, "docs/file.md")

    def test_source_and_audit_rollback_together_when_audit_insert_fails(self) -> None:
        with self._open() as store:
            knowledge = KnowledgeService(store)
            sources = KnowledgeSourceService(store)
            self._seed(knowledge)
            store.connection.execute(
                "CREATE TRIGGER reject_source_audit BEFORE INSERT ON store_audit "
                "WHEN NEW.action = 'KNOWLEDGE_SOURCE_ATTACHED' "
                "BEGIN SELECT RAISE(ABORT, 'audit rejected'); END"
            )
            with self.assertRaises(KnowledgeSourceError):
                sources.attach("source-001", "knowledge-001", repository="repo", revision="rev", path="docs/file.md", start_line=1, end_line=2, section="Section", source_hash=SOURCE_HASH)
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM knowledge_source").fetchone()[0], 0)
            self.assertNotIn("KNOWLEDGE_SOURCE_ATTACHED", [event["action"] for event in store.audit_events()])


if __name__ == "__main__":
    unittest.main()
