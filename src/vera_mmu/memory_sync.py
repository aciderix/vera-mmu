"""Synchronisation Git opt-in et strictement project-local de la mémoire VERA."""
from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import re
import sqlite3
import subprocess
from typing import Any

from .store import MemoryStore, StoreError


SYNC_POLICY_FORMAT = "vera-memory-sync-policy/v1"
_POLICY_FILE = "sync-policy.json"
_OPERATION = re.compile(r"[A-Z][A-Z0-9_]{1,63}")
_POLICY_KEYS = frozenset({"format", "auto_commit", "auto_push", "remote", "branch"})


class MemorySyncError(StoreError):
    """Raised only for invalid local synchronization inputs or invariants."""


def _run(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=15,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise MemorySyncError(detail or f"Git a refusé l’opération {arguments[0]!r}.")
    return completed.stdout.strip()


def _git_root(project_root: Path) -> Path:
    root = Path(_run(project_root, "rev-parse", "--show-toplevel")).resolve(strict=True)
    if project_root != root and root not in project_root.parents:
        raise MemorySyncError("Racine Git hors du périmètre du projet VERA.")
    return root


def _policy(memory_dir: Path) -> dict[str, object]:
    target = memory_dir / _POLICY_FILE
    if target.is_symlink():
        raise MemorySyncError("Politique de synchronisation mémoire ambiguë.")
    if not target.exists():
        return {"auto_commit": False, "auto_push": False, "remote": "origin", "branch": "CURRENT"}
    if not target.is_file():
        raise MemorySyncError("Politique de synchronisation mémoire ambiguë.")
    try:
        value = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MemorySyncError("Politique de synchronisation mémoire illisible.") from exc
    if not isinstance(value, dict) or set(value) != _POLICY_KEYS:
        raise MemorySyncError("Politique de synchronisation mémoire hors contrat fermé.")
    if value.get("format") != SYNC_POLICY_FORMAT:
        raise MemorySyncError("Format de politique de synchronisation inconnu.")
    if not isinstance(value.get("auto_commit"), bool) or not isinstance(value.get("auto_push"), bool):
        raise MemorySyncError("Les drapeaux de synchronisation doivent être booléens.")
    if value["auto_push"] and not value["auto_commit"]:
        raise MemorySyncError("auto_push exige auto_commit.")
    if value.get("remote") != "origin" or value.get("branch") != "CURRENT":
        raise MemorySyncError("La politique VERA impose origin et la branche courante.")
    return value


def _checkpoint(store: MemoryStore) -> dict[str, int | bool]:
    database = store.locator.sqlite_path
    if database.is_symlink() or not database.is_file():
        raise MemorySyncError("Base mémoire absente ou symlinkée : synchronisation refusée.")
    connection = sqlite3.connect(database, timeout=5.0, isolation_level=None)
    try:
        connection.execute("PRAGMA busy_timeout = 5000")
        row = connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
    except sqlite3.DatabaseError as exc:
        raise MemorySyncError("Checkpoint WAL de la mémoire impossible.") from exc
    finally:
        connection.close()
    if row is None:
        raise MemorySyncError("Checkpoint WAL mémoire sans résultat.")
    busy, log_frames, checkpointed_frames = (int(value) for value in row)
    if busy:
        raise MemorySyncError("Checkpoint WAL refusé : connexion mémoire active.")
    return {"checkpointed": True, "busy": busy, "log_frames": log_frames, "checkpointed_frames": checkpointed_frames}


def _current_branch(repository: Path) -> str:
    branch = _run(repository, "symbolic-ref", "--quiet", "--short", "HEAD")
    if not branch:
        raise MemorySyncError("HEAD détachée : aucune branche mémoire à pousser.")
    return branch


def _changes_in_scope(repository: Path, relative_memory: str) -> bool:
    changed = _run(repository, "status", "--porcelain=v1", "--untracked-files=all", "--", relative_memory)
    return bool(changed)


def _commit_memory(repository: Path, relative_memory: str, operation: str) -> str | None:
    if not _changes_in_scope(repository, relative_memory):
        return None
    _run(repository, "add", "--all", "--", relative_memory)
    message = f"VERA-MMU memory: {operation} — {datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')}"
    _run(repository, "commit", "--only", "-m", message, "--", relative_memory)
    return _run(repository, "rev-parse", "HEAD")


def automatic_memory_sync(store: MemoryStore, operation: str) -> dict[str, object]:
    """Commit/push only project-local VERA memory after a successful mutation.

    This boundary never accepts a Git argument from an agent. It is deliberately non-fatal:
    a committed SQLite transaction is not retroactively invalidated when Git is unavailable.
    """
    result: dict[str, object] = {"format": "vera-memory-sync/v1", "operation": operation, "committed": False, "pushed": False}
    try:
        if not isinstance(operation, str) or _OPERATION.fullmatch(operation) is None:
            raise MemorySyncError("Identifiant d’opération de synchronisation invalide.")
        memory_dir = store.locator.runtime_dir
        if memory_dir.is_symlink() or not memory_dir.is_dir():
            raise MemorySyncError("Répertoire mémoire VERA absent ou symlinké.")
        policy = _policy(memory_dir)
        if policy["auto_commit"] is not True:
            return {**result, "status": "DISABLED", "reason": "auto_commit=false"}
        repository = _git_root(store.workspace.project_root)
        try:
            relative = memory_dir.resolve(strict=True).relative_to(repository).as_posix()
        except ValueError as exc:
            raise MemorySyncError("Mémoire VERA hors du dépôt Git du projet.") from exc
        checkpoint = _checkpoint(store)
        head = _commit_memory(repository, relative, operation)
        if head is None:
            return {**result, "status": "NO_CHANGES", "wal_checkpoint": checkpoint}
        result.update({"committed": True, "head": head, "wal_checkpoint": checkpoint})
        if policy["auto_push"] is not True:
            return {**result, "status": "COMMITTED"}
        branch = _current_branch(repository)
        _run(repository, "remote", "get-url", "origin")
        _run(repository, "push", "origin", branch)
        return {**result, "status": "SYNCED", "pushed": True, "remote": "origin", "branch": branch}
    except (MemorySyncError, OSError, subprocess.TimeoutExpired) as exc:
        return {**result, "status": "REFUSED" if isinstance(exc, MemorySyncError) else "ERROR", "reason": str(exc)}
