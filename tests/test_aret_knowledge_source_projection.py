from __future__ import annotations

from pathlib import Path

import pytest

from vera_mmu.domain_packs.aret import (
    AretKnowledgeSourceProjectionError,
    AretV1KnowledgeSourcePage,
    AretV1KnowledgeSourceRecord,
    AretV1KnowledgeSourceSourcePage,
    AretV1KnowledgeSourceSourceRecord,
    project_aret_v1_knowledge_source_page,
)
from vera_mmu.identity import ProjectIdentity


IDENTITY = ProjectIdentity("knowledge-source-projection", "2.0", "1" * 64, "2" * 64, "3" * 64)


def _knowledge_page() -> AretV1KnowledgeSourcePage:
    record = AretV1KnowledgeSourceRecord(
        source_id="CORE-0001",
        source_type="FORENSIC",
        source_status="OBSERVED",
        title="Knowledge",
        content="Content.",
        component_id="CORE",
        function_id=None,
        brick_id=None,
        supersedes_id=None,
        version=1,
        content_hash="a" * 64,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        created_by="fixture",
        effective_at=None,
    )
    return AretV1KnowledgeSourcePage(Path("/tmp/source.sqlite"), "b" * 64, (record,), None)


def _source_page() -> AretV1KnowledgeSourceSourcePage:
    record = AretV1KnowledgeSourceSourceRecord(
        source_id="S-0001",
        knowledge_id="CORE-0001",
        repository="https://github.com/aciderix/Automatic-reverse-engineering-toolkit",
        revision="c" * 40,
        path="docs/vision/source.md",
        start_line=3,
        end_line=7,
        section="Source section",
        source_hash="d" * 64,
        imported_at="2026-01-02T00:00:00Z",
        imported_by="aret-mmu-migrator",
        migration_batch_id="MIG-001",
    )
    return AretV1KnowledgeSourceSourcePage(Path("/tmp/source.sqlite"), "b" * 64, (record,), None)


def test_knowledge_source_projection_maps_declared_provenance_and_preserves_legacy_import_metadata() -> None:
    result = project_aret_v1_knowledge_source_page(
        target_identity=IDENTITY,
        knowledge_page=_knowledge_page(),
        source_page=_source_page(),
        request_id="m4-c-source-projection",
    )

    draft = result.drafts[0]
    assert draft.target_identifier == "aret-knowledge-source--S-0001"
    assert draft.knowledge_identifier == "aret-knowledge--CORE-0001"
    assert draft.payload == {
        "repository": "https://github.com/aciderix/Automatic-reverse-engineering-toolkit",
        "revision": "c" * 40,
        "path": "docs/vision/source.md",
        "start_line": 3,
        "end_line": 7,
        "section": "Source section",
        "source_hash": "d" * 64,
    }
    assert draft.legacy_import_metadata == {
        "imported_at": "2026-01-02T00:00:00Z",
        "imported_by": "aret-mmu-migrator",
        "migration_batch_id": "MIG-001",
    }
    assert result.projection_state == "PROJECTED_NOT_WRITABLE"


def test_knowledge_source_projection_rejects_parent_not_present_in_the_attested_knowledge_set() -> None:
    bad = AretV1KnowledgeSourceSourceRecord(
        source_id="S-0002",
        knowledge_id="MISSING-0001",
        repository="https://github.com/aciderix/Automatic-reverse-engineering-toolkit",
        revision="c" * 40,
        path="docs/vision/source.md",
        start_line=3,
        end_line=7,
        section="Source section",
        source_hash="d" * 64,
        imported_at="2026-01-02T00:00:00Z",
        imported_by="aret-mmu-migrator",
        migration_batch_id="MIG-001",
    )
    page = AretV1KnowledgeSourceSourcePage(Path("/tmp/source.sqlite"), "b" * 64, (bad,), None)
    with pytest.raises(AretKnowledgeSourceProjectionError):
        project_aret_v1_knowledge_source_page(
            target_identity=IDENTITY,
            knowledge_page=_knowledge_page(),
            source_page=page,
            request_id="m4-c-source-projection",
        )
