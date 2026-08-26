from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import shutil

import pytest

from vera_mmu.identity import load_profile
from vera_mmu.import_batches import (
    ImportBatchError,
    ImportBatchService,
    ImportKnowledgeInput,
    KnowledgeImportBatchInput,
)
from vera_mmu.knowledge import KnowledgeService
from vera_mmu.store import MemoryStore


PROFILE = """\
mmu:
  version: "2.0"
project:
  id: "knowledge-import-project"
  name: "Knowledge Import Project"
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


def _store(tmp_path: Path, schema_dir: Path | None = None) -> MemoryStore:
    profile_path = tmp_path / "project" / ".vera-mmu" / "project.yaml"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(PROFILE, encoding="utf-8")
    return MemoryStore.open(load_profile(profile_path), profile_path, schema_dir=schema_dir)


def _batch(batch_id: str = "knowledge-import-001") -> KnowledgeImportBatchInput:
    return KnowledgeImportBatchInput(
        batch_id=batch_id,
        source_system="legacy-v1",
        source_snapshot_sha256="a" * 64,
        mapping_id="legacy-knowledge-to-knowledge-v1",
        actor="import-test",
        resources=(
            ImportKnowledgeInput(
                identifier="legacy-knowledge--001",
                source_identifier="legacy-knowledge-001",
                payload={
                    "type_id": "legacy-knowledge",
                    "status": "OBSERVED",
                    "title": "Imported knowledge",
                    "content": "Source-preserved content.",
                    "metadata": {"source": {"legacy_status": "SUPERSEDED"}},
                },
            ),
        ),
    )


def _type_prerequisite(store: MemoryStore) -> None:
    KnowledgeService(store).register_type("legacy-knowledge", "Legacy knowledge", actor="fixture")


def test_generic_knowledge_import_batch_api_is_declared() -> None:
    from vera_mmu.import_batches import (
        ImportBatchService,
        ImportKnowledgeInput,
        KnowledgeImportBatchInput,
        KnowledgeImportBatchResult,
    )

    assert ImportKnowledgeInput.__name__ == "ImportKnowledgeInput"
    assert KnowledgeImportBatchInput.__name__ == "KnowledgeImportBatchInput"
    assert KnowledgeImportBatchResult.__name__ == "KnowledgeImportBatchResult"
    assert callable(ImportBatchService.commit_knowledge_import_batch)
    assert callable(ImportBatchService.get_knowledge_import_batch)


def test_knowledge_import_batch_commits_ledger_and_is_exactly_idempotent(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        _type_prerequisite(store)
        service = ImportBatchService(store)
        before = len(store.audit_events())
        first = service.commit_knowledge_import_batch(_batch())
        replay_audit = store.audit_events()
        replay = service.commit_knowledge_import_batch(_batch())

        imported = KnowledgeService(store).get("legacy-knowledge--001")
        assert imported.type_id == "legacy-knowledge"
        assert imported.status == "OBSERVED"
        assert imported.content == "Source-preserved content."
        assert imported.metadata == {"source": {"legacy_status": "SUPERSEDED"}}
        assert first.was_already_committed is False
        assert replay.was_already_committed is True
        assert replay.resources == first.resources
        assert [event["action"] for event in store.audit_events()][before:] == [
            "KNOWLEDGE_APPENDED",
            "KNOWLEDGE_IMPORT_BATCH_COMMITTED",
        ]
        assert store.audit_events() == replay_audit
        assert store.connection.execute("SELECT target_identifier FROM knowledge_import_batch_record").fetchone()[0] == "legacy-knowledge--001"


def test_knowledge_import_batch_rejects_missing_type_proven_or_manual_target_before_writes(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        service = ImportBatchService(store)
        before = store.audit_events()
        with pytest.raises(ImportBatchError):
            service.commit_knowledge_import_batch(_batch())
        assert store.audit_events() == before

        _type_prerequisite(store)
        with pytest.raises(ImportBatchError):
            service.commit_knowledge_import_batch(replace(_batch(), resources=(replace(_batch().resources[0], payload={**_batch().resources[0].payload, "status": "PROVEN"}),)))
        assert store.connection.execute("SELECT COUNT(*) FROM knowledge_import_batch").fetchone()[0] == 0

        KnowledgeService(store).append("manual-knowledge--001", "legacy-knowledge", "OBSERVED", "Manual", "Manual content.", actor="fixture")
        before = store.audit_events()
        with pytest.raises(ImportBatchError):
            service.commit_knowledge_import_batch(replace(_batch(), require_empty_target=True))
        assert store.audit_events() == before
        assert store.connection.execute("SELECT COUNT(*) FROM knowledge_import_batch").fetchone()[0] == 0


def test_knowledge_import_batch_fingerprint_rollback_and_schema_upgrade_are_enforced(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        _type_prerequisite(store)
        service = ImportBatchService(store)
        service.commit_knowledge_import_batch(_batch())
        before = store.audit_events()
        with pytest.raises(ImportBatchError):
            service.commit_knowledge_import_batch(replace(_batch(), source_snapshot_sha256="b" * 64))
        assert store.audit_events() == before
        with pytest.raises(Exception):
            store.connection.execute("UPDATE knowledge_import_batch SET mapping_id = 'other' WHERE id = ?", ("knowledge-import-001",))
        with pytest.raises(Exception):
            store.connection.execute("DELETE FROM knowledge_import_batch_record WHERE batch_id = ?", ("knowledge-import-001",))

    schema = tmp_path / "schema"
    schema.mkdir()
    source = Path(__file__).parents[1] / "src" / "vera_mmu" / "schema"
    for version in range(1, 35):
        migration = next(source.glob(f"{version:03d}_*.sql"))
        shutil.copyfile(migration, schema / migration.name)
    with _store(tmp_path / "legacy", schema_dir=schema) as legacy:
        assert legacy.metadata()["store_format"] == {"schema_version": 34}
    migration_035 = next(source.glob("035_*.sql"))
    shutil.copyfile(migration_035, schema / migration_035.name)
    with _store(tmp_path / "legacy", schema_dir=schema) as upgraded:
        assert upgraded.metadata()["store_format"] == {"schema_version": 35}
        assert upgraded.connection.execute("SELECT COUNT(*) FROM knowledge_import_batch").fetchone()[0] == 0
