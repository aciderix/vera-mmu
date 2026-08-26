from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import shutil

import pytest

from vera_mmu.identity import load_profile
from vera_mmu.import_batches import (
    ImportBatchError,
    ImportBatchService,
    ImportKnowledgeSourceInput,
    KnowledgeSourceImportBatchInput,
)
from vera_mmu.knowledge import KnowledgeService
from vera_mmu.provenance import KnowledgeSourceService
from vera_mmu.store import MemoryStore


PROFILE = """\
mmu:
  version: "2.0"
project:
  id: "knowledge-source-import-project"
  name: "Knowledge Source Import Project"
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


def _knowledge_prerequisite(store: MemoryStore) -> None:
    service = KnowledgeService(store)
    service.register_type("legacy-knowledge", "Legacy knowledge", actor="fixture")
    service.append("legacy-knowledge--001", "legacy-knowledge", "OBSERVED", "Imported", "Imported content.", actor="fixture")


def _batch(batch_id: str = "knowledge-source-import-001") -> KnowledgeSourceImportBatchInput:
    return KnowledgeSourceImportBatchInput(
        batch_id=batch_id,
        source_system="legacy-v1",
        source_snapshot_sha256="a" * 64,
        mapping_id="legacy-knowledge-source-v1",
        actor="import-test",
        resources=(
            ImportKnowledgeSourceInput(
                identifier="legacy-knowledge-source--001",
                source_identifier="legacy-source-001",
                knowledge_identifier="legacy-knowledge--001",
                payload={
                    "repository": "https://example.invalid/legacy",
                    "revision": "a" * 40,
                    "path": "docs/source.md",
                    "start_line": 3,
                    "end_line": 7,
                    "section": "Source section",
                    "source_hash": "b" * 64,
                },
            ),
        ),
    )


def test_generic_knowledge_source_import_batch_api_is_declared() -> None:
    from vera_mmu.import_batches import (
        ImportBatchService,
        ImportKnowledgeSourceInput,
        KnowledgeSourceImportBatchInput,
        KnowledgeSourceImportBatchResult,
    )

    assert ImportKnowledgeSourceInput.__name__ == "ImportKnowledgeSourceInput"
    assert KnowledgeSourceImportBatchInput.__name__ == "KnowledgeSourceImportBatchInput"
    assert KnowledgeSourceImportBatchResult.__name__ == "KnowledgeSourceImportBatchResult"
    assert callable(ImportBatchService.commit_knowledge_source_import_batch)
    assert callable(ImportBatchService.get_knowledge_source_import_batch)


def test_knowledge_source_import_batch_commits_atomically_and_replays_exactly(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        _knowledge_prerequisite(store)
        service = ImportBatchService(store)
        before = len(store.audit_events())
        first = service.commit_knowledge_source_import_batch(_batch())
        replay_audit = store.audit_events()
        replay = service.commit_knowledge_source_import_batch(_batch())

        attached = KnowledgeSourceService(store).get("legacy-knowledge-source--001")
        assert attached.knowledge_id == "legacy-knowledge--001"
        assert attached.source_path == "docs/source.md"
        assert first.was_already_committed is False
        assert replay.was_already_committed is True
        assert replay.resources == first.resources
        assert [event["action"] for event in store.audit_events()][before:] == [
            "KNOWLEDGE_SOURCE_ATTACHED",
            "KNOWLEDGE_SOURCE_IMPORT_BATCH_COMMITTED",
        ]
        assert store.audit_events() == replay_audit


def test_knowledge_source_import_batch_rejects_missing_parent_fingerprint_drift_and_nonempty_target(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        service = ImportBatchService(store)
        before = store.audit_events()
        with pytest.raises(ImportBatchError):
            service.commit_knowledge_source_import_batch(_batch())
        assert store.audit_events() == before
        assert store.connection.execute("SELECT COUNT(*) FROM knowledge_source_import_batch").fetchone()[0] == 0

        _knowledge_prerequisite(store)
        service.commit_knowledge_source_import_batch(_batch())
        before = store.audit_events()
        with pytest.raises(ImportBatchError):
            service.commit_knowledge_source_import_batch(replace(_batch(), source_snapshot_sha256="c" * 64))
        assert store.audit_events() == before

    with _store(tmp_path / "second") as store:
        _knowledge_prerequisite(store)
        KnowledgeSourceService(store).attach(
            "manual-source-001",
            "legacy-knowledge--001",
            repository="https://example.invalid/manual",
            revision="d" * 40,
            path="docs/manual.md",
            start_line=1,
            end_line=1,
            section="Manual",
            source_hash="e" * 64,
            actor="fixture",
        )
        with pytest.raises(ImportBatchError):
            ImportBatchService(store).commit_knowledge_source_import_batch(replace(_batch(), require_empty_target=True))


def test_knowledge_source_import_batch_upgrade_and_rows_are_append_only(tmp_path: Path) -> None:
    schema = tmp_path / "schema"
    schema.mkdir()
    source = Path(__file__).parents[1] / "src" / "vera_mmu" / "schema"
    for version in range(1, 36):
        migration = next(source.glob(f"{version:03d}_*.sql"))
        shutil.copyfile(migration, schema / migration.name)
    with _store(tmp_path / "legacy", schema_dir=schema) as legacy:
        assert legacy.metadata()["store_format"] == {"schema_version": 35}
    migration_036 = next(source.glob("036_*.sql"))
    shutil.copyfile(migration_036, schema / migration_036.name)
    with _store(tmp_path / "legacy", schema_dir=schema) as upgraded:
        assert upgraded.metadata()["store_format"] == {"schema_version": 36}
        assert upgraded.connection.execute("SELECT COUNT(*) FROM knowledge_source_import_batch").fetchone()[0] == 0

    with _store(tmp_path / "rows") as store:
        _knowledge_prerequisite(store)
        result = ImportBatchService(store).commit_knowledge_source_import_batch(_batch())
        with pytest.raises(Exception):
            store.connection.execute("UPDATE knowledge_source_import_batch SET mapping_id = 'other' WHERE id = ?", (result.batch.id,))
        with pytest.raises(Exception):
            store.connection.execute("DELETE FROM knowledge_source_import_batch_record WHERE batch_id = ?", (result.batch.id,))
