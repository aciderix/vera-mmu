"""Command-line entry point for VERA-MMU and bounded adapter operations."""
from __future__ import annotations
import argparse
from dataclasses import asdict
import json
from pathlib import Path
from typing import Sequence
from .adapter_catalog import ADAPTER_CATALOG, adapter_spec, call_adapter, call_adapter_json
from .bundles import BundleService, restore_bundle
from .coverage_report import compile_coverage_report
from .doctor import diagnose_project
from .documentation_generator import compile_project_documentation
from .identity import ProfileError, load_profile, profile_identity, project_identity
from .memory_sync import automatic_memory_sync
from .migrations import MigrationError
from .project_import import apply_project_document_import, preview_project_document_import
from .read_api import ReadService
from .runtime import RuntimeLocator
from .project_operations import ProjectOperationError, compile_generation_preview, scan_project
from .project_bootstrap import ProjectBootstrapError, apply_project_initialization, preview_project_initialization
from .store import MemoryStore, StoreError
from .workspace import WorkspaceError, resolve_workspace


def build_parser() -> argparse.ArgumentParser:
    parser=argparse.ArgumentParser(prog="vmmu",description="VERA-MMU: identité, validation et opérations d’adapter bornées.")
    sub=parser.add_subparsers(dest="command",required=True)
    for name,help_text in (("identity","Valide un Project Profile et affiche son identité canonique."),("inspect","Valide le profile, workspace et confinement runtime."),("init","Initialise le substrat SQLite lié au profile.")):
        child=sub.add_parser(name,help=help_text);child.add_argument("profile",type=Path,help="Chemin project.yaml.")
    scan=sub.add_parser("scan",help="Observe une arborescence locale sans lire de contenu ni écrire.");scan.add_argument("root",type=Path,help="Racine locale explicitement sélectionnée.")
    generate=sub.add_parser("generate",help="Compile un preview MCP déterministe sans installer.");generate.add_argument("profile",type=Path,help="Chemin project.yaml.");generate.add_argument("--adapter",required=True)
    install=sub.add_parser("install",help="Prévisualise ou applique la configuration project-local d’un adapter.");install.add_argument("profile",type=Path,help="Chemin project.yaml.");install.add_argument("--adapter",required=True);install.add_argument("--apply-project",action="store_true");install.add_argument("--confirm",action="store_true")
    bootstrap=sub.add_parser("init-project",help="Prévisualise ou initialise les fichiers VERA dans un projet choisi.");bootstrap.add_argument("root",type=Path,help="Racine locale du projet.");bootstrap.add_argument("--template",required=True);bootstrap.add_argument("--project-id",required=True);bootstrap.add_argument("--project-name",required=True);bootstrap.add_argument("--apply",action="store_true");bootstrap.add_argument("--confirm",action="store_true")
    sync=sub.add_parser("memory-sync",help="Synchronise seulement la mémoire VERA selon sa policy project-local.");sync.add_argument("profile",type=Path,help="Chemin project.yaml.")
    doctor=sub.add_parser("doctor",help="Diagnostique sans mutation le profile, runtime, SQLite, catalogues et transports VERA.");doctor.add_argument("profile",type=Path,help="Chemin project.yaml.")
    coverage=sub.add_parser("coverage",help="Compile le rapport de couverture VERA dérivé, sans mutation.");coverage.add_argument("profile",type=Path,help="Chemin project.yaml.")
    documentation=sub.add_parser("documentation",help="Compile la documentation VERA dérivée, sans mutation.");documentation.add_argument("profile",type=Path,help="Chemin project.yaml.")
    vcs_status=sub.add_parser("vcs-status",help="Observe le statut VCS project-local sans lancer de commande ni écrire.");vcs_status.add_argument("profile",type=Path,help="Chemin project.yaml.")
    boot=sub.add_parser("boot",help="Lit l’état de démarrage VERA lié au profile sans armer ni modifier la reprise.");boot.add_argument("profile",type=Path,help="Chemin project.yaml.")
    find=sub.add_parser("find",help="Trouve des références VERA par titre, sans retourner de contenu.");find.add_argument("profile",type=Path,help="Chemin project.yaml.");find.add_argument("--query",required=True);find.add_argument("--resource",action="append",dest="resources")
    read=sub.add_parser("read",help="Lit une ressource VERA exacte par adresse canonique.");read.add_argument("profile",type=Path,help="Chemin project.yaml.");read.add_argument("address")
    read_batch=sub.add_parser("read-batch",help="Lit un batch borné d’adresses VERA exactes.");read_batch.add_argument("profile",type=Path,help="Chemin project.yaml.");read_batch.add_argument("--address",action="append",required=True,dest="addresses")
    related=sub.add_parser("related",help="Parcourt un voisinage relationnel VERA borné depuis une entité exacte.");related.add_argument("profile",type=Path,help="Chemin project.yaml.");related.add_argument("address");related.add_argument("--direction",choices=("INBOUND","OUTBOUND","BOTH"),default="BOTH");related.add_argument("--max-depth",type=int,default=1);related.add_argument("--max-nodes",type=int,default=20)
    executions=sub.add_parser("list-executions",help="Liste un historique d’executions VERA compact et borné.");executions.add_argument("profile",type=Path,help="Chemin project.yaml.");executions.add_argument("--max-items",type=int,default=20)
    evidence=sub.add_parser("list-evidence",help="Liste un historique d’evidences VERA compact et borné.");evidence.add_argument("profile",type=Path,help="Chemin project.yaml.");evidence.add_argument("--max-items",type=int,default=20)
    get_front=sub.add_parser("get-front",help="Lit le Front courant du projet sans accepter d’identifiant client.");get_front.add_argument("profile",type=Path,help="Chemin project.yaml.")
    get_handoff=sub.add_parser("get-handoff",help="Lit le dernier handoff vérifié du projet sans accepter d’identifiant client.");get_handoff.add_argument("profile",type=Path,help="Chemin project.yaml.")
    export=sub.add_parser("bundle-export",help="Exporte un bundle VERA sous le runtime project-local après confirmation.");export.add_argument("profile",type=Path,help="Chemin project.yaml.");export.add_argument("--bundle-id",required=True);export.add_argument("--confirm",action="store_true")
    restore=sub.add_parser("bundle-restore",help="Restaure un bundle vérifié vers une cible VERA vide et de même identité.");restore.add_argument("profile",type=Path,help="Chemin project.yaml cible.");restore.add_argument("--bundle",type=Path,required=True,help="Archive ZIP VERA explicitement sélectionnée.");restore.add_argument("--confirm",action="store_true")
    project_import=sub.add_parser("project-import",help="Prévisualise ou importe explicitement des documents locaux comme observations provenancées.");project_import.add_argument("profile",type=Path,help="Chemin project.yaml.");project_import.add_argument("--document",action="append",required=True,help="Chemin relatif d’un document depuis une racine workspace.");project_import.add_argument("--batch-id",required=True);project_import.add_argument("--knowledge-type-id",required=True);project_import.add_argument("--knowledge-type-label",required=True);project_import.add_argument("--apply",action="store_true");project_import.add_argument("--confirm",action="store_true")
    adapter=sub.add_parser("adapter",help="Opérations project-local des adapters VERA.")
    ops=adapter.add_subparsers(dest="adapter_command",required=True)
    ops.add_parser("matrix",help="Affiche la matrice statique des couvertures attestées.")
    doctor=ops.add_parser("doctor",help="Observe un runtime/configuration sans appliquer de changement.");doctor.add_argument("--profile",type=Path,required=True);doctor.add_argument("--adapter",required=True)
    stage=ops.add_parser("stage",help="Stage le runtime de l’adapter seulement après confirmation.");stage.add_argument("--profile",type=Path,required=True);stage.add_argument("--adapter",required=True);stage.add_argument("--confirm",action="store_true")
    config=ops.add_parser("configure",help="Prévisualise ou applique la configuration project-local de l’adapter.");config.add_argument("--profile",type=Path,required=True);config.add_argument("--adapter",required=True);config.add_argument("--apply-project",action="store_true");config.add_argument("--confirm",action="store_true");config.add_argument("--apply-user-scope",action="store_true")
    validate=ops.add_parser("validate",help="Valide profile/workspace et présente la capacité demandée.");validate.add_argument("--profile",type=Path,required=True);validate.add_argument("--adapter",required=True)
    return parser


def _doctor(profile_path:Path,name:str)->dict[str,object]:
    adapter=adapter_spec(name);profile=load_profile(profile_path);workspace=resolve_workspace(profile,profile_path);locator=RuntimeLocator.from_workspace(profile,workspace)
    runtime=locator.runtime_dir/"generated"/adapter.runtime;config=workspace.project_root/adapter.config
    if runtime.is_symlink() or config.is_symlink():raise StoreError("Cible doctor symlinkée : refus de diagnostic ambigu.")
    return {"adapter":name,"coverage":adapter.coverage,"runtime":"RUNTIME_READY" if runtime.is_file() else "RUNTIME_MISSING","runtimePath":str(runtime),"configuration":"CONFIGURED" if config.exists() else "CONFIG_ABSENT","configurationPath":str(config),"host":"NOT_OBSERVED","userScope":"NOT_OBSERVED"}


def _project_preview_payload(preview: object) -> dict[str, object]:
    value=asdict(preview)
    value["documents"]= [{key:item[key] for key in ("path","sha256","line_count")} for item in value["documents"]]
    return value


def _project_result_payload(result: object) -> dict[str, object]:
    return asdict(result)


def main(argv:Sequence[str]|None=None)->int:
    try:
        args=build_parser().parse_args(argv)
        if args.command=="init-project":
            preview=preview_project_initialization(args.root,template=args.template,project_id=args.project_id,project_name=args.project_name)
            result=apply_project_initialization(args.root,preview,confirm=args.confirm) if args.apply else preview
            payload={"ok":True,"initialization":result.as_dict()}
        elif args.command=="scan":
            payload={"ok":True,"scan":scan_project(args.root).as_dict()}
        elif args.command=="memory-sync":
            profile=load_profile(args.profile)
            with MemoryStore.open(profile,args.profile) as store:payload={"ok":True,"memory_sync":automatic_memory_sync(store,"CLI_MEMORY_SYNC")}
        elif args.command=="vcs-status":
            profile=load_profile(args.profile)
            with MemoryStore.open(profile,args.profile) as store:payload={"ok":True,"vcs":ReadService(store).vcs_status()}
        elif args.command=="coverage":
            profile=load_profile(args.profile)
            with MemoryStore.open(profile,args.profile) as store:payload={"ok":True,"coverage":compile_coverage_report(store).as_dict()}
        elif args.command=="documentation":
            profile=load_profile(args.profile)
            with MemoryStore.open(profile,args.profile) as store:
                documentation=compile_project_documentation(store,str(args.profile))
                payload={"ok":True,"documentation":{"project_identity":documentation.project_identity,"documents":documentation.documents,"bundle_hash":documentation.bundle_hash}}
        elif args.command=="doctor":
            report=diagnose_project(args.profile);payload={"ok":report.status=="PASS","doctor":report.as_dict()}
            if report.status!="PASS":
                print(json.dumps(payload,ensure_ascii=False,sort_keys=True));return 2
        elif args.command in {"boot","find","read","read-batch","related","list-executions","list-evidence","get-front","get-handoff"}:
            profile=load_profile(args.profile)
            with MemoryStore.open(profile,args.profile) as store:
                reader=ReadService(store)
                if args.command=="boot":payload={"ok":True,"boot":reader.boot()}
                elif args.command=="find":payload={"ok":True,"find":reader.find(args.query,resource_types=args.resources)}
                elif args.command=="read":payload={"ok":True,"read":reader.read(args.address)}
                elif args.command=="read-batch":payload={"ok":True,"read_batch":reader.read_batch(args.addresses)}
                elif args.command=="related":payload={"ok":True,"related":reader.related(args.address,direction=args.direction,max_depth=args.max_depth,max_nodes=args.max_nodes)}
                elif args.command=="list-executions":payload={"ok":True,"executions":reader.execution_history(max_items=args.max_items)}
                elif args.command=="list-evidence":payload={"ok":True,"evidence":reader.evidence_history(max_items=args.max_items)}
                elif args.command=="get-front":payload={"ok":True,"front":reader.current_front()}
                else:payload={"ok":True,"handoff":reader.latest_handoff()}
        elif args.command=="bundle-export":
            profile=load_profile(args.profile)
            with MemoryStore.open(profile,args.profile) as store:payload={"ok":True,"bundle":asdict(BundleService(store).export(args.bundle_id,confirm=args.confirm))}
        elif args.command=="bundle-restore":
            payload={"ok":True,"bundle_restore":asdict(restore_bundle(args.bundle,args.profile,confirm=args.confirm))}
        elif args.command=="project-import":
            profile=load_profile(args.profile)
            with MemoryStore.open(profile,args.profile) as store:
                preview=preview_project_document_import(store,tuple(args.document),batch_id=args.batch_id,knowledge_type_id=args.knowledge_type_id,knowledge_type_label=args.knowledge_type_label,actor="vera-cli")
                if args.apply:
                    result=apply_project_document_import(store,preview,confirm=args.confirm)
                    payload={"ok":True,"project_import":_project_result_payload(result)}
                else:payload={"ok":True,"preview":_project_preview_payload(preview)}
        elif args.command=="generate":
            profile=load_profile(args.profile)
            with MemoryStore.open(profile,args.profile) as store:payload={"ok":True,"generation":compile_generation_preview(store,args.adapter).as_dict()}
        elif args.command=="install":
            adapter=adapter_spec(args.adapter);config_args=["--profile",str(args.profile)]+(["--apply-project"] if args.apply_project else [])+(["--confirm"] if args.confirm else [])
            code,adapter_payload=call_adapter_json(adapter.configure_entry,config_args)
            if code!=0 or adapter_payload.get("ok") is not True:raise StoreError(str(adapter_payload.get("error","Installation adapter refusée.")))
            payload={"ok":True,"installation":{key:value for key,value in adapter_payload.items() if key!="ok"}}
        elif args.command=="adapter":
            if args.adapter_command=="matrix":payload={"ok":True,"adapters":[{"adapter":name,"coverage":data.coverage,"config":data.config,"runtime":data.runtime} for name,data in sorted(ADAPTER_CATALOG.items())]}
            elif args.adapter_command=="doctor":payload={"ok":True,"doctor":_doctor(args.profile,args.adapter)}
            elif args.adapter_command=="validate":
                adapter=adapter_spec(args.adapter);profile=load_profile(args.profile);workspace=resolve_workspace(profile,args.profile);payload={"ok":True,"adapter":args.adapter,"coverage":adapter.coverage,"projectIdentity":project_identity(profile,workspace).as_dict(),"runtime":RuntimeLocator.from_workspace(profile,workspace).as_dict()}
            elif args.adapter_command=="stage":
                adapter=adapter_spec(args.adapter);stage_args=["--profile",str(args.profile)]+(["--confirm"] if args.confirm else []);return call_adapter(adapter.stage_entry,stage_args)
            elif args.adapter_command=="configure":
                if args.apply_user_scope:raise StoreError("La voie user-scope ne peut pas être routée par M6 ; utiliser la commande Claude dédiée et deux confirmations explicites.")
                adapter=adapter_spec(args.adapter);config_args=["--profile",str(args.profile)]+(["--apply-project"] if args.apply_project else [])+(["--confirm"] if args.confirm else []);return call_adapter(adapter.configure_entry,config_args)
            else:raise StoreError("Opération d’adapter inconnue.")
        else:
            profile=load_profile(args.profile)
            if args.command=="identity":payload={"ok":True,"identity":profile_identity(profile).as_dict()}
            elif args.command=="inspect":
                workspace=resolve_workspace(profile,args.profile);payload={"ok":True,"profile_identity":profile_identity(profile).as_dict(),"project_identity":project_identity(profile,workspace).as_dict(),"workspace":workspace.as_dict(),"runtime":RuntimeLocator.from_workspace(profile,workspace).as_dict()}
            elif args.command=="init":
                with MemoryStore.open(profile,args.profile) as store:payload={"ok":True,"identity":store.identity.as_dict(),"migration_checksums":store.migration_checksums,"metadata":store.metadata()}
            else:raise StoreError("Commande inconnue.")
    except (MigrationError,ProfileError,ProjectBootstrapError,ProjectOperationError,StoreError,WorkspaceError,ValueError) as exc:
        print(json.dumps({"ok":False,"error":str(exc)},ensure_ascii=False,sort_keys=True));return 2
    print(json.dumps(payload,ensure_ascii=False,sort_keys=True));return 0


if __name__=="__main__":raise SystemExit(main())
