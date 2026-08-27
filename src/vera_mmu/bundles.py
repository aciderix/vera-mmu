"""Project-bound, integrity-checked VERA memory bundles (M11-B)."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
import platform
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
import stat
import tempfile
from typing import Any, Mapping
from uuid import uuid4
import zipfile

from .identity import ProjectIdentity, canonical_json, load_profile, project_identity
from .migrations import MigrationRunner, migration_checksums
from .project_policy import ProjectPolicyError, require_project_write, require_project_write_for_profile
from .store import MemoryStore, StoreError
from .workspace import WorkspaceError, resolve_workspace


BUNDLE_FORMAT = "vera-bundle/v1"
_MANIFEST_NAME = "manifest.json"
_MIGRATIONS_NAME = "schema/migrations.json"
_BUNDLE_ID_MAX_LENGTH = 96
_MAX_FILE_BYTES = 64 * 1024 * 1024
_MAX_BUNDLE_BYTES = 128 * 1024 * 1024
_MAX_MEMBERS = 256
_SHA256_LENGTH = 64


class BundleError(StoreError):
    """Raised when a VERA bundle cannot be exported, verified or restored safely."""


@dataclass(frozen=True)
class BundleExportResult:
    """A newly materialised immutable bundle and the hashes it commits to."""

    format: str
    bundle_id: str
    path: str
    manifest_sha256: str
    memory_sha256: str
    schema_hash: str
    artifact_count: int
    status: str = "EXPORTED"


@dataclass(frozen=True)
class BundleRestoreResult:
    """Result of a verified non-merging restore into one exact project identity."""

    format: str
    bundle_id: str
    path: str
    memory_sha256: str
    artifact_count: int
    status: str


@dataclass(frozen=True)
class _BundleContents:
    manifest: dict[str, Any]
    manifest_bytes: bytes
    files: dict[str, bytes]


class BundleService:
    """Export a project-bound memory snapshot without accepting arbitrary archive content."""

    def __init__(self, store: MemoryStore) -> None:
        if not isinstance(store, MemoryStore):
            raise BundleError("Le bundle exige un MemoryStore VERA actif.")
        self.store = store

    def export(self, bundle_id: str, *, confirm: bool) -> BundleExportResult:
        """Create one bundle under ``.vera-mmu/bundles`` after explicit policy confirmation."""
        identifier = _bundle_id(bundle_id)
        try:
            require_project_write(self.store, confirm=confirm)
        except ProjectPolicyError as exc:
            raise BundleError("Export de bundle refusé par la policy projet.") from exc
        if self.store.connection.in_transaction:
            raise BundleError("Export de bundle refusé pendant une transaction Core active.")

        runtime = _regular_directory(self.store.locator.runtime_dir, "runtime VERA")
        database = _regular_file(self.store.locator.sqlite_path, "mémoire SQLite")
        checkpoint = _checkpoint(self.store)
        snapshot_directory = Path(tempfile.mkdtemp(prefix=".vera-bundle-export-", dir=runtime.parent))
        try:
            snapshot_memory = snapshot_directory / "memory.sqlite"
            _sqlite_snapshot(database, snapshot_memory)
            memory_bytes = _read_regular(snapshot_memory, "snapshot mémoire")
            memory_sha256 = _sha256(memory_bytes)
            migration_payload = canonical_json({str(version): value for version, value in self.store.migration_checksums.items()}).encode("utf-8")
            schema_hash = _sha256(migration_payload)
            files = _runtime_files(runtime, database, snapshot_memory)
            archive_files: dict[str, bytes] = {
                _MIGRATIONS_NAME: migration_payload,
                f"runtime/{database.relative_to(runtime).as_posix()}": memory_bytes,
                **files,
            }
            if len(archive_files) > _MAX_MEMBERS - 1:
                raise BundleError("Le bundle dépasse le nombre maximal de fichiers autorisé.")
            manifest = _manifest(
                identifier,
                self.store.identity,
                schema_hash,
                memory_sha256,
                archive_files,
                checkpoint,
            )
            manifest_bytes = canonical_json(manifest).encode("utf-8")
            output_directory = runtime / "bundles"
            if output_directory.is_symlink():
                raise BundleError("Répertoire de bundles symlinké refusé.")
            output_directory.mkdir(mode=0o700, exist_ok=True)
            if not output_directory.is_dir() or output_directory.is_symlink():
                raise BundleError("Répertoire de bundles invalide.")
            output = output_directory / f"{identifier}.zip"
            if output.exists() or output.is_symlink():
                raise BundleError("Identifiant de bundle déjà matérialisé : écrasement refusé.")
            temporary = output_directory / f".{identifier}.tmp"
            try:
                with zipfile.ZipFile(temporary, mode="x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
                    _write_member(archive, _MANIFEST_NAME, manifest_bytes)
                    for path, payload in sorted(archive_files.items()):
                        _write_member(archive, path, payload)
                with temporary.open("rb") as handle:
                    os.fsync(handle.fileno())
                os.replace(temporary, output)
            except (OSError, zipfile.BadZipFile) as exc:
                temporary.unlink(missing_ok=True)
                raise BundleError("Écriture atomique du bundle impossible.") from exc
            return BundleExportResult(
                format=BUNDLE_FORMAT,
                bundle_id=identifier,
                path=str(output),
                manifest_sha256=_sha256(manifest_bytes),
                memory_sha256=memory_sha256,
                schema_hash=schema_hash,
                artifact_count=sum(1 for path in archive_files if path.startswith("runtime/artifacts/")),
            )
        finally:
            shutil.rmtree(snapshot_directory, ignore_errors=True)


def restore_bundle(bundle_path: str | Path, profile_path: str | Path, *, confirm: bool) -> BundleRestoreResult:
    """Restore one verified bundle only into an empty runtime with the exact same identity."""
    profile_source = _regular_file(Path(profile_path), "profil cible")
    try:
        profile = load_profile(profile_source)
        workspace = resolve_workspace(profile, profile_source)
        identity = project_identity(profile, workspace)
        require_project_write_for_profile(profile_source, confirm=confirm)
    except (ProjectPolicyError, WorkspaceError, ValueError) as exc:
        raise BundleError("Restauration refusée par le profil, le workspace ou la policy projet.") from exc

    contents = _read_bundle(bundle_path)
    manifest = contents.manifest
    if manifest["project_identity"] != identity.as_dict():
        raise BundleError("Le bundle appartient à une autre identité de projet.")
    if manifest["profile_hash"] != identity.profile_hash:
        raise BundleError("Le hash de profil du bundle ne correspond pas à la cible.")
    runtime = _regular_directory(workspace.runtime_dir, "runtime cible")
    database_relative = Path(profile["storage"]["sqlite_file"])
    database = runtime / database_relative
    memory_name = f"runtime/{database_relative.as_posix()}"
    if memory_name not in contents.files:
        raise BundleError("Bundle sans mémoire SQLite à la position déclarée par le profil.")
    _verify_target_configuration(runtime, contents.files)
    if database.exists():
        if database.is_symlink() or not database.is_file():
            raise BundleError("Mémoire cible ambiguë : restauration refusée.")
        if _sha256(_read_regular(database, "mémoire cible")) == manifest["memory_hash"] and _target_matches(runtime, contents.files):
            return BundleRestoreResult(
                format=BUNDLE_FORMAT,
                bundle_id=str(manifest["bundle_id"]),
                path=str(_bundle_source(bundle_path)),
                memory_sha256=str(manifest["memory_hash"]),
                artifact_count=len(manifest["artifact_inventory"]),
                status="ALREADY_RESTORED",
            )
        raise BundleError("Cible de restauration non vide ou divergente : fusion interdite.")

    parent = runtime.parent
    stage_root = Path(tempfile.mkdtemp(prefix=".vera-bundle-stage-", dir=parent))
    staged_runtime = stage_root / "runtime"
    backup = parent / f".{runtime.name}.pre-restore-{uuid4().hex}"
    moved_original = False
    installed = False
    try:
        _materialize_runtime(staged_runtime, contents.files)
        staged_database = staged_runtime / database_relative
        _verify_snapshot_database(staged_database, identity, contents.manifest, contents.files[_MIGRATIONS_NAME])
        if not _target_matches(runtime, contents.files, include_memory=False):
            raise BundleError("La configuration cible a dérivé avant restauration : opération refusée.")
        os.replace(runtime, backup)
        moved_original = True
        os.replace(staged_runtime, runtime)
        installed = True
        shutil.rmtree(backup)
        return BundleRestoreResult(
            format=BUNDLE_FORMAT,
            bundle_id=str(manifest["bundle_id"]),
            path=str(_bundle_source(bundle_path)),
            memory_sha256=str(manifest["memory_hash"]),
            artifact_count=len(manifest["artifact_inventory"]),
            status="RESTORED",
        )
    except (OSError, sqlite3.DatabaseError) as exc:
        if moved_original and not installed and backup.exists() and not runtime.exists():
            os.replace(backup, runtime)
        if installed and backup.exists():
            shutil.rmtree(runtime, ignore_errors=True)
            os.replace(backup, runtime)
        raise BundleError("Restauration atomique impossible ; cible précédente conservée.") from exc
    except Exception:
        if moved_original and not installed and backup.exists() and not runtime.exists():
            os.replace(backup, runtime)
        if installed and backup.exists():
            shutil.rmtree(runtime, ignore_errors=True)
            os.replace(backup, runtime)
        raise
    finally:
        shutil.rmtree(stage_root, ignore_errors=True)
        if backup.exists() and runtime.exists():
            shutil.rmtree(backup, ignore_errors=True)


def _bundle_id(value: object) -> str:
    if not isinstance(value, str) or not 3 <= len(value) <= _BUNDLE_ID_MAX_LENGTH:
        raise BundleError("Identifiant de bundle invalide.")
    if any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-" for character in value) or value[0] == "-" or value[-1] == "-":
        raise BundleError("Identifiant de bundle non canonique.")
    return value


def _sha256(value: bytes) -> str:
    return sha256(value).hexdigest()


def _regular_file(path: Path, label: str) -> Path:
    if path.is_symlink() or not path.is_file():
        raise BundleError(f"{label} absent, non régulier ou symlinké.")
    return path.resolve(strict=True)


def _regular_directory(path: Path, label: str) -> Path:
    if path.is_symlink() or not path.is_dir():
        raise BundleError(f"{label} absent, non répertoire ou symlinké.")
    return path.resolve(strict=True)


def _read_regular(path: Path, label: str) -> bytes:
    source = _regular_file(path, label)
    try:
        if source.stat().st_size > _MAX_FILE_BYTES:
            raise BundleError(f"{label} dépasse la borne de taille.")
        return source.read_bytes()
    except OSError as exc:
        raise BundleError(f"Lecture de {label} impossible.") from exc


def _checkpoint(store: MemoryStore) -> dict[str, int | bool]:
    try:
        row = store.connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
    except sqlite3.DatabaseError as exc:
        raise BundleError("Checkpoint WAL impossible avant export de bundle.") from exc
    if row is None:
        raise BundleError("Checkpoint WAL sans résultat avant export de bundle.")
    busy, log_frames, checkpointed_frames = (int(value) for value in row)
    if busy:
        raise BundleError("Checkpoint WAL refusé : une connexion mémoire est active.")
    return {"checkpointed": True, "busy": busy, "log_frames": log_frames, "checkpointed_frames": checkpointed_frames}


def _sqlite_snapshot(source: Path, destination: Path) -> None:
    try:
        origin = sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True)
        target = sqlite3.connect(destination)
        try:
            origin.backup(target)
        finally:
            target.close()
            origin.close()
    except sqlite3.DatabaseError as exc:
        destination.unlink(missing_ok=True)
        raise BundleError("Snapshot SQLite de bundle impossible.") from exc


def _runtime_files(runtime: Path, database: Path, snapshot: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    excluded = {database.resolve(strict=True), snapshot.resolve(strict=True)}
    for path in sorted(runtime.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(runtime)
        if not relative.parts or relative.parts[0] == "bundles":
            continue
        if path.is_symlink():
            raise BundleError("Runtime contenant un symlink : export de bundle refusé.")
        if path.is_dir():
            continue
        if not path.is_file():
            raise BundleError("Runtime contenant une entrée non régulière : export refusé.")
        if path.resolve(strict=True) in excluded or path.name in {"memory.sqlite-wal", "memory.sqlite-shm"}:
            continue
        arcname = f"runtime/{relative.as_posix()}"
        files[arcname] = _read_regular(path, f"runtime {relative.as_posix()}")
    return files


def _manifest(
    bundle_id: str,
    identity: ProjectIdentity,
    schema_hash: str,
    memory_hash: str,
    files: Mapping[str, bytes],
    checkpoint: Mapping[str, int | bool],
) -> dict[str, Any]:
    inventory = [
        {"path": path, "sha256": _sha256(payload), "size": len(payload)}
        for path, payload in sorted(files.items())
    ]
    artifacts = [item for item in inventory if item["path"].startswith("runtime/artifacts/")]
    return {
        "artifact_inventory": artifacts,
        "bundle_id": bundle_id,
        "checkpoint": dict(checkpoint),
        "files": inventory,
        "format": BUNDLE_FORMAT,
        "memory_hash": memory_hash,
        "profile_hash": identity.profile_hash,
        "project_identity": identity.as_dict(),
        "schema_hash": schema_hash,
        "source_device_id": sha256(f"{identity.project_hash}:{platform.node()}".encode("utf-8")).hexdigest(),
    }


def _write_member(archive: zipfile.ZipFile, path: str, payload: bytes) -> None:
    info = zipfile.ZipInfo(path)
    info.date_time = (1980, 1, 1, 0, 0, 0)
    info.external_attr = (stat.S_IFREG | 0o600) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    archive.writestr(info, payload)


def _bundle_source(value: str | Path) -> Path:
    return _regular_file(Path(value), "bundle")


def _read_bundle(bundle_path: str | Path) -> _BundleContents:
    source = _bundle_source(bundle_path)
    try:
        if source.stat().st_size > _MAX_BUNDLE_BYTES:
            raise BundleError("Bundle trop volumineux.")
        with zipfile.ZipFile(source, "r") as archive:
            infos = archive.infolist()
            if not 2 <= len(infos) <= _MAX_MEMBERS:
                raise BundleError("Nombre de membres de bundle invalide.")
            names = [info.filename for info in infos]
            if len(set(names)) != len(names) or _MANIFEST_NAME not in names or _MIGRATIONS_NAME not in names:
                raise BundleError("Structure de bundle ambiguë ou incomplète.")
            payloads: dict[str, bytes] = {}
            total = 0
            for info in infos:
                _safe_member(info)
                if info.file_size > _MAX_FILE_BYTES or info.file_size < 0:
                    raise BundleError("Membre de bundle hors borne.")
                if info.compress_size and info.file_size > info.compress_size * 128:
                    raise BundleError("Ratio de compression de bundle non admissible.")
                total += info.file_size
                if total > _MAX_BUNDLE_BYTES:
                    raise BundleError("Contenu décompressé du bundle hors borne.")
                payload = archive.read(info)
                if len(payload) != info.file_size:
                    raise BundleError("Taille de membre de bundle incohérente.")
                payloads[info.filename] = payload
    except (OSError, zipfile.BadZipFile) as exc:
        raise BundleError("Lecture du bundle impossible.") from exc
    manifest_bytes = payloads.pop(_MANIFEST_NAME)
    try:
        parsed = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BundleError("Manifest de bundle illisible.") from exc
    if not isinstance(parsed, dict) or canonical_json(parsed).encode("utf-8") != manifest_bytes:
        raise BundleError("Manifest de bundle non canonique.")
    _validate_manifest(parsed, payloads)
    return _BundleContents(manifest=parsed, manifest_bytes=manifest_bytes, files=payloads)


def _safe_member(info: zipfile.ZipInfo) -> None:
    path = PurePosixPath(info.filename)
    if info.is_dir() or path.is_absolute() or ".." in path.parts or "\\" in info.filename or not info.filename or path.as_posix() != info.filename:
        raise BundleError("Chemin de membre de bundle non canonique.")
    if (info.external_attr >> 16) & stat.S_IFMT(stat.S_IFLNK) == stat.S_IFLNK:
        raise BundleError("Symlink dans bundle refusé.")


def _validate_manifest(manifest: Mapping[str, Any], files: Mapping[str, bytes]) -> None:
    expected = {"artifact_inventory", "bundle_id", "checkpoint", "files", "format", "memory_hash", "profile_hash", "project_identity", "schema_hash", "source_device_id"}
    if set(manifest) != expected or manifest.get("format") != BUNDLE_FORMAT:
        raise BundleError("Format de manifest de bundle inconnu.")
    _bundle_id(manifest.get("bundle_id"))
    if not isinstance(manifest.get("project_identity"), dict) or set(manifest["project_identity"]) != {"project_id", "profile_version", "profile_hash", "workspace_hash", "project_hash"}:
        raise BundleError("Identité de projet du manifest invalide.")
    for key in ("memory_hash", "profile_hash", "schema_hash", "source_device_id"):
        if not isinstance(manifest.get(key), str) or len(manifest[key]) != _SHA256_LENGTH or any(character not in "0123456789abcdef" for character in manifest[key]):
            raise BundleError(f"Hash de manifest invalide : {key}.")
    if not isinstance(manifest.get("checkpoint"), dict) or set(manifest["checkpoint"]) != {"checkpointed", "busy", "log_frames", "checkpointed_frames"}:
        raise BundleError("État checkpoint du manifest invalide.")
    inventory = manifest.get("files")
    artifacts = manifest.get("artifact_inventory")
    if not isinstance(inventory, list) or not isinstance(artifacts, list) or not inventory:
        raise BundleError("Inventaire de bundle invalide.")
    expected_names = {_MIGRATIONS_NAME, *files}
    if {item.get("path") for item in inventory if isinstance(item, dict)} != expected_names or len(inventory) != len(expected_names):
        raise BundleError("Inventaire de bundle non bijectif.")
    checked: list[dict[str, Any]] = []
    for item in inventory:
        if not isinstance(item, dict) or set(item) != {"path", "sha256", "size"}:
            raise BundleError("Entrée d’inventaire de bundle invalide.")
        path = item["path"]
        if not isinstance(path, str) or path not in files:
            raise BundleError("Entrée d’inventaire absente du bundle.")
        payload = files[path]
        if item["sha256"] != _sha256(payload) or item["size"] != len(payload):
            raise BundleError("Hash ou taille de membre de bundle incohérent.")
        checked.append(item)
    if checked != sorted(checked, key=lambda item: item["path"]):
        raise BundleError("Inventaire de bundle non déterministe.")
    expected_artifacts = [item for item in checked if item["path"].startswith("runtime/artifacts/")]
    if artifacts != expected_artifacts:
        raise BundleError("Inventaire d’artefacts de bundle incohérent.")
    if _sha256(files[_MIGRATIONS_NAME]) != manifest["schema_hash"]:
        raise BundleError("Hash de schéma du bundle incohérent.")
    memory_paths = [path for path in files if path.startswith("runtime/") and path.endswith("memory.sqlite")]
    if len(memory_paths) != 1 or _sha256(files[memory_paths[0]]) != manifest["memory_hash"]:
        raise BundleError("Hash de mémoire du bundle incohérent.")


def _verify_target_configuration(runtime: Path, files: Mapping[str, bytes]) -> None:
    for name, payload in files.items():
        if not name.startswith("runtime/") or name == "runtime/memory.sqlite" or name.startswith("runtime/artifacts/"):
            continue
        relative = _runtime_relative(name)
        candidate = runtime / relative
        if not candidate.exists() or candidate.is_symlink() or not candidate.is_file():
            raise BundleError("Configuration cible absente ou ambiguë avant restauration.")
        if _read_regular(candidate, f"configuration cible {relative.as_posix()}") != payload:
            raise BundleError("Configuration cible divergente : restauration refusée.")


def _target_matches(runtime: Path, files: Mapping[str, bytes], *, include_memory: bool = True) -> bool:
    try:
        for name, payload in files.items():
            if not name.startswith("runtime/"):
                continue
            if not include_memory and (name.endswith("/memory.sqlite") or name.startswith("runtime/artifacts/")):
                continue
            target = runtime / _runtime_relative(name)
            if not target.exists() or target.is_symlink() or not target.is_file() or _read_regular(target, name) != payload:
                return False
        return True
    except BundleError:
        return False


def _runtime_relative(name: str) -> Path:
    path = PurePosixPath(name)
    if len(path.parts) < 2 or path.parts[0] != "runtime" or ".." in path.parts:
        raise BundleError("Chemin runtime de bundle invalide.")
    return Path(*path.parts[1:])


def _materialize_runtime(runtime: Path, files: Mapping[str, bytes]) -> None:
    for name, payload in files.items():
        if not name.startswith("runtime/"):
            continue
        relative = _runtime_relative(name)
        target = runtime / relative
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if target.parent.is_symlink():
            raise BundleError("Répertoire staging symlinké refusé.")
        with target.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(target, 0o600)


def _verify_snapshot_database(
    path: Path,
    identity: ProjectIdentity,
    manifest: Mapping[str, Any],
    migration_payload: bytes,
) -> None:
    _regular_file(path, "mémoire staging")
    try:
        connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro&immutable=1", uri=True)
        try:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()
            foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
            metadata_rows = connection.execute("SELECT key, value_json FROM store_metadata ORDER BY key").fetchall()
            migration_rows = connection.execute("SELECT version, checksum FROM schema_migrations ORDER BY version").fetchall()
        finally:
            connection.close()
    except sqlite3.DatabaseError as exc:
        raise BundleError("Mémoire staging SQLite invalide.") from exc
    if integrity is None or integrity[0] != "ok" or foreign_keys:
        raise BundleError("Intégrité SQLite du bundle refusée.")
    try:
        metadata = {str(key): json.loads(str(value)) for key, value in metadata_rows}
    except (TypeError, ValueError) as exc:
        raise BundleError("Métadonnées SQLite du bundle invalides.") from exc
    if metadata.get("project_identity") != identity.as_dict():
        raise BundleError("Identité SQLite du bundle incohérente avec la cible.")
    bundled = {str(version): str(checksum) for version, checksum in migration_rows}
    try:
        runtime_checksums = {str(version): value for version, value in migration_checksums(MigrationRunner().discover()).items()}
        declared = json.loads(migration_payload.decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BundleError("Ledger de migrations du bundle invalide.") from exc
    if not isinstance(declared, dict) or declared != bundled or declared != runtime_checksums:
        raise BundleError("Ledger de migrations du bundle incompatible avec le runtime.")
    if _sha256(canonical_json(declared).encode("utf-8")) != manifest["schema_hash"]:
        raise BundleError("Hash de schéma staging incohérent.")
