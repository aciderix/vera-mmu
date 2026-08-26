from __future__ import annotations

import pytest

from vera_mmu.domain_packs.aret import (
    AretFunctionSymbolProjectionError,
    AretV1FunctionSymbolSourcePage,
    AretV1FunctionSymbolSourceRecord,
    project_aret_v1_function_symbol_page,
)
from vera_mmu.identity import ProjectIdentity


IDENTITY = ProjectIdentity("symbol-projection", "2.0", "1" * 64, "2" * 64, "3" * 64)


def _page(record: AretV1FunctionSymbolSourceRecord) -> AretV1FunctionSymbolSourcePage:
    from pathlib import Path
    return AretV1FunctionSymbolSourcePage(Path("/tmp/source.sqlite"), "a" * 64, (record,), None)


def test_function_symbol_projection_is_deterministic_and_preserves_source_fields() -> None:
    result = project_aret_v1_function_symbol_page(
        target_identity=IDENTITY,
        source_page=_page(AretV1FunctionSymbolSourceRecord("CMP-001:core!alpha", "CMP-001", "core", "alpha", "cdecl", "2026-01-01T00:00:00Z", "fixture")),
        request_id="m4-b-symbol-projection",
    )
    draft = result.drafts[0]
    assert draft.target_identifier == "aret-symbol--CMP-001-core-alpha"
    assert draft.owner_entity_id == "aret-component--CMP-001"
    assert draft.kind == "FUNCTION"
    assert draft.path == "core"
    assert draft.identifier == "alpha"
    assert draft.metadata["source"]["calling_convention"] == "cdecl"


def test_function_symbol_projection_rejects_invalid_parent_or_source_id() -> None:
    invalid = AretV1FunctionSymbolSourceRecord("bad/id", "CMP-001", "", "alpha", "cdecl", "2026-01-01T00:00:00Z", "fixture")
    with pytest.raises(AretFunctionSymbolProjectionError):
        project_aret_v1_function_symbol_page(target_identity=IDENTITY, source_page=_page(invalid), request_id="m4-b-symbol-projection")
