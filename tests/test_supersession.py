from __future__ import annotations

from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest

from vera_mmu.identity import load_profile
from vera_mmu.knowledge import KnowledgeService
from vera_mmu.store import MemoryStore
from vera_mmu.supersession import (
    KnowledgeSupersessionError,
    KnowledgeSupersessionNotFoundError,
    KnowledgeSupersessionService,
)


PROFILE = """\
mmu:
  version: "2.0"
project:
  id: "supersession-project"
  name: "Supersession Project"
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


class KnowledgeSupersessionServiceTests(unittest.TestCase):
    """I001/I002/I003/I004/I011/I014/I015: replacement links are immutable, direct and acyclic."""

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
        for index in range(1, 4):
            knowledge.append(
                f"knowledge-{index:03d}",
                "observation",
                "OBSERVED",
                f"Observation {index}",
                f"Observed content {index}.",
                actor="test-suite",
            )

    def test_default_migrations_include_knowledge_supersession(self) -> None:
        with self._open() as store:
            self.assertEqual(store.migration_checksums.keys(), {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12})
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 12})

    def test_existing_m2_5_store_migrates_to_knowledge_supersession(self) -> None:
        schema = Path(self._directory.name) / "m2_5_schema"
        schema.mkdir()
        source_dir = Path(__file__).parents[1] / "src" / "vera_mmu" / "schema"
        for version in (
            "001_core_store.sql",
            "002_entity_registry.sql",
            "003_relation_registry.sql",
            "004_knowledge_registry.sql",
            "005_knowledge_sources.sql",
        ):
            shutil.copyfile(source_dir / version, schema / version)
        with MemoryStore.open(self._profile(), self.profile_path, schema_dir=schema) as m2_5_store:
            self.assertEqual(m2_5_store.metadata()["store_format"], {"schema_version": 5})
        shutil.copyfile(source_dir / "006_knowledge_supersession.sql", schema / "006_knowledge_supersession.sql")
        with MemoryStore.open(self._profile(), self.profile_path, schema_dir=schema) as store:
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 6})
            self.assertEqual(
                [event["action"] for event in store.audit_events()],
                ["STORE_INITIALIZED", "STORE_MIGRATED"],
            )

    def test_create_and_read_direct_supersession_without_mutating_knowledge(self) -> None:
        with self._open() as store:
            knowledge = KnowledgeService(store)
            supersession = KnowledgeSupersessionService(store)
            self._seed(knowledge)
            created = supersession.supersede("knowledge-001", "knowledge-002", actor="test-suite")
            self.assertEqual(supersession.successor_of("knowledge-001"), created)
            self.assertEqual(supersession.predecessor_of("knowledge-002"), created)
            self.assertEqual(knowledge.get("knowledge-001").status, "OBSERVED")
            self.assertEqual(knowledge.get("knowledge-002").status, "OBSERVED")
            self.assertEqual(store.audit_events()[-1]["action"], "KNOWLEDGE_SUPERSESSION_RECORDED")

    def test_rejects_unknown_self_duplicate_predecessor_and_duplicate_successor(self) -> None:
        with self._open() as store:
            knowledge = KnowledgeService(store)
            supersession = KnowledgeSupersessionService(store)
            self._seed(knowledge)
            with self.assertRaises(KnowledgeSupersessionError):
                supersession.supersede("missing", "knowledge-001")
            with self.assertRaises(KnowledgeSupersessionError):
                supersession.supersede("knowledge-001", "missing")
            with self.assertRaises(KnowledgeSupersessionError):
                supersession.supersede("knowledge-001", "knowledge-001")
            created = supersession.supersede("knowledge-001", "knowledge-002")
            with self.assertRaises(KnowledgeSupersessionError):
                supersession.supersede("knowledge-001", "knowledge-003")
            with self.assertRaises(KnowledgeSupersessionError):
                supersession.supersede("knowledge-003", "knowledge-002")
            self.assertEqual(supersession.successor_of("knowledge-001"), created)
            with self.assertRaises(KnowledgeSupersessionNotFoundError):
                supersession.successor_of("knowledge-003")
            with self.assertRaises(KnowledgeSupersessionNotFoundError):
                supersession.predecessor_of("knowledge-001")

    def test_rejects_cycle_before_write(self) -> None:
        with self._open() as store:
            knowledge = KnowledgeService(store)
            supersession = KnowledgeSupersessionService(store)
            self._seed(knowledge)
            supersession.supersede("knowledge-001", "knowledge-002")
            supersession.supersede("knowledge-002", "knowledge-003")
            with self.assertRaises(KnowledgeSupersessionError):
                supersession.supersede("knowledge-003", "knowledge-001")
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM knowledge_supersession").fetchone()[0], 2)

    def test_database_rejects_supersession_rewrites_and_deletes(self) -> None:
        with self._open() as store:
            knowledge = KnowledgeService(store)
            supersession = KnowledgeSupersessionService(store)
            self._seed(knowledge)
            supersession.supersede("knowledge-001", "knowledge-002")
            with self.assertRaises(sqlite3.DatabaseError):
                store.connection.execute(
                    "UPDATE knowledge_supersession SET successor_id = 'knowledge-003' WHERE predecessor_id = 'knowledge-001'"
                )
            with self.assertRaises(sqlite3.DatabaseError):
                store.connection.execute("DELETE FROM knowledge_supersession WHERE predecessor_id = 'knowledge-001'")
            self.assertEqual(supersession.successor_of("knowledge-001").successor_id, "knowledge-002")

    def test_supersession_and_audit_rollback_together_when_audit_insert_fails(self) -> None:
        with self._open() as store:
            knowledge = KnowledgeService(store)
            supersession = KnowledgeSupersessionService(store)
            self._seed(knowledge)
            store.connection.execute(
                "CREATE TRIGGER reject_supersession_audit BEFORE INSERT ON store_audit "
                "WHEN NEW.action = 'KNOWLEDGE_SUPERSESSION_RECORDED' "
                "BEGIN SELECT RAISE(ABORT, 'audit rejected'); END"
            )
            with self.assertRaises(KnowledgeSupersessionError):
                supersession.supersede("knowledge-001", "knowledge-002")
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM knowledge_supersession").fetchone()[0], 0)
            self.assertNotIn("KNOWLEDGE_SUPERSESSION_RECORDED", [event["action"] for event in store.audit_events()])


if __name__ == "__main__":
    unittest.main()
