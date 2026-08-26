from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import shutil

import pytest

from vera_mmu.entities import EntityService
from vera_mmu.identity import load_profile
from vera_mmu.import_batches import ImportBatchError, ImportResourceInput, ImportBatchService, ResourceImportBatchInput
from vera_mmu.store import MemoryStore
from vera_mmu.symbols import SymbolService
from vera_mmu.work_items import WorkItemService


PROFILE = """\
mmu:
  version: "2.0"
project:
  id: "resource-import-project"
  name: "Resource Import Project"
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


def _symbol_batch(batch_id: str = "symbol-import-001") -> ResourceImportBatchInput:
    return ResourceImportBatchInput(
        batch_id=batch_id,
        source_system="legacy-v1",
        source_snapshot_sha256="a" * 64,
        mapping_id="structural-symbol-v1",
        resource_kind="SYMBOL",
        actor="import-test",
        resources=(
            ImportResourceInput(
                identifier="legacy-symbol--001",
                source_identifier="source!fn-001",
                payload={
                    "entity_id": "legacy-entity--001",
                    "kind": "FUNCTION",
                    "path": "pkg/module.py",
                    "symbol_identifier": "run",
                    "signature": "cdecl",
                    "metadata": {"origin": "fixture"},
                },
            ),
        ),
    )


def _work_item_batch(batch_id: str = "work-item-import-001") -> ResourceImportBatchInput:
    return ResourceImportBatchInput(
        batch_id=batch_id,
        source_system="legacy-v1",
        source_snapshot_sha256="a" * 64,
        mapping_id="structural-work-item-v1",
        resource_kind="WORK_ITEM",
        actor="import-test",
        resources=(
            ImportResourceInput(
                identifier="legacy-work-item--001",
                source_identifier="source-brick-001",
                payload={
                    "item_type": "WORK_ITEM",
                    "title": "Preserved item",
                    "description": "Imported without lifecycle transition.",
                    "priority": 3,
                    "parent_id": None,
                    "assignee": None,
                    "metadata": {"legacy_state": "ACTIVE"},
                },
            ),
        ),
    )


def _entity_prerequisite(store: MemoryStore) -> None:
    entities = EntityService(store)
    entities.register_type("component", "Component", actor="fixture")
    entities.create("legacy-entity--001", "component", "Existing owner", actor="fixture")


def test_generic_resource_import_batch_api_is_declared() -> None:
    from vera_mmu.import_batches import ImportResourceInput, ResourceImportBatchInput, ResourceImportBatchResult, ImportBatchService

    assert ImportResourceInput.__name__ == "ImportResourceInput"
    assert ResourceImportBatchInput.__name__ == "ResourceImportBatchInput"
    assert ResourceImportBatchResult.__name__ == "ResourceImportBatchResult"
    assert callable(ImportBatchService.commit_resource_import_batch)


def test_generic_resource_batch_rejects_unknown_resource_kind_before_writes(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        before_audit = store.audit_events()
        unknown = replace(_symbol_batch(), resource_kind="UNKNOWN")
        with pytest.raises(ImportBatchError):
            ImportBatchService(store).commit_resource_import_batch(unknown)
        assert store.audit_events() == before_audit
        assert store.connection.execute("SELECT COUNT(*) FROM resource_import_batch").fetchone()[0] == 0


def test_symbol_resource_batch_commits_resource_ledger_and_audits_atomically(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        _entity_prerequisite(store)
        before = len(store.audit_events())
        result = ImportBatchService(store).commit_resource_import_batch(_symbol_batch())

        assert result.commit_state == "COMMITTED"
        assert result.was_already_committed is False
        assert result.resource_kind == "SYMBOL"
        assert [resource.id for resource in result.resources] == ["legacy-symbol--001"]
        assert SymbolService(store).get("legacy-symbol--001").entity_id == "legacy-entity--001"
        assert [event["action"] for event in store.audit_events()][before:] == ["SYMBOL_CREATED", "RESOURCE_IMPORT_BATCH_COMMITTED"]
        assert store.connection.execute("SELECT COUNT(*) FROM resource_import_batch").fetchone()[0] == 1
        assert store.connection.execute("SELECT target_identifier FROM resource_import_batch_record").fetchone()[0] == "legacy-symbol--001"


def test_work_item_resource_batch_preserves_creation_contract_and_is_idempotent(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        service = ImportBatchService(store)
        first = service.commit_resource_import_batch(_work_item_batch())
        before = store.audit_events()
        replay = service.commit_resource_import_batch(_work_item_batch())

        item = WorkItemService(store).get("legacy-work-item--001")
        assert item.status == "PLANNED"
        assert item.metadata == {"legacy_state": "ACTIVE"}
        assert replay.was_already_committed is True
        assert replay.batch == first.batch
        assert replay.resources == first.resources
        assert store.audit_events() == before


def test_resource_import_batch_id_cannot_be_reused_with_different_fingerprint(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        service = ImportBatchService(store)
        service.commit_resource_import_batch(_work_item_batch())
        before = store.audit_events()
        with pytest.raises(ImportBatchError):
            service.commit_resource_import_batch(replace(_work_item_batch(), source_snapshot_sha256="b" * 64))
        assert store.audit_events() == before
        assert store.connection.execute("SELECT COUNT(*) FROM resource_import_batch").fetchone()[0] == 1


def test_resource_import_batch_rejects_missing_symbol_parent_before_writes(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        before = store.audit_events()
        with pytest.raises(ImportBatchError):
            ImportBatchService(store).commit_resource_import_batch(_symbol_batch())
        assert store.audit_events() == before
        assert store.connection.execute("SELECT COUNT(*) FROM symbol").fetchone()[0] == 0
        assert store.connection.execute("SELECT COUNT(*) FROM resource_import_batch").fetchone()[0] == 0


def test_resource_import_batch_rolls_back_on_late_semantic_conflict(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        _entity_prerequisite(store)
        SymbolService(store).create("existing-symbol--001", "legacy-entity--001", "FUNCTION", "pkg/module.py", "run", actor="fixture")
        before = store.audit_events()
        with pytest.raises(ImportBatchError):
            ImportBatchService(store).commit_resource_import_batch(_symbol_batch())
        assert store.audit_events() == before
        assert store.connection.execute("SELECT COUNT(*) FROM resource_import_batch").fetchone()[0] == 0
        assert store.connection.execute("SELECT COUNT(*) FROM resource_import_batch_record").fetchone()[0] == 0


def test_resource_import_batch_rejects_duplicate_identifiers_before_writes(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        duplicated = replace(_work_item_batch(), resources=(_work_item_batch().resources[0], _work_item_batch().resources[0]))
        before = store.audit_events()
        with pytest.raises(ImportBatchError):
            ImportBatchService(store).commit_resource_import_batch(duplicated)
        assert store.audit_events() == before
        assert store.connection.execute("SELECT COUNT(*) FROM resource_import_batch").fetchone()[0] == 0


def test_resource_import_ledger_migrates_an_existing_033_store(tmp_path: Path) -> None:
    schema = tmp_path / "schema"
    schema.mkdir()
    source = Path(__file__).parents[1] / "src" / "vera_mmu" / "schema"
    for version in range(1, 34):
        migration = next(source.glob(f"{version:03d}_*.sql"))
        shutil.copyfile(migration, schema / migration.name)
    with _store(tmp_path / "legacy", schema_dir=schema) as legacy:
        assert legacy.metadata()["store_format"] == {"schema_version": 33}
    migration_034 = next(source.glob("034_*.sql"))
    shutil.copyfile(migration_034, schema / migration_034.name)
    with _store(tmp_path / "legacy", schema_dir=schema) as upgraded:
        assert upgraded.metadata()["store_format"] == {"schema_version": 34}
        assert upgraded.connection.execute("SELECT COUNT(*) FROM resource_import_batch").fetchone()[0] == 0
        assert upgraded.connection.execute("SELECT COUNT(*) FROM resource_import_batch_record").fetchone()[0] == 0


def test_resource_import_ledger_rows_are_append_only_after_commit(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        result = ImportBatchService(store).commit_resource_import_batch(_work_item_batch())
        with pytest.raises(Exception):
            store.connection.execute("UPDATE resource_import_batch SET mapping_id = 'other' WHERE id = ?", (result.batch.id,))
        with pytest.raises(Exception):
            store.connection.execute("DELETE FROM resource_import_batch_record WHERE batch_id = ?", (result.batch.id,))
