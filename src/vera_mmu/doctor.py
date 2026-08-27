"""Composite, transport-neutral and read-only diagnostics for a VERA project."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3
from typing import Any, Callable, Mapping

from .identity import ProjectIdentity, ProfileError, load_profile, project_identity
from .migrations import MigrationRunner, migration_checksums
from .project_catalogs import ProjectCatalogError, load_project_catalogs
from .workspace import Workspace, WorkspaceError, resolve_workspace


DOCTOR_FORMAT = "vera-doctor-report/v1"
_CHECK_ORDER = (
    "project_identity",
    "profile",
    "workspace",
    "catalogs",
    "runtime",
    "sqlite_integrity",
    "migration_ledger",
    "wal",
    "artifact_store",
    "resume",
    "mcp_transport",
    "vcs",
)


@dataclass(frozen=True)
class DoctorCheck:
    """One deterministic, side-effect-free project health check."""

    name: str
    status: str
    detail: str
    remediation: str

    def as_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "status": self.status,
            "detail": self.detail,
            "remediation": self.remediation,
        }


@dataclass(frozen=True)
class DoctorReport:
    """Machine-readable composite report; only `FAIL` makes the report fail."""

    format: str
    status: str
    project_identity: dict[str, str] | None
    checks: tuple[DoctorCheck, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "format": self.format,
            "status": self.status,
            "project_identity": self.project_identity,
            "checks": [check.as_dict() for check in self.checks],
        }


def diagnose_project(profile_path: str | Path) -> DoctorReport:
    """Inspect one VERA project without opening, initializing or migrating its store.

    The diagnostic never follows symlinks for runtime children and opens SQLite with
    `mode=ro`. An unavailable optional host feature is `INFO`; malformed state is `FAIL`.
    """
    path = Path(profile_path)
    checks: dict[str, DoctorCheck] = {}
    profile: Mapping[str, Any] | None = None
    workspace: Workspace | None = None
    identity: ProjectIdentity | None = None

    try:
        profile = load_profile(path)
        checks["profile"] = _pass("profile", "Project Profile VERA valide.")
    except (ProfileError, OSError, ValueError) as exc:
        checks["profile"] = _fail("profile", str(exc), "Corriger le Project Profile puis relancer le Doctor.")

    if profile is not None:
        try:
            workspace = resolve_workspace(profile, path)
            checks["workspace"] = _pass("workspace", f"Workspace confiné : {workspace.project_root}")
        except (WorkspaceError, OSError, ValueError) as exc:
            checks["workspace"] = _fail("workspace", str(exc), "Corriger la racine et les chemins workspace du profile.")
        try:
            catalogs = load_project_catalogs(path)
            checks["catalogs"] = _pass(
                "catalogs",
                "Catalogues déclaratifs valides : "
                f"capabilities={catalogs.capability_catalog_hash[:12]}, "
                f"gates={catalogs.gate_catalog_hash[:12]}, policies={catalogs.policy_hash[:12]}.",
            )
        except (ProjectCatalogError, OSError, ValueError) as exc:
            checks["catalogs"] = _fail("catalogs", str(exc), "Corriger les catalogues déclarés par le Project Profile.")

    if profile is not None and workspace is not None:
        try:
            identity = project_identity(profile, workspace)
            checks["project_identity"] = _pass("project_identity", f"Identité calculée pour {identity.project_id}.")
        except (ProfileError, WorkspaceError, OSError, ValueError) as exc:
            checks["project_identity"] = _fail("project_identity", str(exc), "Corriger profile/workspace puis vérifier l’identité du projet.")
        _diagnose_runtime(checks, profile, workspace, identity)
    else:
        checks.setdefault("project_identity", _fail("project_identity", "Identité indisponible sans profile et workspace valides.", "Réparer profile et workspace."))
        checks.setdefault("runtime", _fail("runtime", "Runtime indisponible sans workspace valide.", "Réparer le workspace du profile."))
        _database_unavailable(checks, "Runtime indisponible sans profile et workspace valides.")
        checks["artifact_store"] = _fail("artifact_store", "Répertoire d’artefacts indisponible sans runtime valide.", "Réparer le runtime du profile.")
        checks["resume"] = _fail("resume", "Configuration de reprise indisponible sans profile valide.", "Réparer la section resume du profile.")
        checks["vcs"] = _info("vcs", "VCS non observé sans workspace valide.")

    _diagnose_mcp_transport(checks)
    ordered = tuple(checks[name] for name in _CHECK_ORDER)
    status = "FAIL" if any(check.status == "FAIL" for check in ordered) else "PASS"
    return DoctorReport(
        format=DOCTOR_FORMAT,
        status=status,
        project_identity=None if identity is None else identity.as_dict(),
        checks=ordered,
    )


def _diagnose_runtime(
    checks: dict[str, DoctorCheck],
    profile: Mapping[str, Any],
    workspace: Workspace,
    identity: ProjectIdentity | None,
) -> None:
    runtime = workspace.runtime_dir
    try:
        sqlite_name = _runtime_child(profile, "sqlite_file")
        artifacts_name = _runtime_child(profile, "artifacts_dir")
    except ValueError as exc:
        checks["runtime"] = _fail("runtime", str(exc), "Corriger les chemins de storage du profile.")
        _database_unavailable(checks, str(exc))
        checks["artifact_store"] = _fail("artifact_store", str(exc), "Corriger les chemins de storage du profile.")
        checks["resume"] = _diagnose_resume(profile)
        checks["vcs"] = _diagnose_vcs(workspace)
        return

    if runtime.is_symlink() or not runtime.exists() or not runtime.is_dir():
        checks["runtime"] = _fail("runtime", "Runtime absent, non répertoire ou symlinké.", "Initialiser le runtime project-local puis relancer le Doctor.")
        _database_unavailable(checks, "Runtime absent ou ambigu.")
        checks["artifact_store"] = _fail("artifact_store", "Runtime absent ou ambigu.", "Réparer le runtime project-local.")
    else:
        checks["runtime"] = _pass("runtime", f"Runtime project-local valide : {runtime}")
        database = runtime / sqlite_name
        _diagnose_database(checks, database, identity)
        _diagnose_artifact_store(checks, runtime / artifacts_name)
    checks["resume"] = _diagnose_resume(profile)
    checks["vcs"] = _diagnose_vcs(workspace)


def _runtime_child(profile: Mapping[str, Any], key: str) -> Path:
    storage = profile.get("storage")
    if not isinstance(storage, Mapping):
        raise ValueError("Section storage invalide.")
    value = storage.get(key)
    if not isinstance(value, str) or not value or Path(value).is_absolute() or ".." in Path(value).parts or "\\" in value:
        raise ValueError(f"storage.{key} invalide pour Doctor.")
    return Path(value)


def _diagnose_database(
    checks: dict[str, DoctorCheck], database: Path, identity: ProjectIdentity | None
) -> None:
    if database.is_symlink() or not database.exists() or not database.is_file():
        _database_unavailable(checks, "SQLite absent, non fichier ou symlinké.")
        return
    try:
        connection = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
        try:
            integrity_row = connection.execute("PRAGMA integrity_check").fetchone()
            foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
            journal_row = connection.execute("PRAGMA journal_mode").fetchone()
            metadata_rows = connection.execute("SELECT key, value_json FROM store_metadata ORDER BY key").fetchall()
            migration_rows = connection.execute("SELECT version, checksum FROM schema_migrations ORDER BY version").fetchall()
        finally:
            connection.close()
    except sqlite3.DatabaseError as exc:
        _database_unavailable(checks, f"SQLite illisible : {exc}")
        return
    if integrity_row is None or integrity_row[0] != "ok" or foreign_keys:
        checks["sqlite_integrity"] = _fail("sqlite_integrity", "PRAGMA integrity_check ou foreign_key_check invalide.", "Restaurer un bundle VERA vérifié ou réparer la base SQLite hors ligne.")
    else:
        checks["sqlite_integrity"] = _pass("sqlite_integrity", "SQLite integrity_check et foreign_key_check valides.")
    try:
        metadata = {str(key): json.loads(str(value)) for key, value in metadata_rows}
        current = {str(version): checksum for version, checksum in migration_checksums(MigrationRunner().discover()).items()}
        persisted = {str(version): str(checksum) for version, checksum in migration_rows}
        expected_identity = None if identity is None else identity.as_dict()
        expected_version = max(int(version) for version in current)
        schema = metadata.get("store_format")
        valid = (
            metadata.get("project_identity") == expected_identity
            and isinstance(schema, dict)
            and schema == {"schema_version": expected_version}
            and persisted == current
        )
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        valid = False
        metadata_error = str(exc)
    else:
        metadata_error = ""
    if valid:
        checks["migration_ledger"] = _pass("migration_ledger", f"Ledger et métadonnées alignés sur le schéma {expected_version}.")
    else:
        detail = "Ledger de migrations, métadonnées ou identité SQLite incohérents."
        if metadata_error:
            detail = f"{detail} {metadata_error}"
        checks["migration_ledger"] = _fail("migration_ledger", detail, "Restaurer une mémoire de même identité ou appliquer la migration via le cycle VERA normal.")
    journal_mode = "" if journal_row is None else str(journal_row[0]).lower()
    if journal_mode == "wal":
        checks["wal"] = _pass("wal", "SQLite utilise le journal WAL.")
    else:
        checks["wal"] = _fail("wal", f"Journal SQLite inattendu : {journal_mode or 'absent'}.", "Ouvrir et migrer la mémoire avec le runtime VERA afin de rétablir WAL.")


def _database_unavailable(checks: dict[str, DoctorCheck], detail: str) -> None:
    remediation = "Initialiser ou restaurer une mémoire VERA project-bound valide."
    checks["sqlite_integrity"] = _fail("sqlite_integrity", detail, remediation)
    checks["migration_ledger"] = _fail("migration_ledger", detail, remediation)
    checks["wal"] = _fail("wal", detail, remediation)


def _diagnose_artifact_store(checks: dict[str, DoctorCheck], artifacts: Path) -> None:
    if artifacts.is_symlink():
        checks["artifact_store"] = _fail("artifact_store", "Répertoire d’artefacts symlinké : refus de périmètre ambigu.", "Remplacer le symlink par un répertoire local sous le runtime.")
    elif artifacts.exists() and not artifacts.is_dir():
        checks["artifact_store"] = _fail("artifact_store", "Chemin d’artefacts présent mais non répertoire.", "Remplacer le chemin par un répertoire local sous le runtime.")
    elif artifacts.exists():
        checks["artifact_store"] = _pass("artifact_store", "Répertoire d’artefacts local disponible.")
    else:
        checks["artifact_store"] = _pass("artifact_store", "Aucun artefact externe matérialisé : état vide valide.")


def _diagnose_resume(profile: Mapping[str, Any]) -> DoctorCheck:
    resume = profile.get("resume")
    if isinstance(resume, Mapping) and isinstance(resume.get("sections"), list):
        return _pass("resume", "Configuration de reprise déclarative valide.")
    return _fail("resume", "Configuration de reprise absente ou invalide.", "Corriger la section resume du Project Profile.")


def _diagnose_mcp_transport(checks: dict[str, DoctorCheck]) -> None:
    try:
        from mcp.server import MCPServer

        del MCPServer
    except ImportError as exc:
        checks["mcp_transport"] = _fail("mcp_transport", str(exc), "Installer la dépendance MCP déclarée par le paquet VERA.")
    else:
        checks["mcp_transport"] = _pass("mcp_transport", "Runtime MCP importable; le diagnostic ne démarre aucun serveur.")


def _diagnose_vcs(workspace: Workspace) -> DoctorCheck:
    marker = workspace.project_root / ".git"
    if marker.is_symlink():
        return _fail("vcs", "Marqueur VCS symlinké : état ambigu.", "Utiliser un marqueur VCS local non symlinké ou retirer la configuration ambiguë.")
    if marker.exists() and marker.is_dir():
        return _pass("vcs", "Marqueur Git project-local observé.")
    return _info("vcs", "Aucun VCS local observé : configuration no-Git valide.")


def _pass(name: str, detail: str) -> DoctorCheck:
    return DoctorCheck(name, "PASS", detail, "Aucune action requise.")


def _info(name: str, detail: str) -> DoctorCheck:
    return DoctorCheck(name, "INFO", detail, "Information : aucune correction obligatoire.")


def _fail(name: str, detail: str, remediation: str) -> DoctorCheck:
    return DoctorCheck(name, "FAIL", detail, remediation)
