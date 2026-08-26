from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import subprocess

import pytest

from vera_mmu.domain_packs.aret import (
    AretGitSourceIdentityError,
    AretV1ComponentSourceAttestation,
    verify_aret_v1_git_source_identity,
)
import vera_mmu.domain_packs.aret.git_identity as git_identity


def _git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _fixture_attestation(source_root: Path, revision: str) -> AretV1ComponentSourceAttestation:
    snapshot = source_root / ".aret-memory" / "aret_memory.sqlite"
    snapshot.parent.mkdir(parents=True)
    snapshot.write_bytes(b"M4.8 source identity fixture")
    return AretV1ComponentSourceAttestation(
        source_path=snapshot,
        source_snapshot_sha256="a" * 64,
        source_size_bytes=snapshot.stat().st_size,
        expected_legacy_revision=revision,
        source_schema_version=6,
    )


@pytest.fixture
def clean_source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, str, AretV1ComponentSourceAttestation]:
    repository = tmp_path / "aret-repository"
    repository.mkdir()
    _git(repository, "init")
    _git(repository, "config", "user.email", "fixture@example.test")
    _git(repository, "config", "user.name", "Fixture")
    source_root = repository / "aret-memory"
    attestation = _fixture_attestation(source_root, revision="0" * 40)
    _git(repository, "add", ".")
    _git(repository, "commit", "-m", "fixture")
    revision = _git(repository, "rev-parse", "HEAD")
    attestation = replace(attestation, expected_legacy_revision=revision)
    monkeypatch.setattr(git_identity, "ARET_V1_BASELINE_REVISION", revision)
    return source_root, revision, attestation


def test_git_identity_verifies_clean_expected_repository(
    clean_source: tuple[Path, str, AretV1ComponentSourceAttestation]
) -> None:
    source_root, revision, attestation = clean_source

    identity = verify_aret_v1_git_source_identity(
        source_root=source_root,
        source_attestation=attestation,
    )

    assert identity.repository_root == source_root.parent
    assert identity.source_root == source_root
    assert identity.commit_hash == revision
    assert identity.expected_legacy_revision == revision
    assert identity.working_tree_state == "CLEAN"
    assert identity.identity_state == "VERIFIED_CLEAN_BASELINE"
    assert identity.source_snapshot_sha256 == "a" * 64


def test_git_identity_rejects_dirty_source_repository(
    clean_source: tuple[Path, str, AretV1ComponentSourceAttestation]
) -> None:
    source_root, _, attestation = clean_source
    (source_root / "untracked.txt").write_text("dirty", encoding="utf-8")

    with pytest.raises(AretGitSourceIdentityError):
        verify_aret_v1_git_source_identity(source_root=source_root, source_attestation=attestation)


def test_git_identity_rejects_commit_or_attestation_mismatch(
    clean_source: tuple[Path, str, AretV1ComponentSourceAttestation]
) -> None:
    source_root, _, attestation = clean_source

    with pytest.raises(AretGitSourceIdentityError):
        verify_aret_v1_git_source_identity(
            source_root=source_root,
            source_attestation=replace(attestation, expected_legacy_revision="1" * 40),
        )

    with pytest.raises(AretGitSourceIdentityError):
        verify_aret_v1_git_source_identity(
            source_root=source_root,
            source_attestation=replace(attestation, attestation_state="UNVERIFIED_DECLARATION"),
        )


def test_git_identity_rejects_wrong_source_root_or_path_binding(
    clean_source: tuple[Path, str, AretV1ComponentSourceAttestation], tmp_path: Path
) -> None:
    source_root, _, attestation = clean_source

    with pytest.raises(AretGitSourceIdentityError):
        verify_aret_v1_git_source_identity(
            source_root=tmp_path / "outside",
            source_attestation=attestation,
        )

    with pytest.raises(AretGitSourceIdentityError):
        verify_aret_v1_git_source_identity(
            source_root=source_root,
            source_attestation=replace(attestation, source_path=source_root / "other.sqlite"),
        )


def test_git_identity_module_allows_only_fixed_read_only_git_queries() -> None:
    source = (
        Path(__file__).parents[1]
        / "src"
        / "vera_mmu"
        / "domain_packs"
        / "aret"
        / "git_identity.py"
    ).read_text(encoding="utf-8")

    for forbidden in (
        "shell=True",
        "sqlite3",
        "INSERT",
        "UPDATE",
        "DELETE",
        "requests",
        "urllib.",
        "socket",
        "git commit",
        "git reset",
        "git checkout",
        "git clean",
    ):
        assert forbidden not in source
