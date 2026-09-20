"""Composite, transport-neutral and read-only diagnostics for a VERA project."""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import sqlite3
import subprocess
from typing import Any, Callable, Mapping

from .identity import ProjectIdentity, ProfileError, load_profile, project_identity
from .profile_migration import ProfileMigrationError, inspect_profile_migration_journal
from .migrations import MigrationRunner, migration_checksums
from .memory_sync import VOLATILE_PATTERNS
from .playbook import PLAYBOOK_FILE_NAME
from .project_catalogs import ProjectCatalogError, load_project_catalogs
from .write_api import PROOF_HMAC_SECRET_VARIABLE
from .workspace import Workspace, WorkspaceError, resolve_workspace


DOCTOR_FORMAT = "vera-doctor-report/v1"
_CHECK_ORDER = (
    "project_identity",
    "profile",
    "profile_rebind",
    "profile_migration",
    "workspace",
    "capability_catalog",
    "gates",
    "policies",
    "playbook",
    "runtime",
    "sqlite_integrity",
    "migration_ledger",
    "wal",
    "artifact_store",
    "hmac",
    "resume",
    "mcp_transport",
    "hooks",
    "vcs",
    "zero_pollution",
)
# The rows the specification requires the report to carry (§45). Extra rows are welcome;
# a missing one means the report no longer answers what the specification asks of it.
SPECIFIED_CHECKS = frozenset({
    "project_identity", "profile", "migration_ledger", "sqlite_integrity", "wal", "artifact_store",
    "hmac", "capability_catalog", "gates", "policies", "playbook", "runtime", "mcp_transport", "hooks", "resume", "vcs",
})
_CATALOG_FILES = {"capability_catalog": "capabilities.yaml", "gates": "gates.yaml", "policies": "policies.yaml"}
_CATALOG_KEYWORDS = {"capability_catalog": "capabilit", "gates": "gate", "policies": "policie"}


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
        checks["profile_rebind"] = _diagnose_profile_rebind(path)
        checks["profile_migration"] = _diagnose_profile_migration(path)
        try:
            workspace = resolve_workspace(profile, path)
            checks["workspace"] = _pass("workspace", f"Workspace confiné : {workspace.project_root}")
        except (WorkspaceError, OSError, ValueError) as exc:
            checks["workspace"] = _fail("workspace", str(exc), "Corriger la racine et les chemins workspace du profile.")
        _diagnose_catalogs(checks, path)

    if profile is not None and workspace is not None:
        try:
            identity = project_identity(profile, workspace)
            checks["project_identity"] = _pass("project_identity", f"Identité calculée pour {identity.project_id}.")
        except (ProfileError, WorkspaceError, OSError, ValueError) as exc:
            checks["project_identity"] = _fail("project_identity", str(exc), "Corriger profile/workspace puis vérifier l’identité du projet.")
        _diagnose_runtime(checks, profile, workspace, identity)
    else:
        checks["profile_rebind"] = _diagnose_profile_rebind(path)
        checks["profile_migration"] = _diagnose_profile_migration(path)
        checks.setdefault("project_identity", _fail("project_identity", "Identité indisponible sans profile et workspace valides.", "Réparer profile et workspace."))
        checks.setdefault("runtime", _fail("runtime", "Runtime indisponible sans workspace valide.", "Réparer le workspace du profile."))
        _database_unavailable(checks, "Runtime indisponible sans profile et workspace valides.")
        checks["artifact_store"] = _fail("artifact_store", "Répertoire d’artefacts indisponible sans runtime valide.", "Réparer le runtime du profile.")
        checks["resume"] = _fail("resume", "Configuration de reprise indisponible sans profile valide.", "Réparer la section resume du profile.")
        checks["vcs"] = _info("vcs", "VCS non observé sans workspace valide.")
        _diagnose_catalogs(checks, path)

    checks["playbook"] = _diagnose_playbook(store_profile_path=path, workspace=workspace)
    _diagnose_mcp_transport(checks)
    checks.setdefault("hmac", _info("hmac", "Policy de preuve non lisible sans mémoire VERA valide."))
    checks["hooks"] = _diagnose_hooks(profile, workspace)
    # The profile lives in the runtime directory by construction, as the migration row assumes.
    checks["zero_pollution"] = (
        _diagnose_zero_pollution(workspace, path.parent)
        if workspace is not None
        else _info("zero_pollution", "Empreinte non observable sans workspace valide.")
    )
    ordered = tuple(checks[name] for name in _CHECK_ORDER)
    status = "FAIL" if any(check.status == "FAIL" for check in ordered) else "PASS"
    return DoctorReport(
        format=DOCTOR_FORMAT,
        status=status,
        project_identity=None if identity is None else identity.as_dict(),
        checks=ordered,
    )


def _diagnose_profile_rebind(path: Path) -> DoctorCheck:
    journals = list(path.parent.glob(".profile-rebind-*.json")) if path.parent.exists() and not path.parent.is_symlink() else []
    if len(journals) > 1:
        return _fail("profile_rebind", "Plusieurs journaux de rebind présents : reprise ambiguë.", "Exécuter une reprise explicite et conservatrice hors Doctor.")
    if len(journals) == 1:
        return _fail("profile_rebind", "Rebind de Project Profile interrompu ou non acquitté.", "Exécuter la reprise explicite du rebind puis relancer le Doctor.")
    return _pass("profile_rebind", "Aucun rebind de Project Profile en attente.")


def _diagnose_profile_migration(path: Path) -> DoctorCheck:
    control_dir = path.parent.parent if path.parent.name == ".vera-mmu" else path.parent
    if control_dir.is_symlink() or not control_dir.is_dir():
        return _fail("profile_migration", "Répertoire de contrôle de migration ambigu.", "Retirer le symlink puis relancer le Doctor.")
    journals = sorted(control_dir.glob(".vera-profile-migration-*.json"))
    if not journals:
        return _pass("profile_migration", "Aucune migration physique Profile en attente.")
    if len(journals) != 1:
        return _fail("profile_migration", "Plusieurs journaux de migration présents : reprise ambiguë.", "Inspecter et reprendre explicitement un seul journal hors Doctor.")
    try:
        report = inspect_profile_migration_journal(path)
    except ProfileMigrationError as exc:
        return _fail("profile_migration", str(exc), "Corriger ou reprendre explicitement le journal de migration.")
    if report["status"] == "READY_FOR_EXECUTOR":
        return _info("profile_migration", "Migration Profile planifiée et prête pour exécution confirmée.")
    return _fail("profile_migration", f"Migration Profile non stable : {report['status']}.", "Exécuter la reprise physique explicite ou restaurer un état cohérent.")


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
        _diagnose_hmac(checks, database)
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


def _diagnose_zero_pollution(workspace: Workspace, runtime_dir: Path) -> DoctorCheck:
    """Check that nothing SQLite rebuilds on its own is versioned by the project (§36).

    Two different claims are at stake and only one is cheap: that the ignore rules are declared,
    and that nothing volatile is actually tracked. A rule added after the fact does not untrack
    a file, so an installation upgraded from an earlier version can carry versioned sidecars
    while its rules look perfect. This asks Git what it tracks rather than inferring it — and
    says `INFO` when it cannot ask, never `PASS`.
    """
    rules = runtime_dir / ".gitignore"
    declared = rules.is_file() and not rules.is_symlink() and all(
        pattern in rules.read_text(encoding="utf-8", errors="replace") for pattern in VOLATILE_PATTERNS
    )
    marker = workspace.project_root / ".git"
    if not marker.exists() or marker.is_symlink():
        if declared:
            return _info("zero_pollution", "Aucun dépôt Git observé : règles d’ignorance déclarées, rien à vérifier.")
        return _fail(
            "zero_pollution",
            "Règles d’ignorance VERA absentes ou incomplètes.",
            "Restaurer `.vera-mmu/.gitignore` avec `repair`, qui le dérive du Project Profile.",
        )
    try:
        listed = subprocess.run(
            ["git", "ls-files", "--", str(runtime_dir)],
            cwd=workspace.project_root, capture_output=True, text=True, timeout=15, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return _info("zero_pollution", "Git non interrogeable : versionnement des fichiers volatils non observé.")
    if listed.returncode != 0:
        return _info("zero_pollution", "Dépôt Git non interrogeable : versionnement des fichiers volatils non observé.")
    volatile = sorted(path for path in listed.stdout.splitlines() if path.endswith(("-wal", "-shm")))
    if volatile:
        return _fail(
            "zero_pollution",
            f"Fichiers SQLite volatils versionnés : {', '.join(volatile)}.",
            "Les retirer de l’index Git (`git rm --cached`) ; ils sont reconstruits par SQLite et n’appartiennent pas à la mémoire.",
        )
    if not declared:
        return _fail(
            "zero_pollution",
            "Aucun fichier volatil versionné, mais les règles d’ignorance sont absentes ou incomplètes.",
            "Restaurer `.vera-mmu/.gitignore` avec `repair`, qui le dérive du Project Profile.",
        )
    return _pass("zero_pollution", "Aucun fichier SQLite volatil versionné ; règles d’ignorance déclarées.")


def _diagnose_catalogs(checks: dict[str, DoctorCheck], path: Path) -> None:
    """Report one row per declarative catalog so a failure names the file that repairs it."""
    try:
        catalogs = load_project_catalogs(path)
    except (ProjectCatalogError, OSError, ValueError) as exc:
        # The catalogs load as one unit, so attribute the failure to the file the error names
        # and mark the others unevaluated rather than reporting three failures for one broken
        # file, which would hide which element actually needs repair.
        message = str(exc)
        blamed = [name for name, keyword in _CATALOG_KEYWORDS.items() if keyword in message.lower()]
        for name, filename in _CATALOG_FILES.items():
            if not blamed or name in blamed:
                checks[name] = _fail(name, message, f"Corriger `.vera-mmu/{filename}` déclaré par le Project Profile.")
            else:
                checks[name] = _info(name, f"Non évalué : le chargement des catalogues s’est arrêté sur {', '.join(sorted(blamed))}.")
        return
    declared = len(catalogs.capabilities["capabilities"])
    required = sum(1 for gate in catalogs.gates["gates"] if gate.get("required") is True)
    checks["capability_catalog"] = _pass("capability_catalog", f"{declared} capability(ies) déclarée(s), hash={catalogs.capability_catalog_hash[:12]}.")
    checks["gates"] = _pass("gates", f"{len(catalogs.gates['gates'])} gate(s) dont {required} requise(s), hash={catalogs.gate_catalog_hash[:12]}.")
    checks["policies"] = _pass("policies", f"Catalogue de policies valide, hash={catalogs.policy_hash[:12]}.")


def _diagnose_hmac(checks: dict[str, DoctorCheck], database: Path) -> None:
    """Report the proof policy and whether the secret it requires is actually reachable.

    The secret lives in the environment, never in the project runtime, because memory sync
    commits that directory to Git. Only its presence is reported, never its value.
    """
    try:
        connection = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
        try:
            row = connection.execute("SELECT algorithm, hmac_required FROM proof_policy WHERE singleton=1").fetchone()
        finally:
            connection.close()
    except sqlite3.DatabaseError as exc:
        checks["hmac"] = _fail("hmac", f"Policy de preuve illisible : {exc}", "Réparer la mémoire VERA puis relancer le Doctor.")
        return
    if row is None:
        checks["hmac"] = _info("hmac", "Aucune policy de preuve déclarée : aucune promotion n’est possible pour l’instant.")
        return
    algorithm = str(row[0])
    if not bool(row[1]):
        checks["hmac"] = _pass("hmac", f"Policy de preuve `{algorithm}` déclarée sans signature requise.")
        return
    if os.environ.get(PROOF_HMAC_SECRET_VARIABLE, "").strip():
        checks["hmac"] = _pass("hmac", f"Policy `{algorithm}` exige HMAC ; le secret est présent dans l’environnement.")
        return
    checks["hmac"] = _fail(
        "hmac",
        f"Policy `{algorithm}` exige HMAC mais aucun secret n’est disponible : toute promotion serait refusée.",
        f"Définir {PROOF_HMAC_SECRET_VARIABLE} hors du dépôt, jamais sous `.vera-mmu/` que la synchronisation mémoire commit.",
    )


def _diagnose_hooks(profile: Mapping[str, Any] | None, workspace: Workspace | None) -> DoctorCheck:
    """Check that every integration the profile enables is actually installed project-local."""
    if profile is None or workspace is None:
        return _info("hooks", "Intégrations non observables sans profile et workspace valides.")
    enabled = profile.get("integrations", {}).get("enabled", [])
    if not enabled:
        return _info("hooks", "Aucune intégration déclarée : aucun hook project-local attendu.")
    missing = [str(name) for name in enabled if not _integration_installed(workspace.project_root, str(name))]
    if missing:
        return _fail(
            "hooks",
            f"Intégration(s) déclarée(s) mais non installée(s) : {', '.join(sorted(missing))}.",
            "Lancer `vmmu install <profile> --adapter <nom> --apply-project --confirm` après relecture de la preview.",
        )
    # Installée ne veut pas dire exécutable. Mesuré : `doctor` rendait PASS sur un `.mcp.json`
    # et des hooks désignant `vmmu-claude-code-local-mcp` / `-hook`, scripts console qu'aucun
    # artefact de release n'embarque. Un fichier présent atteste qu'on a écrit, pas que l'hôte
    # pourra lancer quoi que ce soit — et se déclarer sain sur une configuration inopérante est
    # exactement ce que ce produit existe pour empêcher.
    from .claude_code_local import HOOK_ENTRYPOINT, MCP_ENTRYPOINT, entrypoint_status

    if any(str(name) == "claude-code-local" for name in enabled):
        statut = entrypoint_status()
        introuvables = sorted(
            {"hook": HOOK_ENTRYPOINT, "mcp": MCP_ENTRYPOINT}[nom]
            for nom, valeur in statut.items()
            if valeur is None
        )
        if introuvables:
            return _fail(
                "hooks",
                "Intégration installée mais inexécutable : commande(s) introuvable(s) — "
                + ", ".join(f"`{nom}`" for nom in introuvables)
                + ".",
                "Installer le paquet VERA (`pip install vera-mmu`) ou réinstaller l’adapter avec "
                "la CLI autonome, puis relancer `vmmu install … --apply-project --confirm`.",
            )
        ecart = _claude_local_drift(workspace.project_root)
        if ecart is not None:
            return _fail("hooks", ecart, "Relancer `vmmu install <profile> --adapter claude-code-local --apply-project --confirm`.")
    verifiees = sorted(str(nom) for nom in enabled if str(nom) in _ADAPTER_MARKERS)
    if len(verifiees) == len(enabled):
        return _pass("hooks", f"{len(enabled)} intégration(s) déclarée(s) et installée(s) project-local.")
    # Dire ce qui a été vérifié, et ce qui ne l’a pas été. Un contrôle qui tait sa portée se
    # fait lire comme s’il avait tout couvert — c’est ainsi que le `.claude/` d’un autre outil
    # passait pour une installation VERA.
    return _pass(
        "hooks",
        f"{len(enabled)} intégration(s) déclarée(s) ; installation vérifiée pour "
        + (", ".join(f"`{nom}`" for nom in verifiees) if verifiees else "aucune")
        + ", non vérifiable pour les autres (marqueurs non catalogués).",
    )


def _claude_local_drift(project_root: Path) -> str | None:
    """Le serveur déclaré dans `.mcp.json` est-il encore celui que l'installation a attesté ?

    **Le défaut mesuré, et c'est le pire du lot.** Éditer `.vera-mmu/playbook.md` — ce que le
    produit demande explicitement de faire — suffit à ce que le serveur MCP déclaré refuse de
    démarrer : « État d'installation Claude local périmé ou altéré ». Pendant ce temps, `doctor`
    rendait PASS sur ses vingt contrôles, `repair` répondait `NOTHING_TO_REPAIR`, et `conclude`
    certifiait « Les 18 étapes sont franchies ». **Le verdict terminal du produit était vert
    pendant que ce qu'il livre était mort.**

    Ce contrôle ne démarre aucun serveur — `diagnose_project` s'interdit d'ouvrir la mémoire — mais
    il compare ce que deux fichiers déclarent, ce qui suffit à voir l'écart le plus courant : un
    `.mcp.json` qui ne désigne plus ce que l'état d'installation atteste, ou un programme devenu
    introuvable depuis. Un contrôle qui ne peut pas tout voir le dit dans son libellé plutôt que
    de laisser croire qu'il a tout vu.
    """
    etat = project_root / ".vera-mmu" / "generated" / "claude-code-local-install.json"
    mcp = project_root / ".mcp.json"
    if not etat.is_file():
        return "Intégration `claude-code-local` installée sans état attesté sous `.vera-mmu/generated/`."
    try:
        atteste = json.loads(etat.read_text(encoding="utf-8"))["claudeCodeLocal"]["mcpServer"]
        identifiant = str(atteste["id"])
        attendu = {cle: valeur for cle, valeur in atteste.items() if cle != "id"}
        declare = json.loads(mcp.read_text(encoding="utf-8"))["mcpServers"]
    except (KeyError, TypeError, ValueError, OSError):
        return "État d’installation `claude-code-local` ou `.mcp.json` illisible : l’intégration n’est pas vérifiable."
    if identifiant not in declare:
        return f"`.mcp.json` ne déclare plus le serveur `{identifiant}` que l’installation atteste."
    if declare[identifiant] != attendu:
        return f"Le serveur `{identifiant}` déclaré dans `.mcp.json` diverge de l’état attesté : il refusera de démarrer."
    programme = attendu.get("command")
    if not isinstance(programme, str) or not programme:
        return f"Le serveur `{identifiant}` ne déclare aucun programme exécutable."
    # Résolu par l'adapter, pas ici : une seule source pour ce que le produit sait lancer. Le
    # doctor ne sonde aucune chaîne d'outils tierce — il vérifie seulement que la commande que
    # VERA a elle-même écrite est encore là.
    from .claude_code_local import program_is_launchable

    if not program_is_launchable(programme):
        return f"Le programme `{programme}` déclaré par `{identifiant}` est introuvable : le serveur ne démarrera pas."
    return None


#: Ce que **chaque** adapter écrit project-local, et rien d'autre. La liste est fermée : un
#: adapter absent n'est pas deviné, il est déclaré non vérifiable — voir `_integration_installed`.
_ADAPTER_MARKERS: dict[str, tuple[str, ...]] = {
    "claude-code-local": (".mcp.json", ".claude/settings.json"),
    "generic-mcp": (".mcp.json",),
}


def _integration_installed(project_root: Path, adapter: str) -> bool:
    """Observe the marker of **this** adapter, project-local, without following symlinks.

    **Le défaut mesuré.** La version précédente rendait vrai dès qu'un seul de cinq répertoires
    existait — `.mcp.json`, `.claude`, `.codex`, `.gemini`, `.antigravity` — sans jamais regarder
    de quel adapter il s'agissait : le paramètre `adapter` était explicitement jeté par un
    `del adapter`. Sur un dépôt réel possédant déjà un `.claude/` pour un tout autre outil, le
    contrôle passait donc avant même que VERA n'ait rien écrit. C'est la classe de défaut que ce
    dépôt rencontre le plus souvent : *une propriété satisfaite par plus d'un chemin n'en prouve
    aucun*.

    Le catalogue est volontairement restreint à ce qui a été **mesuré**. Deviner les marqueurs des
    autres adapters referait la même faute à l'envers : un contrôle qui échoue pour de mauvaises
    raisons ne vaut pas mieux qu'un contrôle qui passe pour de mauvaises raisons. Un adapter hors
    catalogue est donc rendu à l'appelant comme non vérifiable, et le libellé du contrôle le dit.
    """
    marqueurs = _ADAPTER_MARKERS.get(adapter)
    if marqueurs is None:
        return True
    for marqueur in marqueurs:
        candidate = project_root / marqueur
        if not candidate.is_file() or candidate.is_symlink():
            return False
    return True


def render_doctor_report(report: DoctorReport) -> str:
    """Render the machine report as the aligned human rows the specification shows (§45).

    Remediation is printed only for rows that are not `PASS`, so a healthy project stays
    readable and a broken one puts the repair next to the failure.
    """
    identity = report.project_identity or {}
    width = max((len(check.name) for check in report.checks), default=0) + 2
    lines = [f"VERA Doctor — {identity.get('project_id', 'projet inconnu')} — {report.status}", ""]
    for check in report.checks:
        label = check.name.upper().replace("_", " ")
        lines.append(f"{label} {'.' * max(2, width + 18 - len(label))} {check.status}")
        lines.append(f"    {check.detail}")
        if check.status != "PASS":
            lines.append(f"    → {check.remediation}")
    return "\n".join(lines) + "\n"


def _diagnose_playbook(*, store_profile_path: Path, workspace: Workspace | None) -> DoctorCheck:
    """Check the project playbook the generated instructions must quote.

    The playbook is load-bearing since the MCP instructions carry it verbatim: an absent one
    stops generation, so the Doctor names it here rather than letting it surface at generate
    time (invariant I014).
    """
    if workspace is None:
        return _info("playbook", "Playbook non observable sans workspace valide.")
    candidate = workspace.runtime_dir / PLAYBOOK_FILE_NAME
    if candidate.is_symlink():
        return _fail("playbook", "Playbook symlinké : règle de projet ambiguë.", f"Remplacer `{PLAYBOOK_FILE_NAME}` par un fichier régulier du runtime VERA.")
    if not candidate.exists():
        return _fail(
            "playbook",
            "Playbook projet absent : la génération MCP ne peut pas citer les règles du projet.",
            f"Créer `.vera-mmu/{PLAYBOOK_FILE_NAME}` ; `vmmu init-project` en écrit un modèle.",
        )
    del store_profile_path
    return _pass("playbook", f"Playbook projet lisible ({candidate.stat().st_size} octets).")


def _pass(name: str, detail: str) -> DoctorCheck:
    return DoctorCheck(name, "PASS", detail, "Aucune action requise.")


def _info(name: str, detail: str) -> DoctorCheck:
    return DoctorCheck(name, "INFO", detail, "Information : aucune correction obligatoire.")


def _fail(name: str, detail: str, remediation: str) -> DoctorCheck:
    return DoctorCheck(name, "FAIL", detail, remediation)
