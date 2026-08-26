from __future__ import annotations

import pytest

from vera_mmu.domain_packs.aret import (
    AretBrickProjectionError,
    AretV1BrickSourcePage,
    AretV1BrickSourceRecord,
    project_aret_v1_brick_page,
)
from vera_mmu.identity import ProjectIdentity


IDENTITY = ProjectIdentity("brick-projection", "2.0", "1" * 64, "2" * 64, "3" * 64)


def _page(record: AretV1BrickSourceRecord) -> AretV1BrickSourcePage:
    from pathlib import Path
    return AretV1BrickSourcePage(Path("/tmp/source.sqlite"), "a" * 64, (record,), None)


def test_brick_projection_preserves_legacy_state_as_metadata_without_mutation() -> None:
    result = project_aret_v1_brick_page(
        target_identity=IDENTITY,
        source_page=_page(AretV1BrickSourceRecord("BRK-001", "CMP-001", "Roadmap", "ACTIVE", "desc", "M1", "linux", 2, "2026-01-01T00:00:00Z", "fixture")),
        request_id="m4-b-brick-projection",
    )
    draft = result.drafts[0]
    assert draft.target_identifier == "aret-brick--BRK-001"
    assert draft.item_type == "WORK_ITEM"
    assert draft.priority == 2
    assert draft.metadata["source"]["state"] == "ACTIVE"
    assert draft.metadata["source"]["component_id"] == "CMP-001"


def test_brick_projection_rejects_unknown_state_or_priority() -> None:
    invalid = AretV1BrickSourceRecord("BRK-001", None, "Roadmap", "UNKNOWN", "", None, None, 9, "2026-01-01T00:00:00Z", "fixture")
    with pytest.raises(AretBrickProjectionError):
        project_aret_v1_brick_page(target_identity=IDENTITY, source_page=_page(invalid), request_id="m4-b-brick-projection")
