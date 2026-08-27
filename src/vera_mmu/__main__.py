"""Command-line entry point for VERA-MMU and bounded adapter operations."""
from __future__ import annotations
import argparse
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
from typing import Callable, Sequence
from .identity import ProfileError, load_profile, profile_identity, project_identity
from .migrations import MigrationError
from .runtime import RuntimeLocator
from .project_operations import ProjectOperationError, compile_generation_preview, scan_project
from .store import MemoryStore, StoreError
from .workspace import WorkspaceError, resolve_workspace

_ADAPTERS: dict[str, dict[str, object]] = {
    "claude-code-local": {"coverage":"COMPACTION_AWARE", "runtime":"claude-code-local-runtime.json", "config":".claude/settings.json", "stage":"vera_mmu.claude_code_local:claude_code_local_stage_main", "configure":"vera_mmu.claude_code_local:claude_code_local_config_main"},
    "claude-code-cloud": {"coverage":"CLOUD_STAGED_NOT_LIVE", "runtime":"claude-code-cloud-runtime.json", "config":".claude/settings.json + .mcp.json", "stage":"vera_mmu.claude_code_cloud:claude_code_cloud_stage_main", "configure":"vera_mmu.claude_code_cloud:claude_code_cloud_config_main"},
    "codex": {"coverage":"PARTIAL_LOCAL_TOOLS", "runtime":"codex-runtime.json", "config":".codex/hooks.json + .codex/config.toml", "stage":"vera_mmu.codex_adapter:codex_stage_main", "configure":"vera_mmu.codex_adapter:codex_config_main"},
    "gemini": {"coverage":"TOOL_GUARD_NO_POST_COMPACTION", "runtime":"gemini-cli-runtime.json", "config":".gemini/settings.json", "stage":"vera_mmu.gemini_adapter:gemini_stage_main", "configure":"vera_mmu.gemini_adapter:gemini_config_main"},
    "antigravity": {"coverage":"TURN_GUARD_HARD", "runtime":"antigravity-runtime.json", "config":".antigravity/settings.json", "stage":"vera_mmu.antigravity_adapter:antigravity_stage_main", "configure":"vera_mmu.antigravity_adapter:antigravity_config_main"},
    "generic-mcp": {"coverage":"MCP_ONLY", "runtime":"generic-mcp-runtime.json", "config":".mcp.json", "stage":"vera_mmu.generic_mcp_adapter:generic_mcp_stage_main", "configure":"vera_mmu.generic_mcp_adapter:generic_mcp_config_main"},
}

def build_parser() -> argparse.ArgumentParser:
    parser=argparse.ArgumentParser(prog="vmmu",description="VERA-MMU: identité, validation et opérations d’adapter bornées.")
    sub=parser.add_subparsers(dest="command",required=True)
    for name,help_text in (("identity","Valide un Project Profile et affiche son identité canonique."),("inspect","Valide le profile, workspace et confinement runtime."),("init","Initialise le substrat SQLite lié au profile.")):
        child=sub.add_parser(name,help=help_text);child.add_argument("profile",type=Path,help="Chemin project.yaml.")
    scan=sub.add_parser("scan",help="Observe une arborescence locale sans lire de contenu ni écrire.");scan.add_argument("root",type=Path,help="Racine locale explicitement sélectionnée.")
    generate=sub.add_parser("generate",help="Compile un preview MCP déterministe sans installer.");generate.add_argument("profile",type=Path,help="Chemin project.yaml.");generate.add_argument("--adapter",required=True)
    install=sub.add_parser("install",help="Prévisualise ou applique la configuration project-local d’un adapter.");install.add_argument("profile",type=Path,help="Chemin project.yaml.");install.add_argument("--adapter",required=True);install.add_argument("--apply-project",action="store_true");install.add_argument("--confirm",action="store_true")
    adapter=sub.add_parser("adapter",help="Opérations project-local des adapters VERA.")
    ops=adapter.add_subparsers(dest="adapter_command",required=True)
    ops.add_parser("matrix",help="Affiche la matrice statique des couvertures attestées.")
    doctor=ops.add_parser("doctor",help="Observe un runtime/configuration sans appliquer de changement.");doctor.add_argument("--profile",type=Path,required=True);doctor.add_argument("--adapter",required=True)
    stage=ops.add_parser("stage",help="Stage le runtime de l’adapter seulement après confirmation.");stage.add_argument("--profile",type=Path,required=True);stage.add_argument("--adapter",required=True);stage.add_argument("--confirm",action="store_true")
    config=ops.add_parser("configure",help="Prévisualise ou applique la configuration project-local de l’adapter.");config.add_argument("--profile",type=Path,required=True);config.add_argument("--adapter",required=True);config.add_argument("--apply-project",action="store_true");config.add_argument("--confirm",action="store_true");config.add_argument("--apply-user-scope",action="store_true")
    validate=ops.add_parser("validate",help="Valide profile/workspace et présente la capacité demandée.");validate.add_argument("--profile",type=Path,required=True);validate.add_argument("--adapter",required=True)
    return parser

def _adapter(name:str)->dict[str,object]:
    result=_ADAPTERS.get(name)
    if result is None:raise StoreError(f"Adapter inconnu : {name}.")
    return result

def _call(entry:str,args:list[str])->int:
    module_name,function_name=entry.split(":",1)
    module=__import__(module_name,fromlist=[function_name]);function=getattr(module,function_name)
    if not callable(function):raise StoreError("Entry point d’adapter invalide.")
    return int(function(args))
def _adapter_call_json(entry:str,args:list[str])->tuple[int,dict[str,object]]:
    stream=StringIO()
    with redirect_stdout(stream): code=_call(entry,args)
    try: payload=json.loads(stream.getvalue())
    except json.JSONDecodeError as exc: raise StoreError("Réponse adapter non JSON.") from exc
    if not isinstance(payload,dict): raise StoreError("Réponse adapter non objet.")
    return code,payload

def _doctor(profile_path:Path,name:str)->dict[str,object]:
    adapter=_adapter(name);profile=load_profile(profile_path);workspace=resolve_workspace(profile,profile_path);locator=RuntimeLocator.from_workspace(profile,workspace)
    runtime=locator.runtime_dir/"generated"/str(adapter["runtime"]);config=workspace.project_root/str(adapter["config"])
    if runtime.is_symlink() or config.is_symlink():raise StoreError("Cible doctor symlinkée : refus de diagnostic ambigu.")
    return {"adapter":name,"coverage":adapter["coverage"],"runtime":"RUNTIME_READY" if runtime.is_file() else "RUNTIME_MISSING","runtimePath":str(runtime),"configuration":"CONFIGURED" if config.exists() else "CONFIG_ABSENT","configurationPath":str(config),"host":"NOT_OBSERVED","userScope":"NOT_OBSERVED"}
def main(argv:Sequence[str]|None=None)->int:
    try:
        args=build_parser().parse_args(argv)
        if args.command=="scan":
            payload={"ok":True,"scan":scan_project(args.root).as_dict()}
        elif args.command=="generate":
            profile=load_profile(args.profile)
            with MemoryStore.open(profile,args.profile) as store:payload={"ok":True,"generation":compile_generation_preview(store,args.adapter).as_dict()}
        elif args.command=="install":
            adapter=_adapter(args.adapter);config_args=["--profile",str(args.profile)]+(["--apply-project"] if args.apply_project else [])+(["--confirm"] if args.confirm else [])
            code,adapter_payload=_adapter_call_json(str(adapter["configure"]),config_args)
            if code!=0 or adapter_payload.get("ok") is not True:raise StoreError(str(adapter_payload.get("error","Installation adapter refusée.")))
            payload={"ok":True,"installation":{key:value for key,value in adapter_payload.items() if key!="ok"}}
        elif args.command=="adapter":
            if args.adapter_command=="matrix":payload={"ok":True,"adapters":[{"adapter":name,"coverage":data["coverage"],"config":data["config"],"runtime":data["runtime"]} for name,data in sorted(_ADAPTERS.items())]}
            elif args.adapter_command=="doctor":payload={"ok":True,"doctor":_doctor(args.profile,args.adapter)}
            elif args.adapter_command=="validate":
                adapter=_adapter(args.adapter);profile=load_profile(args.profile);workspace=resolve_workspace(profile,args.profile);payload={"ok":True,"adapter":args.adapter,"coverage":adapter["coverage"],"projectIdentity":project_identity(profile,workspace).as_dict(),"runtime":RuntimeLocator.from_workspace(profile,workspace).as_dict()}
            elif args.adapter_command=="stage":
                adapter=_adapter(args.adapter);stage_args=["--profile",str(args.profile)]+(["--confirm"] if args.confirm else []);return _call(str(adapter["stage"]),stage_args)
            elif args.adapter_command=="configure":
                if args.apply_user_scope:raise StoreError("La voie user-scope ne peut pas être routée par M6 ; utiliser la commande Claude dédiée et deux confirmations explicites.")
                adapter=_adapter(args.adapter);config_args=["--profile",str(args.profile)]+(["--apply-project"] if args.apply_project else [])+(["--confirm"] if args.confirm else []);return _call(str(adapter["configure"]),config_args)
            else:raise StoreError("Opération d’adapter inconnue.")
        else:
            profile=load_profile(args.profile)
            if args.command=="identity":payload={"ok":True,"identity":profile_identity(profile).as_dict()}
            elif args.command=="inspect":
                workspace=resolve_workspace(profile,args.profile);payload={"ok":True,"profile_identity":profile_identity(profile).as_dict(),"project_identity":project_identity(profile,workspace).as_dict(),"workspace":workspace.as_dict(),"runtime":RuntimeLocator.from_workspace(profile,workspace).as_dict()}
            elif args.command=="init":
                with MemoryStore.open(profile,args.profile) as store:payload={"ok":True,"identity":store.identity.as_dict(),"migration_checksums":store.migration_checksums,"metadata":store.metadata()}
            else:raise StoreError("Commande inconnue.")
    except (MigrationError,ProfileError,ProjectOperationError,StoreError,WorkspaceError,ValueError) as exc:
        print(json.dumps({"ok":False,"error":str(exc)},ensure_ascii=False,sort_keys=True));return 2
    print(json.dumps(payload,ensure_ascii=False,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
