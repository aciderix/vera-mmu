from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import sqlite3

import pytest

from vera_mmu.domain_packs.aret import (
    AretSqliteSchemaInspectionError,
    AretV1GitSourceIdentity,
    inspect_aret_v1_schema_snapshot,
)
import vera_mmu.domain_packs.aret.sqlite_schema as sqlite_schema
from vera_mmu.domain_packs.aret.schema import aret_v1_schema_manifest


def _make_source(
    tmp_path: Path,
    *,
    migration_versions: tuple[int, ...] = (1, 2, 3, 4, 5, 6),
    table_names: tuple[str, ...] | None = None,
) -> tuple[Path, Path]:
    source_root = (tmp_path / "aret-repository" / "aret-memory").resolve()
    snapshot = source_root / ".aret-memory" / "aret_memory.sqlite"
    snapshot.parent.mkdir(parents=True)
    expected_tables = table_names or aret_v1_schema_manifest().application_tables

    connection = sqlite3.connect(snapshot)
    try:
        connection.execute("CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY)")
        connection.executemany("INSERT INTO schema_migrations(version) VALUES (?)", [(version,) for version in migration_versions])
        for table_name in expected_tables:
            if table_name != "schema_migrations":
                connection.execute(f"CREATE TABLE {table_name} (id TEXT)")
        connection.execute("CREATE TABLE knowledge_fts_shadow (id TEXT)")
        connection.commit()
    finally:
        connection.close()
    return source_root, snapshot


def _identity(source_root: Path, snapshot: Path, revision: str) -> AretV1GitSourceIdentity:
    return AretV1GitSourceIdentity(
        repository_root=source_root.parent,
        source_root=source_root,
        commit_hash=revision,
        expected_legacy_revision=revision,
        source_snapshot_sha256=sha256(snapshot.read_bytes()).hexdigest(),
    )


@pytest.fixture
def verified_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, AretV1GitSourceIdentity]:
    source_root, snapshot = _make_source(tmp_path)
    revision = "0" * 40
    monkeypatch.setattr(sqlite_schema, "ARET_V1_BASELINE_REVISION", revision)
    return source_root, snapshot, _identity(source_root, snapshot, revision)


def test_schema_inspection_reads_only_manifest_metadata(
    verified_source: tuple[Path, Path, AretV1GitSourceIdentity]
) -> None:
    source_root, snapshot, identity = verified_source
    before = snapshot.read_bytes()

    inspection = inspect_aret_v1_schema_snapshot(
        source_root=source_root,
        source_identity=identity,
    )

    manifest = aret_v1_schema_manifest()
    assert inspection.source_path == snapshot
    assert inspection.migration_versions == manifest.migration_versions
    assert inspection.application_tables == manifest.application_tables
    assert inspection.source_access_mode == "SQLITE_READ_ONLY_SCHEMA"
    assert inspection.inspection_state == "SCHEMA_MANIFEST_VERIFIED"
    assert snapshot.read_bytes() == before


def test_schema_inspection_rejects_manifest_or_snapshot_hash_mismatch(
    verified_source: tuple[Path, Path, AretV1GitSourceIdentity]
) -> None:
    source_root, snapshot, identity = verified_source
    snapshot.write_bytes(snapshot.read_bytes() + b"drift")

    with pytest.raises(AretSqliteSchemaInspectionError):
        inspect_aret_v1_schema_snapshot(source_root=source_root, source_identity=identity)


def test_schema_inspection_rejects_migration_or_table_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_root, snapshot = _make_source(tmp_path, migration_versions=(1, 2, 3, 4, 5))
    revision = "1" * 40
    monkeypatch.setattr(sqlite_schema, "ARET_V1_BASELINE_REVISION", revision)

    with pytest.raises(AretSqliteSchemaInspectionError):
        inspect_aret_v1_schema_snapshot(
            source_root=source_root,
            source_identity=_identity(source_root, snapshot, revision),
        )

    table_names = tuple(table for table in aret_v1_schema_manifest().application_tables if table != "asset")
    source_root, snapshot = _make_source(tmp_path / "tables", table_names=table_names)
    with pytest.raises(AretSqliteSchemaInspectionError):
        inspect_aret_v1_schema_snapshot(
            source_root=source_root,
            source_identity=_identity(source_root, snapshot, revision),
        )


def test_schema_inspection_rejects_unverified_identity_or_path_binding(
    verified_source: tuple[Path, Path, AretV1GitSourceIdentity], tmp_path: Path
) -> None:
    source_root, _, identity = verified_source

    with pytest.raises(AretSqliteSchemaInspectionError):
        inspect_aret_v1_schema_snapshot(
            source_root=tmp_path / "outside",
            source_identity=identity,
        )

    with pytest.raises(AretSqliteSchemaInspectionError):
        inspect_aret_v1_schema_snapshot(
            source_root=source_root,
            source_identity=replace(identity, identity_state="UNVERIFIED"),
        )


def test_schema_module_permits_only_read_only_metadata_queries() -> None:
    source = (
        Path(__file__).parents[1]
        / "src"
        / "vera_mmu"
        / "domain_packs"
        / "aret"
        / "sqlite_schema.py"
    ).read_text(encoding="utf-8")

    for required in ("sqlite3.connect", "mode=ro", "PRAGMA query_only", "schema_migrations", "sqlite_schema"):
        assert required in source
    for forbidden in (
        "INSERT",
        "UPDATE",
        "DELETE",
        "SELECT *",
        "subprocess",
        "requests",
        "urllib.",
        "socket",
        "os.system",
    ):
        assert forbidden not in source
