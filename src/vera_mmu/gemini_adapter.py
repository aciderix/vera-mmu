"""Gemini CLI adapter with documented lifecycle limits.

Gemini supplies SessionStart and BeforeTool hooks but only advisory PreCompress;
this adapter therefore never claims a post-compaction rearm or durable host support.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile
from typing import Any, Mapping, Sequence

from .lifecycle_adapters import LifecycleAdapterPlan, LifecycleAdapterRegistry, compile_lifecycle_adapter_plan
from .mcp_hooks import MCPHookPlan, MCPHookPlanError, compile_mcp_hook_plan
from .mcp_instructions import MCPInstructions, MCPInstructionsError, compile_mcp_instructions
from .mcp_integration import MCPIntegration, MCPIntegrationError, compile_mcp_integration
from .mcp_manifest import MCPManifest, MCPManifestError, compile_mcp_manifest, verify_mcp_manifest
from .mcp_server import DenyRuntimeAdapter, create_server
from .session_lifecycle import GuardDecision, ResumeDossierService, ResumeGuardService, ResumeSectionRequirement
from .store import MemoryStore, StoreError

GEMINI_FORMAT = "vera-gemini-cli-adapter/v1"
GEMINI_RUNTIME_FORMAT = "vera-gemini-cli-runtime/v1"
GEMINI_HOST_CONFIG_FORMAT = "vera-gemini-cli-host-config/v1"
GEMINI_ADAPTER_ID = "gemini-cli-v1"
GEMINI_ADAPTER_VERSION = "1.0.0"
GEMINI_MAXIMUM_GUARD_MODE = "HARD"
GEMINI_MCP_ENTRYPOINT = "vmmu-gemini-mcp"
GEMINI_HOOK_ENTRYPOINT = "vmmu-gemini-hook"
GEMINI_EVENTS = ("SessionStart", "BeforeTool", "AfterTool", "PreCompress", "SessionEnd")
GEMINI_COVERAGE = "TOOL_GUARD_NO_POST_COMPACTION"

class GeminiAdapterError(StoreError):
    """A Gemini adapter input cannot be accepted safely."""

@dataclass(frozen=True)
class GeminiPlan:
    format: str; project_id: str; mcp_build_hash: str; instructions_hash: str; config_hash: str; hook_plan_hash: str; lifecycle_plan_hash: str; plan_hash: str; json_text: str
@dataclass(frozen=True)
class GeminiStageResult:
    status: str; state_path: Path; plan_hash: str
@dataclass(frozen=True)
class GeminiHostConfigPreview:
    status: str; settings_path: Path; state_path: Path; settings_json_text: str; plan_hash: str; coverage: str
@dataclass(frozen=True)
class GeminiHostConfigApplyResult:
    status: str; settings_path: Path; state_path: Path; plan_hash: str; coverage: str
@dataclass(frozen=True)
class _GeminiRuntime:
    manifest: MCPManifest; instructions: MCPInstructions; lifecycle: LifecycleAdapterPlan; plan: GeminiPlan

class GeminiSessionAdapter:
    adapter_id = GEMINI_ADAPTER_ID; adapter_version = GEMINI_ADAPTER_VERSION; maximum_guard_mode = GEMINI_MAXIMUM_GUARD_MODE
    def __init__(self, store: MemoryStore) -> None: self.store = store
    def session_identity(self) -> str | None:
        row = _read_session(self.store)
        return None if row is None else row["session_id"]

def compile_gemini_plan(store: MemoryStore, manifest: MCPManifest, instructions: MCPInstructions, integration: MCPIntegration, hooks: MCPHookPlan, lifecycle: LifecycleAdapterPlan) -> GeminiPlan:
    if not isinstance(store, MemoryStore): raise GeminiAdapterError("Store invalide pour le plan Gemini.")
    try:
        verify_mcp_manifest(store, manifest)
        expected_i = compile_mcp_instructions(store, manifest)
        expected_c = compile_mcp_integration(store, manifest, expected_i)
        expected_h = compile_mcp_hook_plan(store, manifest, expected_i, expected_c)
        expected_l = compile_lifecycle_adapter_plan(store, manifest, adapter_id=GEMINI_ADAPTER_ID, adapter_version=GEMINI_ADAPTER_VERSION, maximum_guard_mode=GEMINI_MAXIMUM_GUARD_MODE)
    except (MCPManifestError, MCPInstructionsError, MCPIntegrationError, MCPHookPlanError, StoreError) as exc: raise GeminiAdapterError("Snapshots invalides pour Gemini.") from exc
    if (instructions, integration, hooks, lifecycle) != (expected_i, expected_c, expected_h, expected_l): raise GeminiAdapterError("Snapshot Gemini périmé, altéré ou étranger.")
    server_id, profile_arg = _server_identity(integration)
    profile = _profile_path(store, profile_arg)
    payload = {"gemini": {"coverage": GEMINI_COVERAGE, "hooks": {"events": list(GEMINI_EVENTS), "projectTrust": "HOST_FINGERPRINT_REQUIRED"}, "mcpServer": {"id": server_id, "command": GEMINI_MCP_ENTRYPOINT, "args": ["--profile", str(profile)], "cwd": str(store.workspace.project_root.resolve(strict=False)), "includeTools": ["mmu_acknowledge_resume"], "trust": False}, "runtime": {"network": "FORBIDDEN", "provider": "PREINSTALLED_VERA"}}}
    text = _json(payload)
    return GeminiPlan(GEMINI_FORMAT, store.identity.project_id, manifest.mcp_build_hash, instructions.instructions_hash, integration.config_hash, hooks.hook_plan_hash, lifecycle.lifecycle_plan_hash, sha256(text.encode()).hexdigest(), text)

def stage_gemini_runtime(store: MemoryStore, manifest: MCPManifest, instructions: MCPInstructions, integration: MCPIntegration, hooks: MCPHookPlan, lifecycle: LifecycleAdapterPlan, plan: GeminiPlan, *, confirm: bool) -> GeminiStageResult:
    if confirm is not True: raise GeminiAdapterError("Staging Gemini refusé sans confirmation explicite.")
    if plan != compile_gemini_plan(store, manifest, instructions, integration, hooks, lifecycle): raise GeminiAdapterError("Plan Gemini périmé, altéré ou étranger.")
    target = _runtime_path(store, create=True); text = _runtime_text(plan, manifest); current = _read(target)
    if current is not None and current != text: raise GeminiAdapterError("État runtime Gemini divergent : refus sans écriture.")
    if current == text: return GeminiStageResult("UNCHANGED", target, plan.plan_hash)
    _write(target, text, ".vera-gemini-runtime-"); return GeminiStageResult("STAGED", target, plan.plan_hash)

def preview_gemini_host_config(store: MemoryStore, existing_settings: Mapping[str, Any]) -> GeminiHostConfigPreview:
    settings = _object(existing_settings, "settings Gemini")
    runtime = _load_runtime(store); desired = _hook_config(runtime.plan); server = _mcp_server(runtime.plan)
    merged, _ = _merge_hooks(settings, desired)
    servers = merged.get("mcpServers", {})
    if not isinstance(servers, dict): raise GeminiAdapterError("mcpServers Gemini doit être un objet.")
    current = servers.get(server["id"]); entry = {k: v for k, v in server.items() if k != "id"}
    if current is not None and current != entry: raise GeminiAdapterError("Conflit : serveur MCP VERA Gemini divergent.")
    if current != entry:
        out = dict(servers); out[server["id"]] = entry; merged["mcpServers"] = out
    text = _json(merged); h = sha256(text.encode()).hexdigest()
    return GeminiHostConfigPreview("PREVIEW", _settings_path(store, create=False), _host_state_path(store, create=False), text, h, GEMINI_COVERAGE)

def apply_gemini_host_config(store: MemoryStore, preview: GeminiHostConfigPreview, *, confirm: bool) -> GeminiHostConfigApplyResult:
    if confirm is not True: raise GeminiAdapterError("Application Gemini refusée sans confirmation explicite.")
    if not isinstance(preview, GeminiHostConfigPreview) or preview.coverage != GEMINI_COVERAGE: raise GeminiAdapterError("Preview Gemini invalide.")
    settings = _settings_path(store, create=False); state = _host_state_path(store, create=False)
    expected = preview_gemini_host_config(store, _load_json(settings, "settings Gemini"))
    if preview != expected: raise GeminiAdapterError("Preview Gemini périmé, altéré ou divergent.")
    receipt = _json({"geminiHostConfig": {"format": GEMINI_HOST_CONFIG_FORMAT, "planHash": preview.plan_hash, "settingsSha256": sha256(preview.settings_json_text.encode()).hexdigest()}})
    existing_receipt = _read(state)
    if existing_receipt is not None and existing_receipt != receipt: raise GeminiAdapterError("État configuration Gemini divergent : refus sans écriture.")
    current = _read(settings)
    if current != preview.settings_json_text: _write(settings, preview.settings_json_text, ".vera-gemini-settings-")
    if existing_receipt != receipt: _write(state, receipt, ".vera-gemini-host-")
    return GeminiHostConfigApplyResult("UNCHANGED" if current == preview.settings_json_text and existing_receipt == receipt else "APPLIED_PROJECT_LOCAL", settings, state, preview.plan_hash, GEMINI_COVERAGE)

def handle_gemini_hook(store: MemoryStore, lifecycle: LifecycleAdapterPlan, plan: GeminiPlan, event: str, payload: Mapping[str, object]) -> dict[str, object]:
    runtime = _load_runtime(store)
    if lifecycle != runtime.lifecycle or plan != runtime.plan: raise GeminiAdapterError("Lifecycle Gemini étranger au runtime staged.")
    if event not in GEMINI_EVENTS or not isinstance(payload, Mapping): raise GeminiAdapterError("Événement ou payload Gemini invalide.")
    session = _session_id(payload); _cwd(store, payload.get("cwd")); guard = ResumeGuardService(store)
    if event == "SessionStart":
        _claim_session(store, session); dossier = _dossier(store); source = payload.get("source")
        guard.arm(session, GEMINI_ADAPTER_ID, "RESUME" if source == "resume" else "SESSION_OPEN", dossier, mode="HARD")
        return {"hookSpecificOutput": {"additionalContext": "Resume Dossier VERA Gemini — lire et acquitter via mmu_acknowledge_resume :\n" + dossier.json_text}}
    if _read_session(store) != {"project_id": store.identity.project_id, "session_id": session}: raise GeminiAdapterError("Session Gemini non liée au runtime courant.")
    if event == "BeforeTool":
        tool = payload.get("tool_name")
        if not isinstance(tool, str): raise GeminiAdapterError("BeforeTool Gemini sans nom de tool.")
        if tool in _ack_tools(store): return {}
        outcome = guard.precheck(session, GEMINI_ADAPTER_ID)
        return {"decision": "deny", "reason": outcome.reason} if outcome.decision == GuardDecision.DENY else ({"systemMessage": outcome.reason} if outcome.decision == GuardDecision.ALLOW_WITH_NOTICE else {})
    if event == "AfterTool":
        outcome = guard.precheck(session, GEMINI_ADAPTER_ID); return {"systemMessage": outcome.reason} if outcome.decision != GuardDecision.ALLOW else {}
    if event == "PreCompress": return {"systemMessage": "VERA enregistre que PreCompress Gemini est advisory : il ne peut pas réarmer la garde sans événement post-compaction."}
    _release_session(store, session); return {}

def gemini_stage_main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Staging runtime Gemini VERA-MMU"); parser.add_argument("--profile", type=Path, required=True); parser.add_argument("--confirm", action="store_true"); args = parser.parse_args(argv)
    try:
        from .identity import load_profile
        with MemoryStore.open(load_profile(args.profile), args.profile) as store:
            manifest = compile_mcp_manifest(store, adapter_bindings=_deny_bindings(store)); ins = compile_mcp_instructions(store, manifest); integ = compile_mcp_integration(store, manifest, ins); hooks = compile_mcp_hook_plan(store, manifest, ins, integ); life = compile_lifecycle_adapter_plan(store, manifest, adapter_id=GEMINI_ADAPTER_ID, adapter_version=GEMINI_ADAPTER_VERSION, maximum_guard_mode=GEMINI_MAXIMUM_GUARD_MODE); result = stage_gemini_runtime(store, manifest, ins, integ, hooks, life, compile_gemini_plan(store, manifest, ins, integ, hooks, life), confirm=args.confirm)
    except StoreError as exc: print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)); return 2
    print(json.dumps({"ok": True, "status": result.status, "planHash": result.plan_hash, "statePath": str(result.state_path)}, ensure_ascii=False)); return 0

def gemini_hook_main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hook lifecycle Gemini VERA-MMU"); parser.add_argument("--profile", type=Path, required=True); parser.add_argument("--event", choices=GEMINI_EVENTS, required=True); args = parser.parse_args(argv)
    try:
        payload = json.loads(sys.stdin.read())
        if not isinstance(payload, dict): raise GeminiAdapterError("Payload JSON Gemini requis.")
        from .identity import load_profile
        with MemoryStore.open(load_profile(args.profile), args.profile) as store:
            runtime = _load_runtime(store); result = handle_gemini_hook(store, runtime.lifecycle, runtime.plan, args.event, payload)
    except (StoreError, json.JSONDecodeError) as exc: print(json.dumps({"decision": "deny", "reason": str(exc)}, ensure_ascii=False)); return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True)); return 0

def gemini_mcp_main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Serveur MCP lifecycle Gemini VERA-MMU"); parser.add_argument("--profile", type=Path, required=True); args = parser.parse_args(argv)
    from .identity import load_profile
    with MemoryStore.open(load_profile(args.profile), args.profile) as store:
        runtime = _load_runtime(store); create_server(store, runtime_adapter=DenyRuntimeAdapter(), manifest=runtime.manifest, instructions=runtime.instructions, lifecycle_adapter_registry=LifecycleAdapterRegistry((GeminiSessionAdapter(store),)), lifecycle_adapter_plan=runtime.lifecycle, actor="vera-gemini-cli").run("stdio")

def gemini_config_main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Configuration Gemini project-local VERA-MMU"); parser.add_argument("--profile", type=Path, required=True); parser.add_argument("--apply-project", action="store_true"); parser.add_argument("--confirm", action="store_true"); args = parser.parse_args(argv)
    try:
        from .identity import load_profile
        with MemoryStore.open(load_profile(args.profile), args.profile) as store:
            preview = preview_gemini_host_config(store, _load_json(_settings_path(store, create=False), "settings Gemini")); result = apply_gemini_host_config(store, preview, confirm=args.confirm) if args.apply_project else preview
    except StoreError as exc: print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)); return 2
    print(json.dumps({"ok": True, "status": result.status, "planHash": result.plan_hash, "settingsPath": str(result.settings_path), "coverage": result.coverage}, ensure_ascii=False)); return 0

def _server_identity(integration: MCPIntegration) -> tuple[str, str]:
    try:
        servers = json.loads(integration.json_text)["mcpServers"]; key, server = next(iter(servers.items())); args = server["args"]
    except (KeyError, TypeError, StopIteration, json.JSONDecodeError) as exc: raise GeminiAdapterError("Configuration MCP attestée illisible.") from exc
    if not isinstance(servers, dict) or len(servers) != 1 or not isinstance(key, str) or not isinstance(args, list) or len(args) != 2 or args[0] != "--profile" or not isinstance(args[1], str): raise GeminiAdapterError("Identité MCP attestée invalide.")
    return key, args[1]
def _profile_path(store: MemoryStore, arg: str) -> Path:
    value = arg.removeprefix("${CLAUDE_PROJECT_DIR:-.}/"); path = Path(value)
    if path.is_absolute() or ".." in path.parts: raise GeminiAdapterError("Profil Gemini hors projet.")
    target = (store.workspace.project_root / path).resolve(strict=False)
    try: target.relative_to(store.workspace.project_root.resolve(strict=False))
    except ValueError as exc: raise GeminiAdapterError("Profil Gemini hors projet.") from exc
    return target
def _plan_payload(plan: GeminiPlan) -> dict[str, Any]:
    if not isinstance(plan, GeminiPlan) or plan.plan_hash != sha256(plan.json_text.encode()).hexdigest(): raise GeminiAdapterError("Plan Gemini altéré.")
    try: value = json.loads(plan.json_text)["gemini"]
    except (KeyError, TypeError, json.JSONDecodeError) as exc: raise GeminiAdapterError("Plan Gemini illisible.") from exc
    if not isinstance(value, dict): raise GeminiAdapterError("Plan Gemini hors format fermé.")
    return value
def _mcp_server(plan: GeminiPlan) -> dict[str, object]:
    value = _plan_payload(plan).get("mcpServer")
    if not isinstance(value, dict) or value.get("command") != GEMINI_MCP_ENTRYPOINT or value.get("trust") is not False or value.get("includeTools") != ["mmu_acknowledge_resume"]: raise GeminiAdapterError("Serveur Gemini attesté invalide.")
    if not isinstance(value.get("id"), str) or not isinstance(value.get("args"), list) or not isinstance(value.get("cwd"), str): raise GeminiAdapterError("Serveur Gemini attesté invalide.")
    return dict(value)
def _hook_config(plan: GeminiPlan) -> dict[str, list[dict[str, object]]]:
    args = _mcp_server(plan)["args"]
    if not isinstance(args, list) or len(args) != 2 or not isinstance(args[1], str): raise GeminiAdapterError("Profil hook Gemini invalide.")
    def group(event: str, matcher: str | None = None) -> dict[str, object]:
        item: dict[str, object] = {"hooks": [{"name": "vera-gemini-lifecycle", "type": "command", "command": f'{GEMINI_HOOK_ENTRYPOINT} --profile {json.dumps(args[1])} --event {event}', "timeout": 10000}]}
        if matcher is not None: item["matcher"] = matcher
        return item
    return {"SessionStart":[group("SessionStart", "*")], "BeforeTool":[group("BeforeTool", ".*")], "AfterTool":[group("AfterTool", ".*")], "PreCompress":[group("PreCompress", "*")], "SessionEnd":[group("SessionEnd", "*")]}
def _merge_hooks(existing: dict[str, Any], desired: Mapping[str, list[dict[str, object]]]) -> tuple[dict[str, Any], bool]:
    old = existing.get("hooks", {})
    if not isinstance(old, dict): raise GeminiAdapterError("hooks Gemini doit être un objet.")
    new = {k: list(v) if isinstance(v, list) else v for k,v in old.items()}; changed = False
    for event, groups in desired.items():
        current = new.get(event, [])
        if not isinstance(current, list): raise GeminiAdapterError("Événement hooks Gemini doit être une liste.")
        if any(_is_vera(item) and item not in groups for item in current): raise GeminiAdapterError("Conflit : hook lifecycle VERA Gemini divergent.")
        add = [item for item in groups if item not in current]
        if add: new[event] = [*current, *add]; changed = True
    result = dict(existing)
    if changed: result["hooks"] = new
    return result, changed
def _is_vera(group: object) -> bool:
    return isinstance(group, dict) and isinstance(group.get("hooks"), list) and any(isinstance(v,dict) and isinstance(v.get("command"),str) and v["command"].startswith(GEMINI_HOOK_ENTRYPOINT) for v in group["hooks"])
def _runtime_path(store: MemoryStore, *, create: bool) -> Path:
    target = store.locator.runtime_dir / "generated" / "gemini-cli-runtime.json"
    if target.is_symlink(): raise GeminiAdapterError("Runtime Gemini symlinké refusé.")
    if create: _parent(target.parent, "runtime Gemini")
    return target
def _runtime_text(plan: GeminiPlan, manifest: MCPManifest) -> str:
    bindings = [{"capability_id": c.capability_id, "adapter_id": c.adapter_id} for c in manifest.capabilities]
    return _json({"geminiRuntime":{"format":GEMINI_RUNTIME_FORMAT,"plan":_plan_payload(plan),"planHash":plan.plan_hash,"adapterBindings":bindings}})
def _load_runtime(store: MemoryStore) -> _GeminiRuntime:
    raw = _read(_runtime_path(store, create=False))
    if raw is None: raise GeminiAdapterError("Adapter Gemini non staged : état attesté absent.")
    try:
        item = json.loads(raw)["geminiRuntime"]; bindings={str(x["capability_id"]):str(x["adapter_id"]) for x in item["adapterBindings"]}; planhash=item["planHash"]; payload=item["plan"]
        if item.get("format") != GEMINI_RUNTIME_FORMAT or not bindings or len(bindings) != len(item["adapterBindings"]): raise ValueError("format")
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc: raise GeminiAdapterError("Runtime Gemini hors format fermé.") from exc
    manifest=compile_mcp_manifest(store, adapter_bindings=bindings); ins=compile_mcp_instructions(store, manifest); integ=compile_mcp_integration(store,manifest,ins); hooks=compile_mcp_hook_plan(store,manifest,ins,integ); life=compile_lifecycle_adapter_plan(store,manifest,adapter_id=GEMINI_ADAPTER_ID,adapter_version=GEMINI_ADAPTER_VERSION,maximum_guard_mode=GEMINI_MAXIMUM_GUARD_MODE); plan=compile_gemini_plan(store,manifest,ins,integ,hooks,life)
    if plan.plan_hash != planhash or payload != json.loads(plan.json_text)["gemini"]: raise GeminiAdapterError("Runtime Gemini périmé ou altéré.")
    return _GeminiRuntime(manifest,ins,life,plan)
def _settings_path(store: MemoryStore, *, create: bool) -> Path:
    directory=store.workspace.project_root/".gemini"
    if directory.is_symlink(): raise GeminiAdapterError("Répertoire .gemini symlinké refusé.")
    if create: _parent(directory,"répertoire .gemini")
    elif directory.exists() and not directory.is_dir(): raise GeminiAdapterError("Répertoire .gemini non régulier.")
    target=directory/"settings.json"
    if target.is_symlink(): raise GeminiAdapterError("settings Gemini symlinké refusé.")
    return target
def _host_state_path(store: MemoryStore, *, create: bool) -> Path:
    target=store.locator.runtime_dir/"generated"/"gemini-cli-host-config.json"
    if target.is_symlink(): raise GeminiAdapterError("État Gemini symlinké refusé.")
    if create: _parent(target.parent,"runtime Gemini")
    return target
def _session_path(store: MemoryStore) -> Path:
    target=store.locator.runtime_dir/"lifecycle"/"gemini-cli-session.json"; _parent(target.parent,"lifecycle Gemini")
    if target.is_symlink(): raise GeminiAdapterError("Session Gemini symlinkée refusée.")
    return target
def _read_session(store: MemoryStore) -> dict[str,str]|None:
    raw=_read(_session_path(store))
    if raw is None:return None
    try:v=json.loads(raw)
    except json.JSONDecodeError as exc: raise GeminiAdapterError("Session Gemini illisible.") from exc
    if not isinstance(v,dict) or set(v)!={"project_id","session_id"} or v.get("project_id")!=store.identity.project_id or not isinstance(v.get("session_id"),str):raise GeminiAdapterError("Session Gemini invalide.")
    return {"project_id":store.identity.project_id,"session_id":v["session_id"]}
def _claim_session(store:MemoryStore,session:str)->None:
    existing=_read_session(store); value={"project_id":store.identity.project_id,"session_id":session}
    if existing is not None and existing != value:raise GeminiAdapterError("Conflit : une autre session Gemini est active.")
    if existing is None:_write(_session_path(store),_json(value),".vera-gemini-session-")
def _release_session(store:MemoryStore,session:str)->None:
    path=_session_path(store); item=_read_session(store)
    if item is not None and item["session_id"]==session:path.unlink()
def _session_id(payload:Mapping[str,object])->str:
    value=payload.get("session_id")
    if not isinstance(value,str) or not value or len(value)>256 or "/" in value or "\\" in value:raise GeminiAdapterError("Identité session Gemini invalide.")
    return value
def _cwd(store:MemoryStore,value:object)->None:
    if not isinstance(value,str) or not value:raise GeminiAdapterError("Répertoire courant Gemini absent.")
    try:Path(value).resolve(strict=False).relative_to(store.workspace.project_root.resolve(strict=False))
    except ValueError as exc:raise GeminiAdapterError("Répertoire Gemini hors projet.") from exc
def _dossier(store:MemoryStore):return ResumeDossierService(store).compile((ResumeSectionRequirement("working-rules",12,512),ResumeSectionRequirement("current-state",12,512)),{"working-rules":"Mesurer les faits avant toute conclusion.","current-state":"La garde Gemini attend un acquittement."})
def _ack_tools(store:MemoryStore)->frozenset[str]:return frozenset(("mmu_acknowledge_resume",f"mcp_vera-mmu-{store.identity.project_id}_mmu_acknowledge_resume"))
def _deny_bindings(store:MemoryStore)->dict[str,str]:
    rows=store.connection.execute("SELECT capability_id FROM capability_policy WHERE decision = 'ALLOW' ORDER BY capability_id").fetchall(); value={str(r["capability_id"]):"gemini-deny-v1" for r in rows}
    if not value:raise GeminiAdapterError("Aucune capability ALLOW à stage pour Gemini.")
    return value
def _object(value:Mapping[str,Any],label:str)->dict[str,Any]:
    if not isinstance(value,Mapping):raise GeminiAdapterError(f"{label} doit être un objet JSON.")
    try:out=json.loads(json.dumps(dict(value),ensure_ascii=False))
    except (TypeError,ValueError) as exc:raise GeminiAdapterError(f"{label} non sérialisable.") from exc
    if not isinstance(out,dict):raise GeminiAdapterError(f"{label} doit être un objet JSON.")
    return out
def _load_json(path:Path,label:str)->dict[str,Any]:
    raw=_read(path)
    if raw is None:return {}
    try:value=json.loads(raw)
    except json.JSONDecodeError as exc:raise GeminiAdapterError(f"{label} illisible.") from exc
    return _object(value,label)
def _read(path:Path)->str|None:
    if not path.exists():return None
    if path.is_symlink() or not path.is_file():raise GeminiAdapterError("État Gemini non régulier.")
    try:return path.read_text(encoding="utf-8")
    except (OSError,UnicodeDecodeError) as exc:raise GeminiAdapterError("État Gemini illisible.") from exc
def _parent(path:Path,label:str)->None:
    if path.is_symlink():raise GeminiAdapterError(f"{label} symlinké refusé.")
    try:path.mkdir(mode=0o700,parents=True,exist_ok=True)
    except OSError as exc:raise GeminiAdapterError(f"Création {label} impossible.") from exc
    if not path.is_dir() or path.is_symlink():raise GeminiAdapterError(f"{label} invalide.")
def _json(value:Mapping[str,Any])->str:return json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
def _write(path:Path,text:str,prefix:str)->None:
    _parent(path.parent,"répertoire cible Gemini"); temp:Path|None=None
    try:
        with NamedTemporaryFile(mode="w",encoding="utf-8",newline="\n",dir=path.parent,prefix=prefix,suffix=".tmp",delete=False) as h:temp=Path(h.name);h.write(text);h.flush();os.fsync(h.fileno())
        os.chmod(temp,0o600);os.replace(temp,path)
    except OSError as exc:
        if temp is not None:temp.unlink(missing_ok=True)
        raise GeminiAdapterError("Écriture atomique Gemini impossible.") from exc
if __name__ == "__main__":raise SystemExit(gemini_hook_main())
