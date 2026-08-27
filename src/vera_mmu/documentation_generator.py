"""Deterministic read-only project documentation derived from canonical VERA state."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Mapping

from .coverage_report import compile_coverage_report
from .identity import canonical_json, load_profile, project_identity
from .project_catalogs import ProjectCatalogError, load_project_catalogs
from .store import MemoryStore, StoreError
from .workspace import resolve_workspace

DOCUMENT_NAMES = ("MMU_SETUP.md", "TOOLS.md", "GATES.md", "POLICIES.md", "ARCHITECTURE.md", "MAINTENANCE.md")
DOCUMENTATION_FORMAT = "vera-project-documentation/v1"


@dataclass(frozen=True)
class ProjectDocumentation:
    """Immutable documentation projection; compilation never writes project files."""
    project_identity: dict[str, str]
    documents: dict[str, str]
    bundle_hash: str


def compile_project_documentation(store: MemoryStore, profile_path: str) -> ProjectDocumentation:
    if not isinstance(store, MemoryStore):
        raise StoreError("Documentation VERA exige un store actif.")
    profile = load_profile(profile_path)
    if project_identity(profile, resolve_workspace(profile, profile_path)).as_dict() != store.identity.as_dict():
        raise StoreError("Profile lié à une identité différente du store actif.")
    try:
        catalogs = load_project_catalogs(profile_path)
        catalog_payload = {"capabilities": catalogs.capabilities, "gates": catalogs.gates, "policies": catalogs.policies, "agent_profiles": catalogs.agent_profiles}
        catalog_status = "CONFIGURED"
    except ProjectCatalogError as exc:
        catalog_payload = {"capabilities": {"format": "not-configured", "capabilities": []}, "gates": {"format": "not-configured", "gates": []}, "policies": {"format": "not-configured"}, "agent_profiles": {}}
        catalog_status = f"NOT_CONFIGURED: {exc}"
    coverage = compile_coverage_report(store).as_dict()
    project = profile["project"]
    docs = {
        "MMU_SETUP.md": _document("MMU_SETUP", {"project": project, "identity": store.identity.as_dict()}),
        "TOOLS.md": _document("TOOLS", {"catalog_status": catalog_status, "capabilities": catalog_payload["capabilities"], "agent_profiles": catalog_payload["agent_profiles"]}),
        "GATES.md": _document("GATES", {"catalog_status": catalog_status, "gates": catalog_payload["gates"]}),
        "POLICIES.md": _document("POLICIES", {"catalog_status": catalog_status, "policies": catalog_payload["policies"]}),
        "ARCHITECTURE.md": _document("ARCHITECTURE", {"workspace": profile["workspace"], "storage": profile["storage"], "identity": store.identity.as_dict()}),
        "MAINTENANCE.md": _document("MAINTENANCE", {"coverage": coverage, "limitations": coverage["unsupported_surfaces"]}),
    }
    if tuple(docs) != DOCUMENT_NAMES:
        raise StoreError("Projection documentaire incomplète.")
    bundle = {"format": DOCUMENTATION_FORMAT, "project_identity": store.identity.as_dict(), "documents": docs}
    return ProjectDocumentation(dict(store.identity.as_dict()), docs, sha256(canonical_json(bundle).encode()).hexdigest())


def _document(title: str, payload: Mapping[str, object]) -> str:
    return f"# {title}\n\n```json\n{canonical_json(dict(payload))}\n```\n"
