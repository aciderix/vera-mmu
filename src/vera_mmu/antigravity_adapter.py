"""Antigravity adapter with bounded turn-level lifecycle coverage.

Antigravity exposes invocation and tool hooks, not a documented durable SessionStart or
compaction lifecycle. The adapter consequently arms per invocation and never synthesizes
a missing restore/compaction event.
"""
from __future__ import annotations
import argparse
from dataclasses import dataclass
from hashlib import sha256
import json, os
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile
from typing import Any, Mapping, Sequence
from .lifecycle_adapters import LifecycleAdapterPlan, LifecycleAdapterRegistry, compile_lifecycle_adapter_plan
from .mcp_hooks import MCPHookPlan, compile_mcp_hook_plan
from .mcp_instructions import MCPInstructions, compile_mcp_instructions
from .mcp_integration import MCPIntegration, compile_mcp_integration
from .mcp_manifest import MCPManifest, compile_mcp_manifest, verify_mcp_manifest
from .mcp_server import DenyRuntimeAdapter, create_server
from .session_lifecycle import GuardDecision, ResumeDossierService, ResumeGuardService, ResumeSectionRequirement
from .store import MemoryStore, StoreError

ANTIGRAVITY_FORMAT="vera-antigravity-adapter/v1"; ANTIGRAVITY_RUNTIME_FORMAT="vera-antigravity-runtime/v1"; ANTIGRAVITY_HOST_CONFIG_FORMAT="vera-antigravity-host-config/v1"
ANTIGRAVITY_ADAPTER_ID="antigravity-v1"; ANTIGRAVITY_ADAPTER_VERSION="1.0.0"; ANTIGRAVITY_MAXIMUM_GUARD_MODE="HARD"; ANTIGRAVITY_MCP_ENTRYPOINT="vmmu-antigravity-mcp"; ANTIGRAVITY_HOOK_ENTRYPOINT="vmmu-antigravity-hook"
ANTIGRAVITY_EVENTS=("PreInvocation","PreToolUse","PostToolUse","Stop"); ANTIGRAVITY_COVERAGE="TURN_GUARD_HARD"
class AntigravityAdapterError(StoreError): pass
@dataclass(frozen=True)
class AntigravityPlan:
    format:str; project_id:str; mcp_build_hash:str; instructions_hash:str; config_hash:str; hook_plan_hash:str; lifecycle_plan_hash:str; plan_hash:str; json_text:str
@dataclass(frozen=True)
class AntigravityStageResult: status:str; state_path:Path; plan_hash:str
@dataclass(frozen=True)
class AntigravityHostConfigPreview: status:str; settings_path:Path; state_path:Path; settings_json_text:str; plan_hash:str; coverage:str
@dataclass(frozen=True)
class AntigravityHostConfigApplyResult: status:str;settings_path:Path;state_path:Path;plan_hash:str;coverage:str
@dataclass(frozen=True)
class _Runtime: manifest:MCPManifest;instructions:MCPInstructions;lifecycle:LifecycleAdapterPlan;plan:AntigravityPlan
class AntigravitySessionAdapter:
    adapter_id=ANTIGRAVITY_ADAPTER_ID;adapter_version=ANTIGRAVITY_ADAPTER_VERSION;maximum_guard_mode=ANTIGRAVITY_MAXIMUM_GUARD_MODE
    def __init__(self,store:MemoryStore):self.store=store
    def session_identity(self)->str|None:
        row=_read_session(self.store);return None if row is None else row["invocation_id"]

def compile_antigravity_plan(store:MemoryStore,manifest:MCPManifest,instructions:MCPInstructions,integration:MCPIntegration,hooks:MCPHookPlan,lifecycle:LifecycleAdapterPlan)->AntigravityPlan:
    try:
        verify_mcp_manifest(store,manifest);i=compile_mcp_instructions(store,manifest);c=compile_mcp_integration(store,manifest,i);h=compile_mcp_hook_plan(store,manifest,i,c);l=compile_lifecycle_adapter_plan(store,manifest,adapter_id=ANTIGRAVITY_ADAPTER_ID,adapter_version=ANTIGRAVITY_ADAPTER_VERSION,maximum_guard_mode=ANTIGRAVITY_MAXIMUM_GUARD_MODE)
    except StoreError as exc:raise AntigravityAdapterError("Snapshots Antigravity invalides.") from exc
    if (instructions,integration,hooks,lifecycle)!=(i,c,h,l):raise AntigravityAdapterError("Snapshot Antigravity périmé, altéré ou étranger.")
    sid,parg=_server_identity(integration);profile=_profile(store,parg);value={"antigravity":{"coverage":ANTIGRAVITY_COVERAGE,"hooks":{"events":list(ANTIGRAVITY_EVENTS),"projectTrust":"HOST_REVIEW_REQUIRED"},"mcpServer":{"id":sid,"command":ANTIGRAVITY_MCP_ENTRYPOINT,"args":["--profile",str(profile)],"cwd":str(store.workspace.project_root.resolve(strict=False)),"includeTools":["mmu_acknowledge_resume"],"trust":False},"runtime":{"network":"FORBIDDEN","provider":"PREINSTALLED_VERA"}}};text=_json(value)
    return AntigravityPlan(ANTIGRAVITY_FORMAT,store.identity.project_id,manifest.mcp_build_hash,instructions.instructions_hash,integration.config_hash,hooks.hook_plan_hash,lifecycle.lifecycle_plan_hash,sha256(text.encode()).hexdigest(),text)
def stage_antigravity_runtime(store:MemoryStore,manifest:MCPManifest,instructions:MCPInstructions,integration:MCPIntegration,hooks:MCPHookPlan,lifecycle:LifecycleAdapterPlan,plan:AntigravityPlan,*,confirm:bool)->AntigravityStageResult:
    if confirm is not True:raise AntigravityAdapterError("Staging Antigravity refusé sans confirmation explicite.")
    if plan!=compile_antigravity_plan(store,manifest,instructions,integration,hooks,lifecycle):raise AntigravityAdapterError("Plan Antigravity périmé, altéré ou étranger.")
    target=_runtime_path(store,True);text=_runtime_text(plan,manifest);old=_read(target)
    if old is not None and old!=text:raise AntigravityAdapterError("État runtime Antigravity divergent.")
    if old==text:return AntigravityStageResult("UNCHANGED",target,plan.plan_hash)
    _write(target,text,".vera-antigravity-runtime-");return AntigravityStageResult("STAGED",target,plan.plan_hash)
def preview_antigravity_host_config(store:MemoryStore,existing:Mapping[str,Any])->AntigravityHostConfigPreview:
    settings=_object(existing,"settings Antigravity");runtime=_load_runtime(store);desired=_hook_config(runtime.plan);merged,_=_merge_hooks(settings,desired);server=_server(runtime.plan);servers=merged.get("mcpServers",{})
    if not isinstance(servers,dict):raise AntigravityAdapterError("mcpServers Antigravity doit être un objet.")
    entry={k:v for k,v in server.items() if k!="id"};current=servers.get(server["id"])
    if current is not None and current!=entry:raise AntigravityAdapterError("Conflit : serveur MCP VERA Antigravity divergent.")
    if current!=entry:allservers=dict(servers);allservers[server["id"]]=entry;merged["mcpServers"]=allservers
    text=_json(merged);return AntigravityHostConfigPreview("PREVIEW",_settings_path(store,False),_host_state_path(store,False),text,sha256(text.encode()).hexdigest(),ANTIGRAVITY_COVERAGE)
def apply_antigravity_host_config(store:MemoryStore,preview:AntigravityHostConfigPreview,*,confirm:bool)->AntigravityHostConfigApplyResult:
    if confirm is not True:raise AntigravityAdapterError("Application Antigravity refusée sans confirmation explicite.")
    if not isinstance(preview,AntigravityHostConfigPreview) or preview.coverage!=ANTIGRAVITY_COVERAGE:raise AntigravityAdapterError("Preview Antigravity invalide.")
    settings=_settings_path(store,False);state=_host_state_path(store,False);expected=preview_antigravity_host_config(store,_load_json(settings,"settings Antigravity"))
    if preview!=expected:raise AntigravityAdapterError("Preview Antigravity périmé, altéré ou divergent.")
    receipt=_json({"antigravityHostConfig":{"format":ANTIGRAVITY_HOST_CONFIG_FORMAT,"planHash":preview.plan_hash,"settingsSha256":sha256(preview.settings_json_text.encode()).hexdigest()}});oldreceipt=_read(state);oldsettings=_read(settings)
    if oldreceipt is not None and oldreceipt!=receipt:raise AntigravityAdapterError("État configuration Antigravity divergent.")
    if oldsettings!=preview.settings_json_text:_write(settings,preview.settings_json_text,".vera-antigravity-settings-")
    if oldreceipt!=receipt:_write(state,receipt,".vera-antigravity-host-")
    return AntigravityHostConfigApplyResult("UNCHANGED" if oldsettings==preview.settings_json_text and oldreceipt==receipt else "APPLIED_PROJECT_LOCAL",settings,state,preview.plan_hash,ANTIGRAVITY_COVERAGE)
def handle_antigravity_hook(store:MemoryStore,lifecycle:LifecycleAdapterPlan,plan:AntigravityPlan,event:str,payload:Mapping[str,object])->dict[str,object]:
    runtime=_load_runtime(store)
    if lifecycle!=runtime.lifecycle or plan!=runtime.plan:raise AntigravityAdapterError("Lifecycle Antigravity étranger au runtime staged.")
    if event not in ANTIGRAVITY_EVENTS or not isinstance(payload,Mapping):raise AntigravityAdapterError("Événement ou payload Antigravity invalide.")
    invocation=_invocation(payload);_cwd(store,payload.get("cwd"));guard=ResumeGuardService(store)
    if event=="PreInvocation":
        _claim_session(store,invocation);dossier=_dossier(store);guard.arm(invocation,ANTIGRAVITY_ADAPTER_ID,"SESSION_OPEN",dossier,mode="HARD");return {"context":"Resume Dossier VERA Antigravity — lire et acquitter via mmu_acknowledge_resume :\n"+dossier.json_text}
    if _read_session(store)!={"project_id":store.identity.project_id,"invocation_id":invocation}:raise AntigravityAdapterError("Invocation Antigravity non liée au runtime courant.")
    if event=="PreToolUse":
        tool=payload.get("tool_name")
        if not isinstance(tool,str):raise AntigravityAdapterError("PreToolUse Antigravity sans tool.")
        if tool in _ack_tools(store):return {}
        result=guard.precheck(invocation,ANTIGRAVITY_ADAPTER_ID);return {"decision":"deny","reason":result.reason} if result.decision==GuardDecision.DENY else ({"notice":result.reason} if result.decision==GuardDecision.ALLOW_WITH_NOTICE else {})
    if event=="PostToolUse":
        result=guard.precheck(invocation,ANTIGRAVITY_ADAPTER_ID);return {"notice":result.reason} if result.decision!=GuardDecision.ALLOW else {}
    _release_session(store,invocation);return {"status":"SESSION_ENDED"}
def antigravity_stage_main(argv:Sequence[str]|None=None)->int:
    p=argparse.ArgumentParser(description="Staging runtime Antigravity VERA-MMU");p.add_argument("--profile",type=Path,required=True);p.add_argument("--confirm",action="store_true");a=p.parse_args(argv)
    try:
        from .identity import load_profile
        with MemoryStore.open(load_profile(a.profile),a.profile) as s:
            m=compile_mcp_manifest(s,adapter_bindings=_deny(s));i=compile_mcp_instructions(s,m);c=compile_mcp_integration(s,m,i);h=compile_mcp_hook_plan(s,m,i,c);l=compile_lifecycle_adapter_plan(s,m,adapter_id=ANTIGRAVITY_ADAPTER_ID,adapter_version=ANTIGRAVITY_ADAPTER_VERSION,maximum_guard_mode=ANTIGRAVITY_MAXIMUM_GUARD_MODE);r=stage_antigravity_runtime(s,m,i,c,h,l,compile_antigravity_plan(s,m,i,c,h,l),confirm=a.confirm)
    except StoreError as exc:print(json.dumps({"ok":False,"error":str(exc)},ensure_ascii=False));return 2
    print(json.dumps({"ok":True,"status":r.status,"planHash":r.plan_hash,"statePath":str(r.state_path)},ensure_ascii=False));return 0
def antigravity_hook_main(argv:Sequence[str]|None=None)->int:
    p=argparse.ArgumentParser(description="Hook lifecycle Antigravity VERA-MMU");p.add_argument("--profile",type=Path,required=True);p.add_argument("--event",choices=ANTIGRAVITY_EVENTS,required=True);a=p.parse_args(argv)
    try:
        payload=json.loads(sys.stdin.read())
        if not isinstance(payload,dict):raise AntigravityAdapterError("Payload JSON Antigravity requis.")
        from .identity import load_profile
        with MemoryStore.open(load_profile(a.profile),a.profile) as s:r=_load_runtime(s);out=handle_antigravity_hook(s,r.lifecycle,r.plan,a.event,payload)
    except (StoreError,json.JSONDecodeError) as exc:print(json.dumps({"decision":"deny","reason":str(exc)},ensure_ascii=False));return 2
    print(json.dumps(out,ensure_ascii=False,sort_keys=True));return 0
def antigravity_mcp_main(argv:Sequence[str]|None=None)->None:
    p=argparse.ArgumentParser(description="Serveur MCP lifecycle Antigravity VERA-MMU");p.add_argument("--profile",type=Path,required=True);a=p.parse_args(argv);from .identity import load_profile
    with MemoryStore.open(load_profile(a.profile),a.profile) as s:r=_load_runtime(s);create_server(s,runtime_adapter=DenyRuntimeAdapter(),manifest=r.manifest,instructions=r.instructions,lifecycle_adapter_registry=LifecycleAdapterRegistry((AntigravitySessionAdapter(s),)),lifecycle_adapter_plan=r.lifecycle,actor="vera-antigravity").run("stdio")
def antigravity_config_main(argv:Sequence[str]|None=None)->int:
    p=argparse.ArgumentParser(description="Configuration Antigravity project-local VERA-MMU");p.add_argument("--profile",type=Path,required=True);p.add_argument("--apply-project",action="store_true");p.add_argument("--confirm",action="store_true");a=p.parse_args(argv)
    try:
        from .identity import load_profile
        with MemoryStore.open(load_profile(a.profile),a.profile) as s:q=preview_antigravity_host_config(s,_load_json(_settings_path(s,False),"settings Antigravity"));r=apply_antigravity_host_config(s,q,confirm=a.confirm) if a.apply_project else q
    except StoreError as exc:print(json.dumps({"ok":False,"error":str(exc)},ensure_ascii=False));return 2
    print(json.dumps({"ok":True,"status":r.status,"planHash":r.plan_hash,"settingsPath":str(r.settings_path),"coverage":r.coverage},ensure_ascii=False));return 0
# Attested-state helpers below intentionally accept no command, path, verdict, or host-provided adapter selection.
def _server_identity(c:MCPIntegration)->tuple[str,str]:
    try:servers=json.loads(c.json_text)["mcpServers"];key,server=next(iter(servers.items()));args=server["args"]
    except (KeyError,TypeError,StopIteration,json.JSONDecodeError) as exc:raise AntigravityAdapterError("Configuration MCP attestée illisible.") from exc
    if not isinstance(servers,dict) or len(servers)!=1 or not isinstance(key,str) or not isinstance(args,list) or len(args)!=2 or args[0]!="--profile" or not isinstance(args[1],str):raise AntigravityAdapterError("Identité MCP attestée invalide.")
    return key,args[1]
def _profile(s:MemoryStore,arg:str)->Path:
    v=arg.removeprefix("${CLAUDE_PROJECT_DIR:-.}/");p=Path(v)
    if p.is_absolute() or ".." in p.parts:raise AntigravityAdapterError("Profil Antigravity hors projet.")
    t=(s.workspace.project_root/p).resolve(strict=False)
    try:t.relative_to(s.workspace.project_root.resolve(strict=False))
    except ValueError as exc:raise AntigravityAdapterError("Profil Antigravity hors projet.") from exc
    return t
def _payload(p:AntigravityPlan)->dict[str,Any]:
    if not isinstance(p,AntigravityPlan) or p.plan_hash!=sha256(p.json_text.encode()).hexdigest():raise AntigravityAdapterError("Plan Antigravity altéré.")
    try:v=json.loads(p.json_text)["antigravity"]
    except (KeyError,TypeError,json.JSONDecodeError) as exc:raise AntigravityAdapterError("Plan Antigravity illisible.") from exc
    if not isinstance(v,dict):raise AntigravityAdapterError("Plan Antigravity hors format fermé.")
    return v
def _server(p:AntigravityPlan)->dict[str,object]:
    v=_payload(p).get("mcpServer")
    if not isinstance(v,dict) or v.get("command")!=ANTIGRAVITY_MCP_ENTRYPOINT or v.get("trust") is not False or v.get("includeTools")!=["mmu_acknowledge_resume"] or not isinstance(v.get("id"),str) or not isinstance(v.get("args"),list) or not isinstance(v.get("cwd"),str):raise AntigravityAdapterError("Serveur Antigravity attesté invalide.")
    return dict(v)
def _hook_config(p:AntigravityPlan)->dict[str,list[dict[str,object]]]:
    args=_server(p)["args"]
    if not isinstance(args,list) or len(args)!=2 or not isinstance(args[1],str):raise AntigravityAdapterError("Profil hook Antigravity invalide.")
    return {event:[{"command":f'{ANTIGRAVITY_HOOK_ENTRYPOINT} --profile {json.dumps(args[1])} --event {event}',"name":"vera-antigravity-lifecycle","timeout":10000}] for event in ANTIGRAVITY_EVENTS}
def _merge_hooks(existing:dict[str,Any],desired:Mapping[str,list[dict[str,object]]])->tuple[dict[str,Any],bool]:
    old=existing.get("hooks",{})
    if not isinstance(old,dict):raise AntigravityAdapterError("hooks Antigravity doit être un objet.")
    new={k:list(v) if isinstance(v,list) else v for k,v in old.items()};changed=False
    for event,items in desired.items():
        current=new.get(event,[])
        if not isinstance(current,list):raise AntigravityAdapterError("Événement hook Antigravity doit être une liste.")
        if any(_is_vera(x) and x not in items for x in current):raise AntigravityAdapterError("Conflit : hook VERA Antigravity divergent.")
        add=[x for x in items if x not in current]
        if add:new[event]=[*current,*add];changed=True
    out=dict(existing)
    if changed:out["hooks"]=new
    return out,changed
def _is_vera(x:object)->bool:return isinstance(x,dict) and isinstance(x.get("command"),str) and x["command"].startswith(ANTIGRAVITY_HOOK_ENTRYPOINT)
def _runtime_path(s:MemoryStore,create:bool)->Path:
    t=s.locator.runtime_dir/"generated"/"antigravity-runtime.json"
    if t.is_symlink():raise AntigravityAdapterError("Runtime Antigravity symlinké refusé.")
    if create:_parent(t.parent,"runtime Antigravity")
    return t
def _runtime_text(p:AntigravityPlan,m:MCPManifest)->str:return _json({"antigravityRuntime":{"format":ANTIGRAVITY_RUNTIME_FORMAT,"plan":_payload(p),"planHash":p.plan_hash,"adapterBindings":[{"capability_id":c.capability_id,"adapter_id":c.adapter_id} for c in m.capabilities]}})
def _load_runtime(s:MemoryStore)->_Runtime:
    raw=_read(_runtime_path(s,False))
    if raw is None:raise AntigravityAdapterError("Adapter Antigravity non staged.")
    try:x=json.loads(raw)["antigravityRuntime"];bindings={str(v["capability_id"]):str(v["adapter_id"]) for v in x["adapterBindings"]};ph=x["planHash"];payload=x["plan"]
    except (KeyError,TypeError,ValueError,json.JSONDecodeError) as exc:raise AntigravityAdapterError("Runtime Antigravity hors format fermé.") from exc
    if x.get("format")!=ANTIGRAVITY_RUNTIME_FORMAT or not bindings or len(bindings)!=len(x["adapterBindings"]):raise AntigravityAdapterError("Runtime Antigravity invalide.")
    m=compile_mcp_manifest(s,adapter_bindings=bindings);i=compile_mcp_instructions(s,m);c=compile_mcp_integration(s,m,i);h=compile_mcp_hook_plan(s,m,i,c);l=compile_lifecycle_adapter_plan(s,m,adapter_id=ANTIGRAVITY_ADAPTER_ID,adapter_version=ANTIGRAVITY_ADAPTER_VERSION,maximum_guard_mode=ANTIGRAVITY_MAXIMUM_GUARD_MODE);p=compile_antigravity_plan(s,m,i,c,h,l)
    if p.plan_hash!=ph or payload!=json.loads(p.json_text)["antigravity"]:raise AntigravityAdapterError("Runtime Antigravity périmé ou altéré.")
    return _Runtime(m,i,l,p)
def _settings_path(s:MemoryStore,create:bool)->Path:
    d=s.workspace.project_root/".antigravity"
    if d.is_symlink():raise AntigravityAdapterError("Répertoire .antigravity symlinké refusé.")
    if create:_parent(d,"répertoire .antigravity")
    elif d.exists() and not d.is_dir():raise AntigravityAdapterError("Répertoire .antigravity invalide.")
    t=d/"settings.json"
    if t.is_symlink():raise AntigravityAdapterError("settings Antigravity symlinké refusé.")
    return t
def _host_state_path(s:MemoryStore,create:bool)->Path:
    t=s.locator.runtime_dir/"generated"/"antigravity-host-config.json"
    if t.is_symlink():raise AntigravityAdapterError("État Antigravity symlinké refusé.")
    if create:_parent(t.parent,"runtime Antigravity")
    return t
def _session_path(s:MemoryStore)->Path:
    t=s.locator.runtime_dir/"lifecycle"/"antigravity-session.json";_parent(t.parent,"lifecycle Antigravity")
    if t.is_symlink():raise AntigravityAdapterError("Session Antigravity symlinkée refusée.")
    return t
def _read_session(s:MemoryStore)->dict[str,str]|None:
    raw=_read(_session_path(s))
    if raw is None:return None
    try:v=json.loads(raw)
    except json.JSONDecodeError as exc:raise AntigravityAdapterError("Session Antigravity illisible.") from exc
    if not isinstance(v,dict) or set(v)!={"project_id","invocation_id"} or v.get("project_id")!=s.identity.project_id or not isinstance(v.get("invocation_id"),str):raise AntigravityAdapterError("Session Antigravity invalide.")
    return {"project_id":s.identity.project_id,"invocation_id":v["invocation_id"]}
def _claim_session(s:MemoryStore,key:str)->None:
    old=_read_session(s);v={"project_id":s.identity.project_id,"invocation_id":key}
    if old is not None and old!=v:raise AntigravityAdapterError("Conflit : une autre invocation Antigravity est active.")
    if old is None:_write(_session_path(s),_json(v),".vera-antigravity-session-")
def _release_session(s:MemoryStore,key:str)->None:
    p=_session_path(s);v=_read_session(s)
    if v is not None and v["invocation_id"]==key:p.unlink()
def _invocation(p:Mapping[str,object])->str:
    v=p.get("invocation_id")
    if not isinstance(v,str) or not v or len(v)>256 or "/" in v or "\\" in v:raise AntigravityAdapterError("Identité invocation Antigravity invalide.")
    return v
def _cwd(s:MemoryStore,v:object)->None:
    if not isinstance(v,str) or not v:raise AntigravityAdapterError("Répertoire Antigravity absent.")
    try:Path(v).resolve(strict=False).relative_to(s.workspace.project_root.resolve(strict=False))
    except ValueError as exc:raise AntigravityAdapterError("Répertoire Antigravity hors projet.") from exc
def _dossier(s:MemoryStore):return ResumeDossierService(s).compile((ResumeSectionRequirement("working-rules",12,512),ResumeSectionRequirement("current-state",12,512)),{"working-rules":"Mesurer les faits avant toute conclusion.","current-state":"La garde Antigravity attend un acquittement."})
def _ack_tools(s:MemoryStore)->frozenset[str]:return frozenset(("mmu_acknowledge_resume",f"mcp_vera-mmu-{s.identity.project_id}_mmu_acknowledge_resume"))
def _deny(s:MemoryStore)->dict[str,str]:
    rows=s.connection.execute("SELECT capability_id FROM capability_policy WHERE decision = 'ALLOW' ORDER BY capability_id").fetchall();v={str(r["capability_id"]):"antigravity-deny-v1" for r in rows}
    if not v:raise AntigravityAdapterError("Aucune capability ALLOW à stage pour Antigravity.")
    return v
def _object(v:Mapping[str,Any],label:str)->dict[str,Any]:
    if not isinstance(v,Mapping):raise AntigravityAdapterError(f"{label} doit être un objet JSON.")
    try:o=json.loads(json.dumps(dict(v),ensure_ascii=False))
    except (TypeError,ValueError) as exc:raise AntigravityAdapterError(f"{label} non sérialisable.") from exc
    if not isinstance(o,dict):raise AntigravityAdapterError(f"{label} doit être un objet JSON.")
    return o
def _load_json(p:Path,label:str)->dict[str,Any]:
    raw=_read(p)
    if raw is None:return {}
    try:v=json.loads(raw)
    except json.JSONDecodeError as exc:raise AntigravityAdapterError(f"{label} illisible.") from exc
    return _object(v,label)
def _read(p:Path)->str|None:
    if not p.exists():return None
    if p.is_symlink() or not p.is_file():raise AntigravityAdapterError("État Antigravity non régulier.")
    try:return p.read_text(encoding="utf-8")
    except (OSError,UnicodeDecodeError) as exc:raise AntigravityAdapterError("État Antigravity illisible.") from exc
def _parent(p:Path,label:str)->None:
    if p.is_symlink():raise AntigravityAdapterError(f"{label} symlinké refusé.")
    try:p.mkdir(mode=0o700,parents=True,exist_ok=True)
    except OSError as exc:raise AntigravityAdapterError(f"Création {label} impossible.") from exc
    if not p.is_dir() or p.is_symlink():raise AntigravityAdapterError(f"{label} invalide.")
def _json(v:Mapping[str,Any])->str:return json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
def _write(p:Path,text:str,prefix:str)->None:
    _parent(p.parent,"répertoire cible Antigravity");tmp:Path|None=None
    try:
        with NamedTemporaryFile(mode="w",encoding="utf-8",newline="\n",dir=p.parent,prefix=prefix,suffix=".tmp",delete=False) as f:tmp=Path(f.name);f.write(text);f.flush();os.fsync(f.fileno())
        os.chmod(tmp,0o600);os.replace(tmp,p)
    except OSError as exc:
        if tmp is not None:tmp.unlink(missing_ok=True)
        raise AntigravityAdapterError("Écriture atomique Antigravity impossible.") from exc
if __name__=="__main__":raise SystemExit(antigravity_hook_main())
