from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from vera_mmu.domain_packs.aret import (
    AretComponentAuthorizedImportError,
    AretV1ComponentEntityProjection,
    AretV1ComponentImportPreflight,
    AretV1ComponentTargetClearCheck,
    AretV1EntityDraft,
    authorize_aret_v1_component_import,
    import_authorized_aret_v1_component_entities,
)
from vera_mmu.entities import EntityService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore


PROFILE = """\
mmu:
  version: "2.0"
project:
  id: "authorized-import-project"
  name: "Authorized Import Project"
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


def _open_store(tmp_path: Path) -> MemoryStore:
    profile_path = tmp_path / "project" / ".vera-mmu" / "project.yaml"
    profile_path.parent.mkdir(parents=True)
    profile_path.write_text(PROFILE, encoding="utf-8")
    return MemoryStore.open(load_profile(profile_path), profile_path)


def _preflight(store: MemoryStore) -> AretV1ComponentImportPreflight:
    return AretV1ComponentImportPreflight(
        target_identity=store.identity,
        request_id="m4-15-component-import",
        preflight_id="m4-15-component-page",
        confirmed_by="preflight-actor",
        source_snapshot_sha256="a" * 64,
        source_record_count=2,
        source_first_id="CMP-001",
        source_last_id="CMP-002",
    )


def _projection(store: MemoryStore) -> AretV1ComponentEntityProjection:
    drafts = (
        AretV1EntityDraft(
            target_identifier="aret-component--CMP-001",
            target_address=f"vera://{store.identity.project_id}/entity/aret-component--CMP-001",
            entity_type_id="component",
            title="Alpha",
            description="First",
            metadata={
                "source": {
                    "domain_pack": "aret-v1",
                    "legacy_table": "component",
                    "source_id": "CMP-001",
                    "source_snapshot_sha256": "a" * 64,
                    "source_created_at": "2026-01-01T00:00:00Z",
                    "source_created_by": "fixture",
                }
            },
        ),
        AretV1EntityDraft(
            target_identifier="aret-component--CMP-002",
            target_address=f"vera://{store.identity.project_id}/entity/aret-component--CMP-002",
            entity_type_id="component",
            title="Beta",
            description="Second",
            metadata={
                "source": {
                    "domain_pack": "aret-v1",
                    "legacy_table": "component",
                    "source_id": "CMP-002",
                    "source_snapshot_sha256": "a" * 64,
                    "source_created_at": "2026-01-02T00:00:00Z",
                    "source_created_by": "fixture",
                }
            },
        ),
    )
    return AretV1ComponentEntityProjection(
        target_identity=store.identity,
        request_id="m4-15-component-import",
        preflight_id="m4-15-component-page",
        source_snapshot_sha256="a" * 64,
        entity_type_id="component",
        entity_type_registration_required=True,
        drafts=drafts,
    )


def _clear(store: MemoryStore) -> AretV1ComponentTargetClearCheck:
    return AretV1ComponentTargetClearCheck(
        target_identity=store.identity,
        entity_type_id="component",
        entity_type_state="ABSENT_REQUIRED",
        checked_entity_count=2,
    )


def test_authorized_import_creates_exact_entities_atomically_with_source_metadata_and_core_audit(tmp_path: Path) -> None:
    with _open_store(tmp_path) as store:
        authorization = authorize_aret_v1_component_import(
            preflight=_preflight(store),
            projection=_projection(store),
            target_clear_check=_clear(store),
            authorization_id="m4-15-authorized-import",
            authorized_by="user-confirmed",
        )
        before_audit = store.audit_events()
        result = import_authorized_aret_v1_component_entities(
            authorization=authorization,
            preflight=_preflight(store),
            projection=_projection(store),
            target_clear_check=_clear(store),
            target_store=store,
        )

        assert result.import_state == "IMPORTED_NO_PROMOTION"
        assert result.imported_entity_count == 2
        assert [entity.id for entity in result.entities] == ["aret-component--CMP-001", "aret-component--CMP-002"]
        assert EntityService(store).get("aret-component--CMP-001").metadata["source"]["source_id"] == "CMP-001"
        assert [event["action"] for event in store.audit_events()][len(before_audit) :] == [
            "ENTITY_TYPE_REGISTERED",
            "ENTITY_CREATED",
            "ENTITY_CREATED",
        ]
        assert all("PROOF" not in event["action"] for event in store.audit_events()[len(before_audit) :])


def test_authorization_is_explicit_bound_and_performs_no_write(tmp_path: Path) -> None:
    with _open_store(tmp_path) as store:
        before_audit = store.audit_events()
        authorization = authorize_aret_v1_component_import(
            preflight=_preflight(store),
            projection=_projection(store),
            target_clear_check=_clear(store),
            authorization_id="m4-15-authorized-import",
            authorized_by="user-confirmed",
        )

        assert authorization.authorization_state == "EXPLICIT_ONE_SHOT_IMPORT_ALLOWED"
        assert authorization.promotion_policy == "FORBID"
        assert store.audit_events() == before_audit
        assert store.connection.execute("SELECT COUNT(*) FROM entity_type").fetchone()[0] == 0


def test_import_rejects_invalid_authorization_or_binding_without_writing(tmp_path: Path) -> None:
    with _open_store(tmp_path) as store:
        authorization = authorize_aret_v1_component_import(
            preflight=_preflight(store),
            projection=_projection(store),
            target_clear_check=_clear(store),
            authorization_id="m4-15-authorized-import",
            authorized_by="user-confirmed",
        )
        before_audit = store.audit_events()

        with pytest.raises(AretComponentAuthorizedImportError):
            import_authorized_aret_v1_component_entities(
                authorization=replace(authorization, promotion_policy="ALLOW"),
                preflight=_preflight(store),
                projection=_projection(store),
                target_clear_check=_clear(store),
                target_store=store,
            )

        with pytest.raises(AretComponentAuthorizedImportError):
            import_authorized_aret_v1_component_entities(
                authorization=authorization,
                preflight=_preflight(store),
                projection=replace(_projection(store), source_snapshot_sha256="b" * 64),
                target_clear_check=_clear(store),
                target_store=store,
            )

        assert store.audit_events() == before_audit
        assert store.connection.execute("SELECT COUNT(*) FROM entity_type").fetchone()[0] == 0
        assert store.connection.execute("SELECT COUNT(*) FROM entity").fetchone()[0] == 0


def test_import_rechecks_target_and_rolls_back_when_collision_appears_after_authorization(tmp_path: Path) -> None:
    with _open_store(tmp_path) as store:
        authorization = authorize_aret_v1_component_import(
            preflight=_preflight(store),
            projection=_projection(store),
            target_clear_check=_clear(store),
            authorization_id="m4-15-authorized-import",
            authorized_by="user-confirmed",
        )
        service = EntityService(store)
        service.register_type("other", "Other", actor="fixture")
        service.create("aret-component--CMP-001", "other", "Existing", actor="fixture")
        before_audit = store.audit_events()

        with pytest.raises(AretComponentAuthorizedImportError):
            import_authorized_aret_v1_component_entities(
                authorization=authorization,
                preflight=_preflight(store),
                projection=_projection(store),
                target_clear_check=_clear(store),
                target_store=store,
            )

        assert store.audit_events() == before_audit
        assert store.connection.execute("SELECT 1 FROM entity_type WHERE id = 'component'").fetchone() is None
        assert EntityService(store).get("aret-component--CMP-001").type_id == "other"


def test_import_module_has_no_source_read_or_promotion_capability() -> None:
    source = (
        Path(__file__).parents[1]
        / "src"
        / "vera_mmu"
        / "domain_packs"
        / "aret"
        / "component_authorized_import.py"
    ).read_text(encoding="utf-8")

    for required in ("EXPLICIT_ONE_SHOT_IMPORT_ALLOWED", "IMPORTED_NO_PROMOTION", "register_type_and_create_batch"):
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
    ):
        assert forbidden not in source
