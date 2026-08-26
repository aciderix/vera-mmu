from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import sqlite3

import pytest

from vera_mmu.domain_packs.aret import (
    AretFunctionSymbolReadError,
    AretV1GitSourceIdentity,
    inspect_aret_v1_schema_snapshot,
    read_aret_v1_function_symbol_page,
)
from vera_mmu.domain_packs.aret import sqlite_schema


def _source(tmp_path: Path) -> tuple[Path, Path, AretV1GitSourceIdentity]:
    root = tmp_path / "aret-source"
    snapshot = root / ".aret-memory" / "aret_memory.sqlite"
    snapshot.parent.mkdir(parents=True)
    connection = sqlite3.connect(snapshot)
    try:
        connection.execute("CREATE TABLE schema_migrations (version INTEGER)")
        for version in range(1, 7):
            connection.execute("INSERT INTO schema_migrations VALUES(?)", (version,))
        from vera_mmu.domain_packs.aret import aret_v1_schema_manifest
        for table in aret_v1_schema_manifest().application_tables:
            if table != "schema_migrations":
                connection.execute(f"CREATE TABLE {table} (id TEXT)")
        connection.execute("DROP TABLE function_symbol")
        connection.execute("CREATE TABLE function_symbol (id TEXT PRIMARY KEY, component_id TEXT NOT NULL, module TEXT NOT NULL, symbol TEXT NOT NULL, calling_convention TEXT NOT NULL, created_at TEXT NOT NULL, created_by TEXT NOT NULL)")
        connection.executemany("INSERT INTO function_symbol VALUES(?, ?, ?, ?, ?, ?, ?)", [
            ("CMP-001:core!alpha", "CMP-001", "core", "alpha", "cdecl", "2026-01-01T00:00:00Z", "fixture"),
            ("CMP-001:!beta", "CMP-001", "", "beta", "stdcall", "2026-01-01T00:00:01Z", "fixture"),
        ])
        connection.commit()
    finally:
        connection.close()
    revision = "0" * 40
    identity = AretV1GitSourceIdentity(root, root, revision, revision, sha256(snapshot.read_bytes()).hexdigest())
    return root, snapshot, identity


def test_function_symbol_reader_is_keyset_ordered_and_read_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, snapshot, identity = _source(tmp_path)
    monkeypatch.setattr(sqlite_schema, "ARET_V1_BASELINE_REVISION", "0" * 40)
    inspection = inspect_aret_v1_schema_snapshot(source_root=root, source_identity=identity)
    before = snapshot.read_bytes()

    first = read_aret_v1_function_symbol_page(source_root=root, schema_inspection=inspection, after_id=None, limit=1)
    second = read_aret_v1_function_symbol_page(source_root=root, schema_inspection=inspection, after_id=first.records[-1].source_id, limit=1)

    assert [r.source_id for r in first.records] == ["CMP-001:!beta"]
    assert [r.source_id for r in second.records] == ["CMP-001:core!alpha"]
    assert first.source_snapshot_sha256 == sha256(before).hexdigest()
    assert snapshot.read_bytes() == before


def test_function_symbol_reader_rejects_invalid_paging_or_schema_binding(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, _, identity = _source(tmp_path)
    monkeypatch.setattr(sqlite_schema, "ARET_V1_BASELINE_REVISION", "0" * 40)
    inspection = inspect_aret_v1_schema_snapshot(source_root=root, source_identity=identity)
    for after_id, limit in (("", 1), (None, 0), (None, 101)):
        with pytest.raises(AretFunctionSymbolReadError):
            read_aret_v1_function_symbol_page(source_root=root, schema_inspection=inspection, after_id=after_id, limit=limit)


def test_function_symbol_reader_has_no_write_or_network_capability() -> None:
    source = (Path(__file__).parents[1] / "src" / "vera_mmu" / "domain_packs" / "aret" / "function_symbol_reader.py").read_text(encoding="utf-8")
    for forbidden in ("INSERT", "UPDATE", "DELETE", "subprocess", "os.system", "requests", "urllib.", "socket"):
        assert forbidden not in source
