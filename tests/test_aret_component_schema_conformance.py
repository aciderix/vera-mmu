from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import sqlite3

import pytest

from vera_mmu.domain_packs.aret import (
    AretComponentSchemaConformanceError,
    AretV1GitSourceIdentity,
    inspect_aret_v1_component_schema,
    inspect_aret_v1_schema_snapshot,
)
import vera_mmu.domain_packs.aret.sqlite_schema as sqlite_schema
from vera_mmu.domain_packs.aret.schema import aret_v1_schema_manifest


_COMPONENT_SQL = """
CREATE TABLE component (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL
) STRICT
"""


def _make_source(tmp_path: Path, *, component_sql: str = _COMPONENT_SQL) -> tuple[Path, Path]:
    source_root = (tmp_path / "aret-repository" / "aret-memory").resolve()
    snapshot = source_root / ".aret-memory" / "aret_memory.sqlite"
    snapshot.parent.mkdir(parents=True)
    connection = sqlite3.connect(snapshot)
    try:
        connection.execute("CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY)")
        connection.executemany("INSERT INTO schema_migrations(version) VALUES (?)", [(version,) for version in range(1, 7)])
        for table_name in aret_v1_schema_manifest().application_tables:
            if table_name not in {"schema_migrations", "component"}:
                connection.execute(f"CREATE TABLE {table_name} (id TEXT)")
        connection.execute(component_sql)
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


def _inspection(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, component_sql: str = _COMPONENT_SQL):
    source_root, snapshot = _make_source(tmp_path, component_sql=component_sql)
    revision = "0" * 40
    monkeypatch.setattr(sqlite_schema, "ARET_V1_BASELINE_REVISION", revision)
    return inspect_aret_v1_schema_snapshot(
        source_root=source_root,
        source_identity=_identity(source_root, snapshot, revision),
    )


def test_component_schema_conformance_verifies_exact_import_columns_read_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inspection = _inspection(tmp_path, monkeypatch)
    before = inspection.source_path.read_bytes()

    result = inspect_aret_v1_component_schema(inspection=inspection)

    assert result.columns == (
        ("id", "TEXT", True, True, None),
        ("title", "TEXT", True, False, None),
        ("description", "TEXT", True, False, "''"),
        ("created_at", "TEXT", True, False, None),
        ("created_by", "TEXT", True, False, None),
    )
    assert result.conformance_state == "COMPONENT_SCHEMA_CONFORMANT"
    assert inspection.source_path.read_bytes() == before


@pytest.mark.parametrize(
    "component_sql",
    (
        "CREATE TABLE component (id TEXT PRIMARY KEY, title TEXT NOT NULL, created_at TEXT NOT NULL, created_by TEXT NOT NULL) STRICT",
        "CREATE TABLE component (id TEXT PRIMARY KEY, title TEXT, description TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, created_by TEXT NOT NULL) STRICT",
        "CREATE TABLE component (id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, created_by TEXT NOT NULL, extra TEXT) STRICT",
    ),
)
def test_component_schema_conformance_rejects_column_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, component_sql: str
) -> None:
    inspection = _inspection(tmp_path, monkeypatch, component_sql=component_sql)

    with pytest.raises(AretComponentSchemaConformanceError):
        inspect_aret_v1_component_schema(inspection=inspection)


def test_component_schema_conformance_rejects_unverified_or_mutated_inspection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inspection = _inspection(tmp_path, monkeypatch)

    with pytest.raises(AretComponentSchemaConformanceError):
        inspect_aret_v1_component_schema(inspection=replace(inspection, inspection_state="UNVERIFIED"))


def test_component_schema_module_is_read_only_and_has_no_import_write_capability() -> None:
    source = (
        Path(__file__).parents[1]
        / "src"
        / "vera_mmu"
        / "domain_packs"
        / "aret"
        / "component_schema_conformance.py"
    ).read_text(encoding="utf-8")

    for required in ("PRAGMA table_info(component)", "mode=ro", "COMPONENT_SCHEMA_CONFORMANT"):
        assert required in source
    for forbidden in ("INSERT", "UPDATE", "DELETE", "EntityService", "ImportBatchService", "subprocess", "requests", "urllib.", "socket", "os.system"):
        assert forbidden not in source
