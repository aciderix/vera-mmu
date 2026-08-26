from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from vera_mmu.domain_packs.aret import (
    AretAuthorizedKnowledgeImportError,
    AretKnowledgeImportAuthorizationError,
    AretV1KnowledgeSourcePage,
    AretV1KnowledgeSourceRecord,
    authorize_aret_v1_knowledge_import,
    check_aret_v1_knowledge_target_clear,
    ensure_aret_v1_knowledge_target_type,
    import_authorized_aret_v1_knowledge_page,
    post_validate_authorized_aret_v1_knowledge_page,
    prepare_aret_v1_knowledge_import,
    project_aret_v1_knowledge_page,
)
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore


PROFILE = """\
mmu:
  version: "2.0"
project:
  id: "authorized-knowledge-import"
  name: "Authorized Knowledge Import"
  domain: "generic"
workspace:
  root: "."
storage:
  memory_dir: ".vera-mmu"
  sqlite_file: "memory.sqlite"
  artifacts_dir: "artifacts"
identity:
  include_vcs_revision: false
  include_profile_hash: true
"""


def _store(tmp_path: Path) -> MemoryStore:
    profile_path = tmp_path / "project" / ".vera-mmu" / "project.yaml"
    profile_path.parent.mkdir(parents=True)
    profile_path.write_text(PROFILE, encoding="utf-8")
    return MemoryStore.open(load_profile(profile_path), profile_path)


def _record(source_id: str, *, status: str = "OBSERVED") -> AretV1KnowledgeSourceRecord:
    content = f"Content for {source_id}."
    return AretV1KnowledgeSourceRecord(
        source_id=source_id,
        source_type="FORENSIC",
        source_status=status,
        title=f"Title {source_id}",
        content=content,
        component_id="CORE",
        function_id=None,
        brick_id=None,
        supersedes_id=None,
        version=1,
        content_hash=sha256(content.encode("utf-8")).hexdigest(),
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        created_by="fixture",
        effective_at=None,
    )


def _page(record: AretV1KnowledgeSourceRecord) -> AretV1KnowledgeSourcePage:
    return AretV1KnowledgeSourcePage(Path("/tmp/source.sqlite"), "a" * 64, (record,), None)


def _authorize(store: MemoryStore, *, source_id: str, index: int):
    page = _page(_record(source_id))
    projection = project_aret_v1_knowledge_page(
        target_identity=store.identity,
        source_page=page,
        request_id="knowledge-import-request",
    )
    preflight = prepare_aret_v1_knowledge_import(
        target_identity=store.identity,
        source_page=page,
        projection=projection,
        preflight_id=f"knowledge-preflight-{index:03d}",
        confirmed_by="fixture",
    )
    clear = check_aret_v1_knowledge_target_clear(
        preflight=preflight,
        projection=projection,
        target_store=store,
    )
    authorization = authorize_aret_v1_knowledge_import(
        preflight=preflight,
        projection=projection,
        clear_check=clear,
        target_store=store,
        authorization_id=f"knowledge-authorization-{index:03d}",
        authorized_by="fixture",
    )
    return page, projection, preflight, clear, authorization


def test_authorized_knowledge_import_requires_explicit_target_type_and_is_replay_safe(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        page = _page(_record("KNOW-001", status="SUPERSEDED"))
        projection = project_aret_v1_knowledge_page(
            target_identity=store.identity,
            source_page=page,
            request_id="knowledge-import-request",
        )
        preflight = prepare_aret_v1_knowledge_import(
            target_identity=store.identity,
            source_page=page,
            projection=projection,
            preflight_id="knowledge-preflight-001",
            confirmed_by="fixture",
        )
        clear = check_aret_v1_knowledge_target_clear(preflight=preflight, projection=projection, target_store=store)
        with pytest.raises(AretKnowledgeImportAuthorizationError):
            authorize_aret_v1_knowledge_import(
                preflight=preflight,
                projection=projection,
                clear_check=clear,
                target_store=store,
                authorization_id="knowledge-authorization-001",
                authorized_by="fixture",
            )

        ensure_aret_v1_knowledge_target_type(target_store=store, actor="fixture")
        clear = check_aret_v1_knowledge_target_clear(preflight=preflight, projection=projection, target_store=store)
        authorization = authorize_aret_v1_knowledge_import(
            preflight=preflight,
            projection=projection,
            clear_check=clear,
            target_store=store,
            authorization_id="knowledge-authorization-001",
            authorized_by="fixture",
        )
        result = import_authorized_aret_v1_knowledge_page(
            preflight=preflight,
            projection=projection,
            authorization=authorization,
            target_store=store,
        )
        post = post_validate_authorized_aret_v1_knowledge_page(
            authorization=authorization,
            projection=projection,
            import_result=result,
            target_store=store,
        )
        replay_audit = store.audit_events()
        replay = import_authorized_aret_v1_knowledge_page(
            preflight=preflight,
            projection=projection,
            authorization=authorization,
            target_store=store,
        )

        assert clear.target_series_state == "INITIAL_EMPTY_TARGET_REQUIRED"
        assert result.resources[0].status == "OBSERVED"
        assert result.resources[0].metadata["source"]["legacy_status"] == "SUPERSEDED"
        assert post.validation_state == "POST_VALIDATED_NO_PROMOTION"
        assert replay.was_already_imported is True
        assert replay.resources == result.resources
        assert store.audit_events() == replay_audit


def test_authorized_knowledge_import_accepts_only_the_matching_prior_series(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        ensure_aret_v1_knowledge_target_type(target_store=store, actor="fixture")
        page_one, projection_one, preflight_one, _, authorization_one = _authorize(store, source_id="KNOW-001", index=1)
        import_authorized_aret_v1_knowledge_page(
            preflight=preflight_one,
            projection=projection_one,
            authorization=authorization_one,
            target_store=store,
        )
        page_two, projection_two, preflight_two, clear_two, authorization_two = _authorize(store, source_id="KNOW-002", index=2)
        result = import_authorized_aret_v1_knowledge_page(
            preflight=preflight_two,
            projection=projection_two,
            authorization=authorization_two,
            target_store=store,
        )

        assert page_one.records[0].source_id == "KNOW-001"
        assert page_two.records[0].source_id == "KNOW-002"
        assert clear_two.target_series_state == "MATCHING_PRIOR_SERIES_REQUIRED"
        assert authorization_two.target_series_state == "MATCHING_PRIOR_SERIES_REQUIRED"
        assert result.resources[0].id == "aret-knowledge--KNOW-002"


def test_authorized_knowledge_import_rejects_authorization_or_target_series_drift(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        ensure_aret_v1_knowledge_target_type(target_store=store, actor="fixture")
        _, projection, preflight, _, authorization = _authorize(store, source_id="KNOW-001", index=1)
        with pytest.raises(AretAuthorizedKnowledgeImportError):
            import_authorized_aret_v1_knowledge_page(
                preflight=preflight,
                projection=replace(projection, projection_state="IMPORTED"),
                authorization=authorization,
                target_store=store,
            )
