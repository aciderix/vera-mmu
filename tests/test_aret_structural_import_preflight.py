from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from vera_mmu.domain_packs.aret import (
    AretStructuralImportPreflightError,
    AretV1BrickSchemaConformance,
    AretV1BrickSourcePage,
    AretV1BrickSourceRecord,
    AretV1FunctionSymbolSchemaConformance,
    AretV1FunctionSymbolSourcePage,
    AretV1FunctionSymbolSourceRecord,
    AretV1SchemaSnapshotInspection,
    structural_import_preflight,
    structural_import_preparation,
)
from vera_mmu.domain_packs.aret.schema import aret_v1_schema_manifest
from vera_mmu.identity import ProjectIdentity


def _identity() -> ProjectIdentity:
    return ProjectIdentity("structural-import", "2.0", "a" * 64, "b" * 64, "c" * 64)


def _facts(tmp_path: Path):
    source_root = (tmp_path / "aret-memory").resolve()
    snapshot = source_root / ".aret-memory" / "aret_memory.sqlite"
    snapshot.parent.mkdir(parents=True)
    snapshot.write_bytes(b"structural-preflight-fixture")
    digest = sha256(snapshot.read_bytes()).hexdigest()
    manifest = aret_v1_schema_manifest()
    inspection = AretV1SchemaSnapshotInspection(
        source_path=snapshot,
        source_snapshot_sha256=digest,
        migration_versions=manifest.migration_versions,
        application_tables=manifest.application_tables,
        source_root=source_root,
    )
    function_conformance = AretV1FunctionSymbolSchemaConformance(snapshot, digest, (), (), ())
    brick_conformance = AretV1BrickSchemaConformance(snapshot, digest, (), (), (), (), ())
    return source_root, snapshot, digest, inspection, function_conformance, brick_conformance


def _function_page(snapshot: Path, digest: str) -> AretV1FunctionSymbolSourcePage:
    record = AretV1FunctionSymbolSourceRecord("component:pkg/mod!run", "component", "pkg/mod", "run", "cdecl", "now", "fixture")
    return AretV1FunctionSymbolSourcePage(snapshot, digest, (record,), None)


def _brick_page(snapshot: Path, digest: str) -> AretV1BrickSourcePage:
    record = AretV1BrickSourceRecord("brick-001", "component", "Retain state", "ACTIVE", "legacy state remains metadata", "M1", "win32", 3, "now", "fixture")
    return AretV1BrickSourcePage(snapshot, digest, (record,), None)


def test_function_symbol_preflight_binds_all_read_only_facts_without_write(tmp_path: Path) -> None:
    _, snapshot, digest, inspection, function_conformance, _ = _facts(tmp_path)
    preparation = structural_import_preparation(
        target_identity=_identity(),
        source_snapshot_sha256=digest,
        request_id="function-request-001",
        requested_by="fixture",
        legacy_table="function_symbol",
    )

    result = structural_import_preflight(
        preparation=preparation,
        schema_inspection=inspection,
        schema_conformance=function_conformance,
        source_page=_function_page(snapshot, digest),
        preflight_id="function-preflight-001",
        confirmed_by="fixture",
    )

    assert result.legacy_table == "function_symbol"
    assert result.resource_kind == "SYMBOL"
    assert result.source_record_count == 1
    assert result.collision_policy == "REJECT_EXISTING_TARGET"
    assert result.write_policy == "FORBID"
    assert result.promotion_policy == "FORBID"
    assert result.preflight_state == "PREFLIGHT_NOT_EXECUTABLE"


def test_brick_preflight_preserves_status_as_source_fact_without_lifecycle_write(tmp_path: Path) -> None:
    _, snapshot, digest, inspection, _, brick_conformance = _facts(tmp_path)
    preparation = structural_import_preparation(
        target_identity=_identity(),
        source_snapshot_sha256=digest,
        request_id="brick-request-001",
        requested_by="fixture",
        legacy_table="brick",
    )

    result = structural_import_preflight(
        preparation=preparation,
        schema_inspection=inspection,
        schema_conformance=brick_conformance,
        source_page=_brick_page(snapshot, digest),
        preflight_id="brick-preflight-001",
        confirmed_by="fixture",
    )

    assert result.legacy_table == "brick"
    assert result.resource_kind == "WORK_ITEM"
    assert result.source_first_id == "brick-001"
    assert result.lifecycle_policy == "PRESERVE_LEGACY_STATE_AS_METADATA"
    assert result.write_policy == "FORBID"


@pytest.mark.parametrize(
    "mutator",
    (
        lambda facts, page: replace(facts[3], source_snapshot_sha256="f" * 64),
        lambda facts, page: replace(facts[4], source_snapshot_sha256="f" * 64),
        lambda facts, page: replace(page, source_snapshot_sha256="f" * 64),
    ),
)
def test_function_preflight_rejects_divergent_bindings_before_any_write(tmp_path: Path, mutator) -> None:
    _, snapshot, digest, inspection, function_conformance, _ = _facts(tmp_path)
    preparation = structural_import_preparation(
        target_identity=_identity(), source_snapshot_sha256=digest, request_id="function-request-002", requested_by="fixture", legacy_table="function_symbol"
    )
    page = _function_page(snapshot, digest)
    mutated = mutator((None, snapshot, digest, inspection, function_conformance, None), page)
    if isinstance(mutated, AretV1SchemaSnapshotInspection):
        inspection = mutated
    elif isinstance(mutated, AretV1FunctionSymbolSchemaConformance):
        function_conformance = mutated
    else:
        page = mutated

    with pytest.raises(AretStructuralImportPreflightError):
        structural_import_preflight(
            preparation=preparation,
            schema_inspection=inspection,
            schema_conformance=function_conformance,
            source_page=page,
            preflight_id="function-preflight-002",
            confirmed_by="fixture",
        )


def test_structural_preflight_rejects_wrong_page_type_and_noncanonical_brick_facts(tmp_path: Path) -> None:
    _, snapshot, digest, inspection, function_conformance, brick_conformance = _facts(tmp_path)
    function_preparation = structural_import_preparation(
        target_identity=_identity(), source_snapshot_sha256=digest, request_id="function-request-003", requested_by="fixture", legacy_table="function_symbol"
    )
    with pytest.raises(AretStructuralImportPreflightError):
        structural_import_preflight(
            preparation=function_preparation,
            schema_inspection=inspection,
            schema_conformance=function_conformance,
            source_page=_brick_page(snapshot, digest),
            preflight_id="function-preflight-003",
            confirmed_by="fixture",
        )

    brick_preparation = structural_import_preparation(
        target_identity=_identity(), source_snapshot_sha256=digest, request_id="brick-request-002", requested_by="fixture", legacy_table="brick"
    )
    invalid_record = replace(_brick_page(snapshot, digest).records[0], state="UNKNOWN", priority=0)
    with pytest.raises(AretStructuralImportPreflightError):
        structural_import_preflight(
            preparation=brick_preparation,
            schema_inspection=inspection,
            schema_conformance=brick_conformance,
            source_page=replace(_brick_page(snapshot, digest), records=(invalid_record,)),
            preflight_id="brick-preflight-002",
            confirmed_by="fixture",
        )


def test_structural_preflight_modules_have_no_source_io_or_write_capability() -> None:
    base = Path(__file__).parents[1] / "src" / "vera_mmu" / "domain_packs" / "aret"
    for name in ("structural_import_preparation.py", "structural_import_preflight.py"):
        source = (base / name).read_text(encoding="utf-8")
        for forbidden in ("sqlite3", ".open(", "read_bytes", "INSERT", "UPDATE", "DELETE", "ImportBatchService", "SymbolService", "WorkItemService", "subprocess", "requests", "urllib.", "socket", "os.system"):
            assert forbidden not in source
