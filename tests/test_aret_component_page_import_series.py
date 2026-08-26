from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

import pytest

from vera_mmu.domain_packs.aret import (
    AretComponentPageImportError,
    AretV1ComponentEntityProjection,
    AretV1ComponentImportPreflight,
    AretV1ComponentSchemaConformance,
    AretV1EntityDraft,
    authorize_aret_v1_component_page_import,
    import_authorized_aret_v1_component_page,
)
from vera_mmu.entities import EntityService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore


PROFILE = """\
mmu:
  version: "2.0"
project:
  id: "component-series-project"
  name: "Component Series Project"
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


@dataclass(frozen=True)
class _Page:
    request_id: str
    preflight_id: str
    first_id: str
    last_id: str
    source_ids: tuple[str, ...]


def _open_store(tmp_path: Path) -> MemoryStore:
    profile_path = tmp_path / "project" / ".vera-mmu" / "project.yaml"
    profile_path.parent.mkdir(parents=True)
    profile_path.write_text(PROFILE, encoding="utf-8")
    return MemoryStore.open(load_profile(profile_path), profile_path)


def _page_one() -> _Page:
    return _Page("m4-a-component-series", "m4-a-page-001", "CMP-001", "CMP-002", ("CMP-001", "CMP-002"))


def _page_two() -> _Page:
    return _Page("m4-a-component-series", "m4-a-page-002", "CMP-003", "CMP-004", ("CMP-003", "CMP-004"))


def _preflight(store: MemoryStore, page: _Page) -> AretV1ComponentImportPreflight:
    return AretV1ComponentImportPreflight(
        target_identity=store.identity,
        request_id=page.request_id,
        preflight_id=page.preflight_id,
        confirmed_by="preflight-actor",
        source_snapshot_sha256="a" * 64,
        source_record_count=len(page.source_ids),
        source_first_id=page.first_id,
        source_last_id=page.last_id,
    )


def _projection(store: MemoryStore, page: _Page) -> AretV1ComponentEntityProjection:
    drafts = tuple(
        AretV1EntityDraft(
            target_identifier=f"aret-component--{source_id}",
            target_address=f"vera://{store.identity.project_id}/entity/aret-component--{source_id}",
            entity_type_id="component",
            title=f"Title {source_id}",
            description=f"Description {source_id}",
            metadata={
                "source": {
                    "domain_pack": "aret-v1",
                    "legacy_table": "component",
                    "source_id": source_id,
                    "source_snapshot_sha256": "a" * 64,
                    "source_created_at": "2026-01-01T00:00:00Z",
                    "source_created_by": "fixture",
                }
            },
        )
        for source_id in page.source_ids
    )
    return AretV1ComponentEntityProjection(
        target_identity=store.identity,
        request_id=page.request_id,
        preflight_id=page.preflight_id,
        source_snapshot_sha256="a" * 64,
        entity_type_id="component",
        entity_type_registration_required=True,
        drafts=drafts,
    )


def _schema() -> AretV1ComponentSchemaConformance:
    return AretV1ComponentSchemaConformance(
        source_path=Path("/tmp/aret-component-snapshot.sqlite"),
        source_snapshot_sha256="a" * 64,
        columns=(
            ("id", "TEXT", True, True, None),
            ("title", "TEXT", True, False, None),
            ("description", "TEXT", True, False, "''"),
            ("created_at", "TEXT", True, False, None),
            ("created_by", "TEXT", True, False, None),
        ),
    )


def _authorize(store: MemoryStore, page: _Page, authorization_id: str):
    return authorize_aret_v1_component_page_import(
        preflight=_preflight(store, page),
        projection=_projection(store, page),
        component_schema=_schema(),
        target_store=store,
        authorization_id=authorization_id,
        authorized_by="user-confirmed-series",
    )


def test_page_authorization_is_explicit_bound_and_has_no_write_effect(tmp_path: Path) -> None:
    with _open_store(tmp_path) as store:
        before_audit = store.audit_events()

        authorization = _authorize(store, _page_one(), "m4-a-series-page-001")

        assert authorization.authorization_state == "EXPLICIT_PAGE_IMPORT_ALLOWED"
        assert authorization.target_series_state == "INITIAL_EMPTY_TARGET_REQUIRED"
        assert authorization.promotion_policy == "FORBID"
        assert store.audit_events() == before_audit
        assert store.connection.execute("SELECT COUNT(*) FROM import_batch").fetchone()[0] == 0


def test_first_page_commits_entities_and_ledger_then_exact_replay_is_idempotent(tmp_path: Path) -> None:
    with _open_store(tmp_path) as store:
        authorization = _authorize(store, _page_one(), "m4-a-series-page-001")
        before_audit = store.audit_events()

        result = import_authorized_aret_v1_component_page(
            authorization=authorization,
            preflight=_preflight(store, _page_one()),
            projection=_projection(store, _page_one()),
            component_schema=_schema(),
            target_store=store,
        )

        assert result.import_state == "IMPORTED_NO_PROMOTION"
        assert result.was_already_imported is False
        assert [entity.id for entity in result.entities] == ["aret-component--CMP-001", "aret-component--CMP-002"]
        assert [event["action"] for event in store.audit_events()][len(before_audit) :] == [
            "ENTITY_TYPE_REGISTERED",
            "ENTITY_CREATED",
            "ENTITY_CREATED",
            "IMPORT_BATCH_COMMITTED",
        ]
        assert store.connection.execute("SELECT COUNT(*) FROM import_batch").fetchone()[0] == 1
        replay_before_audit = store.audit_events()

        replay = import_authorized_aret_v1_component_page(
            authorization=authorization,
            preflight=_preflight(store, _page_one()),
            projection=_projection(store, _page_one()),
            component_schema=_schema(),
            target_store=store,
        )

        assert replay.was_already_imported is True
        assert replay.entities == result.entities
        assert store.audit_events() == replay_before_audit


def test_following_page_requires_matching_prior_aret_series_and_reuses_only_compatible_type(tmp_path: Path) -> None:
    with _open_store(tmp_path) as store:
        first_authorization = _authorize(store, _page_one(), "m4-a-series-page-001")
        import_authorized_aret_v1_component_page(
            authorization=first_authorization,
            preflight=_preflight(store, _page_one()),
            projection=_projection(store, _page_one()),
            component_schema=_schema(),
            target_store=store,
        )
        before_audit = store.audit_events()
        following_authorization = _authorize(store, _page_two(), "m4-a-series-page-002")

        assert following_authorization.target_series_state == "MATCHING_PRIOR_SERIES_REQUIRED"
        result = import_authorized_aret_v1_component_page(
            authorization=following_authorization,
            preflight=_preflight(store, _page_two()),
            projection=_projection(store, _page_two()),
            component_schema=_schema(),
            target_store=store,
        )

        assert result.was_already_imported is False
        assert [entity.id for entity in result.entities] == ["aret-component--CMP-003", "aret-component--CMP-004"]
        assert [event["action"] for event in store.audit_events()][len(before_audit) :] == [
            "ENTITY_CREATED",
            "ENTITY_CREATED",
            "IMPORT_BATCH_COMMITTED",
        ]
        assert store.connection.execute("SELECT COUNT(*) FROM import_batch").fetchone()[0] == 2


def test_page_authorization_rejects_manual_or_mismatched_existing_type_without_writing(tmp_path: Path) -> None:
    with _open_store(tmp_path) as store:
        EntityService(store).register_type(
            "component",
            "Component",
            description="Generic component entities created through an explicitly authorized paged ARET import.",
            schema={"kind": "generic", "resource": "entity"},
            actor="fixture",
        )
        before_audit = store.audit_events()

        with pytest.raises(AretComponentPageImportError):
            _authorize(store, _page_one(), "m4-a-series-page-001")

        assert store.audit_events() == before_audit
        assert store.connection.execute("SELECT COUNT(*) FROM import_batch").fetchone()[0] == 0


def test_page_import_rechecks_target_and_rolls_back_on_late_collision(tmp_path: Path) -> None:
    with _open_store(tmp_path) as store:
        authorization = _authorize(store, _page_one(), "m4-a-series-page-001")
        EntityService(store).register_type("other", "Other", actor="fixture")
        EntityService(store).create("aret-component--CMP-002", "other", "Existing", actor="fixture")
        before_audit = store.audit_events()

        with pytest.raises(AretComponentPageImportError):
            import_authorized_aret_v1_component_page(
                authorization=authorization,
                preflight=_preflight(store, _page_one()),
                projection=_projection(store, _page_one()),
                component_schema=_schema(),
                target_store=store,
            )

        assert store.audit_events() == before_audit
        assert store.connection.execute("SELECT 1 FROM entity_type WHERE id = 'component'").fetchone() is None
        assert store.connection.execute("SELECT COUNT(*) FROM import_batch").fetchone()[0] == 0


def test_page_import_rejects_any_changed_binding_before_write(tmp_path: Path) -> None:
    with _open_store(tmp_path) as store:
        authorization = _authorize(store, _page_one(), "m4-a-series-page-001")
        before_audit = store.audit_events()

        with pytest.raises(AretComponentPageImportError):
            import_authorized_aret_v1_component_page(
                authorization=replace(authorization, promotion_policy="ALLOW"),
                preflight=_preflight(store, _page_one()),
                projection=_projection(store, _page_one()),
                component_schema=_schema(),
                target_store=store,
            )

        assert store.audit_events() == before_audit
        assert store.connection.execute("SELECT COUNT(*) FROM entity").fetchone()[0] == 0


def test_page_import_module_has_no_source_read_sqlite_or_proof_capability() -> None:
    source = (
        Path(__file__).parents[1]
        / "src"
        / "vera_mmu"
        / "domain_packs"
        / "aret"
        / "component_page_import.py"
    ).read_text(encoding="utf-8")

    for required in ("EXPLICIT_PAGE_IMPORT_ALLOWED", "IMPORTED_NO_PROMOTION", "ImportBatchService"):
        assert required in source
    for forbidden in (
        "sqlite3",
        "open(",
        "subprocess",
        "requests",
        "urllib.",
        "socket",
        "os.system",
        "ProofService",
        "create_proof",
        "EntityService",
    ):
        assert forbidden not in source
