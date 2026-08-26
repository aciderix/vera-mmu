from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import subprocess

from .source_attestation import ARET_V1_BASELINE_REVISION, AretV1ComponentSourceAttestation


_GIT_HASH_RE = re.compile(r"^[0-9a-f]{40}$")
_GIT_TIMEOUT_SECONDS = 5


class AretGitSourceIdentityError(ValueError):
    """Raised when an ARET V1 snapshot cannot be bound to one clean fixed Git baseline."""


@dataclass(frozen=True)
class AretV1GitSourceIdentity:
    """Read-only Git binding for one already-attested ARET V1 snapshot; not an import admission."""

    repository_root: Path
    source_root: Path
    commit_hash: str
    expected_legacy_revision: str
    source_snapshot_sha256: str
    working_tree_state: str = "CLEAN"
    identity_state: str = "VERIFIED_CLEAN_BASELINE"


def _canonical_source_root(value: str | Path) -> Path:
    source_root = Path(value)
    if not source_root.is_absolute() or source_root != source_root.resolve() or source_root.is_symlink() or not source_root.is_dir():
        raise AretGitSourceIdentityError("source_root doit être un répertoire absolu, canonique, existant et non lié.")
    return source_root


def _require_snapshot_binding(
    source_root: Path, value: object
) -> AretV1ComponentSourceAttestation:
    if not isinstance(value, AretV1ComponentSourceAttestation):
        raise AretGitSourceIdentityError("source_attestation doit être une attestation M4.7 ARET V1.")
    expected_snapshot = source_root / ".aret-memory" / "aret_memory.sqlite"
    if (
        value.source_path != expected_snapshot
        or value.expected_legacy_revision != ARET_V1_BASELINE_REVISION
        or value.source_schema_version != 6
        or value.source_access_mode != "READ_ONLY_SNAPSHOT"
        or value.attestation_state != "ATTESTED_SNAPSHOT_ONLY"
        or not isinstance(value.source_size_bytes, int)
        or value.source_size_bytes < 0
        or not isinstance(value.source_snapshot_sha256, str)
        or not re.fullmatch(r"[0-9a-f]{64}", value.source_snapshot_sha256)
    ):
        raise AretGitSourceIdentityError("source_attestation doit rester liée au snapshot ARET V1 attendu et attesté.")
    return value


def _run_read_only_git(source_root: Path, *arguments: str) -> str:
    environment = dict(os.environ)
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    environment["GIT_CONFIG_NOSYSTEM"] = "1"
    environment["GIT_CONFIG_GLOBAL"] = os.devnull
    command = (
        "git",
        "-c",
        "core.fsmonitor=false",
        "-c",
        "core.hooksPath=/dev/null",
        "-C",
        str(source_root),
        *arguments,
    )
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT_SECONDS,
            env=environment,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AretGitSourceIdentityError("Vérification Git de la source ARET V1 impossible.") from exc
    if completed.returncode != 0:
        raise AretGitSourceIdentityError("La source ARET V1 ne satisfait pas la requête Git read-only attendue.")
    return completed.stdout.strip()


def _repository_root_for(source_root: Path) -> Path:
    raw_root = _run_read_only_git(source_root, "rev-parse", "--show-toplevel")
    repository_root = Path(raw_root)
    if (
        not repository_root.is_absolute()
        or repository_root != repository_root.resolve()
        or repository_root.is_symlink()
        or not repository_root.is_dir()
        or source_root != repository_root
        and repository_root not in source_root.parents
    ):
        raise AretGitSourceIdentityError("source_root doit appartenir à une racine Git canonique non liée.")
    return repository_root


def verify_aret_v1_git_source_identity(
    *,
    source_root: str | Path,
    source_attestation: AretV1ComponentSourceAttestation,
) -> AretV1GitSourceIdentity:
    """Verify a clean fixed Git identity only; this never opens SQLite, imports rows, or writes VERA."""
    canonical_root = _canonical_source_root(source_root)
    attestation = _require_snapshot_binding(canonical_root, source_attestation)
    repository_root = _repository_root_for(canonical_root)
    commit_hash = _run_read_only_git(canonical_root, "rev-parse", "HEAD")
    if not _GIT_HASH_RE.fullmatch(commit_hash) or commit_hash != ARET_V1_BASELINE_REVISION:
        raise AretGitSourceIdentityError("Le commit Git de la source ARET V1 ne correspond pas à la baseline figée.")
    if _run_read_only_git(canonical_root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise AretGitSourceIdentityError("Le dépôt source ARET V1 doit être propre pour être attesté.")
    return AretV1GitSourceIdentity(
        repository_root=repository_root,
        source_root=canonical_root,
        commit_hash=commit_hash,
        expected_legacy_revision=ARET_V1_BASELINE_REVISION,
        source_snapshot_sha256=attestation.source_snapshot_sha256,
    )
