"""Shared no-trust project operations for CLI and future local bridge consumers."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any
from .mcp_hooks import compile_mcp_hook_plan
from .mcp_instructions import compile_mcp_instructions
from .mcp_integration import compile_mcp_integration
from .mcp_manifest import compile_mcp_manifest
from .project_catalogs import ProjectCatalogError, load_project_catalogs
# The scanner moved to its own module when §30 grew to fourteen categories; re-exported so
# existing callers keep one import site.
from .project_scan import SCAN_FORMAT, MAX_SCAN_DEPTH, MAX_SCAN_ENTRIES, ProjectScanError, ScanObservation, ScanReport, scan_project  # noqa: F401
from .store import MemoryStore, StoreError

GENERATION_FORMAT="vera-generation-preview/v1"
_ADAPTER_BINDINGS={"claude-code-local":"claude-code-local-deny-v1","claude-code-cloud":"claude-code-cloud-deny-v1","codex":"codex-deny-v1","gemini":"gemini-deny-v1","antigravity":"antigravity-deny-v1","generic-mcp":"generic-mcp-deny-v1"}
class ProjectOperationError(StoreError):pass
@dataclass(frozen=True)
class GenerationPreview:
    format:str;project_id:str;adapter:str;manifest_json_text:str;instructions_text:str;integration_json_text:str;hook_plan_json_text:str;profile_hash:str;capability_catalog_hash:str;gate_catalog_hash:str;policy_hash:str;mcp_build_hash:str;instructions_hash:str;config_hash:str;hook_plan_hash:str;preview_hash:str;status:str="PREVIEW"
    def as_dict(self)->dict[str,object]:return {"format":self.format,"project_id":self.project_id,"adapter":self.adapter,"profile_hash":self.profile_hash,"capability_catalog_hash":self.capability_catalog_hash,"gate_catalog_hash":self.gate_catalog_hash,"policy_hash":self.policy_hash,"mcp_build_hash":self.mcp_build_hash,"instructions_hash":self.instructions_hash,"config_hash":self.config_hash,"hook_plan_hash":self.hook_plan_hash,"preview_hash":self.preview_hash,"status":self.status,"outputs":{"manifest":self.manifest_json_text,"instructions":self.instructions_text,"integration":self.integration_json_text,"hook_plan":self.hook_plan_json_text}}
def compile_generation_preview(store:MemoryStore,adapter:str)->GenerationPreview:
    if not isinstance(store,MemoryStore):raise ProjectOperationError("Store invalide pour génération.")
    binding=_ADAPTER_BINDINGS.get(adapter)
    if binding is None:raise ProjectOperationError(f"Adapter de génération inconnu : {adapter}.")
    try:catalogs=load_project_catalogs(store.workspace.profile_path)
    except ProjectCatalogError as exc:raise ProjectOperationError("Catalogues du Project Profile invalides ou absents pour génération.") from exc
    rows=store.connection.execute("SELECT capability_id FROM capability_policy WHERE decision = 'ALLOW' ORDER BY capability_id").fetchall();bindings={str(row["capability_id"]):binding for row in rows}
    if not bindings:raise ProjectOperationError("Génération impossible : aucune capability ALLOW déclarée.")
    manifest=compile_mcp_manifest(store,adapter_bindings=bindings);instructions=compile_mcp_instructions(store,manifest);integration=compile_mcp_integration(store,manifest,instructions);hooks=compile_mcp_hook_plan(store,manifest,instructions,integration)
    joined="\0".join((adapter,store.identity.profile_hash,catalogs.capability_catalog_hash,catalogs.gate_catalog_hash,catalogs.policy_hash,manifest.canonical_json,instructions.text,integration.json_text,hooks.json_text));return GenerationPreview(GENERATION_FORMAT,store.identity.project_id,adapter,manifest.canonical_json,instructions.text,integration.json_text,hooks.json_text,store.identity.profile_hash,catalogs.capability_catalog_hash,catalogs.gate_catalog_hash,catalogs.policy_hash,manifest.mcp_build_hash,instructions.instructions_hash,integration.config_hash,hooks.hook_plan_hash,sha256(joined.encode()).hexdigest())
def _json(value:dict[str,Any])->str:return json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
