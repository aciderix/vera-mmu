from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from vera_mmu.domain_packs.aret import (
    AretStructuralPostValidationError,
    post_validate_authorized_aret_v1_structural_page,
)
from tests.test_aret_authorized_structural_import import _authorize_brick, _authorize_symbol
from tests.test_aret_structural_target_collision import _component_parent, _store


def test_symbol_post_validation_reads_exact_ledger_resource_and_stays_zero_write(tmp_path: Path) -> None:
    from vera_mmu.domain_packs.aret import import_authorized_aret_v1_structural_page

    with _store(tmp_path) as store:
        _component_parent(store)
        preflight, projection, authorization = _authorize_symbol(store)
        result = import_authorized_aret_v1_structural_page(
            preflight=preflight, projection=projection, authorization=authorization, target_store=store
        )
        before = store.audit_events()

        validation = post_validate_authorized_aret_v1_structural_page(
            authorization=authorization, projection=projection, import_result=result, target_store=store
        )

        assert validation.validation_state == "POST_VALIDATED_NO_PROMOTION"
        assert validation.resource_kind == "SYMBOL"
        assert validation.validated_resource_count == 1
        assert validation.source_identifiers == ("component:pkg!run",)
        assert store.audit_events() == before
        assert store.connection.execute("SELECT COUNT(*) FROM evidence").fetchone()[0] == 0
        assert store.connection.execute("SELECT COUNT(*) FROM evidence_admission").fetchone()[0] == 0
        assert store.connection.execute("SELECT COUNT(*) FROM knowledge_proof").fetchone()[0] == 0


def test_brick_post_validation_retains_planned_core_status_and_active_legacy_metadata(tmp_path: Path) -> None:
    from vera_mmu.domain_packs.aret import import_authorized_aret_v1_structural_page

    with _store(tmp_path) as store:
        preflight, projection, authorization = _authorize_brick(store)
        result = import_authorized_aret_v1_structural_page(
            preflight=preflight, projection=projection, authorization=authorization, target_store=store
        )
        validation = post_validate_authorized_aret_v1_structural_page(
            authorization=authorization, projection=projection, import_result=result, target_store=store
        )

        assert validation.resource_kind == "WORK_ITEM"
        assert validation.validation_state == "POST_VALIDATED_NO_PROMOTION"
        assert result.resources[0].status == "PLANNED"
        assert result.resources[0].metadata["source"]["state"] == "ACTIVE"


def test_structural_post_validation_rejects_result_or_projection_binding_drift_without_writing(tmp_path: Path) -> None:
    from vera_mmu.domain_packs.aret import import_authorized_aret_v1_structural_page

    with _store(tmp_path) as store:
        _component_parent(store)
        preflight, projection, authorization = _authorize_symbol(store)
        result = import_authorized_aret_v1_structural_page(
            preflight=preflight, projection=projection, authorization=authorization, target_store=store
        )
        before = store.audit_events()
        with pytest.raises(AretStructuralPostValidationError):
            post_validate_authorized_aret_v1_structural_page(
                authorization=authorization,
                projection=replace(projection, source_snapshot_sha256="f" * 64),
                import_result=result,
                target_store=store,
            )
        with pytest.raises(AretStructuralPostValidationError):
            post_validate_authorized_aret_v1_structural_page(
                authorization=authorization,
                projection=projection,
                import_result=replace(result, import_state="PROMOTED"),
                target_store=store,
            )
        assert store.audit_events() == before


def test_structural_post_validation_module_is_read_only_and_has_no_epistemic_capability() -> None:
    source = (Path(__file__).parents[1] / "src" / "vera_mmu" / "domain_packs" / "aret" / "structural_post_validation.py").read_text(encoding="utf-8")
    for required in ("SELECT source_system", "SELECT source_identifier", "POST_VALIDATED_NO_PROMOTION"):
        assert required in source
    for forbidden in ("INSERT", "UPDATE", "DELETE", "ImportBatchService", "Evidence", "Proof", "Admission", "Promotion", "subprocess", "requests", "urllib.", "socket", "os.system"):
        assert forbidden not in source
