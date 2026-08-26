from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import sqlite3

import pytest

from vera_mmu.domain_packs.aret import (
    AretRuntimeResolutionError,
    AretV1GitSourceIdentity,
    ARET_V1_BASELINE_REVISION,
    attest_aret_v1_component_source,
    component_import_preparation,
    inspect_aret_v1_runtime_snapshot_safety,
    inspect_aret_v1_schema_snapshot,
    aret_v1_schema_manifest,
    read_aret_v1_component_page,
    resolve_aret_v1_runtime,
)
from vera_mmu.identity import ProjectIdentity
from vera_mmu.domain_packs.aret import sqlite_schema


IDENTITY = ProjectIdentity(
    project_id="runtime-chain-fixture",
    profile_version="2.0",
    profile_hash="1" * 64,
    workspace_hash="2" * 64,
    project_hash="3" * 64,
)


def _create_snapshot(snapshot: Path) -> None:
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(snapshot)
    try:
        connection.execute("CREATE TABLE schema_migrations (version INTEGER)")
        for version in range(1, 7):
            connection.execute("INSERT INTO schema_migrations(version) VALUES(?)", (version,))
        for table in aret_v1_schema_manifest().application_tables:
            if table != "schema_migrations":
                connection.execute(f"CREATE TABLE {table} (id TEXT)")
        connection.execute("DROP TABLE component")
        connection.execute(
            "CREATE TABLE component (id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL, created_at TEXT NOT NULL, created_by TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO component VALUES ('CMP-001', 'Runtime chain', '', '2026-01-01T00:00:00Z', 'fixture')"
        )
        connection.commit()
    finally:
        connection.close()


def _preparation(snapshot: Path):
    return component_import_preparation(
        target_identity=IDENTITY,
        source_snapshot_sha256=sha256(snapshot.read_bytes()).hexdigest(),
        request_id="m4-a3-runtime-chain",
        requested_by="test",
    )


def test_external_runtime_override_flows_from_resolution_to_attestation_without_implicit_default(tmp_path: Path) -> None:
    source_root = tmp_path / "aret-source"
    source_root.mkdir()
    snapshot = tmp_path / "external-runtime" / "aret_memory.sqlite"
    _create_snapshot(snapshot)
    resolution = resolve_aret_v1_runtime(
        source_root=source_root,
        environment={"ARET_MEMORY_DIR": str(snapshot.parent)},
    )
    safety = inspect_aret_v1_runtime_snapshot_safety(resolution=resolution)

    attestation = attest_aret_v1_component_source(
        source_root=source_root,
        expected_legacy_revision=ARET_V1_BASELINE_REVISION,
        preparation=_preparation(snapshot),
        runtime_resolution=resolution,
        runtime_safety=safety,
    )

    assert attestation.source_root == source_root
    assert attestation.source_path == snapshot
    assert attestation.runtime_resolution_basis == "ARET_MEMORY_DIR_OVERRIDE"
    assert attestation.runtime_wal_state == "NO_WAL_SIDECARS"


def test_schema_and_reader_follow_verified_external_runtime_snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source_root = tmp_path / "aret-source"
    source_root.mkdir()
    snapshot = tmp_path / "external-runtime" / "aret_memory.sqlite"
    _create_snapshot(snapshot)
    digest = sha256(snapshot.read_bytes()).hexdigest()
    monkeypatch.setattr(sqlite_schema, "ARET_V1_BASELINE_REVISION", "0" * 40)
    source_identity = AretV1GitSourceIdentity(
        repository_root=source_root,
        source_root=source_root,
        commit_hash="0" * 40,
        expected_legacy_revision="0" * 40,
        source_snapshot_sha256=digest,
        source_path=snapshot,
    )

    inspection = inspect_aret_v1_schema_snapshot(source_root=source_root, source_identity=source_identity)
    page = read_aret_v1_component_page(
        source_root=source_root,
        schema_inspection=inspection,
        after_id=None,
        limit=10,
    )

    assert inspection.source_root == source_root
    assert inspection.source_path == snapshot
    assert [record.source_id for record in page.records] == ["CMP-001"]


def test_attestation_rejects_resolution_or_safety_not_bound_to_the_given_source_root(tmp_path: Path) -> None:
    source_root = tmp_path / "aret-source"
    source_root.mkdir()
    snapshot = tmp_path / "external-runtime" / "aret_memory.sqlite"
    _create_snapshot(snapshot)
    resolution = resolve_aret_v1_runtime(
        source_root=source_root,
        environment={"ARET_MEMORY_DIR": str(snapshot.parent)},
    )
    safety = inspect_aret_v1_runtime_snapshot_safety(resolution=resolution)

    other_source = tmp_path / "other-source"
    other_source.mkdir()
    with pytest.raises(AretRuntimeResolutionError):
        attest_aret_v1_component_source(
            source_root=other_source,
            expected_legacy_revision=ARET_V1_BASELINE_REVISION,
            preparation=_preparation(snapshot),
            runtime_resolution=resolution,
            runtime_safety=safety,
        )
