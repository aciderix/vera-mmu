"""Shared no-trust project operations for CLI and future local bridge consumers."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any
from .mcp_hooks import compile_mcp_hook_plan
from .mcp_instructions import compile_mcp_instructions
from .mcp_integration import compile_mcp_integration
from .mcp_manifest import compile_mcp_manifest
from .store import MemoryStore, StoreError

SCAN_FORMAT="vera-scan-report/v1";GENERATION_FORMAT="vera-generation-preview/v1";MAX_SCAN_ENTRIES=4096;MAX_SCAN_DEPTH=5
_ADAPTER_BINDINGS={"claude-code-local":"claude-code-local-deny-v1","claude-code-cloud":"claude-code-cloud-deny-v1","codex":"codex-deny-v1","gemini":"gemini-deny-v1","antigravity":"antigravity-deny-v1","generic-mcp":"generic-mcp-deny-v1"}
_EXCLUDED_DIRECTORIES={".git",".vera-mmu",".venv","node_modules","__pycache__","dist","build","target"}
_EXACT_MARKERS={"pyproject.toml":"python","requirements.txt":"python","setup.py":"python","setup.cfg":"python","package.json":"node","tsconfig.json":"typescript","Cargo.toml":"rust","go.mod":"go","pom.xml":"java","build.gradle":"java","README.md":"documentation","README.rst":"documentation","Dockerfile":"container"}
class ProjectOperationError(StoreError):pass
@dataclass(frozen=True)
class ScanObservation:
    kind:str;path:str;detail:str;status:str="OBSERVED"
    def as_dict(self)->dict[str,str]:return {"kind":self.kind,"path":self.path,"detail":self.detail,"status":self.status}
@dataclass(frozen=True)
class ScanReport:
    format:str;root:str;observations:tuple[ScanObservation,...];status:str;report_hash:str;json_text:str
    def as_dict(self)->dict[str,object]:return {"format":self.format,"root":self.root,"observations":[x.as_dict() for x in self.observations],"status":self.status,"report_hash":self.report_hash}
@dataclass(frozen=True)
class GenerationPreview:
    format:str;project_id:str;adapter:str;manifest_json_text:str;instructions_text:str;integration_json_text:str;hook_plan_json_text:str;mcp_build_hash:str;instructions_hash:str;config_hash:str;hook_plan_hash:str;preview_hash:str;status:str="PREVIEW"
    def as_dict(self)->dict[str,object]:return {"format":self.format,"project_id":self.project_id,"adapter":self.adapter,"mcp_build_hash":self.mcp_build_hash,"instructions_hash":self.instructions_hash,"config_hash":self.config_hash,"hook_plan_hash":self.hook_plan_hash,"preview_hash":self.preview_hash,"status":self.status,"outputs":{"manifest":self.manifest_json_text,"instructions":self.instructions_text,"integration":self.integration_json_text,"hook_plan":self.hook_plan_json_text}}
def scan_project(root:str|Path)->ScanReport:
    source=Path(root).expanduser()
    if source.is_symlink():raise ProjectOperationError("Racine de scan symlinkée refusée.")
    try:resolved=source.resolve(strict=True)
    except OSError as exc:raise ProjectOperationError("Racine de scan introuvable.") from exc
    if not resolved.is_dir():raise ProjectOperationError("Racine de scan non répertoire.")
    observed:dict[tuple[str,str],ScanObservation]={};count=0
    for current,dirs,files in os.walk(resolved,followlinks=False):
        here=Path(current);relative=here.relative_to(resolved);depth=len(relative.parts) if relative!=Path(".") else 0
        dirs[:]=sorted(d for d in dirs if d not in _EXCLUDED_DIRECTORIES and not (here/d).is_symlink() and depth<MAX_SCAN_DEPTH)
        if relative==Path(".") and (resolved/".git").exists():_observe(observed,"vcs",".git","Git marker present")
        if relative==Path(".") and (resolved/".github"/"workflows").is_dir():_observe(observed,"ci",".github/workflows","GitHub Actions directory present")
        for name in sorted(files):
            path=here/name
            if path.is_symlink() or not path.is_file():continue
            count+=1
            if count>MAX_SCAN_ENTRIES:
                _observe(observed,"scan-limit",".",f"maximum {MAX_SCAN_ENTRIES} regular files observed");dirs[:]=[];break
            rel=path.relative_to(resolved).as_posix();kind=_EXACT_MARKERS.get(name)
            if kind is not None:_observe(observed,kind,rel,f"marker {name} present")
            if rel.startswith("tests/") or name.startswith("test_") or name.endswith("_test.py"):_observe(observed,"tests",rel,"test-like path present")
            if name.endswith((".md",".rst",".adoc")):_observe(observed,"documentation",rel,"documentation extension present")
        if count>MAX_SCAN_ENTRIES:break
    items=tuple(sorted(observed.values(),key=lambda x:(x.kind,x.path,x.detail)))
    body={"format":SCAN_FORMAT,"root":str(resolved),"observations":[x.as_dict() for x in items],"status":"OBSERVED"};text=_json(body);return ScanReport(SCAN_FORMAT,str(resolved),items,"OBSERVED",sha256(text.encode()).hexdigest(),text)
def compile_generation_preview(store:MemoryStore,adapter:str)->GenerationPreview:
    if not isinstance(store,MemoryStore):raise ProjectOperationError("Store invalide pour génération.")
    binding=_ADAPTER_BINDINGS.get(adapter)
    if binding is None:raise ProjectOperationError(f"Adapter de génération inconnu : {adapter}.")
    rows=store.connection.execute("SELECT capability_id FROM capability_policy WHERE decision = 'ALLOW' ORDER BY capability_id").fetchall();bindings={str(row["capability_id"]):binding for row in rows}
    if not bindings:raise ProjectOperationError("Génération impossible : aucune capability ALLOW déclarée.")
    manifest=compile_mcp_manifest(store,adapter_bindings=bindings);instructions=compile_mcp_instructions(store,manifest);integration=compile_mcp_integration(store,manifest,instructions);hooks=compile_mcp_hook_plan(store,manifest,instructions,integration)
    joined="\0".join((adapter,manifest.canonical_json,instructions.text,integration.json_text,hooks.json_text));return GenerationPreview(GENERATION_FORMAT,store.identity.project_id,adapter,manifest.canonical_json,instructions.text,integration.json_text,hooks.json_text,manifest.mcp_build_hash,instructions.instructions_hash,integration.config_hash,hooks.hook_plan_hash,sha256(joined.encode()).hexdigest())
def _observe(target:dict[tuple[str,str],ScanObservation],kind:str,path:str,detail:str)->None:target[(kind,path)]=ScanObservation(kind,path,detail)
def _json(value:dict[str,Any])->str:return json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
