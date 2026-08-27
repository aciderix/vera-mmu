from __future__ import annotations

from pathlib import Path
import shutil
import zipfile

import pytest

from vera_mmu.bundles import BundleError, BundleService, restore_bundle
from vera_mmu.identity import load_profile
from vera_mmu.knowledge import KnowledgeService
from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization
from vera_mmu.project_import import (
    ProjectImportError,
    apply_project_document_import,
    preview_project_document_import,
)
from vera_mmu.provenance import KnowledgeSourceService
from vera_mmu.store import MemoryStore


def _initialize(root: Path, project_id: str = "m11b-project") -> Path:
    root.mkdir(parents=True, exist_ok=True)
    preview = preview_project_initialization(
        root,
        template="documentation",
        project_id=project_id,
        project_name="M11-B Project",
    )
    apply_project_initialization(root, preview, confirm=True)
    return root / ".vera-mmu" / "project.yaml"


def _store(profile_path: Path) -> MemoryStore:
    return MemoryStore.open(load_profile(profile_path), profile_path)


def _source_bundle(tmp_path: Path) -> tuple[Path, Path]:
    profile_path = _initialize(tmp_path / "source")
    with _store(profile_path) as store:
        knowledge = KnowledgeService(store)
        knowledge.register_type("project-document", "Imported project document", actor="fixture")
        knowledge.append(
            "bundle-knowledge-001",
            "project-document",
            "OBSERVED",
            "Bundle source",
            "A source record retained by the snapshot.",
            metadata={"fixture": True},
            actor="fixture",
        )
        artifact = store.locator.artifacts_dir / "evidence.txt"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text("artifact payload\n", encoding="utf-8")
        result = BundleService(store).export("snapshot-001", confirm=True)
    return profile_path, Path(result.path)


def _copy_runtime_without_memory(source_profile: Path, target_root: Path) -> Path:
    source_runtime = source_profile.parent
    target_runtime = target_root / ".vera-mmu"
    shutil.copytree(source_runtime, target_runtime, ignore=shutil.ignore_patterns("memory.sqlite", "memory.sqlite-wal", "memory.sqlite-shm", "artifacts", "bundles"))
    return target_runtime / "project.yaml"


def test_i010_i011_bundle_exports_chain_and_restores_exact_project_snapshot(tmp_path: Path) -> None:
    source_profile, bundle_path = _source_bundle(tmp_path)
    with zipfile.ZipFile(bundle_path) as archive:
        names = set(archive.namelist())
    assert {"manifest.json", "schema/migrations.json", "runtime/memory.sqlite", "runtime/project.yaml", "runtime/artifacts/evidence.txt"} <= names

    target_profile = _copy_runtime_without_memory(source_profile, tmp_path / "target")
    restored = restore_bundle(bundle_path, target_profile, confirm=True)
    assert restored.status == "RESTORED"
    assert restored.memory_sha256
    with _store(target_profile) as target:
        record = KnowledgeService(target).get("bundle-knowledge-001")
        assert record.status == "OBSERVED"
        assert record.content == "A source record retained by the snapshot."
        assert (target.locator.artifacts_dir / "evidence.txt").read_text(encoding="utf-8") == "artifact payload\n"


def test_i010_bundle_tampering_and_i011_identity_mismatch_refuse_before_target_mutation(tmp_path: Path) -> None:
    source_profile, bundle_path = _source_bundle(tmp_path)
    tampered = tmp_path / "tampered.zip"
    with zipfile.ZipFile(bundle_path) as source, zipfile.ZipFile(tampered, "w", compression=zipfile.ZIP_DEFLATED) as target:
        for info in source.infolist():
            payload = source.read(info.filename)
            target.writestr(info.filename, b"tampered database" if info.filename == "runtime/memory.sqlite" else payload)

    target_profile = _copy_runtime_without_memory(source_profile, tmp_path / "target-tampered")
    with pytest.raises(BundleError):
        restore_bundle(tampered, target_profile, confirm=True)
    assert not (target_profile.parent / "memory.sqlite").exists()

    other_profile = _initialize(tmp_path / "other-project", project_id="other-project")
    with pytest.raises(BundleError):
        restore_bundle(bundle_path, other_profile, confirm=True)
    assert not (other_profile.parent / "memory.sqlite").exists()


def test_i010_restore_refuses_non_empty_target_and_is_idempotent_after_exact_restore(tmp_path: Path) -> None:
    source_profile, bundle_path = _source_bundle(tmp_path)
    target_profile = _copy_runtime_without_memory(source_profile, tmp_path / "target-nonempty")
    with _store(target_profile):
        pass
    with pytest.raises(BundleError):
        restore_bundle(bundle_path, target_profile, confirm=True)

    exact_profile = _copy_runtime_without_memory(source_profile, tmp_path / "target-exact")
    first = restore_bundle(bundle_path, exact_profile, confirm=True)
    second = restore_bundle(bundle_path, exact_profile, confirm=True)
    assert first.status == "RESTORED"
    assert second.status == "ALREADY_RESTORED"


def test_i003_i011_project_document_import_is_explicit_observed_provenanced_and_non_merging(tmp_path: Path) -> None:
    root = tmp_path / "existing-project"
    profile_path = _initialize(root)
    (root / "README.md").write_text("# Existing project\n\nDocumented behavior.\n", encoding="utf-8")
    (root / "docs").mkdir()
    (root / "docs" / "architecture.md").write_text("# Architecture\n\nA documented decision.\n", encoding="utf-8")

    with _store(profile_path) as store:
        preview = preview_project_document_import(
            store,
            ("README.md", "docs/architecture.md"),
            batch_id="existing-documents-001",
            knowledge_type_id="project-document",
            knowledge_type_label="Imported project document",
            actor="fixture",
        )
        result = apply_project_document_import(store, preview, confirm=True)
        assert result.status == "IMPORTED"
        assert {item.status for item in result.knowledge} == {"OBSERVED"}
        assert {item.metadata["import"]["path"] for item in result.knowledge} == {"README.md", "docs/architecture.md"}
        assert len(result.provenance) == 2
        assert all(item.source_path in {"README.md", "docs/architecture.md"} for item in result.provenance)
        replay = apply_project_document_import(store, preview, confirm=True)
        assert replay.status == "ALREADY_IMPORTED"
        assert replay.knowledge == result.knowledge

        (root / "CHANGELOG.md").write_text("# Changes\n\nNo merge.\n", encoding="utf-8")
        another = preview_project_document_import(
            store,
            ("CHANGELOG.md",),
            batch_id="existing-documents-002",
            knowledge_type_id="project-document",
            knowledge_type_label="Imported project document",
            actor="fixture",
        )
        with pytest.raises(ProjectImportError):
            apply_project_document_import(store, another, confirm=True)
        assert len(KnowledgeSourceService(store).list_for(result.knowledge[0].id)) == 1


def test_i003_i014_project_document_preview_refuses_symlink_stale_or_unconfirmed_import(tmp_path: Path) -> None:
    root = tmp_path / "unsafe-project"
    profile_path = _initialize(root)
    (root / "README.md").write_text("# Initial\n", encoding="utf-8")
    outside = tmp_path / "outside.md"
    outside.write_text("outside\n", encoding="utf-8")
    (root / "linked.md").symlink_to(outside)

    with _store(profile_path) as store:
        with pytest.raises(ProjectImportError):
            preview_project_document_import(
                store,
                ("linked.md",),
                batch_id="unsafe-documents-001",
                knowledge_type_id="project-document",
                knowledge_type_label="Imported project document",
            )
        preview = preview_project_document_import(
            store,
            ("README.md",),
            batch_id="unsafe-documents-002",
            knowledge_type_id="project-document",
            knowledge_type_label="Imported project document",
        )
        with pytest.raises(ProjectImportError):
            apply_project_document_import(store, preview, confirm=False)
        (root / "README.md").write_text("# Changed\n", encoding="utf-8")
        with pytest.raises(ProjectImportError):
            apply_project_document_import(store, preview, confirm=True)
        assert store.connection.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0] == 0


def test_i013_bundle_export_requires_explicit_confirmation(tmp_path: Path) -> None:
    profile_path = _initialize(tmp_path / "confirmation")
    with _store(profile_path) as store:
        with pytest.raises(BundleError):
            BundleService(store).export("snapshot-001", confirm=False)
    assert not (profile_path.parent / "bundles" / "snapshot-001.zip").exists()


def test_i010_restore_rolls_back_runtime_when_final_swap_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import vera_mmu.bundles as bundles

    source_profile, bundle_path = _source_bundle(tmp_path)
    target_profile = _copy_runtime_without_memory(source_profile, tmp_path / "target-rollback")
    original_profile = target_profile.read_bytes()
    original_replace = bundles.os.replace

    def fail_stage_swap(source: str | Path, destination: str | Path) -> None:
        if Path(destination) == target_profile.parent and Path(source).name == "runtime":
            raise OSError("simulated final swap failure")
        original_replace(source, destination)

    monkeypatch.setattr(bundles.os, "replace", fail_stage_swap)
    with pytest.raises(BundleError):
        restore_bundle(bundle_path, target_profile, confirm=True)
    assert target_profile.read_bytes() == original_profile
    assert not (target_profile.parent / "memory.sqlite").exists()
