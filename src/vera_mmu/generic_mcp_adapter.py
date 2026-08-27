"""Safe MCP-only fallback for hosts without an attested lifecycle hook surface."""
from __future__ import annotations
import argparse
from dataclasses import dataclass
from hashlib import sha256
import json, os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Mapping, Sequence
from .mcp_instructions import MCPInstructions, compile_mcp_instructions
from .mcp_integration import MCPIntegration, compile_mcp_integration
from .mcp_manifest import MCPManifest, compile_mcp_manifest, verify_mcp_manifest
from .mcp_server import DenyRuntimeAdapter, create_server
from .store import MemoryStore, StoreError
GENERIC_MCP_FORMAT="vera-generic-mcp-adapter/v1";GENERIC_MCP_RUNTIME_FORMAT="vera-generic-mcp-runtime/v1";GENERIC_MCP_CONFIG_FORMAT="vera-generic-mcp-config/v1";GENERIC_MCP_ENTRYPOINT="vmmu-generic-mcp";GENERIC_MCP_COVERAGE="MCP_ONLY"
class GenericMCPAdapterError(StoreError):pass
@dataclass(frozen=True)
class GenericMCPPlan: format:str;project_id:str;mcp_build_hash:str;instructions_hash:str;plan_hash:str;json_text:str
@dataclass(frozen=True)
class GenericMCPStageResult:status:str;state_path:Path;plan_hash:str
@dataclass(frozen=True)
class GenericMCPConfigPreview:status:str;config_path:Path;state_path:Path;json_text:str;plan_hash:str;coverage:str
@dataclass(frozen=True)
class GenericMCPConfigApplyResult:status:str;config_path:Path;state_path:Path;plan_hash:str;coverage:str
@dataclass(frozen=True)
class _Runtime:manifest:MCPManifest;instructions:MCPInstructions;plan:GenericMCPPlan

def compile_generic_mcp_plan(store:MemoryStore)->GenericMCPPlan:
    if not isinstance(store,MemoryStore):raise GenericMCPAdapterError("Store MCP générique invalide.")
    m=compile_mcp_manifest(store,adapter_bindings=_deny_bindings(store));i=compile_mcp_instructions(store,m);integration=compile_mcp_integration(store,m,i);server_id,profile_arg=_server_identity(integration)
    payload={"genericMcp":{"coverage":GENERIC_MCP_COVERAGE,"mcpServer":{"id":server_id,"command":GENERIC_MCP_ENTRYPOINT,"args":["--profile",profile_arg],"cwd":str(store.workspace.project_root.resolve(strict=False)),"includeTools":["mmu_get_capability_catalog","mmu_acknowledge_resume"],"trust":False},"runtime":{"network":"FORBIDDEN","provider":"PREINSTALLED_VERA"}}};text=_json(payload)
    return GenericMCPPlan(GENERIC_MCP_FORMAT,store.identity.project_id,m.mcp_build_hash,i.instructions_hash,sha256(text.encode()).hexdigest(),text)
def stage_generic_mcp_runtime(store:MemoryStore,plan:GenericMCPPlan,*,confirm:bool)->GenericMCPStageResult:
    if confirm is not True:raise GenericMCPAdapterError("Staging MCP générique refusé sans confirmation explicite.")
    if plan!=compile_generic_mcp_plan(store):raise GenericMCPAdapterError("Plan MCP générique périmé, altéré ou étranger.")
    target=_runtime_path(store,True);text=_runtime_text(store,plan);old=_read(target)
    if old is not None and old!=text:raise GenericMCPAdapterError("Runtime MCP générique divergent.")
    if old==text:return GenericMCPStageResult("UNCHANGED",target,plan.plan_hash)
    _write(target,text,".vera-generic-mcp-runtime-");return GenericMCPStageResult("STAGED",target,plan.plan_hash)
def preview_generic_mcp_config(store:MemoryStore,existing:Mapping[str,Any])->GenericMCPConfigPreview:
    current=_object(existing,"configuration MCP générique");runtime=_load_runtime(store);server=_server(runtime.plan);servers=current.get("mcpServers",{})
    if not isinstance(servers,dict):raise GenericMCPAdapterError("mcpServers doit être un objet.")
    entry={k:v for k,v in server.items() if k!="id"};present=servers.get(server["id"])
    if present is not None and present!=entry:raise GenericMCPAdapterError("Conflit : serveur MCP VERA générique divergent.")
    if present!=entry:updated=dict(servers);updated[server["id"]]=entry;current["mcpServers"]=updated
    text=_json(current);return GenericMCPConfigPreview("PREVIEW",_config_path(store,False),_state_path(store,False),text,sha256(text.encode()).hexdigest(),GENERIC_MCP_COVERAGE)
def apply_generic_mcp_config(store:MemoryStore,preview:GenericMCPConfigPreview,*,confirm:bool)->GenericMCPConfigApplyResult:
    if confirm is not True:raise GenericMCPAdapterError("Configuration MCP générique refusée sans confirmation explicite.")
    if not isinstance(preview,GenericMCPConfigPreview) or preview.coverage!=GENERIC_MCP_COVERAGE:raise GenericMCPAdapterError("Preview MCP générique invalide.")
    config=_config_path(store,False);state=_state_path(store,False);expected=preview_generic_mcp_config(store,_load_json(config,"configuration MCP générique"))
    if preview!=expected:raise GenericMCPAdapterError("Preview MCP générique périmé, altéré ou divergent.")
    receipt=_json({"genericMcpConfig":{"format":GENERIC_MCP_CONFIG_FORMAT,"planHash":preview.plan_hash,"configSha256":sha256(preview.json_text.encode()).hexdigest()}});oldr=_read(state);old=_read(config)
    if oldr is not None and oldr!=receipt:raise GenericMCPAdapterError("Reçu MCP générique divergent.")
    if old!=preview.json_text:_write(config,preview.json_text,".vera-generic-mcp-config-")
    if oldr!=receipt:_write(state,receipt,".vera-generic-mcp-state-")
    return GenericMCPConfigApplyResult("UNCHANGED" if old==preview.json_text and oldr==receipt else "APPLIED_PROJECT_LOCAL",config,state,preview.plan_hash,GENERIC_MCP_COVERAGE)
def generic_mcp_main(argv:Sequence[str]|None=None)->None:
    parser=argparse.ArgumentParser(description="Serveur MCP générique VERA-MMU");parser.add_argument("--profile",type=Path,required=True);args=parser.parse_args(argv)
    from .identity import load_profile
    with MemoryStore.open(load_profile(args.profile),args.profile) as store:
        runtime=_load_runtime(store);create_server(store,runtime_adapter=DenyRuntimeAdapter(),manifest=runtime.manifest,instructions=runtime.instructions,actor="vera-generic-mcp").run("stdio")
def generic_mcp_stage_main(argv:Sequence[str]|None=None)->int:
    parser=argparse.ArgumentParser(description="Staging MCP générique VERA-MMU");parser.add_argument("--profile",type=Path,required=True);parser.add_argument("--confirm",action="store_true");args=parser.parse_args(argv)
    try:
        from .identity import load_profile
        with MemoryStore.open(load_profile(args.profile),args.profile) as store:result=stage_generic_mcp_runtime(store,compile_generic_mcp_plan(store),confirm=args.confirm)
    except StoreError as exc:print(json.dumps({"ok":False,"error":str(exc)},ensure_ascii=False));return 2
    print(json.dumps({"ok":True,"status":result.status,"statePath":str(result.state_path),"planHash":result.plan_hash},ensure_ascii=False));return 0
def generic_mcp_config_main(argv:Sequence[str]|None=None)->int:
    parser=argparse.ArgumentParser(description="Configuration MCP générique VERA-MMU");parser.add_argument("--profile",type=Path,required=True);parser.add_argument("--apply-project",action="store_true");parser.add_argument("--confirm",action="store_true");args=parser.parse_args(argv)
    try:
        from .identity import load_profile
        with MemoryStore.open(load_profile(args.profile),args.profile) as store:
            preview=preview_generic_mcp_config(store,_load_json(_config_path(store,False),"configuration MCP générique"));result=apply_generic_mcp_config(store,preview,confirm=args.confirm) if args.apply_project else preview
    except StoreError as exc:print(json.dumps({"ok":False,"error":str(exc)},ensure_ascii=False));return 2
    print(json.dumps({"ok":True,"status":result.status,"configPath":str(result.config_path),"coverage":result.coverage,"planHash":result.plan_hash},ensure_ascii=False));return 0
def _deny_bindings(store:MemoryStore)->dict[str,str]:
    rows=store.connection.execute("SELECT capability_id FROM capability_policy WHERE decision = 'ALLOW' ORDER BY capability_id").fetchall();v={str(r["capability_id"]):"generic-mcp-deny-v1" for r in rows}
    if not v:raise GenericMCPAdapterError("Aucune capability ALLOW pour MCP générique.")
    return v
def _server_identity(integration:MCPIntegration)->tuple[str,str]:
    try:servers=json.loads(integration.json_text)["mcpServers"];key,server=next(iter(servers.items()));args=server["args"]
    except (KeyError,TypeError,StopIteration,json.JSONDecodeError) as exc:raise GenericMCPAdapterError("Configuration MCP attestée illisible.") from exc
    if not isinstance(servers,dict) or len(servers)!=1 or not isinstance(key,str) or not isinstance(args,list) or len(args)!=2 or args[0]!="--profile" or not isinstance(args[1],str):raise GenericMCPAdapterError("Identité MCP attestée invalide.")
    return key,args[1]
def _payload(plan:GenericMCPPlan)->dict[str,Any]:
    if not isinstance(plan,GenericMCPPlan) or plan.plan_hash!=sha256(plan.json_text.encode()).hexdigest():raise GenericMCPAdapterError("Plan MCP générique altéré.")
    try:value=json.loads(plan.json_text)["genericMcp"]
    except (KeyError,TypeError,json.JSONDecodeError) as exc:raise GenericMCPAdapterError("Plan MCP générique illisible.") from exc
    if not isinstance(value,dict):raise GenericMCPAdapterError("Plan MCP générique hors format fermé.")
    return value
def _server(plan:GenericMCPPlan)->dict[str,object]:
    value=_payload(plan).get("mcpServer")
    if not isinstance(value,dict) or value.get("command")!=GENERIC_MCP_ENTRYPOINT or value.get("trust") is not False or value.get("includeTools")!=["mmu_get_capability_catalog","mmu_acknowledge_resume"] or not isinstance(value.get("id"),str) or not isinstance(value.get("args"),list) or not isinstance(value.get("cwd"),str):raise GenericMCPAdapterError("Serveur MCP générique attesté invalide.")
    return dict(value)
def _runtime_path(s:MemoryStore,create:bool)->Path:
    p=s.locator.runtime_dir/"generated"/"generic-mcp-runtime.json"
    if p.is_symlink():raise GenericMCPAdapterError("Runtime MCP générique symlinké refusé.")
    if create:_parent(p.parent,"runtime MCP générique")
    return p
def _runtime_text(s:MemoryStore,p:GenericMCPPlan)->str:
    return _json({"genericMcpRuntime":{"format":GENERIC_MCP_RUNTIME_FORMAT,"plan":_payload(p),"planHash":p.plan_hash,"adapterBindings":[{"capability_id":x.capability_id,"adapter_id":x.adapter_id} for x in compile_mcp_manifest(s,adapter_bindings=_deny_bindings(s)).capabilities]}})
def _load_runtime(s:MemoryStore)->_Runtime:
    raw=_read(_runtime_path(s,False))
    if raw is None:raise GenericMCPAdapterError("MCP générique non staged.")
    try:x=json.loads(raw)["genericMcpRuntime"];bindings={str(v["capability_id"]):str(v["adapter_id"]) for v in x["adapterBindings"]};ph=x["planHash"];payload=x["plan"]
    except (KeyError,TypeError,ValueError,json.JSONDecodeError) as exc:raise GenericMCPAdapterError("Runtime MCP générique hors format fermé.") from exc
    if x.get("format")!=GENERIC_MCP_RUNTIME_FORMAT or not bindings or len(bindings)!=len(x["adapterBindings"]):raise GenericMCPAdapterError("Runtime MCP générique invalide.")
    m=compile_mcp_manifest(s,adapter_bindings=bindings);i=compile_mcp_instructions(s,m);p=compile_generic_mcp_plan(s)
    if p.plan_hash!=ph or payload!=json.loads(p.json_text)["genericMcp"]:raise GenericMCPAdapterError("Runtime MCP générique périmé ou altéré.")
    return _Runtime(m,i,p)
def _config_path(s:MemoryStore,create:bool)->Path:
    p=s.workspace.project_root/".mcp.json"
    if p.is_symlink():raise GenericMCPAdapterError(".mcp.json symlinké refusé.")
    if create:_parent(p.parent,"projet MCP générique")
    return p
def _state_path(s:MemoryStore,create:bool)->Path:
    p=s.locator.runtime_dir/"generated"/"generic-mcp-config.json"
    if p.is_symlink():raise GenericMCPAdapterError("Reçu MCP générique symlinké refusé.")
    if create:_parent(p.parent,"runtime MCP générique")
    return p
def _object(v:Mapping[str,Any],label:str)->dict[str,Any]:
    if not isinstance(v,Mapping):raise GenericMCPAdapterError(f"{label} doit être un objet JSON.")
    try:o=json.loads(json.dumps(dict(v),ensure_ascii=False))
    except (TypeError,ValueError) as exc:raise GenericMCPAdapterError(f"{label} non sérialisable.") from exc
    if not isinstance(o,dict):raise GenericMCPAdapterError(f"{label} doit être un objet JSON.")
    return o
def _load_json(p:Path,label:str)->dict[str,Any]:
    raw=_read(p)
    if raw is None:return {}
    try:v=json.loads(raw)
    except json.JSONDecodeError as exc:raise GenericMCPAdapterError(f"{label} illisible.") from exc
    return _object(v,label)
def _read(p:Path)->str|None:
    if not p.exists():return None
    if p.is_symlink() or not p.is_file():raise GenericMCPAdapterError("État MCP générique non régulier.")
    try:return p.read_text(encoding="utf-8")
    except (OSError,UnicodeDecodeError) as exc:raise GenericMCPAdapterError("État MCP générique illisible.") from exc
def _parent(p:Path,label:str)->None:
    if p.is_symlink():raise GenericMCPAdapterError(f"{label} symlinké refusé.")
    try:p.mkdir(mode=0o700,parents=True,exist_ok=True)
    except OSError as exc:raise GenericMCPAdapterError(f"Création {label} impossible.") from exc
    if not p.is_dir() or p.is_symlink():raise GenericMCPAdapterError(f"{label} invalide.")
def _json(v:Mapping[str,Any])->str:return json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
def _write(p:Path,text:str,prefix:str)->None:
    _parent(p.parent,"répertoire cible MCP générique");tmp:Path|None=None
    try:
        with NamedTemporaryFile(mode="w",encoding="utf-8",newline="\n",dir=p.parent,prefix=prefix,suffix=".tmp",delete=False) as f:tmp=Path(f.name);f.write(text);f.flush();os.fsync(f.fileno())
        os.chmod(tmp,0o600);os.replace(tmp,p)
    except OSError as exc:
        if tmp is not None:tmp.unlink(missing_ok=True)
        raise GenericMCPAdapterError("Écriture atomique MCP générique impossible.") from exc
