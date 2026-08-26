from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import stat

from .import_preparation import AretComponentImportPreparation
from .runtime import legacy_runtime_layout
from .runtime_resolution import (
    AretRuntimeResolutionError,
    AretV1RuntimeResolution,
    AretV1RuntimeSnapshotSafety,
)
from .schema import aret_v1_schema_manifest


ARET_V1_BASELINE_REVISION = "7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4"
_SNAPSHOT_CHUNK_BYTES = 64 * 1024


class AretSourceAttestationError(ValueError):
    """Raised when one declared ARET V1 component-source snapshot cannot be safely attested."""


@dataclass(frozen=True)
class AretV1ComponentSourceAttestation:
    """Hash attestation for one read-only legacy snapshot; not an import result or source proof."""

    source_path: Path
    source_snapshot_sha256: str
    source_size_bytes: int
    expected_legacy_revision: str
    source_schema_version: int
    source_access_mode: str = "READ_ONLY_SNAPSHOT"
    attestation_state: str = "ATTESTED_SNAPSHOT_ONLY"
    source_root: Path | None = None
    runtime_resolution_basis: str = "DEFAULT_RUNTIME_LAYOUT"
    runtime_wal_state: str = "UNVERIFIED_RUNTIME_POLICY"


def _require_baseline_revision(value: object) -> str:
    if value != ARET_V1_BASELINE_REVISION:
        raise AretSourceAttestationError("expected_legacy_revision doit être exactement la baseline ARET V1 figée.")
    return ARET_V1_BASELINE_REVISION


def _require_pending_component_preparation(value: object) -> AretComponentImportPreparation:
    if not isinstance(value, AretComponentImportPreparation):
        raise AretSourceAttestationError("preparation doit être un pré-contrat d’import de composant ARET V1.")
    if (
        value.legacy_table,
        value.vera_resource,
        value.vera_type,
        value.source_schema_version,
        value.requires_explicit_import,
        value.execution_state,
        value.source_attestation_state,
    ) != (
        "component",
        "entity",
        "COMPONENT",
        6,
        True,
        "PREPARED_NOT_EXECUTED",
        "UNVERIFIED_DECLARATION",
    ):
        raise AretSourceAttestationError("preparation doit rester une demande de composant ARET V1 non exécutée et non attestée.")
    return value


def _expected_snapshot_path(source_root: str | Path) -> Path:
    root = Path(source_root)
    if not root.is_absolute() or root != root.resolve() or root.is_symlink() or not root.is_dir():
        raise AretSourceAttestationError("source_root doit être un répertoire absolu, canonique, existant et non lié.")

    layout = legacy_runtime_layout()
    runtime_dir = root / layout.default_runtime_dir
    snapshot = runtime_dir / layout.sqlite_filename
    if runtime_dir.is_symlink() or not runtime_dir.is_dir():
        raise AretSourceAttestationError("Le répertoire runtime ARET V1 attendu doit exister et ne pas être un lien.")
    if snapshot.is_symlink() or not snapshot.is_file():
        raise AretSourceAttestationError("Le snapshot SQLite ARET V1 attendu doit être un fichier régulier non lié.")
    return snapshot


def _runtime_snapshot_binding(
    source_root: Path,
    runtime_resolution: object | None,
    runtime_safety: object | None,
) -> tuple[Path, str, str]:
    if runtime_resolution is None and runtime_safety is None:
        return _expected_snapshot_path(source_root), "DEFAULT_RUNTIME_LAYOUT", "UNVERIFIED_RUNTIME_POLICY"
    if not isinstance(runtime_resolution, AretV1RuntimeResolution) or not isinstance(runtime_safety, AretV1RuntimeSnapshotSafety):
        raise AretRuntimeResolutionError("runtime_resolution et runtime_safety doivent être fournis ensemble pour attester un runtime ARET V1.")
    if (
        runtime_resolution.source_root != source_root
        or runtime_safety.source_root != source_root
        or runtime_safety.runtime_dir != runtime_resolution.runtime_dir
        or runtime_safety.snapshot_path != runtime_resolution.snapshot_path
        or runtime_safety.wal_state != "NO_WAL_SIDECARS"
        or runtime_safety.snapshot_access_mode != "READ_ONLY_IMMUTABLE_SNAPSHOT"
        or runtime_safety.safety_state != "RUNTIME_SNAPSHOT_SAFE"
        or runtime_resolution.resolution_state != "RUNTIME_RESOLVED_READ_ONLY"
    ):
        raise AretRuntimeResolutionError("La résolution runtime et la safety WAL doivent rester exactement liées à la racine source attestée.")
    return runtime_resolution.snapshot_path, runtime_resolution.resolution_basis, runtime_safety.wal_state


def _hash_stable_regular_file(snapshot: Path) -> tuple[str, int]:
    before = snapshot.stat()
    if not stat.S_ISREG(before.st_mode):
        raise AretSourceAttestationError("Le snapshot ARET V1 doit être un fichier régulier.")

    digest = sha256()
    size = 0
    try:
        with snapshot.open("rb") as stream:
            while chunk := stream.read(_SNAPSHOT_CHUNK_BYTES):
                digest.update(chunk)
                size += len(chunk)
    except OSError as exc:
        raise AretSourceAttestationError("Lecture du snapshot ARET V1 impossible.") from exc

    after = snapshot.stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ) or size != before.st_size:
        raise AretSourceAttestationError("Le snapshot ARET V1 a changé pendant son attestation.")
    return digest.hexdigest(), size


def attest_aret_v1_component_source(
    *,
    source_root: str | Path,
    expected_legacy_revision: str,
    preparation: AretComponentImportPreparation,
    runtime_resolution: AretV1RuntimeResolution | None = None,
    runtime_safety: AretV1RuntimeSnapshotSafety | None = None,
) -> AretV1ComponentSourceAttestation:
    """Attest one expected snapshot only; no SQLite is opened and no legacy row or VERA store is touched."""
    _require_baseline_revision(expected_legacy_revision)
    pending = _require_pending_component_preparation(preparation)
    root = Path(source_root)
    if not root.is_absolute() or root != root.resolve() or root.is_symlink() or not root.is_dir():
        raise AretSourceAttestationError("source_root doit être un répertoire absolu, canonique, existant et non lié.")
    snapshot, resolution_basis, wal_state = _runtime_snapshot_binding(root, runtime_resolution, runtime_safety)
    snapshot_sha256, snapshot_size = _hash_stable_regular_file(snapshot)
    if snapshot_sha256 != pending.source_snapshot_sha256:
        raise AretSourceAttestationError("Le hash du snapshot ne correspond pas à la déclaration du pré-contrat.")

    manifest = aret_v1_schema_manifest()
    if manifest.migration_versions != (1, 2, 3, 4, 5, 6):
        raise AretSourceAttestationError("Le manifeste de schéma ARET V1 n’est pas admissible pour cette attestation.")
    return AretV1ComponentSourceAttestation(
        source_path=snapshot,
        source_snapshot_sha256=snapshot_sha256,
        source_size_bytes=snapshot_size,
        expected_legacy_revision=ARET_V1_BASELINE_REVISION,
        source_schema_version=manifest.migration_versions[-1],
        source_root=root,
        runtime_resolution_basis=resolution_basis,
        runtime_wal_state=wal_state,
    )
