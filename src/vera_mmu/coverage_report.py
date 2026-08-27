"""Deterministic, non-sensitive coverage projection for the public VERA Core surface."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from .mcp_manifest import TOOL_NAMES
from .read_api import FINDABLE_RESOURCE_TYPES, MAX_EXECUTION_HISTORY, READABLE_RESOURCE_TYPES
from .store import MemoryStore, StoreError


COVERAGE_REPORT_FORMAT = "vera-coverage-report/v1"


@dataclass(frozen=True)
class CoverageReport:
    """A project-bound static capability map; it is not an attestation of host or pack parity."""

    project_identity: dict[str, str]
    mcp_tools: tuple[str, ...]
    readable_resources: tuple[str, ...]
    findable_resources: tuple[str, ...]
    bounded_histories: dict[str, int]
    unsupported_surfaces: tuple[str, ...]
    report_hash: str

    def as_dict(self) -> dict[str, object]:
        return {
            "format": COVERAGE_REPORT_FORMAT,
            "project_identity": dict(self.project_identity),
            "mcp_tools": list(self.mcp_tools),
            "readable_resources": list(self.readable_resources),
            "findable_resources": list(self.findable_resources),
            "bounded_histories": dict(self.bounded_histories),
            "unsupported_surfaces": list(self.unsupported_surfaces),
            "report_hash": self.report_hash,
        }


def compile_coverage_report(store: MemoryStore) -> CoverageReport:
    """Compile a stable report from declared public Core contracts without opening a transaction."""
    if not isinstance(store, MemoryStore):
        raise StoreError("Store invalide pour le rapport de couverture VERA.")
    report = {
        "format": COVERAGE_REPORT_FORMAT,
        "project_identity": store.identity.as_dict(),
        "mcp_tools": sorted(TOOL_NAMES),
        "readable_resources": sorted(READABLE_RESOURCE_TYPES),
        "findable_resources": sorted(FINDABLE_RESOURCE_TYPES),
        "bounded_histories": {"evidence": MAX_EXECUTION_HISTORY, "execution": MAX_EXECUTION_HISTORY},
        "unsupported_surfaces": [
            "dashboard-configurator",
            "document-generation-write",
            "document-generation-project-export",
            "legacy-address-storage-migration",
            "vcs-multi-provider",
            "domain-pack-migration-parity",
            "host-runtime-proof",
        ],
    }
    serialized = _canonical_json(report)
    return CoverageReport(
        project_identity=dict(store.identity.as_dict()),
        mcp_tools=tuple(report["mcp_tools"]),
        readable_resources=tuple(report["readable_resources"]),
        findable_resources=tuple(report["findable_resources"]),
        bounded_histories=dict(report["bounded_histories"]),
        unsupported_surfaces=tuple(report["unsupported_surfaces"]),
        report_hash=sha256(serialized.encode("utf-8")).hexdigest(),
    )


def _canonical_json(value: dict[str, Any]) -> str:
    import json
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
