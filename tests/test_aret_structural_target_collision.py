from __future__ import annotations

from pathlib import Path

import pytest

from vera_mmu.domain_packs.aret import (
    AretStructuralTargetCollisionError,
    AretV1BrickProjection,
    AretV1StructuralImportPreflight,
    AretV1WorkItemDraft,
    AretV1FunctionSymbolProjection,
    AretV1SymbolDraft,
    check_aret_v1_structural_target_clear,
)
from vera_mmu.entities import EntityService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore
from vera_mmu.symbols import SymbolService
from vera_mmu.work_items import WorkItemService


PROFILE = """\
mmu:
  version: "2.0"
project:
  id: "structural-collision"
  name: "Structural Collision"
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


def _store(tmp_path: Path) -> MemoryStore:
    profile_path = tmp_path / "project" / ".vera-mmu" / "project.yaml"
    profile_path.parent.mkdir(parents=True)
    profile_path.write_text(PROFILE, encoding="utf-8")
    return MemoryStore.open(load_profile(profile_path), profile_path)


def _preflight(store: MemoryStore, *, table: str) -> AretV1StructuralImportPreflight:
    is_function = table == "function_symbol"
    return AretV1StructuralImportPreflight(
        target_identity=store.identity,
        request_id=f"{table}-request-001",
        preflight_id=f"{table}-preflight-001",
        confirmed_by="fixture",
        legacy_table=table,
        vera_resource="symbol" if is_function else "work_item",
        resource_kind="SYMBOL" if is_function else "WORK_ITEM",
        source_snapshot_sha256="a" * 64,
        source_record_count=1,
        source_first_id="component:pkg!run" if is_function else "brick-001",
        source_last_id="component:pkg!run" if is_function else "brick-001",
        lifecycle_policy="NOT_APPLICABLE" if is_function else "PRESERVE_LEGACY_STATE_AS_METADATA",
    )


def _symbol_projection(store: MemoryStore) -> AretV1FunctionSymbolProjection:
    draft = AretV1SymbolDraft(
        "aret-symbol--component-pkg-run", "aret-component--component", "FUNCTION", "pkg", "run", "",
        {"source": {"domain_pack": "aret-v1", "legacy_table": "function_symbol", "source_id": "component:pkg!run", "source_snapshot_sha256": "a" * 64}},
    )
    return AretV1FunctionSymbolProjection(store.identity, "function_symbol-request-001", "a" * 64, (draft,))


def _brick_projection(store: MemoryStore) -> AretV1BrickProjection:
    draft = AretV1WorkItemDraft(
        "aret-brick--brick-001", "WORK_ITEM", "Brick", "Description", 3,
        {"source": {"domain_pack": "aret-v1", "legacy_table": "brick", "source_id": "brick-001", "source_snapshot_sha256": "a" * 64, "state": "ACTIVE"}},
    )
    return AretV1BrickProjection(store.identity, "brick-request-001", "a" * 64, (draft,))


def _component_parent(store: MemoryStore) -> None:
    entities = EntityService(store)
    entities.register_type("component", "Component", actor="fixture")
    entities.create("aret-component--component", "component", "Parent", actor="fixture")


def test_symbol_collision_check_requires_parent_and_clear_target_without_writing(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        _component_parent(store)
        before = store.audit_events()
        result = check_aret_v1_structural_target_clear(
            preflight=_preflight(store, table="function_symbol"), projection=_symbol_projection(store), target_store=store
        )
        assert result.resource_kind == "SYMBOL"
        assert result.target_series_state == "INITIAL_EMPTY_RESOURCE_TARGET_REQUIRED"
        assert result.checked_resource_count == 1
        assert result.checked_parent_entity_count == 1
        assert result.clear_state == "TARGET_CLEAR_NOT_WRITABLE"
        assert store.audit_events() == before


def test_symbol_collision_check_rejects_missing_parent_or_semantic_collision(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        with pytest.raises(AretStructuralTargetCollisionError):
            check_aret_v1_structural_target_clear(
                preflight=_preflight(store, table="function_symbol"), projection=_symbol_projection(store), target_store=store
            )
        _component_parent(store)
        SymbolService(store).create("existing-symbol--001", "aret-component--component", "FUNCTION", "pkg", "run", actor="fixture")
        before = store.audit_events()
        with pytest.raises(AretStructuralTargetCollisionError):
            check_aret_v1_structural_target_clear(
                preflight=_preflight(store, table="function_symbol"), projection=_symbol_projection(store), target_store=store
            )
        assert store.audit_events() == before


def test_work_item_collision_check_requires_clear_resource_target_and_preserves_lifecycle_deferral(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        before = store.audit_events()
        result = check_aret_v1_structural_target_clear(
            preflight=_preflight(store, table="brick"), projection=_brick_projection(store), target_store=store
        )
        assert result.resource_kind == "WORK_ITEM"
        assert result.target_series_state == "INITIAL_EMPTY_RESOURCE_TARGET_REQUIRED"
        assert result.lifecycle_state == "DEFERRED_NOT_EXECUTABLE"
        assert store.audit_events() == before
        WorkItemService(store).create("existing-work-item--001", "WORK_ITEM", "Existing", actor="fixture")
        with pytest.raises(AretStructuralTargetCollisionError):
            check_aret_v1_structural_target_clear(
                preflight=_preflight(store, table="brick"), projection=_brick_projection(store), target_store=store
            )


def test_work_item_collision_check_resolves_legacy_component_to_projected_vera_parent_without_writing(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        _component_parent(store)
        projection = AretV1BrickProjection(
            store.identity,
            "brick-request-001",
            "a" * 64,
            (
                AretV1WorkItemDraft(
                    "aret-brick--brick-001",
                    "WORK_ITEM",
                    "Brick",
                    "Description",
                    3,
                    {
                        "source": {
                            "domain_pack": "aret-v1",
                            "legacy_table": "brick",
                            "source_id": "brick-001",
                            "source_snapshot_sha256": "a" * 64,
                            "component_id": "component",
                            "state": "ACTIVE",
                        }
                    },
                ),
            ),
        )
        before = store.audit_events()

        result = check_aret_v1_structural_target_clear(
            preflight=_preflight(store, table="brick"), projection=projection, target_store=store
        )

        assert result.resource_kind == "WORK_ITEM"
        assert result.checked_parent_entity_count == 1
        assert result.clear_state == "TARGET_CLEAR_NOT_WRITABLE"
        assert store.audit_events() == before


def test_structural_collision_check_rejects_binding_or_projection_drift(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        _component_parent(store)
        projection = _symbol_projection(store)
        with pytest.raises(AretStructuralTargetCollisionError):
            check_aret_v1_structural_target_clear(
                preflight=_preflight(store, table="function_symbol"),
                projection=projection.__class__(**{**projection.__dict__, "projection_state": "IMPORTED"}),
                target_store=store,
            )


def test_structural_collision_module_is_read_only_and_has_no_authorization_or_import_capability() -> None:
    source = (Path(__file__).parents[1] / "src" / "vera_mmu" / "domain_packs" / "aret" / "structural_target_collision.py").read_text(encoding="utf-8")
    for required in ("SELECT COUNT(*) FROM {resource_table}", "resource_import_batch", "TARGET_CLEAR_NOT_WRITABLE"):
        assert required in source
    for forbidden in ("INSERT", "UPDATE", "DELETE", "ImportBatchService", "authorize_", "subprocess", "requests", "urllib.", "socket", "os.system"):
        assert forbidden not in source
