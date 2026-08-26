from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from vera_mmu.domain_packs.aret import (
    AretComponentImportPreflightError,
    AretV1ComponentSourcePage,
    AretV1ComponentSourceRecord,
    AretV1SchemaSnapshotInspection,
    component_import_preflight,
    component_import_preparation,
)
from vera_mmu.domain_packs.aret.schema import aret_v1_schema_manifest
from vera_mmu.identity import ProjectIdentity


SNAPSHOT_HASH = "a" * 64
TARGET_IDENTITY = ProjectIdentity(
    project_id="vera-target",
    profile_version="2.0",
    profile_hash="1" * 64,
    workspace_hash="2" * 64,
    project_hash="3" * 64,
)


def _inspection() -> AretV1SchemaSnapshotInspection:
    manifest = aret_v1_schema_manifest()
    return AretV1SchemaSnapshotInspection(
        source_path=Path("/tmp/aret-fixture/.aret-memory/aret_memory.sqlite"),
        source_snapshot_sha256=SNAPSHOT_HASH,
        migration_versions=manifest.migration_versions,
        application_tables=manifest.application_tables,
    )


def _page() -> AretV1ComponentSourcePage:
    return AretV1ComponentSourcePage(
        source_path=_inspection().source_path,
        source_snapshot_sha256=SNAPSHOT_HASH,
        records=(
            AretV1ComponentSourceRecord("CMP-001", "Alpha", "A", "2026-01-01T00:00:00Z", "fixture"),
            AretV1ComponentSourceRecord("CMP-002", "Beta", "B", "2026-01-02T00:00:00Z", "fixture"),
        ),
        next_after_id="CMP-002",
    )


def _preparation():
    return component_import_preparation(
        target_identity=TARGET_IDENTITY,
        source_snapshot_sha256=SNAPSHOT_HASH,
        request_id="m4-11-component-preflight",
        requested_by="integration-test",
    )


def test_preflight_binds_component_request_to_verified_snapshot_and_zero_write_policy() -> None:
    preflight = component_import_preflight(
        preparation=_preparation(),
        schema_inspection=_inspection(),
        source_page=_page(),
        preflight_id="m4-11-component-page",
        confirmed_by="integration-test",
    )

    assert preflight.target_identity == TARGET_IDENTITY
    assert preflight.request_id == "m4-11-component-preflight"
    assert preflight.source_snapshot_sha256 == SNAPSHOT_HASH
    assert preflight.source_record_count == 2
    assert preflight.source_first_id == "CMP-001"
    assert preflight.source_last_id == "CMP-002"
    assert preflight.collision_policy == "REJECT_EXISTING_TARGET"
    assert preflight.merge_policy == "FORBID"
    assert preflight.promotion_policy == "FORBID"
    assert preflight.write_policy == "FORBID"
    assert preflight.rollback_requirement == "REQUIRED_BEFORE_WRITE"
    assert preflight.audit_requirement == "REQUIRED_BEFORE_WRITE"
    assert preflight.provenance_requirement == "REQUIRED_BEFORE_WRITE"
    assert preflight.preflight_state == "PREFLIGHT_NOT_EXECUTABLE"


def test_preflight_rejects_any_non_pending_or_non_component_preparation() -> None:
    for preparation in (
        replace(_preparation(), execution_state="EXECUTED"),
        replace(_preparation(), requires_explicit_import=False),
        replace(_preparation(), legacy_table="knowledge"),
        replace(_preparation(), vera_type="KNOWLEDGE"),
    ):
        with pytest.raises(AretComponentImportPreflightError):
            component_import_preflight(
                preparation=preparation,
                schema_inspection=_inspection(),
                source_page=_page(),
                preflight_id="m4-11-component-page",
                confirmed_by="integration-test",
            )


def test_preflight_rejects_unverified_or_mismatched_page_and_inspection() -> None:
    with pytest.raises(AretComponentImportPreflightError):
        component_import_preflight(
            preparation=_preparation(),
            schema_inspection=replace(_inspection(), inspection_state="UNVERIFIED"),
            source_page=_page(),
            preflight_id="m4-11-component-page",
            confirmed_by="integration-test",
        )

    with pytest.raises(AretComponentImportPreflightError):
        component_import_preflight(
            preparation=_preparation(),
            schema_inspection=_inspection(),
            source_page=replace(_page(), source_snapshot_sha256="b" * 64),
            preflight_id="m4-11-component-page",
            confirmed_by="integration-test",
        )

    with pytest.raises(AretComponentImportPreflightError):
        component_import_preflight(
            preparation=_preparation(),
            schema_inspection=_inspection(),
            source_page=replace(_page(), records=()),
            preflight_id="m4-11-component-page",
            confirmed_by="integration-test",
        )


def test_preflight_rejects_unordered_records_or_noncanonical_confirmation() -> None:
    unordered = replace(
        _page(),
        records=(
            AretV1ComponentSourceRecord("CMP-002", "Beta", "B", "t2", "fixture"),
            AretV1ComponentSourceRecord("CMP-001", "Alpha", "A", "t1", "fixture"),
        ),
    )
    with pytest.raises(AretComponentImportPreflightError):
        component_import_preflight(
            preparation=_preparation(),
            schema_inspection=_inspection(),
            source_page=unordered,
            preflight_id="m4-11-component-page",
            confirmed_by="integration-test",
        )

    with pytest.raises(AretComponentImportPreflightError):
        component_import_preflight(
            preparation=_preparation(),
            schema_inspection=_inspection(),
            source_page=_page(),
            preflight_id="BAD",
            confirmed_by="integration-test\nother",
        )


def test_preflight_module_has_no_source_or_vera_write_capability() -> None:
    source = (
        Path(__file__).parents[1]
        / "src"
        / "vera_mmu"
        / "domain_packs"
        / "aret"
        / "component_import_preflight.py"
    ).read_text(encoding="utf-8")

    for forbidden in (
        "sqlite3",
        "open(",
        "INSERT",
        "UPDATE",
        "DELETE",
        "subprocess",
        "requests",
        "urllib.",
        "socket",
        "os.system",
        "MemoryStore",
    ):
        assert forbidden not in source
