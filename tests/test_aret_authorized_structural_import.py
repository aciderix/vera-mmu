from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from vera_mmu.domain_packs.aret import (
    AretAuthorizedStructuralImportError,
    AretV1FunctionSymbolProjection,
    AretV1SymbolDraft,
    authorize_aret_v1_structural_import,
    check_aret_v1_structural_target_clear,
    import_authorized_aret_v1_structural_page,
)
from vera_mmu.symbols import SymbolService
from tests.test_aret_structural_target_collision import _brick_projection, _component_parent, _preflight, _store, _symbol_projection


def _authorize_symbol(store):
    preflight = _preflight(store, table="function_symbol")
    projection = _symbol_projection(store)
    clear = check_aret_v1_structural_target_clear(preflight=preflight, projection=projection, target_store=store)
    authorization = authorize_aret_v1_structural_import(
        preflight=preflight, projection=projection, clear_check=clear, target_store=store,
        authorization_id="function-import-authorization-001", authorized_by="fixture",
    )
    return preflight, projection, authorization


def _authorize_brick(store):
    preflight = _preflight(store, table="brick")
    projection = _brick_projection(store)
    clear = check_aret_v1_structural_target_clear(preflight=preflight, projection=projection, target_store=store)
    authorization = authorize_aret_v1_structural_import(
        preflight=preflight, projection=projection, clear_check=clear, target_store=store,
        authorization_id="brick-import-authorization-001", authorized_by="fixture",
    )
    return preflight, projection, authorization


def test_authorized_function_symbol_import_commits_audited_batch_and_replays_exactly(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        _component_parent(store)
        preflight, projection, authorization = _authorize_symbol(store)
        before = store.audit_events()

        result = import_authorized_aret_v1_structural_page(
            preflight=preflight, projection=projection, authorization=authorization, target_store=store
        )

        assert result.import_state == "IMPORTED_NO_PROMOTION"
        assert result.resource_kind == "SYMBOL"
        assert result.imported_resource_count == 1
        assert result.resources[0].id == "aret-symbol--component-pkg-run"
        assert result.resources[0].entity_id == "aret-component--component"
        assert result.resources[0].metadata["source"]["legacy_table"] == "function_symbol"
        assert len(store.audit_events()) == len(before) + 2
        assert store.connection.execute("SELECT COUNT(*) FROM resource_import_batch").fetchone()[0] == 1
        assert store.connection.execute("SELECT COUNT(*) FROM resource_import_batch_record").fetchone()[0] == 1
        assert store.connection.execute("SELECT COUNT(*) FROM evidence").fetchone()[0] == 0
        assert store.connection.execute("SELECT COUNT(*) FROM evidence_admission").fetchone()[0] == 0
        assert store.connection.execute("SELECT COUNT(*) FROM knowledge_proof").fetchone()[0] == 0

        replay_before = store.audit_events()
        replay = import_authorized_aret_v1_structural_page(
            preflight=preflight, projection=projection, authorization=authorization, target_store=store
        )
        assert replay.was_already_imported is True
        assert replay.resources == result.resources
        assert store.audit_events() == replay_before


def test_authorized_brick_import_preserves_legacy_state_metadata_without_lifecycle_promotion(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        preflight, projection, authorization = _authorize_brick(store)

        result = import_authorized_aret_v1_structural_page(
            preflight=preflight, projection=projection, authorization=authorization, target_store=store
        )

        item = result.resources[0]
        assert result.resource_kind == "WORK_ITEM"
        assert item.id == "aret-brick--brick-001"
        assert item.status == "PLANNED"
        assert item.priority == 3
        assert item.metadata["source"]["state"] == "ACTIVE"
        assert result.import_state == "IMPORTED_NO_PROMOTION"
        assert store.connection.execute("SELECT COUNT(*) FROM evidence").fetchone()[0] == 0
        assert store.connection.execute("SELECT COUNT(*) FROM evidence_admission").fetchone()[0] == 0
        assert store.connection.execute("SELECT COUNT(*) FROM knowledge_proof").fetchone()[0] == 0


def test_authorized_structural_import_rechecks_late_collision_and_rolls_back_all_writes(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        _component_parent(store)
        original = _symbol_projection(store)
        second = AretV1SymbolDraft(
            "aret-symbol--component-pkg-stop", "aret-component--component", "FUNCTION", "pkg", "stop", "",
            {"source": {"domain_pack": "aret-v1", "legacy_table": "function_symbol", "source_id": "component:pkg!stop", "source_snapshot_sha256": "a" * 64}},
        )
        projection = replace(original, drafts=(original.drafts[0], second))
        preflight = replace(
            _preflight(store, table="function_symbol"),
            source_record_count=2,
            source_last_id="component:pkg!stop",
        )
        clear = check_aret_v1_structural_target_clear(preflight=preflight, projection=projection, target_store=store)
        authorization = authorize_aret_v1_structural_import(
            preflight=preflight, projection=projection, clear_check=clear, target_store=store,
            authorization_id="function-import-authorization-002", authorized_by="fixture",
        )
        SymbolService(store).create(
            "aret-symbol--component-pkg-stop", "aret-component--component", "FUNCTION", "pkg", "stop", actor="race"
        )
        before = store.audit_events()

        with pytest.raises(AretAuthorizedStructuralImportError):
            import_authorized_aret_v1_structural_page(
                preflight=preflight, projection=projection, authorization=authorization, target_store=store
            )

        assert SymbolService(store).get("aret-symbol--component-pkg-stop").id == "aret-symbol--component-pkg-stop"
        with pytest.raises(Exception):
            SymbolService(store).get("aret-symbol--component-pkg-run")
        assert store.connection.execute("SELECT COUNT(*) FROM resource_import_batch").fetchone()[0] == 0
        assert store.audit_events() == before


def test_authorized_structural_import_rejects_binding_drift_before_any_write(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        _component_parent(store)
        preflight, projection, authorization = _authorize_symbol(store)
        with pytest.raises(AretAuthorizedStructuralImportError):
            import_authorized_aret_v1_structural_page(
                preflight=preflight,
                projection=replace(projection, source_snapshot_sha256="f" * 64),
                authorization=authorization,
                target_store=store,
            )
        assert store.connection.execute("SELECT COUNT(*) FROM symbol").fetchone()[0] == 0
        assert store.connection.execute("SELECT COUNT(*) FROM resource_import_batch").fetchone()[0] == 0


def test_authorized_structural_import_uses_core_service_without_pack_sql_writes_or_epistemic_writes() -> None:
    source = (Path(__file__).parents[1] / "src" / "vera_mmu" / "domain_packs" / "aret" / "authorized_structural_import.py").read_text(encoding="utf-8")
    assert "commit_resource_import_batch" in source
    for forbidden in ("INSERT", "UPDATE", "DELETE", "connection.execute", "sqlite3", "Evidence", "Proof", "Admission", "Promotion", "subprocess", "requests", "urllib.", "socket", "os.system"):
        assert forbidden not in source
