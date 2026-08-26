from __future__ import annotations

from pathlib import Path

import pytest

from vera_mmu.domain_packs.aret import (
    AretRuntimeResolutionError,
    AretV1RuntimeResolution,
    inspect_aret_v1_runtime_snapshot_safety,
    resolve_aret_v1_runtime,
)


def _make_root(tmp_path: Path) -> tuple[Path, Path]:
    source_root = tmp_path / "aret-source"
    snapshot = source_root / ".aret-memory" / "aret_memory.sqlite"
    snapshot.parent.mkdir(parents=True)
    snapshot.write_bytes(b"sqlite fixture")
    return source_root, snapshot


def test_default_runtime_resolution_is_bounded_to_canonical_source_root(tmp_path: Path) -> None:
    source_root, snapshot = _make_root(tmp_path)

    resolution = resolve_aret_v1_runtime(source_root=source_root, environment={})

    assert resolution.source_root == source_root
    assert resolution.runtime_dir == source_root / ".aret-memory"
    assert resolution.snapshot_path == snapshot
    assert resolution.resolution_basis == "DEFAULT_RUNTIME_LAYOUT"
    assert resolution.resolution_state == "RUNTIME_RESOLVED_READ_ONLY"


def test_explicit_aret_memory_dir_override_requires_a_canonical_existing_runtime(tmp_path: Path) -> None:
    source_root, _ = _make_root(tmp_path)
    override_runtime = tmp_path / "separate-runtime"
    override_snapshot = override_runtime / "aret_memory.sqlite"
    override_runtime.mkdir()
    override_snapshot.write_bytes(b"override sqlite fixture")

    resolution = resolve_aret_v1_runtime(
        source_root=source_root,
        environment={"ARET_MEMORY_DIR": str(override_runtime)},
    )

    assert resolution.source_root == source_root
    assert resolution.runtime_dir == override_runtime
    assert resolution.snapshot_path == override_snapshot
    assert resolution.resolution_basis == "ARET_MEMORY_DIR_OVERRIDE"


@pytest.mark.parametrize(
    "environment",
    [
        {"ARET_MEMORY_DIR": "relative"},
        {"ARET_MEMORY_DIR": ""},
        {"ARET_MEMORY_DIR": "\n"},
        {"ARET_MEMORY_DIR": "/does/not/exist"},
        {"ARET_MEMORY_DIR": 42},
        {"UNRELATED": "/ignored"},
    ],
)
def test_runtime_resolution_rejects_untrusted_override_inputs(tmp_path: Path, environment: dict[str, object]) -> None:
    source_root, _ = _make_root(tmp_path)

    with pytest.raises(AretRuntimeResolutionError):
        resolve_aret_v1_runtime(source_root=source_root, environment=environment)


def test_runtime_resolution_rejects_linked_source_or_runtime(tmp_path: Path) -> None:
    source_root, _ = _make_root(tmp_path)
    root_link = tmp_path / "root-link"
    root_link.symlink_to(source_root, target_is_directory=True)

    with pytest.raises(AretRuntimeResolutionError):
        resolve_aret_v1_runtime(source_root=root_link, environment={})

    runtime_link = tmp_path / "runtime-link"
    runtime_link.symlink_to(source_root / ".aret-memory", target_is_directory=True)
    with pytest.raises(AretRuntimeResolutionError):
        resolve_aret_v1_runtime(source_root=source_root, environment={"ARET_MEMORY_DIR": str(runtime_link)})


def test_runtime_safety_accepts_a_stable_snapshot_without_wal_sidecars(tmp_path: Path) -> None:
    source_root, snapshot = _make_root(tmp_path)
    resolution = resolve_aret_v1_runtime(source_root=source_root, environment={})
    before = snapshot.read_bytes()

    safety = inspect_aret_v1_runtime_snapshot_safety(resolution=resolution)

    assert safety.snapshot_path == snapshot
    assert safety.wal_state == "NO_WAL_SIDECARS"
    assert safety.snapshot_access_mode == "READ_ONLY_IMMUTABLE_SNAPSHOT"
    assert safety.safety_state == "RUNTIME_SNAPSHOT_SAFE"
    assert snapshot.read_bytes() == before


@pytest.mark.parametrize("sidecar", ["aret_memory.sqlite-wal", "aret_memory.sqlite-shm"])
def test_runtime_safety_refuses_uncheckpointed_wal_or_shm_sidecars(tmp_path: Path, sidecar: str) -> None:
    source_root, _ = _make_root(tmp_path)
    resolution = resolve_aret_v1_runtime(source_root=source_root, environment={})
    (resolution.runtime_dir / sidecar).write_bytes(b"sidecar")

    with pytest.raises(AretRuntimeResolutionError):
        inspect_aret_v1_runtime_snapshot_safety(resolution=resolution)


def test_runtime_safety_refuses_linked_snapshot_or_sidecar(tmp_path: Path) -> None:
    source_root, snapshot = _make_root(tmp_path)
    resolution = resolve_aret_v1_runtime(source_root=source_root, environment={})
    outside = tmp_path / "outside.sqlite"
    outside.write_bytes(snapshot.read_bytes())
    snapshot.unlink()
    snapshot.symlink_to(outside)

    with pytest.raises(AretRuntimeResolutionError):
        inspect_aret_v1_runtime_snapshot_safety(resolution=resolution)


def test_runtime_resolver_module_is_read_only_and_has_no_process_or_network_capability() -> None:
    source = (
        Path(__file__).parents[1]
        / "src"
        / "vera_mmu"
        / "domain_packs"
        / "aret"
        / "runtime_resolution.py"
    ).read_text(encoding="utf-8")

    for required in ("ARET_MEMORY_DIR", "NO_WAL_SIDECARS", "RUNTIME_SNAPSHOT_SAFE"):
        assert required in source
    for forbidden in (
        "sqlite3",
        "open(",
        "subprocess",
        "os.system",
        "requests",
        "urllib.",
        "socket",
        "INSERT",
        "UPDATE",
        "DELETE",
    ):
        assert forbidden not in source
