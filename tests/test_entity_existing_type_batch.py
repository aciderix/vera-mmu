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
  id: "existing-type-batch-project"
  name: "Existing Type Batch Project"
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
        EntityCreateInput("component-002", "Second component", "Second", {"rank": 2}),
        EntityCreateInput("component-003", "Third component", "Third", {"rank": 3}),
    )


def test_create_batch_for_registered_type_is_atomic_and_audited(tmp_path: Path) -> None:
    with _open_store(tmp_path) as store:
        service = EntityService(store)
        registered = service.register_type("component", "Component", actor="fixture")
        before_audit = store.audit_events()

        result = service.create_batch_for_registered_type("component", _inputs(), actor="batch-test")

        assert result.entity_type == registered
        assert [entity.id for entity in result.entities] == ["component-002", "component-003"]
        assert [entity.type_id for entity in result.entities] == ["component", "component"]
        assert [event["action"] for event in store.audit_events()][len(before_audit) :] == [
            "ENTITY_CREATED",
            "ENTITY_CREATED",
        ]
        assert service.get("component-002").metadata == {"rank": 2}


def test_existing_type_batch_rejects_unknown_type_before_any_write(tmp_path: Path) -> None:
    with _open_store(tmp_path) as store:
        service = EntityService(store)
        before_audit = store.audit_events()

        with pytest.raises(EntityError):
            service.create_batch_for_registered_type("component", _inputs(), actor="batch-test")

        assert store.audit_events() == before_audit
        assert store.connection.execute("SELECT COUNT(*) FROM entity").fetchone()[0] == 0


def test_existing_type_batch_rolls_back_every_entity_and_audit_on_late_conflict(tmp_path: Path) -> None:
    with _open_store(tmp_path) as store:
        service = EntityService(store)
        service.register_type("component", "Component", actor="fixture")
        service.create("component-003", "component", "Existing", actor="fixture")
        before_audit = store.audit_events()

        with pytest.raises(EntityError):
            service.create_batch_for_registered_type("component", _inputs(), actor="batch-test")

        assert store.audit_events() == before_audit
        assert [row[0] for row in store.connection.execute("SELECT id FROM entity ORDER BY id").fetchall()] == ["component-003"]


def test_existing_type_batch_rejects_duplicate_request_identifiers_before_any_write(tmp_path: Path) -> None:
    with _open_store(tmp_path) as store:
        service = EntityService(store)
        service.register_type("component", "Component", actor="fixture")
        before_audit = store.audit_events()
        duplicate_inputs = (
            EntityCreateInput("component-002", "Second"),
            EntityCreateInput("component-002", "Duplicate"),
        )

        with pytest.raises(EntityError):
            service.create_batch_for_registered_type("component", duplicate_inputs, actor="batch-test")

        assert store.audit_events() == before_audit
        assert store.connection.execute("SELECT COUNT(*) FROM entity").fetchone()[0] == 0
