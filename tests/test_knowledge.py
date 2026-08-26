from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest

from vera_mmu.identity import load_profile
from vera_mmu.knowledge import (
    KnowledgeAdmissionError,
    KnowledgeError,
    KnowledgeNotFoundError,
    KnowledgeService,
)
from vera_mmu.store import MemoryStore


PROFILE = """\
mmu:
  version: "2.0"
project:
  id: "knowledge-project"
  name: "Knowledge Project"
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


class KnowledgeServiceTests(unittest.TestCase):
    """I001/I002/I003/I004/I011/I014/I015: knowledge is append-only and cannot self-promote to PROVEN."""

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

    def test_default_migrations_include_knowledge_registry(self) -> None:
        with self._open() as store:
            self.assertEqual(store.migration_checksums.keys(), {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25})
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 25})

    def test_existing_m2_3_store_migrates_to_knowledge_registry(self) -> None:
        schema = Path(self._directory.name) / "m2_3_schema"
        schema.mkdir()
        source_dir = Path(__file__).parents[1] / "src" / "vera_mmu" / "schema"
        for version in ("001_core_store.sql", "002_entity_registry.sql", "003_relation_registry.sql"):
            shutil.copyfile(source_dir / version, schema / version)
        with MemoryStore.open(self._profile(), self.profile_path, schema_dir=schema) as m2_3_store:
            self.assertEqual(m2_3_store.metadata()["store_format"], {"schema_version": 3})
        shutil.copyfile(source_dir / "004_knowledge_registry.sql", schema / "004_knowledge_registry.sql")
        with MemoryStore.open(self._profile(), self.profile_path, schema_dir=schema) as store:
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 4})
            self.assertEqual(
                [event["action"] for event in store.audit_events()],
                ["STORE_INITIALIZED", "STORE_MIGRATED"],
            )

    def test_register_append_and_read_exact_knowledge_with_hash(self) -> None:
        with self._open() as store:
            knowledge = KnowledgeService(store)
            registered = knowledge.register_type("observation", "Observation", actor="test-suite")
            content = "The configured source returned 42."
            appended = knowledge.append(
                "knowledge-001",
                "observation",
                "OBSERVED",
                "Observed result",
                content,
                metadata={"measurement": 42, "units": "count"},
                actor="test-suite",
            )
            self.assertEqual(registered.id, "observation")
            self.assertEqual(knowledge.get("knowledge-001"), appended)
            self.assertEqual(appended.content_hash, sha256(content.encode("utf-8")).hexdigest())
            self.assertEqual(appended.metadata, {"measurement": 42, "units": "count"})
            self.assertEqual(appended.address, "vera://knowledge-project/knowledge/knowledge-001")
            self.assertEqual(
                [event["action"] for event in store.audit_events()][-2:],
                ["KNOWLEDGE_TYPE_REGISTERED", "KNOWLEDGE_APPENDED"],
            )

    def test_accepts_only_safe_initial_epistemic_statuses(self) -> None:
        with self._open() as store:
            knowledge = KnowledgeService(store)
            knowledge.register_type("state", "State")
            for index, status in enumerate(("ACTIVE", "OBSERVED", "HYPOTHESIS", "CONFLICTING"), start=1):
                appended = knowledge.append(
                    f"knowledge-{index:03d}",
                    "state",
                    status,
                    f"Title {index}",
                    f"Content {index}",
                )
                self.assertEqual(appended.status, status)
            with self.assertRaises(KnowledgeAdmissionError):
                knowledge.append("knowledge-proven", "state", "PROVEN", "Proven", "No evidence")
            with self.assertRaises(KnowledgeAdmissionError):
                knowledge.append("knowledge-obsolete", "state", "OBSOLETE", "Obsolete", "No lifecycle")
            with self.assertRaises(sqlite3.IntegrityError):
                store.connection.execute(
                    "INSERT INTO knowledge(id, type_id, status, title, content, content_hash, metadata_json, created_at, created_by) "
                    "VALUES('knowledge-direct-proven', 'state', 'PROVEN', 'Direct', 'No evidence', ?, '{}', '2026-01-01T00:00:00Z', 'test-suite')",
                    (sha256(b"No evidence").hexdigest(),),
                )
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0], 4)

    def test_rejects_unknown_type_duplicate_and_invalid_identifier(self) -> None:
        with self._open() as store:
            knowledge = KnowledgeService(store)
            with self.assertRaises(KnowledgeError):
                knowledge.append("knowledge-001", "missing", "ACTIVE", "Title", "Content")
            knowledge.register_type("hypothesis", "Hypothesis")
            with self.assertRaises(KnowledgeError):
                knowledge.register_type("hypothesis", "Duplicate")
            with self.assertRaises(KnowledgeError):
                knowledge.append("../escape", "hypothesis", "HYPOTHESIS", "Title", "Content")
            with self.assertRaises(KnowledgeError):
                knowledge.append("knowledge-001", "hypothesis", "active", "Title", "Content")
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0], 0)

    def test_exact_read_rejects_inconsistent_content_hash(self) -> None:
        with self._open() as store:
            knowledge = KnowledgeService(store)
            knowledge.register_type("decision", "Decision")
            store.connection.execute(
                "INSERT INTO knowledge(id, type_id, status, title, content, content_hash, metadata_json, created_at, created_by) "
                "VALUES('knowledge-tampered', 'decision', 'ACTIVE', 'Tampered', 'Original content', ?, '{}', '2026-01-01T00:00:00Z', 'test-suite')",
                ("0" * 64,),
            )
            with self.assertRaises(KnowledgeError):
                knowledge.get("knowledge-tampered")

    def test_rejects_duplicate_and_requires_exact_read(self) -> None:
        with self._open() as store:
            knowledge = KnowledgeService(store)
            knowledge.register_type("decision", "Decision")
            first = knowledge.append("knowledge-001", "decision", "ACTIVE", "Decision", "Use strict addresses")
            with self.assertRaises(KnowledgeError):
                knowledge.append("knowledge-001", "decision", "ACTIVE", "Duplicate", "Duplicate")
            self.assertEqual(knowledge.get("knowledge-001"), first)
            with self.assertRaises(KnowledgeNotFoundError):
                knowledge.get("knowledge-002")

    def test_database_rejects_knowledge_and_type_rewrites_and_deletes(self) -> None:
        with self._open() as store:
            knowledge = KnowledgeService(store)
            knowledge.register_type("decision", "Decision")
            knowledge.append("knowledge-001", "decision", "ACTIVE", "Decision", "Use strict addresses")
            with self.assertRaises(sqlite3.DatabaseError):
                store.connection.execute("UPDATE knowledge SET status = 'PROVEN' WHERE id = 'knowledge-001'")
            with self.assertRaises(sqlite3.DatabaseError):
                store.connection.execute("UPDATE knowledge_type SET label = 'Rewrite' WHERE id = 'decision'")
            with self.assertRaises(sqlite3.DatabaseError):
                store.connection.execute("DELETE FROM knowledge WHERE id = 'knowledge-001'")
            with self.assertRaises(sqlite3.DatabaseError):
                store.connection.execute("DELETE FROM knowledge_type WHERE id = 'decision'")
            self.assertEqual(knowledge.get("knowledge-001").status, "ACTIVE")

    def test_knowledge_and_audit_rollback_together_when_audit_insert_fails(self) -> None:
        with self._open() as store:
            knowledge = KnowledgeService(store)
            knowledge.register_type("observation", "Observation")
            store.connection.execute(
                "CREATE TRIGGER reject_knowledge_audit BEFORE INSERT ON store_audit "
                "WHEN NEW.action = 'KNOWLEDGE_APPENDED' "
                "BEGIN SELECT RAISE(ABORT, 'audit rejected'); END"
            )
            with self.assertRaises(KnowledgeError):
                knowledge.append("knowledge-001", "observation", "OBSERVED", "Observed", "No partial write")
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0], 0)
            self.assertNotIn("KNOWLEDGE_APPENDED", [event["action"] for event in store.audit_events()])


if __name__ == "__main__":
    unittest.main()
