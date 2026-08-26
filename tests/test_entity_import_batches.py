from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from vera_mmu.entities import EntityService
from vera_mmu.identity import load_profile
from vera_mmu.import_batches import (
    EntityImportBatchInput,
    ImportBatchError,
    ImportEntityInput,
    ImportBatchService,
)
from vera_mmu.store import MemoryStore


PROFILE = """\
mmu:
  version: "2.0"
project:
  id: "import-batch-project"
  name: "Import Batch Project"
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


def _open_store(tmp_path: Path) -> MemoryStore:
    profile_path = tmp_path / "project" / ".vera-mmu" / "project.yaml"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(PROFILE, encoding="utf-8")
    return MemoryStore.open(load_profile(profile_path), profile_path)


def _batch(batch_id: str = "source-import-001") -> EntityImportBatchInput:
    return EntityImportBatchInput(
        batch_id=batch_id,
        source_system="legacy-v1",
        source_snapshot_sha256="a" * 64,
        mapping_id="source-record-to-entity-v1",
        target_type_id="component",
        target_type_label="Component",
        target_type_description="Generic imported components.",
        target_type_schema={"kind": "generic", "resource": "entity"},
        actor="import-test",
        entities=(
            ImportEntityInput(
                identifier="legacy-component--001",
                source_identifier="SRC-001",
                title="First",
                description="First source record",
                metadata={"source": {"id": "SRC-001"}},
            ),
            ImportEntityInput(
                identifier="legacy-component--002",
                source_identifier="SRC-002",
                title="Second",
                description="Second source record",
                metadata={"source": {"id": "SRC-002"}},
            ),
        ),
    )


def test_entity_import_batch_commits_type_entities_ledger_and_audit_atomically(tmp_path: Path) -> None:
    with _open_store(tmp_path) as store:
        before_audit = store.audit_events()
        result = ImportBatchService(store).commit_entity_import_batch(_batch())

        assert result.commit_state == "COMMITTED"
        assert result.was_already_committed is False
        assert [entity.id for entity in result.entities] == ["legacy-component--001", "legacy-component--002"]
        assert result.batch.source_system == "legacy-v1"
        assert result.batch.source_snapshot_sha256 == "a" * 64
        assert [event["action"] for event in store.audit_events()][len(before_audit) :] == [
            "ENTITY_TYPE_REGISTERED",
            "ENTITY_CREATED",
            "ENTITY_CREATED",
            "IMPORT_BATCH_COMMITTED",
        ]
        assert store.connection.execute("SELECT COUNT(*) FROM import_batch").fetchone()[0] == 1
        assert [row[0] for row in store.connection.execute("SELECT source_identifier FROM import_batch_entity ORDER BY source_identifier").fetchall()] == [
            "SRC-001",
            "SRC-002",
        ]


def test_identical_import_batch_is_idempotent_without_a_new_write_or_audit(tmp_path: Path) -> None:
    with _open_store(tmp_path) as store:
        service = ImportBatchService(store)
        first = service.commit_entity_import_batch(_batch())
        before_audit = store.audit_events()

        replay = service.commit_entity_import_batch(_batch())

        assert replay.commit_state == "COMMITTED"
        assert replay.was_already_committed is True
        assert replay.batch == first.batch
        assert replay.entities == first.entities
        assert store.audit_events() == before_audit
        assert store.connection.execute("SELECT COUNT(*) FROM import_batch").fetchone()[0] == 1


def test_import_batch_id_cannot_be_reused_with_a_different_fingerprint(tmp_path: Path) -> None:
    with _open_store(tmp_path) as store:
        service = ImportBatchService(store)
        service.commit_entity_import_batch(_batch())
        before_audit = store.audit_events()

        with pytest.raises(ImportBatchError):
            service.commit_entity_import_batch(replace(_batch(), source_snapshot_sha256="b" * 64))

        assert store.audit_events() == before_audit
        assert store.connection.execute("SELECT COUNT(*) FROM import_batch").fetchone()[0] == 1


def test_import_batch_rolls_back_type_entities_ledger_and_audit_on_late_target_conflict(tmp_path: Path) -> None:
    with _open_store(tmp_path) as store:
        entities = EntityService(store)
        entities.register_type("other", "Other", actor="fixture")
        entities.create("legacy-component--002", "other", "Existing", actor="fixture")
        before_audit = store.audit_events()

        with pytest.raises(ImportBatchError):
            ImportBatchService(store).commit_entity_import_batch(_batch())

        assert store.audit_events() == before_audit
        assert store.connection.execute("SELECT 1 FROM entity_type WHERE id = 'component'").fetchone() is None
        assert store.connection.execute("SELECT COUNT(*) FROM import_batch").fetchone()[0] == 0
        assert store.connection.execute("SELECT COUNT(*) FROM import_batch_entity").fetchone()[0] == 0


def test_import_batch_allows_only_an_exactly_compatible_existing_type(tmp_path: Path) -> None:
    with _open_store(tmp_path) as store:
        entities = EntityService(store)
        entities.register_type(
            "component",
            "Component",
            description="Generic imported components.",
            schema={"kind": "generic", "resource": "entity"},
            actor="fixture",
        )

        result = ImportBatchService(store).commit_entity_import_batch(_batch())

        assert result.was_already_committed is False
        assert [entity.id for entity in result.entities] == ["legacy-component--001", "legacy-component--002"]

    with _open_store(tmp_path / "incompatible") as store:
        EntityService(store).register_type("component", "Incompatible", actor="fixture")
        before_audit = store.audit_events()

        with pytest.raises(ImportBatchError):
            ImportBatchService(store).commit_entity_import_batch(_batch())

        assert store.audit_events() == before_audit
        assert store.connection.execute("SELECT COUNT(*) FROM import_batch").fetchone()[0] == 0


def test_import_batch_rejects_duplicate_source_or_target_identifiers_before_any_write(tmp_path: Path) -> None:
    with _open_store(tmp_path) as store:
        duplicate_source = replace(
            _batch(),
            entities=(
                _batch().entities[0],
                replace(_batch().entities[1], source_identifier="SRC-001"),
            ),
        )
        before_audit = store.audit_events()

        with pytest.raises(ImportBatchError):
            ImportBatchService(store).commit_entity_import_batch(duplicate_source)

        assert store.audit_events() == before_audit
        assert store.connection.execute("SELECT COUNT(*) FROM entity").fetchone()[0] == 0
        assert store.connection.execute("SELECT COUNT(*) FROM import_batch").fetchone()[0] == 0
