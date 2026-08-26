"""Closed semantic mapping declarations for the ARET V1 structural tables."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AretStructuralMapping:
    """A reviewed target shape; this declaration never reads or converts a legacy row."""

    legacy_table: str
    vera_resource: str
    vera_type: str | None
    requires_explicit_import: bool = True


def aret_v1_structural_mappings() -> tuple[AretStructuralMapping, ...]:
    """Return only the three specification-approved V1 structural mappings."""
    return (
        AretStructuralMapping("component", "entity", "COMPONENT"),
        AretStructuralMapping("function_symbol", "symbol", None),
        AretStructuralMapping("brick", "work_item", None),
    )
