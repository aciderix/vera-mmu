from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from vera_mmu.domain_packs.aret import (
    AretComponentImportPreparationError,
    component_import_preparation,
)
from vera_mmu.identity import ProjectIdentity


TARGET_IDENTITY = ProjectIdentity(
    project_id="vera-fixture",
    profile_version="2.0",
    profile_hash="1" * 64,
    workspace_hash="2" * 64,
    project_hash="3" * 64,
)
SOURCE_SNAPSHOT_SHA256 = "a" * 64


def test_component_import_preparation_binds_one_explicit_unverified_request() -> None:
    preparation = component_import_preparation(
        target_identity=TARGET_IDENTITY,
        source_snapshot_sha256=SOURCE_SNAPSHOT_SHA256,
        request_id="m4-6-component-fixture",
        requested_by="integration-test",
    )

    assert preparation.target_identity is TARGET_IDENTITY
    assert preparation.source_snapshot_sha256 == SOURCE_SNAPSHOT_SHA256
    assert preparation.request_id == "m4-6-component-fixture"
    assert preparation.requested_by == "integration-test"
    assert preparation.legacy_table == "component"
    assert preparation.vera_resource == "entity"
    assert preparation.vera_type == "COMPONENT"
    assert preparation.source_schema_version == 6
    assert preparation.requires_explicit_import is True
    assert preparation.execution_state == "PREPARED_NOT_EXECUTED"
    assert preparation.source_attestation_state == "UNVERIFIED_DECLARATION"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_snapshot_sha256", "A" * 64),
        ("source_snapshot_sha256", "a" * 63),
        ("source_snapshot_sha256", "not-a-sha256"),
        ("request_id", ""),
        ("request_id", "M4-6 component"),
        ("requested_by", ""),
        ("requested_by", "actor\nname"),
    ],
)
def test_component_import_preparation_rejects_unbound_or_noncanonical_claims(field: str, value: str) -> None:
    arguments = {
        "target_identity": TARGET_IDENTITY,
        "source_snapshot_sha256": SOURCE_SNAPSHOT_SHA256,
        "request_id": "m4-6-component-fixture",
        "requested_by": "integration-test",
    }
    arguments[field] = value

    with pytest.raises(AretComponentImportPreparationError):
        component_import_preparation(**arguments)


def test_component_import_preparation_rejects_non_identity_target() -> None:
    with pytest.raises(AretComponentImportPreparationError):
        component_import_preparation(
            target_identity=replace(TARGET_IDENTITY).as_dict(),
            source_snapshot_sha256=SOURCE_SNAPSHOT_SHA256,
            request_id="m4-6-component-fixture",
            requested_by="integration-test",
        )


def test_component_import_preparation_module_is_declarative_only() -> None:
    source = (
        Path(__file__).parents[1]
        / "src"
        / "vera_mmu"
        / "domain_packs"
        / "aret"
        / "import_preparation.py"
    ).read_text(encoding="utf-8")

    for forbidden in ("sqlite3", "open(", "Path(", "os.", "INSERT", "UPDATE", "DELETE"):
        assert forbidden not in source
