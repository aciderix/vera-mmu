from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
import stat

from .runtime import legacy_runtime_layout


class AretRuntimeResolutionError(ValueError):
    """Raised when the legacy runtime cannot be resolved or observed read-only without ambiguity."""


@dataclass(frozen=True)
class AretV1RuntimeResolution:
    """A canonical, existing ARET V1 runtime location; resolving it never creates a directory or store."""

    source_root: Path
    runtime_dir: Path
    snapshot_path: Path
    resolution_basis: str
    resolution_state: str = "RUNTIME_RESOLVED_READ_ONLY"


@dataclass(frozen=True)
class AretV1RuntimeSnapshotSafety:
    """A sidecar-free stable observation precondition for SQLite immutable reads; not an SQLite connection."""

    source_root: Path
    runtime_dir: Path
    snapshot_path: Path
    snapshot_size_bytes: int
    wal_state: str
    snapshot_access_mode: str = "READ_ONLY_IMMUTABLE_SNAPSHOT"
    safety_state: str = "RUNTIME_SNAPSHOT_SAFE"


def _canonical_existing_directory(value: object, label: str) -> Path:
    if not isinstance(value, (str, Path)):
        raise AretRuntimeResolutionError(f"{label} doit être un chemin absolu canonique.")
    path = Path(value)
    if not path.is_absolute() or path != path.resolve() or path.is_symlink() or not path.is_dir():
        raise AretRuntimeResolutionError(f"{label} doit être un répertoire absolu, canonique, existant et non lié.")
    return path


def _require_environment(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise AretRuntimeResolutionError("environment doit être un mapping explicite, jamais l’environnement global implicite.")
    if set(value) - {legacy_runtime_layout().environment_override}:
        raise AretRuntimeResolutionError("environment ne peut contenir que l’override ARET_MEMORY_DIR explicite.")
    return value


def _override_runtime(value: object) -> Path:
    if not isinstance(value, str) or not value or value != value.strip() or "\x00" in value or "\r" in value or "\n" in value:
        raise AretRuntimeResolutionError("ARET_MEMORY_DIR doit être une chaîne de chemin absolu non vide sur une ligne.")
    return _canonical_existing_directory(value, "ARET_MEMORY_DIR")


def _require_runtime_snapshot(runtime_dir: Path) -> Path:
    snapshot = runtime_dir / legacy_runtime_layout().sqlite_filename
    if snapshot.is_symlink() or not snapshot.is_file():
        raise AretRuntimeResolutionError("Le snapshot SQLite ARET V1 doit être un fichier régulier existant et non lié.")
    try:
        mode = snapshot.stat().st_mode
    except OSError as exc:
        raise AretRuntimeResolutionError("Le snapshot SQLite ARET V1 ne peut pas être observé.") from exc
    if not stat.S_ISREG(mode):
        raise AretRuntimeResolutionError("Le snapshot SQLite ARET V1 doit être un fichier régulier.")
    return snapshot


def resolve_aret_v1_runtime(
    *,
    source_root: str | Path,
    environment: Mapping[str, object],
) -> AretV1RuntimeResolution:
    """Resolve only an existing V1 runtime through a supplied mapping; no environment read, creation, SQLite or write occurs."""
    root = _canonical_existing_directory(source_root, "source_root")
    supplied_environment = _require_environment(environment)
    layout = legacy_runtime_layout()
    if layout.environment_override in supplied_environment:
        runtime_dir = _override_runtime(supplied_environment[layout.environment_override])
        resolution_basis = "ARET_MEMORY_DIR_OVERRIDE"
    else:
        runtime_dir = root / layout.default_runtime_dir
        if runtime_dir.is_symlink() or not runtime_dir.is_dir():
            raise AretRuntimeResolutionError("Le runtime ARET V1 par défaut doit exister sous la racine source et ne pas être un lien.")
        resolution_basis = "DEFAULT_RUNTIME_LAYOUT"
    return AretV1RuntimeResolution(
        source_root=root,
        runtime_dir=runtime_dir,
        snapshot_path=_require_runtime_snapshot(runtime_dir),
        resolution_basis=resolution_basis,
    )


def _require_resolution(value: object) -> AretV1RuntimeResolution:
    if not isinstance(value, AretV1RuntimeResolution):
        raise AretRuntimeResolutionError("resolution doit être une résolution runtime ARET V1 explicite.")
    if (
        not isinstance(value.source_root, Path)
        or not isinstance(value.runtime_dir, Path)
        or not isinstance(value.snapshot_path, Path)
        or value.resolution_basis not in {"DEFAULT_RUNTIME_LAYOUT", "ARET_MEMORY_DIR_OVERRIDE"}
        or value.resolution_state != "RUNTIME_RESOLVED_READ_ONLY"
    ):
        raise AretRuntimeResolutionError("resolution runtime ARET V1 invalide.")
    root = _canonical_existing_directory(value.source_root, "resolution.source_root")
    runtime_dir = _canonical_existing_directory(value.runtime_dir, "resolution.runtime_dir")
    if value.resolution_basis == "DEFAULT_RUNTIME_LAYOUT" and runtime_dir != root / legacy_runtime_layout().default_runtime_dir:
        raise AretRuntimeResolutionError("Le runtime par défaut doit rester sous la racine source ARET.")
    if value.snapshot_path != runtime_dir / legacy_runtime_layout().sqlite_filename:
        raise AretRuntimeResolutionError("Le snapshot runtime doit garder le nom SQLite ARET V1 attendu.")
    _require_runtime_snapshot(runtime_dir)
    return value


def inspect_aret_v1_runtime_snapshot_safety(*, resolution: AretV1RuntimeResolution) -> AretV1RuntimeSnapshotSafety:
    """Refuse WAL/SHM actifs rather than checkpointing or opening SQLite; this is a read-only safety gate."""
    checked = _require_resolution(resolution)
    snapshot = checked.snapshot_path
    try:
        before = snapshot.stat()
    except OSError as exc:
        raise AretRuntimeResolutionError("Le snapshot ARET V1 ne peut pas être staté pour la policy WAL.") from exc
    if not stat.S_ISREG(before.st_mode):
        raise AretRuntimeResolutionError("Le snapshot ARET V1 doit rester un fichier régulier.")
    for suffix in ("-wal", "-shm"):
        sidecar = Path(f"{snapshot}{suffix}")
        if sidecar.is_symlink():
            raise AretRuntimeResolutionError("Les sidecars WAL/SHM ARET ne doivent jamais être des liens.")
        if sidecar.exists():
            raise AretRuntimeResolutionError("Un sidecar WAL/SHM actif exige un checkpoint externe ; la lecture immutable est refusée.")
    try:
        after = snapshot.stat()
    except OSError as exc:
        raise AretRuntimeResolutionError("Le snapshot ARET V1 ne peut pas être restaté pour la policy WAL.") from exc
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ):
        raise AretRuntimeResolutionError("Le snapshot ARET V1 a changé pendant le contrôle WAL read-only.")
    return AretV1RuntimeSnapshotSafety(
        source_root=checked.source_root,
        runtime_dir=checked.runtime_dir,
        snapshot_path=snapshot,
        snapshot_size_bytes=before.st_size,
        wal_state="NO_WAL_SIDECARS",
    )
