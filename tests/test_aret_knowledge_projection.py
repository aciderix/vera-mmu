from __future__ import annotations

from pathlib import Path

import pytest

from vera_mmu.domain_packs.aret import (
    AretKnowledgeProjectionError,
    AretV1KnowledgeSourcePage,
    AretV1KnowledgeSourceRecord,
    project_aret_v1_knowledge_page,
)
from vera_mmu.identity import ProjectIdentity


IDENTITY = ProjectIdentity("knowledge-projection", "2.0", "1" * 64, "2" * 64, "3" * 64)


def _record(*, source_type: str = "FORENSIC", source_status: str = "SUPERSEDED") -> AretV1KnowledgeSourceRecord:
    return AretV1KnowledgeSourceRecord(
        source_id="KNOW-001",
        source_type=source_type,
        source_status=source_status,
        title="Legacy knowledge",
        content="Preserved semantic content.",
        component_id="CORE",
        function_id=None,
        brick_id="BRICK-001",
        supersedes_id="KNOW-000",
        version=7,
        content_hash="a" * 64,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-02T00:00:00Z",
        created_by="fixture",
        effective_at="2026-01-03T00:00:00Z",
    )


def _page(record: AretV1KnowledgeSourceRecord) -> AretV1KnowledgeSourcePage:
    return AretV1KnowledgeSourcePage(Path("/tmp/source.sqlite"), "b" * 64, (record,), None)


def test_knowledge_projection_preserves_legacy_semantics_without_promotion_or_supersession_write() -> None:
    result = project_aret_v1_knowledge_page(
        target_identity=IDENTITY,
        source_page=_page(_record()),
        request_id="m4-c-knowledge-projection",
    )

    draft = result.drafts[0]
    assert draft.target_identifier == "aret-knowledge--KNOW-001"
    assert draft.type_id == "aret-legacy-knowledge"
    assert draft.status == "OBSERVED"
    assert draft.title == "Legacy knowledge"
    assert draft.content == "Preserved semantic content."
    assert draft.metadata == {
        "source": {
            "domain_pack": "aret-v1",
            "legacy_table": "knowledge",
            "source_id": "KNOW-001",
            "source_snapshot_sha256": "b" * 64,
            "legacy_type": "FORENSIC",
            "legacy_status": "SUPERSEDED",
            "component_id": "CORE",
            "function_id": None,
            "brick_id": "BRICK-001",
            "supersedes_id": "KNOW-000",
            "version": 7,
            "content_hash": "a" * 64,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-02T00:00:00Z",
            "created_by": "fixture",
            "effective_at": "2026-01-03T00:00:00Z",
        }
    }
    assert result.projection_state == "PROJECTED_NOT_WRITABLE"


@pytest.mark.parametrize("source_type,source_status", [("UNKNOWN", "OBSERVED"), ("FORENSIC", "PROVEN")])
def test_knowledge_projection_rejects_unknown_source_taxonomy_or_status(source_type: str, source_status: str) -> None:
    with pytest.raises(AretKnowledgeProjectionError):
        project_aret_v1_knowledge_page(
            target_identity=IDENTITY,
            source_page=_page(_record(source_type=source_type, source_status=source_status)),
            request_id="m4-c-knowledge-projection",
        )
