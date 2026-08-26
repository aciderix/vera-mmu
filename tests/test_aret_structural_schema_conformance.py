from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import sqlite3

import pytest

from vera_mmu.domain_packs.aret import (
    AretStructuralSchemaConformanceError,
    AretV1GitSourceIdentity,
    inspect_aret_v1_brick_schema,
    inspect_aret_v1_function_symbol_schema,
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
_FUNCTION_SQL = """
CREATE TABLE function_symbol (
    id TEXT PRIMARY KEY,
    component_id TEXT NOT NULL REFERENCES component(id),
    module TEXT NOT NULL DEFAULT '',
    symbol TEXT NOT NULL,
    calling_convention TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL,
    UNIQUE(component_id, module, symbol)
) STRICT
"""
_BRICK_SQL = """
CREATE TABLE brick (
    id TEXT PRIMARY KEY,
    component_id TEXT REFERENCES component(id),
    title TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('PLANNED', 'ACTIVE', 'BLOCKED', 'DONE', 'OBSOLETE')),
    description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL,
    milestone TEXT,
    target_platform TEXT,
    priority INTEGER NOT NULL DEFAULT 3 CHECK (priority BETWEEN 1 AND 5)
) STRICT
"""


def _make_source(
    tmp_path: Path,
    *,
    function_sql: str = _FUNCTION_SQL,
    brick_sql: str = _BRICK_SQL,
    roadmap_index_sql: str = "CREATE INDEX idx_brick_roadmap ON brick(milestone, target_platform, priority, state, component_id, id)",
) -> tuple[Path, Path]:
    source_root = (tmp_path / "aret-repository" / "aret-memory").resolve()
    snapshot = source_root / ".aret-memory" / "aret_memory.sqlite"
    snapshot.parent.mkdir(parents=True)
    connection = sqlite3.connect(snapshot)
    try:
        connection.execute("CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY)")
        connection.executemany("INSERT INTO schema_migrations(version) VALUES (?)", [(version,) for version in range(1, 7)])
        for table_name in aret_v1_schema_manifest().application_tables:
            if table_name not in {"schema_migrations", "component", "function_symbol", "brick"}:
                connection.execute(f"CREATE TABLE {table_name} (id TEXT)")
        connection.execute(_COMPONENT_SQL)
        connection.execute(function_sql)
        connection.execute(brick_sql)
        connection.execute(roadmap_index_sql)
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


def _inspection(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, **source_kwargs: str):
    source_root, snapshot = _make_source(tmp_path, **source_kwargs)
    revision = "0" * 40
    monkeypatch.setattr(sqlite_schema, "ARET_V1_BASELINE_REVISION", revision)
    return inspect_aret_v1_schema_snapshot(
        source_root=source_root,
        source_identity=_identity(source_root, snapshot, revision),
    )


def test_function_symbol_schema_conformance_verifies_columns_fk_and_unique_read_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inspection = _inspection(tmp_path, monkeypatch)
    before = inspection.source_path.read_bytes()

    result = inspect_aret_v1_function_symbol_schema(inspection=inspection)

    assert result.columns == (
        ("id", "TEXT", True, True, None),
        ("component_id", "TEXT", True, False, None),
        ("module", "TEXT", True, False, "''"),
        ("symbol", "TEXT", True, False, None),
        ("calling_convention", "TEXT", True, False, "''"),
        ("created_at", "TEXT", True, False, None),
        ("created_by", "TEXT", True, False, None),
    )
    assert result.foreign_keys == (("component", "component_id", "id"),)
    assert result.unique_constraints == (("component_id", "module", "symbol"),)
    assert result.conformance_state == "FUNCTION_SYMBOL_SCHEMA_CONFORMANT"
    assert inspection.source_path.read_bytes() == before


def test_brick_schema_conformance_verifies_columns_constraints_and_roadmap_index_read_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inspection = _inspection(tmp_path, monkeypatch)
    before = inspection.source_path.read_bytes()

    result = inspect_aret_v1_brick_schema(inspection=inspection)

    assert result.columns == (
        ("id", "TEXT", True, True, None),
        ("component_id", "TEXT", False, False, None),
        ("title", "TEXT", True, False, None),
        ("state", "TEXT", True, False, None),
        ("description", "TEXT", True, False, "''"),
        ("created_at", "TEXT", True, False, None),
        ("created_by", "TEXT", True, False, None),
        ("milestone", "TEXT", False, False, None),
        ("target_platform", "TEXT", False, False, None),
        ("priority", "INTEGER", True, False, "3"),
    )
    assert result.foreign_keys == (("component", "component_id", "id"),)
    assert result.state_values == ("PLANNED", "ACTIVE", "BLOCKED", "DONE", "OBSOLETE")
    assert result.priority_range == (1, 5)
    assert result.roadmap_index_columns == ("milestone", "target_platform", "priority", "state", "component_id", "id")
    assert result.conformance_state == "BRICK_SCHEMA_CONFORMANT"
    assert inspection.source_path.read_bytes() == before


@pytest.mark.parametrize(
    "function_sql, brick_sql, roadmap_index_sql, function_rejected, brick_rejected",
    (
        (
            "CREATE TABLE function_symbol (id TEXT PRIMARY KEY, component_id TEXT NOT NULL REFERENCES component(id), module TEXT NOT NULL DEFAULT '', symbol TEXT NOT NULL, calling_convention TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, created_by TEXT NOT NULL) STRICT",
            _BRICK_SQL,
            "CREATE INDEX idx_brick_roadmap ON brick(milestone, target_platform, priority, state, component_id, id)",
            True,
            False,
        ),
        (
            _FUNCTION_SQL,
            "CREATE TABLE brick (id TEXT PRIMARY KEY, component_id TEXT REFERENCES component(id), title TEXT NOT NULL, state TEXT NOT NULL CHECK (state IN ('PLANNED', 'ACTIVE', 'BLOCKED', 'DONE')), description TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, created_by TEXT NOT NULL, milestone TEXT, target_platform TEXT, priority INTEGER NOT NULL DEFAULT 3 CHECK (priority BETWEEN 1 AND 5)) STRICT",
            "CREATE INDEX idx_brick_roadmap ON brick(milestone, target_platform, priority, state, component_id, id)",
            False,
            True,
        ),
        (
            _FUNCTION_SQL,
            _BRICK_SQL,
            "CREATE INDEX idx_brick_roadmap ON brick(priority, milestone, target_platform, state, component_id, id)",
            False,
            True,
        ),
    ),
)
def test_structural_schema_conformance_rejects_legacy_constraint_or_index_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    function_sql: str,
    brick_sql: str,
    roadmap_index_sql: str,
    function_rejected: bool,
    brick_rejected: bool,
) -> None:
    inspection = _inspection(
        tmp_path,
        monkeypatch,
        function_sql=function_sql,
        brick_sql=brick_sql,
        roadmap_index_sql=roadmap_index_sql,
    )

    if function_rejected:
        with pytest.raises(AretStructuralSchemaConformanceError):
            inspect_aret_v1_function_symbol_schema(inspection=inspection)
    else:
        inspect_aret_v1_function_symbol_schema(inspection=inspection)
    if brick_rejected:
        with pytest.raises(AretStructuralSchemaConformanceError):
            inspect_aret_v1_brick_schema(inspection=inspection)
    else:
        inspect_aret_v1_brick_schema(inspection=inspection)


def test_structural_schema_conformance_rejects_unverified_inspection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inspection = _inspection(tmp_path, monkeypatch)

    with pytest.raises(AretStructuralSchemaConformanceError):
        inspect_aret_v1_function_symbol_schema(inspection=replace(inspection, inspection_state="UNVERIFIED"))
    with pytest.raises(AretStructuralSchemaConformanceError):
        inspect_aret_v1_brick_schema(inspection=replace(inspection, inspection_state="UNVERIFIED"))


def test_structural_schema_conformance_module_is_read_only_and_has_no_import_write_capability() -> None:
    source = (
        Path(__file__).parents[1]
        / "src"
        / "vera_mmu"
        / "domain_packs"
        / "aret"
        / "structural_schema_conformance.py"
    ).read_text(encoding="utf-8")

    for required in ("PRAGMA table_info", "PRAGMA foreign_key_list", "PRAGMA index_list", "mode=ro", "PRAGMA query_only"):
        assert required in source
    for forbidden in ("INSERT", "UPDATE", "DELETE", "ImportBatchService", "SymbolService", "WorkItemService", "subprocess", "requests", "urllib.", "socket", "os.system"):
        assert forbidden not in source
