from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import sqlite3

import pytest

from vera_mmu.domain_packs.aret import (
    AretComponentSourceReadError,
    AretV1SchemaSnapshotInspection,
    read_aret_v1_component_page,
)
from vera_mmu.domain_packs.aret.schema import aret_v1_schema_manifest


def _make_source(tmp_path: Path) -> tuple[Path, Path, AretV1SchemaSnapshotInspection]:
    source_root = (tmp_path / "repository" / "aret-memory").resolve()
    snapshot = source_root / ".aret-memory" / "aret_memory.sqlite"
    snapshot.parent.mkdir(parents=True)
    connection = sqlite3.connect(snapshot)
    try:
        connection.execute(
            "CREATE TABLE component ("
            "id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL, "
            "created_at TEXT NOT NULL, created_by TEXT NOT NULL)"
        )
        connection.executemany(
            "INSERT INTO component(id, title, description, created_at, created_by) VALUES (?, ?, ?, ?, ?)",
            [
                ("CMP-001", "Alpha", "First observed component", "2026-01-01T00:00:00Z", "fixture"),
                ("CMP-002", "Beta", "Second observed component", "2026-01-02T00:00:00Z", "fixture"),
                ("CMP-010", "Gamma", "Third observed component", "2026-01-03T00:00:00Z", "fixture"),
            ],
        )
        connection.commit()
    finally:
        connection.close()
    manifest = aret_v1_schema_manifest()
    inspection = AretV1SchemaSnapshotInspection(
        source_path=snapshot,
        source_snapshot_sha256=sha256(snapshot.read_bytes()).hexdigest(),
        migration_versions=manifest.migration_versions,
        application_tables=manifest.application_tables,
    )
    return source_root, snapshot, inspection


def test_component_reader_returns_raw_rows_in_bounded_stable_pages(tmp_path: Path) -> None:
    source_root, snapshot, inspection = _make_source(tmp_path)
    before = snapshot.read_bytes()

    first = read_aret_v1_component_page(
        source_root=source_root,
        schema_inspection=inspection,
        after_id=None,
        limit=2,
    )
    second = read_aret_v1_component_page(
        source_root=source_root,
        schema_inspection=inspection,
        after_id=first.next_after_id,
        limit=2,
    )

    assert [record.source_id for record in first.records] == ["CMP-001", "CMP-002"]
    assert first.records[0].title == "Alpha"
    assert first.records[0].description == "First observed component"
    assert first.next_after_id == "CMP-002"
    assert [record.source_id for record in second.records] == ["CMP-010"]
    assert second.next_after_id is None
    assert first.source_snapshot_sha256 == inspection.source_snapshot_sha256
    assert first.read_state == "SOURCE_ROWS_OBSERVED"
    assert snapshot.read_bytes() == before


@pytest.mark.parametrize(
    ("after_id", "limit"),
    [
        ("", 1),
        ("CMP-001\n", 1),
        (None, 0),
        (None, 101),
        (None, True),
    ],
)
def test_component_reader_rejects_unbounded_or_noncanonical_pagination(
    tmp_path: Path, after_id: str | None, limit: int
) -> None:
    source_root, _, inspection = _make_source(tmp_path)

    with pytest.raises(AretComponentSourceReadError):
        read_aret_v1_component_page(
            source_root=source_root,
            schema_inspection=inspection,
            after_id=after_id,
            limit=limit,
        )


def test_component_reader_rejects_drifted_snapshot_or_unverified_schema(tmp_path: Path) -> None:
    source_root, snapshot, inspection = _make_source(tmp_path)
    snapshot.write_bytes(snapshot.read_bytes() + b"drift")

    with pytest.raises(AretComponentSourceReadError):
        read_aret_v1_component_page(
            source_root=source_root,
            schema_inspection=inspection,
            after_id=None,
            limit=1,
        )

    source_root, _, inspection = _make_source(tmp_path / "unverified")
    with pytest.raises(AretComponentSourceReadError):
        read_aret_v1_component_page(
            source_root=source_root,
            schema_inspection=replace(inspection, inspection_state="UNVERIFIED"),
            after_id=None,
            limit=1,
        )


def test_component_reader_rejects_wrong_path_binding(tmp_path: Path) -> None:
    source_root, _, inspection = _make_source(tmp_path)

    with pytest.raises(AretComponentSourceReadError):
        read_aret_v1_component_page(
            source_root=tmp_path / "outside",
            schema_inspection=inspection,
            after_id=None,
            limit=1,
        )

    with pytest.raises(AretComponentSourceReadError):
        read_aret_v1_component_page(
            source_root=source_root,
            schema_inspection=replace(inspection, source_path=source_root / "other.sqlite"),
            after_id=None,
            limit=1,
        )


def test_component_reader_module_is_read_only_and_does_not_map_or_import() -> None:
    source = (
        Path(__file__).parents[1]
        / "src"
        / "vera_mmu"
        / "domain_packs"
        / "aret"
        / "component_reader.py"
    ).read_text(encoding="utf-8")

    for required in ("mode=ro", "PRAGMA query_only", "FROM component", "ORDER BY id", "LIMIT ?"):
        assert required in source
    for forbidden in (
        "INSERT",
        "UPDATE",
        "DELETE",
        "subprocess",
        "requests",
        "urllib.",
        "socket",
        "os.system",
        "vera_resource",
        "component_import_preparation",
    ):
        assert forbidden not in source
