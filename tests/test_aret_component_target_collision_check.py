from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from vera_mmu.domain_packs.aret import (
    AretComponentTargetCollisionError,
    AretV1ComponentEntityProjection,
    AretV1EntityDraft,
    check_aret_v1_component_target_clear,
)
from vera_mmu.entities import EntityService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore


PROFILE = """\
mmu:
  version: "2.0"
project:
  id: "collision-project"
  name: "Collision Project"
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


def _projection(store: MemoryStore) -> AretV1ComponentEntityProjection:
    draft = AretV1EntityDraft(
        target_identifier="aret-component--CMP-001",
        target_address=f"vera://{store.identity.project_id}/entity/aret-component--CMP-001",
        entity_type_id="component",
        title="Alpha",
        description="First",
        metadata={"source": {"source_id": "CMP-001"}},
    )
    return AretV1ComponentEntityProjection(
        target_identity=store.identity,
        request_id="m4-13-collision-check",
        preflight_id="m4-13-component-page",
        source_snapshot_sha256="a" * 64,
        entity_type_id="component",
        entity_type_registration_required=True,
        drafts=(draft,),
    )


def test_target_collision_check_reports_clear_existing_store_without_writing(tmp_path: Path) -> None:
    with _open_store(tmp_path) as store:
        before_audit = store.audit_events()
        result = check_aret_v1_component_target_clear(
            projection=_projection(store),
            target_store=store,
        )

        assert result.target_identity == store.identity
        assert result.entity_type_state == "ABSENT_REQUIRED"
        assert result.checked_entity_count == 1
        assert result.clear_state == "TARGET_CLEAR_NOT_WRITABLE"
        assert store.audit_events() == before_audit


def test_target_collision_check_rejects_existing_component_type(tmp_path: Path) -> None:
    with _open_store(tmp_path) as store:
        EntityService(store).register_type("component", "Component", actor="fixture")
        before_audit = store.audit_events()

        with pytest.raises(AretComponentTargetCollisionError):
            check_aret_v1_component_target_clear(projection=_projection(store), target_store=store)

        assert store.audit_events() == before_audit


def test_target_collision_check_rejects_existing_draft_identifier(tmp_path: Path) -> None:
    with _open_store(tmp_path) as store:
        EntityService(store).register_type("other", "Other", actor="fixture")
        EntityService(store).create(
            "aret-component--CMP-001",
            "other",
            "Existing target",
            actor="fixture",
        )
        before_audit = store.audit_events()

        with pytest.raises(AretComponentTargetCollisionError):
            check_aret_v1_component_target_clear(projection=_projection(store), target_store=store)

        assert store.audit_events() == before_audit


def test_target_collision_check_rejects_target_identity_or_projection_state_mismatch(tmp_path: Path) -> None:
    with _open_store(tmp_path) as store:
        projection = _projection(store)
        with pytest.raises(AretComponentTargetCollisionError):
            check_aret_v1_component_target_clear(
                projection=projection.__class__(
                    **{**projection.__dict__, "projection_state": "IMPORTED"}
                ),
                target_store=store,
            )

    with _open_store(tmp_path / "target") as target_store:
        projection = _projection(target_store)
        mismatched_projection = replace(
            projection,
            target_identity=replace(target_store.identity, project_id="different-project"),
        )
        with pytest.raises(AretComponentTargetCollisionError):
            check_aret_v1_component_target_clear(
                projection=mismatched_projection,
                target_store=target_store,
            )


def test_target_collision_module_uses_only_read_queries() -> None:
    source = (
        Path(__file__).parents[1]
        / "src"
        / "vera_mmu"
        / "domain_packs"
        / "aret"
        / "component_target_collision.py"
    ).read_text(encoding="utf-8")

    for required in ("SELECT 1 FROM entity_type", "SELECT id FROM entity", "TARGET_CLEAR_NOT_WRITABLE"):
        assert required in source
    for forbidden in (
        "INSERT",
        "UPDATE",
        "DELETE",
        "open(",
        "sqlite3",
        "subprocess",
        "requests",
        "urllib.",
        "socket",
        "os.system",
        "EntityService",
    ):
        assert forbidden not in source
