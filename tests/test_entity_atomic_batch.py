from __future__ import annotations

from pathlib import Path

import pytest

from vera_mmu.entities import EntityCreateInput, EntityError, EntityService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore


PROFILE = """\
mmu:
  version: "2.0"
project:
  id: "atomic-entity-project"
  name: "Atomic Entity Project"
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
    profile_path.parent.mkdir(parents=True)
    profile_path.write_text(PROFILE, encoding="utf-8")
    return MemoryStore.open(load_profile(profile_path), profile_path)


def _inputs() -> tuple[EntityCreateInput, ...]:
    return (
        EntityCreateInput("component-001", "First component", "First", {"rank": 1}),
        EntityCreateInput("component-002", "Second component", "Second", {"rank": 2}),
    )


def test_register_type_and_create_batch_is_atomic_and_audited(tmp_path: Path) -> None:
    with _open_store(tmp_path) as store:
        result = EntityService(store).register_type_and_create_batch(
            "component",
            "Component",
            _inputs(),
            type_description="Generic components",
            type_schema={"kind": "generic"},
            actor="batch-test",
        )

        assert result.entity_type.id == "component"
        assert [entity.id for entity in result.entities] == ["component-001", "component-002"]
        assert [entity.type_id for entity in result.entities] == ["component", "component"]
        assert [event["action"] for event in store.audit_events()] == [
            "STORE_INITIALIZED",
            "ENTITY_TYPE_REGISTERED",
            "ENTITY_CREATED",
            "ENTITY_CREATED",
        ]
        assert EntityService(store).get("component-001").metadata == {"rank": 1}


def test_batch_rejects_duplicate_request_identifiers_before_any_write(tmp_path: Path) -> None:
    with _open_store(tmp_path) as store:
        before_audit = store.audit_events()
        duplicate_inputs = (
            EntityCreateInput("component-001", "One"),
            EntityCreateInput("component-001", "Two"),
        )

        with pytest.raises(EntityError):
            EntityService(store).register_type_and_create_batch("component", "Component", duplicate_inputs, actor="batch-test")

        assert store.audit_events() == before_audit
        assert store.connection.execute("SELECT 1 FROM entity_type WHERE id = 'component'").fetchone() is None
        assert store.connection.execute("SELECT COUNT(*) FROM entity").fetchone()[0] == 0


def test_batch_rolls_back_type_and_entities_when_target_identifier_conflicts(tmp_path: Path) -> None:
    with _open_store(tmp_path) as store:
        service = EntityService(store)
        service.register_type("other", "Other", actor="fixture")
        service.create("component-001", "other", "Existing", actor="fixture")
        before_audit = store.audit_events()

        with pytest.raises(EntityError):
            service.register_type_and_create_batch("component", "Component", _inputs(), actor="batch-test")

        assert store.audit_events() == before_audit
        assert store.connection.execute("SELECT 1 FROM entity_type WHERE id = 'component'").fetchone() is None
        assert store.connection.execute("SELECT id FROM entity ORDER BY id").fetchall()[0][0] == "component-001"


def test_batch_rejects_existing_type_without_any_additional_write(tmp_path: Path) -> None:
    with _open_store(tmp_path) as store:
        service = EntityService(store)
        service.register_type("component", "Component", actor="fixture")
        before_audit = store.audit_events()

        with pytest.raises(EntityError):
            service.register_type_and_create_batch("component", "Component", _inputs(), actor="batch-test")

        assert store.audit_events() == before_audit
        assert store.connection.execute("SELECT COUNT(*) FROM entity").fetchone()[0] == 0
