from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from vera_mmu.domain_packs.aret import (
    AretComponentEntityProjectionError,
    AretV1ComponentImportPreflight,
    AretV1ComponentSourcePage,
    AretV1ComponentSourceRecord,
    project_aret_v1_component_entities,
)
from vera_mmu.identity import ProjectIdentity


SNAPSHOT_HASH = "a" * 64
TARGET_IDENTITY = ProjectIdentity(
    project_id="vera-target",
    profile_version="2.0",
    profile_hash="1" * 64,
    workspace_hash="2" * 64,
    project_hash="3" * 64,
)


def _page() -> AretV1ComponentSourcePage:
    return AretV1ComponentSourcePage(
        source_path=Path("/tmp/aret-fixture/.aret-memory/aret_memory.sqlite"),
        source_snapshot_sha256=SNAPSHOT_HASH,
        records=(
            AretV1ComponentSourceRecord("CMP-001", "Alpha", "First", "2026-01-01T00:00:00Z", "fixture"),
            AretV1ComponentSourceRecord("CMP-002", "Beta", "Second", "2026-01-02T00:00:00Z", "fixture"),
        ),
        next_after_id=None,
    )


def _preflight() -> AretV1ComponentImportPreflight:
    return AretV1ComponentImportPreflight(
        target_identity=TARGET_IDENTITY,
        request_id="m4-12-component-projection",
        preflight_id="m4-12-component-page",
        confirmed_by="integration-test",
        source_snapshot_sha256=SNAPSHOT_HASH,
        source_record_count=2,
        source_first_id="CMP-001",
        source_last_id="CMP-002",
    )


def test_projection_is_deterministic_raw_and_not_writable() -> None:
    projection = project_aret_v1_component_entities(preflight=_preflight(), source_page=_page())

    assert projection.target_identity == TARGET_IDENTITY
    assert projection.source_snapshot_sha256 == SNAPSHOT_HASH
    assert projection.projection_state == "PROJECTED_NOT_WRITABLE"
    assert projection.entity_type_id == "component"
    assert projection.entity_type_registration_required is True
    assert len(projection.drafts) == 2
    first = projection.drafts[0]
    assert first.target_identifier == "aret-component--CMP-001"
    assert first.target_address == "vera://vera-target/entity/aret-component--CMP-001"
    assert first.title == "Alpha"
    assert first.description == "First"
    assert first.metadata == {
        "source": {
            "domain_pack": "aret-v1",
            "legacy_table": "component",
            "source_id": "CMP-001",
            "source_snapshot_sha256": SNAPSHOT_HASH,
            "source_created_at": "2026-01-01T00:00:00Z",
            "source_created_by": "fixture",
        }
    }
    assert projection == project_aret_v1_component_entities(preflight=_preflight(), source_page=_page())


def test_projection_rejects_non_preflight_or_mismatched_source_page() -> None:
    with pytest.raises(AretComponentEntityProjectionError):
        project_aret_v1_component_entities(
            preflight=replace(_preflight(), preflight_state="EXECUTED"),
            source_page=_page(),
        )

    with pytest.raises(AretComponentEntityProjectionError):
        project_aret_v1_component_entities(
            preflight=_preflight(),
            source_page=replace(_page(), source_snapshot_sha256="b" * 64),
        )

    with pytest.raises(AretComponentEntityProjectionError):
        project_aret_v1_component_entities(
            preflight=replace(_preflight(), source_record_count=1),
            source_page=_page(),
        )


def test_projection_rejects_noncanonical_or_unsafe_source_fields() -> None:
    unsafe_identifier = replace(
        _page(),
        records=(AretV1ComponentSourceRecord("../escape", "Alpha", "First", "t", "fixture"),),
    )
    with pytest.raises(AretComponentEntityProjectionError):
        project_aret_v1_component_entities(
            preflight=replace(_preflight(), source_record_count=1, source_first_id="../escape", source_last_id="../escape"),
            source_page=unsafe_identifier,
        )

    noncanonical_title = replace(
        _page(),
        records=(AretV1ComponentSourceRecord("CMP-001", " Alpha", "First", "t", "fixture"),),
    )
    with pytest.raises(AretComponentEntityProjectionError):
        project_aret_v1_component_entities(
            preflight=replace(_preflight(), source_record_count=1, source_first_id="CMP-001", source_last_id="CMP-001"),
            source_page=noncanonical_title,
        )


def test_projection_module_has_no_store_or_write_capability() -> None:
    source = (
        Path(__file__).parents[1]
        / "src"
        / "vera_mmu"
        / "domain_packs"
        / "aret"
        / "component_entity_projection.py"
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
        "EntityService",
    ):
        assert forbidden not in source
