from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from vera_mmu.domain_packs.aret import (
    ARET_V1_BASELINE_REVISION,
    AretSourceAttestationError,
    attest_aret_v1_component_source,
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


def _make_source(tmp_path: Path, payload: bytes = b"ARET V1 snapshot fixture") -> tuple[Path, bytes]:
    source_root = tmp_path / "aret-fixture"
    source_file = source_root / ".aret-memory" / "aret_memory.sqlite"
    source_file.parent.mkdir(parents=True)
    source_file.write_bytes(payload)
    return source_root, payload


def _preparation(payload: bytes):
    return component_import_preparation(
        target_identity=TARGET_IDENTITY,
        source_snapshot_sha256=sha256(payload).hexdigest(),
        request_id="m4-7-component-fixture",
        requested_by="integration-test",
    )


def test_attestation_hashes_only_the_expected_read_only_v1_snapshot(tmp_path: Path) -> None:
    source_root, payload = _make_source(tmp_path)
    before = (source_root / ".aret-memory" / "aret_memory.sqlite").read_bytes()

    attestation = attest_aret_v1_component_source(
        source_root=source_root,
        expected_legacy_revision=ARET_V1_BASELINE_REVISION,
        preparation=_preparation(payload),
    )

    assert attestation.source_path == source_root / ".aret-memory" / "aret_memory.sqlite"
    assert attestation.source_snapshot_sha256 == sha256(payload).hexdigest()
    assert attestation.source_size_bytes == len(payload)
    assert attestation.expected_legacy_revision == ARET_V1_BASELINE_REVISION
    assert attestation.source_schema_version == 6
    assert attestation.source_access_mode == "READ_ONLY_SNAPSHOT"
    assert attestation.attestation_state == "ATTESTED_SNAPSHOT_ONLY"
    assert (source_root / ".aret-memory" / "aret_memory.sqlite").read_bytes() == before


@pytest.mark.parametrize(
    "expected_revision",
    [
        "",
        "0" * 40,
        "7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac5",
        "not-a-revision",
    ],
)
def test_attestation_rejects_any_legacy_reference_except_the_fixed_baseline(
    tmp_path: Path, expected_revision: str
) -> None:
    source_root, payload = _make_source(tmp_path)

    with pytest.raises(AretSourceAttestationError):
        attest_aret_v1_component_source(
            source_root=source_root,
            expected_legacy_revision=expected_revision,
            preparation=_preparation(payload),
        )


def test_attestation_rejects_missing_or_mismatched_snapshot(tmp_path: Path) -> None:
    source_root, payload = _make_source(tmp_path)

    with pytest.raises(AretSourceAttestationError):
        attest_aret_v1_component_source(
            source_root=tmp_path / "missing-root",
            expected_legacy_revision=ARET_V1_BASELINE_REVISION,
            preparation=_preparation(payload),
        )

    with pytest.raises(AretSourceAttestationError):
        attest_aret_v1_component_source(
            source_root=source_root,
            expected_legacy_revision=ARET_V1_BASELINE_REVISION,
            preparation=replace(_preparation(payload), source_snapshot_sha256="b" * 64),
        )


def test_attestation_rejects_symlinked_root_or_snapshot(tmp_path: Path) -> None:
    physical_root, payload = _make_source(tmp_path)
    root_link = tmp_path / "root-link"
    root_link.symlink_to(physical_root, target_is_directory=True)

    with pytest.raises(AretSourceAttestationError):
        attest_aret_v1_component_source(
            source_root=root_link,
            expected_legacy_revision=ARET_V1_BASELINE_REVISION,
            preparation=_preparation(payload),
        )

    source_file = physical_root / ".aret-memory" / "aret_memory.sqlite"
    outside_file = tmp_path / "outside.sqlite"
    outside_file.write_bytes(payload)
    source_file.unlink()
    source_file.symlink_to(outside_file)

    with pytest.raises(AretSourceAttestationError):
        attest_aret_v1_component_source(
            source_root=physical_root,
            expected_legacy_revision=ARET_V1_BASELINE_REVISION,
            preparation=_preparation(payload),
        )


def test_attestation_rejects_a_preparation_that_is_not_pending_or_component_bound(tmp_path: Path) -> None:
    source_root, payload = _make_source(tmp_path)

    with pytest.raises(AretSourceAttestationError):
        attest_aret_v1_component_source(
            source_root=source_root,
            expected_legacy_revision=ARET_V1_BASELINE_REVISION,
            preparation=replace(_preparation(payload), execution_state="EXECUTED"),
        )

    with pytest.raises(AretSourceAttestationError):
        attest_aret_v1_component_source(
            source_root=source_root,
            expected_legacy_revision=ARET_V1_BASELINE_REVISION,
            preparation=replace(_preparation(payload), legacy_table="knowledge"),
        )


def test_attestation_module_is_snapshot_only_and_not_an_importer() -> None:
    source = (
        Path(__file__).parents[1]
        / "src"
        / "vera_mmu"
        / "domain_packs"
        / "aret"
        / "source_attestation.py"
    ).read_text(encoding="utf-8")

    for forbidden in (
        "sqlite3",
        "subprocess",
        "os.system",
        "socket",
        "requests",
        "urllib.",
        "INSERT",
        "UPDATE",
        "DELETE",
    ):
        assert forbidden not in source
