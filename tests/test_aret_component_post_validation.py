from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

import pytest

from vera_mmu.domain_packs.aret import (
    AretComponentPostValidationError,
    AretV1ComponentEntityProjection,
    AretV1ComponentImportPreflight,
    AretV1ComponentSchemaConformance,
    AretV1EntityDraft,
    authorize_aret_v1_component_page_import,
    import_authorized_aret_v1_component_page,
    post_validate_authorized_aret_v1_component_page,
)
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore

PROFILE = """\
mmu:
  version: "2.0"
project:
  id: "component-post-validation"
  name: "Component Post Validation"
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
class _Input:
    preflight: AretV1ComponentImportPreflight
    projection: AretV1ComponentEntityProjection
    schema: AretV1ComponentSchemaConformance


def _store(tmp_path: Path) -> MemoryStore:
    profile_path = tmp_path / "target" / ".vera-mmu" / "project.yaml"
    profile_path.parent.mkdir(parents=True)
    profile_path.write_text(PROFILE, encoding="utf-8")
    return MemoryStore.open(load_profile(profile_path), profile_path)


def _input(store: MemoryStore) -> _Input:
    source_ids = ("CMP-001", "CMP-002")
    preflight = AretV1ComponentImportPreflight(
        target_identity=store.identity,
        request_id="m4-a-post-validation",
        preflight_id="m4-a-post-validation-page",
        confirmed_by="fixture",
        source_snapshot_sha256="a" * 64,
        source_record_count=2,
        source_first_id=source_ids[0],
        source_last_id=source_ids[-1],
    )
    drafts = tuple(
        AretV1EntityDraft(
            target_identifier=f"aret-component--{source_id}",
            target_address=f"vera://{store.identity.project_id}/entity/aret-component--{source_id}",
            entity_type_id="component",
            title=f"Title {source_id}",
            description="",
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
        for source_id in source_ids
    )
    projection = AretV1ComponentEntityProjection(
        target_identity=store.identity,
        request_id=preflight.request_id,
        preflight_id=preflight.preflight_id,
        source_snapshot_sha256=preflight.source_snapshot_sha256,
        entity_type_id="component",
        entity_type_registration_required=True,
        drafts=drafts,
    )
    schema = AretV1ComponentSchemaConformance(
        source_path=Path("/tmp/component-post-validation.sqlite"),
        source_snapshot_sha256="a" * 64,
        columns=(
            ("id", "TEXT", True, True, None),
            ("title", "TEXT", True, False, None),
            ("description", "TEXT", True, False, "''"),
            ("created_at", "TEXT", True, False, None),
            ("created_by", "TEXT", True, False, None),
        ),
    )
    return _Input(preflight, projection, schema)


def _import(store: MemoryStore):
    input_data = _input(store)
    authorization = authorize_aret_v1_component_page_import(
        preflight=input_data.preflight,
        projection=input_data.projection,
        component_schema=input_data.schema,
        target_store=store,
        authorization_id="m4-a-post-validation-import",
        authorized_by="fixture-authorized",
    )
    result = import_authorized_aret_v1_component_page(
        authorization=authorization,
        preflight=input_data.preflight,
        projection=input_data.projection,
        component_schema=input_data.schema,
        target_store=store,
    )
    return input_data, authorization, result


def test_post_validation_confirms_exact_ledger_and_entity_projection_without_writing(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        input_data, authorization, result = _import(store)
        before_audits = store.audit_events()

        validation = post_validate_authorized_aret_v1_component_page(
            authorization=authorization,
            projection=input_data.projection,
            import_result=result,
            target_store=store,
        )

        assert validation.validation_state == "POST_VALIDATED_NO_PROMOTION"
        assert validation.validated_entity_count == 2
        assert validation.source_identifiers == ("CMP-001", "CMP-002")
        assert store.audit_events() == before_audits
        assert store.connection.execute("SELECT COUNT(*) FROM evidence").fetchone()[0] == 0
        assert store.connection.execute("SELECT COUNT(*) FROM knowledge_proof").fetchone()[0] == 0


def test_post_validation_rejects_projection_or_result_binding_divergence_without_writing(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        input_data, authorization, result = _import(store)
        before_audits = store.audit_events()

        with pytest.raises(AretComponentPostValidationError):
            post_validate_authorized_aret_v1_component_page(
                authorization=authorization,
                projection=replace(input_data.projection, request_id="mismatch-request"),
                import_result=result,
                target_store=store,
            )

        assert store.audit_events() == before_audits


def test_post_validation_rejects_a_mismatched_ledger_link_without_writing(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        input_data, authorization, result = _import(store)
        original = input_data.projection.drafts[1]
        metadata = dict(original.metadata)
        source = dict(metadata["source"])
        source["source_id"] = "CMP-999"
        metadata["source"] = source
        divergent = replace(
            original,
            target_identifier="aret-component--CMP-999",
            target_address=f"vera://{store.identity.project_id}/entity/aret-component--CMP-999",
            metadata=metadata,
        )
        projection = replace(input_data.projection, drafts=(input_data.projection.drafts[0], divergent))
        before_audits = store.audit_events()

        with pytest.raises(AretComponentPostValidationError):
            post_validate_authorized_aret_v1_component_page(
                authorization=authorization,
                projection=projection,
                import_result=result,
                target_store=store,
            )

        assert store.audit_events() == before_audits


def test_post_validation_module_is_read_only_and_has_no_proof_or_source_capability() -> None:
    source = (
        Path(__file__).parents[1]
        / "src"
        / "vera_mmu"
        / "domain_packs"
        / "aret"
        / "component_post_validation.py"
    ).read_text(encoding="utf-8")

    for required in ("POST_VALIDATED_NO_PROMOTION", "import_batch_entity", "EntityService"):
        assert required in source
    for forbidden in (
        "sqlite3",
        "open(",
        "subprocess",
        "os.system",
        "requests",
        "urllib.",
        "socket",
        "INSERT",
        "UPDATE",
        "DELETE",
        "ProofService",
        "create_proof",
    ):
        assert forbidden not in source
