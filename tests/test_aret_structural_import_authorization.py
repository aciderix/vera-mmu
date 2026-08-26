from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from vera_mmu.domain_packs.aret import (
    AretStructuralImportAuthorizationError,
    authorize_aret_v1_structural_import,
    check_aret_v1_structural_target_clear,
)
from tests.test_aret_structural_target_collision import _brick_projection, _component_parent, _preflight, _store, _symbol_projection


def test_symbol_authorization_is_explicit_bound_and_zero_write(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        _component_parent(store)
        preflight = _preflight(store, table="function_symbol")
        projection = _symbol_projection(store)
        clear = check_aret_v1_structural_target_clear(preflight=preflight, projection=projection, target_store=store)
        before = store.audit_events()

        authorization = authorize_aret_v1_structural_import(
            preflight=preflight,
            projection=projection,
            clear_check=clear,
            target_store=store,
            authorization_id="function-authorization-001",
            authorized_by="fixture",
        )

        assert authorization.resource_kind == "SYMBOL"
        assert authorization.mapping_id == "aret-v1-function-symbol-to-symbol-v1"
        assert authorization.target_series_state == "INITIAL_EMPTY_RESOURCE_TARGET_REQUIRED"
        assert authorization.authorization_state == "EXPLICIT_STRUCTURAL_IMPORT_ALLOWED"
        assert store.audit_events() == before


def test_brick_authorization_retains_lifecycle_deferral_and_zero_promotion(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        preflight = _preflight(store, table="brick")
        projection = _brick_projection(store)
        clear = check_aret_v1_structural_target_clear(preflight=preflight, projection=projection, target_store=store)
        before = store.audit_events()

        authorization = authorize_aret_v1_structural_import(
            preflight=preflight,
            projection=projection,
            clear_check=clear,
            target_store=store,
            authorization_id="brick-authorization-001",
            authorized_by="fixture",
        )

        assert authorization.resource_kind == "WORK_ITEM"
        assert authorization.mapping_id == "aret-v1-brick-to-work-item-v1"
        assert authorization.lifecycle_policy == "PRESERVE_LEGACY_STATE_AS_METADATA"
        assert authorization.promotion_policy == "FORBID"
        assert store.audit_events() == before


def test_structural_authorization_rejects_stale_clear_check_or_projection_binding(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        _component_parent(store)
        preflight = _preflight(store, table="function_symbol")
        projection = _symbol_projection(store)
        clear = check_aret_v1_structural_target_clear(preflight=preflight, projection=projection, target_store=store)
        with pytest.raises(AretStructuralImportAuthorizationError):
            authorize_aret_v1_structural_import(
                preflight=preflight,
                projection=projection,
                clear_check=replace(clear, resource_kind="WORK_ITEM"),
                target_store=store,
                authorization_id="function-authorization-002",
                authorized_by="fixture",
            )
        with pytest.raises(AretStructuralImportAuthorizationError):
            authorize_aret_v1_structural_import(
                preflight=preflight,
                projection=replace(projection, source_snapshot_sha256="f" * 64),
                clear_check=clear,
                target_store=store,
                authorization_id="function-authorization-003",
                authorized_by="fixture",
            )


def test_structural_authorization_module_has_no_import_or_source_io_capability() -> None:
    source = (Path(__file__).parents[1] / "src" / "vera_mmu" / "domain_packs" / "aret" / "structural_import_authorization.py").read_text(encoding="utf-8")
    for forbidden in ("ImportBatchService", "INSERT", "UPDATE", "DELETE", "sqlite3", ".open(", "read_bytes", "subprocess", "requests", "urllib.", "socket", "os.system"):
        assert forbidden not in source
