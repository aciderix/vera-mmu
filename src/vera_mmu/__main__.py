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
from .doctor import diagnose_project, render_doctor_report
from .documentation_generator import compile_project_documentation
from .identity import ProfileError, load_profile, profile_identity, project_identity
import shutil
from .install_repair import apply_install_repair, preview_install_repair
from .mcp_compiler import compile_mcp_package
from .mcp_manifest import TOOL_NAMES
from .mcp_server import main as mcp_server_main
from .project_validation import validate_project
from .memory_sync import automatic_memory_sync
from .migrations import MigrationError
from .project_import import apply_project_document_import, preview_project_document_import
from .read_api import ReadService
from .runtime import RuntimeLocator
from .write_api import WriteApiError, WriteService
from .project_operations import ProjectOperationError, compile_generation_preview, scan_project
from .project_recommendation import RecommendationError, recommend_profile
from .wizard import WizardError, wizard_state
from .project_bootstrap import ProjectBootstrapError, apply_project_initialization, preview_project_initialization
from .profile_migration import inspect_profile_migration_journal, recover_profile_physical_migration
from .store import MemoryStore, StoreError
from .workspace import WorkspaceError, resolve_workspace


def build_parser() -> argparse.ArgumentParser:
    parser=argparse.ArgumentParser(prog="vmmu",description="VERA-MMU: identité, validation et opérations d’adapter bornées.")
    sub=parser.add_subparsers(dest="command",required=True)
    for name,help_text in (("identity","Valide un Project Profile et affiche son identité canonique."),("inspect","Valide le profile, workspace et confinement runtime."),("init","Initialise le substrat SQLite lié au profile.")):
        child=sub.add_parser(name,help=help_text);child.add_argument("profile",type=Path,help="Chemin project.yaml.")
    scan=sub.add_parser("scan",help="Observe une arborescence locale sans lire de contenu ni écrire.");scan.add_argument("root",type=Path,help="Racine locale explicitement sélectionnée.")
    recommend=sub.add_parser("recommend",help="Propose un template, des capabilities et des gates depuis un scan, sans rien écrire.");recommend.add_argument("root",type=Path,help="Racine locale explicitement sélectionnée.")
    wizard=sub.add_parser("wizard",help="Décrit où en est le parcours de configuration en dix-huit étapes, sans rien écrire.");wizard.add_argument("root",type=Path,help="Racine locale explicitement sélectionnée.")
    compile_pkg=sub.add_parser("compile",help="Exécute le pipeline MCP ordonné et produit le package, sans écriture hôte.");compile_pkg.add_argument("profile",type=Path,help="Chemin project.yaml.");compile_pkg.add_argument("--adapter",required=True);compile_pkg.add_argument("--with-outputs",action="store_true",help="Inclut le texte complet des sorties générées.")
    validate=sub.add_parser("validate",help="Valide les fichiers déclaratifs du projet et leurs relations.");validate.add_argument("profile",type=Path,help="Chemin project.yaml.")
    configure=sub.add_parser("configure",help="Prévisualise ou applique la configuration project-local d’une intégration.");configure.add_argument("profile",type=Path,help="Chemin project.yaml.");configure.add_argument("--adapter",required=True);configure.add_argument("--apply-project",action="store_true");configure.add_argument("--confirm",action="store_true")
    serve=sub.add_parser("serve",help="Démarre le serveur MCP project-local, ou décrit son transport.");serve.add_argument("profile",type=Path,help="Chemin project.yaml.");serve.add_argument("--describe",action="store_true",help="Décrit le transport sans démarrer le serveur.");serve.add_argument("--streamable-http",action="store_true");serve.add_argument("--host",default="127.0.0.1");serve.add_argument("--port",type=int,default=8765)
    import_bundle=sub.add_parser("import",help="Vérifie un bundle project-local et décrit une restauration, sans écrire.");import_bundle.add_argument("profile",type=Path,help="Chemin project.yaml.");import_bundle.add_argument("--bundle-id",required=True)
    upgrade=sub.add_parser("upgrade",help="Applique les migrations de schéma en attente après confirmation.");upgrade.add_argument("profile",type=Path,help="Chemin project.yaml.");upgrade.add_argument("--confirm",action="store_true")
    dashboard=sub.add_parser("dashboard",help="Localise l’application desktop VERA et indique comment la lancer.");dashboard.add_argument("profile",type=Path,help="Chemin project.yaml.");dashboard.add_argument("--describe",action="store_true")
    generate=sub.add_parser("generate",help="Compile un preview MCP déterministe sans installer.");generate.add_argument("profile",type=Path,help="Chemin project.yaml.");generate.add_argument("--adapter",required=True)
    install=sub.add_parser("install",help="Prévisualise ou applique la configuration project-local d’un adapter.");install.add_argument("profile",type=Path,help="Chemin project.yaml.");install.add_argument("--adapter",required=True);install.add_argument("--apply-project",action="store_true");install.add_argument("--confirm",action="store_true")
    bootstrap=sub.add_parser("init-project",help="Prévisualise ou initialise les fichiers VERA dans un projet choisi.");bootstrap.add_argument("root",type=Path,help="Racine locale du projet.");bootstrap.add_argument("--template",required=True);bootstrap.add_argument("--project-id",required=True);bootstrap.add_argument("--project-name",required=True);bootstrap.add_argument("--apply",action="store_true");bootstrap.add_argument("--confirm",action="store_true")
    sync=sub.add_parser("memory-sync",help="Synchronise seulement la mémoire VERA selon sa policy project-local.");sync.add_argument("profile",type=Path,help="Chemin project.yaml.")
    doctor=sub.add_parser("doctor",help="Diagnostique sans mutation le profile, runtime, SQLite, catalogues et transports VERA.");doctor.add_argument("profile",type=Path,help="Chemin project.yaml.");doctor.add_argument("--human",action="store_true",help="Rend le rapport en lignes lisibles au lieu du JSON.")
    repair=sub.add_parser("repair",help="Prévisualise ou applique la réparation des fichiers déclaratifs manquants.");repair.add_argument("profile",type=Path,help="Chemin project.yaml.");repair.add_argument("--apply",action="store_true");repair.add_argument("--confirm",action="store_true")
    migrate=sub.add_parser("migrate",help="Observe ou pilote explicitement une migration Profile.")
    migration_ops=migrate.add_subparsers(dest="migration_command",required=True)
    migration_status=migration_ops.add_parser("status",help="Observe l’état d’une migration Profile sans mutation.");migration_status.add_argument("profile",type=Path,help="Chemin project.yaml.")
    migration_recover=migration_ops.add_parser("recover",help="Reprend explicitement un journal EXECUTING après confirmation.");migration_recover.add_argument("journal",type=Path,help="Chemin du journal EXECUTING.");migration_recover.add_argument("--confirm",action="store_true")
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
    sync_caps=sub.add_parser("sync-capabilities",help="Matérialise le catalogue de capabilities déclaré par le Project Profile.");sync_caps.add_argument("profile",type=Path,help="Chemin project.yaml.");sync_caps.add_argument("--actor",default="vera-cli")
    sync_types=sub.add_parser("sync-knowledge-types",help="Enregistre exactement les types knowledge déclarés par le Project Profile.");sync_types.add_argument("profile",type=Path,help="Chemin project.yaml.");sync_types.add_argument("--actor",default="vera-cli")
    append_knowledge=sub.add_parser("append-knowledge",help="Ajoute exactement une connaissance ; PROVEN reste refusé à l’append.");append_knowledge.add_argument("profile",type=Path,help="Chemin project.yaml.");append_knowledge.add_argument("--id",required=True,dest="identifier");append_knowledge.add_argument("--type-id",required=True);append_knowledge.add_argument("--status",required=True);append_knowledge.add_argument("--title",required=True);append_knowledge.add_argument("--content",required=True);append_knowledge.add_argument("--actor",default="vera-cli")
    replace_front=sub.add_parser("replace-front",help="Enregistre un snapshot Front complet après confirmation explicite.");replace_front.add_argument("profile",type=Path,help="Chemin project.yaml.");replace_front.add_argument("--id",required=True,dest="identifier");replace_front.add_argument("--field",action="append",required=True,dest="fields",help="Champ Front déclaré, au format cle=valeur.");replace_front.add_argument("--actor",default="vera-cli");replace_front.add_argument("--confirm",action="store_true")
    update_front=sub.add_parser("update-front",help="Dérive un nouveau Front en ne modifiant que les champs fournis.");update_front.add_argument("profile",type=Path,help="Chemin project.yaml.");update_front.add_argument("--id",required=True,dest="identifier");update_front.add_argument("--field",action="append",required=True,dest="fields",help="Champ Front déclaré, au format cle=valeur.");update_front.add_argument("--actor",default="vera-cli");update_front.add_argument("--confirm",action="store_true")
    prepare_handoff=sub.add_parser("prepare-handoff",help="Prépare un handoff en compilant le contrat de reprise depuis le profile.");prepare_handoff.add_argument("profile",type=Path,help="Chemin project.yaml.");prepare_handoff.add_argument("--id",required=True,dest="identifier");prepare_handoff.add_argument("--section",action="append",required=True,dest="sections",help="Section de reprise requise, au format id=texte.");prepare_handoff.add_argument("--actor",default="vera-cli");prepare_handoff.add_argument("--confirm",action="store_true")
    resume_brief=sub.add_parser("resume-brief",help="Indique ce qu’une reprise doit contenir, sans armer ni acquitter.");resume_brief.add_argument("profile",type=Path,help="Chemin project.yaml.")
    export_projection=sub.add_parser("export",help="Projette l’état vérifiable du projet sans produire d’archive.");export_projection.add_argument("profile",type=Path,help="Chemin project.yaml.")
    import_bundle=sub.add_parser("bundle-preview",help="Vérifie un bundle project-local et décrit une restauration, sans écrire.");import_bundle.add_argument("profile",type=Path,help="Chemin project.yaml.");import_bundle.add_argument("--bundle-id",required=True)
    restore_by_id=sub.add_parser("bundle-restore-id",help="Restaure un bundle project-local nommé après confirmation explicite.");restore_by_id.add_argument("profile",type=Path,help="Chemin project.yaml.");restore_by_id.add_argument("--bundle-id",required=True);restore_by_id.add_argument("--confirm",action="store_true")
    attach=sub.add_parser("attach-proof",help="Rattache une evidence existante à une gate déclarée.");attach.add_argument("profile",type=Path,help="Chemin project.yaml.");attach.add_argument("--gate-id",required=True);attach.add_argument("--evidence-id",required=True);attach.add_argument("--actor",default="vera-cli")
    work_graph=sub.add_parser("work-graph",help="Lit le work graph borné : items, dépendances et gates déclarées.");work_graph.add_argument("profile",type=Path,help="Chemin project.yaml.")
    list_proofs=sub.add_parser("list-proofs",help="Liste les promotions persistées sans jamais retourner de signature.");list_proofs.add_argument("profile",type=Path,help="Chemin project.yaml.");list_proofs.add_argument("--max-items",type=int,default=20)
    create_work_item=sub.add_parser("create-work-item",help="Crée un work item dans l’état initial du cycle de vie Core.");create_work_item.add_argument("profile",type=Path,help="Chemin project.yaml.");create_work_item.add_argument("--id",required=True,dest="identifier");create_work_item.add_argument("--type",required=True,dest="item_type");create_work_item.add_argument("--title",required=True);create_work_item.add_argument("--description",default="");create_work_item.add_argument("--priority",type=int);create_work_item.add_argument("--parent-id");create_work_item.add_argument("--assignee");create_work_item.add_argument("--actor",default="vera-cli")
    transition=sub.add_parser("transition-work-item",help="Applique un événement de cycle de vie du catalogue fermé.");transition.add_argument("profile",type=Path,help="Chemin project.yaml.");transition.add_argument("--id",required=True,dest="identifier");transition.add_argument("--work-item-id",required=True);transition.add_argument("--event",required=True);transition.add_argument("--reason",required=True);transition.add_argument("--actor",default="vera-cli")
    dependency=sub.add_parser("add-work-dependency",help="Déclare un prérequis entre deux work items, sans cycle.");dependency.add_argument("profile",type=Path,help="Chemin project.yaml.");dependency.add_argument("--dependent-id",required=True);dependency.add_argument("--prerequisite-id",required=True);dependency.add_argument("--actor",default="vera-cli")
    declare_gate=sub.add_parser("declare-gate",help="Déclare une gate d’admission liant un work item à son evidence.");declare_gate.add_argument("profile",type=Path,help="Chemin project.yaml.");declare_gate.add_argument("--id",required=True,dest="identifier");declare_gate.add_argument("--work-item-id",required=True);declare_gate.add_argument("--evidence-id",required=True);declare_gate.add_argument("--requirement-evidence-id",action="append",dest="requirements");declare_gate.add_argument("--actor",default="vera-cli")
    proof_policy=sub.add_parser("declare-proof-policy",help="Déclare la policy de preuve du projet ; la promotion l’exige.");proof_policy.add_argument("profile",type=Path,help="Chemin project.yaml.");proof_policy.add_argument("--algorithm",default="HMAC_SHA256");proof_policy.add_argument("--hmac-required",action="store_true");proof_policy.add_argument("--actor",default="vera-cli")
    promote=sub.add_parser("promote-knowledge",help="Promeut une connaissance en PROVEN contre une evidence PASS admise.");promote.add_argument("profile",type=Path,help="Chemin project.yaml.");promote.add_argument("--id",required=True,dest="identifier");promote.add_argument("--knowledge-id",required=True);promote.add_argument("--evidence-id",required=True);promote.add_argument("--admission-id",required=True);promote.add_argument("--actor",default="vera-cli")
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


def _pairs(values:Sequence[str],label:str)->dict[str,str]:
    """Parse repeated `key=value` options without ever evaluating or splitting on the value."""
    parsed:dict[str,str]={}
    for item in values:
        key,separator,value=item.partition("=")
        if not separator or not key.strip():raise WriteApiError(f"{label} attendu au format cle=valeur.")
        if key.strip() in parsed:raise WriteApiError(f"{label} dupliqué : {key.strip()}.")
        parsed[key.strip()]=value
    return parsed


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
        elif args.command=="recommend":
            payload={"ok":True,"recommendation":recommend_profile(scan_project(args.root)).as_dict()}
        elif args.command=="wizard":
            payload={"ok":True,"wizard":wizard_state(args.root).as_dict()}
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
            report=diagnose_project(args.profile)
            if args.human:
                print(render_doctor_report(report),end="");return 0 if report.status=="PASS" else 2
            payload={"ok":report.status=="PASS","doctor":report.as_dict()}
            if report.status!="PASS":
                print(json.dumps(payload,ensure_ascii=False,sort_keys=True));return 2
        elif args.command=="migrate":
            if args.migration_command == "recover":
                result=recover_profile_physical_migration(args.journal, confirm=args.confirm)
                payload={"ok":True,"migration":result}
            elif args.migration_command == "status":
                profile_path = args.profile.expanduser()
                control_dir = profile_path.parent.parent if profile_path.parent.name == ".vera-mmu" else profile_path.parent
                journals = sorted(control_dir.glob(".vera-profile-migration-*.json")) if control_dir.is_dir() and not control_dir.is_symlink() else []
                if not journals:
                    payload={"ok":True,"migration":{"format":"vera-profile-physical-migration-status/v1","status":"NO_PENDING_MIGRATION","journal_path":None,"mutation":"NONE"}}
                else:
                    report=inspect_profile_migration_journal(profile_path)
                    payload={"ok":report["status"] == "READY_FOR_EXECUTOR","migration":report}
                    if not payload["ok"]:
                        print(json.dumps(payload,ensure_ascii=False,sort_keys=True));return 2
            else:
                raise StoreError("Opération de migration inconnue.")
        elif args.command in {"boot","find","read","read-batch","related","list-executions","list-evidence","get-front","get-handoff","work-graph","list-proofs","resume-brief","export","bundle-preview","import"}:
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
                elif args.command=="work-graph":payload={"ok":True,"work_graph":reader.work_graph()}
                elif args.command=="list-proofs":payload={"ok":True,"proofs":reader.list_proofs(max_items=args.max_items)}
                elif args.command=="resume-brief":payload={"ok":True,"resume_brief":reader.resume_brief()}
                elif args.command=="export":payload={"ok":True,"export":reader.export_projection()}
                elif args.command=="bundle-preview":payload={"ok":True,"bundle_preview":reader.preview_bundle_import(args.bundle_id)}
                elif args.command=="import":payload={"ok":True,"import":reader.preview_bundle_import(args.bundle_id)}
                else:payload={"ok":True,"handoff":reader.latest_handoff()}
        elif args.command in {"sync-knowledge-types","sync-capabilities","append-knowledge","replace-front","update-front","prepare-handoff","create-work-item","transition-work-item","add-work-dependency","declare-gate","declare-proof-policy","promote-knowledge","bundle-restore-id","attach-proof"}:
            profile=load_profile(args.profile)
            with MemoryStore.open(profile,args.profile) as store:
                writer=WriteService(store)
                if args.command=="sync-capabilities":payload={"ok":True,"capabilities":writer.sync_profile_capabilities(actor=args.actor)}
                elif args.command=="sync-knowledge-types":payload={"ok":True,"knowledge_types":writer.sync_profile_knowledge_types(actor=args.actor)}
                elif args.command=="append-knowledge":payload={"ok":True,"knowledge":writer.append_knowledge(args.identifier,type_id=args.type_id,status=args.status,title=args.title,content=args.content,actor=args.actor)}
                elif args.command=="replace-front":payload={"ok":True,"front":writer.replace_front(args.identifier,_pairs(args.fields,"Champ Front"),actor=args.actor,confirm=args.confirm)}
                elif args.command=="update-front":payload={"ok":True,"front":writer.update_front(args.identifier,_pairs(args.fields,"Champ Front"),actor=args.actor,confirm=args.confirm)}
                elif args.command=="prepare-handoff":payload={"ok":True,"handoff":writer.prepare_handoff(args.identifier,_pairs(args.sections,"Section de reprise"),actor=args.actor,confirm=args.confirm)}
                elif args.command=="create-work-item":payload={"ok":True,"work_item":writer.create_work_item(args.identifier,item_type=args.item_type,title=args.title,description=args.description,priority=args.priority,parent_id=args.parent_id,assignee=args.assignee,actor=args.actor)}
                elif args.command=="transition-work-item":payload={"ok":True,"lifecycle":writer.transition_work_item(args.identifier,work_item_id=args.work_item_id,event=args.event,reason=args.reason,actor=args.actor)}
                elif args.command=="add-work-dependency":payload={"ok":True,"dependency":writer.add_work_dependency(args.dependent_id,args.prerequisite_id,actor=args.actor)}
                elif args.command=="declare-gate":payload={"ok":True,"gate":writer.declare_gate(args.identifier,work_item_id=args.work_item_id,evidence_id=args.evidence_id,requirement_evidence_ids=tuple(args.requirements or ()),actor=args.actor)}
                elif args.command=="declare-proof-policy":payload={"ok":True,"proof_policy":writer.declare_proof_policy(args.algorithm,hmac_required=args.hmac_required,actor=args.actor)}
                elif args.command=="bundle-restore-id":payload={"ok":True,"bundle_restore":writer.restore_bundle_by_id(args.bundle_id,confirm=args.confirm)}
                elif args.command=="attach-proof":payload={"ok":True,"attachment":writer.attach_proof(args.gate_id,evidence_id=args.evidence_id,actor=args.actor)}
                else:payload={"ok":True,"proof":writer.promote_knowledge(args.identifier,knowledge_id=args.knowledge_id,evidence_id=args.evidence_id,admission_id=args.admission_id,actor=args.actor)}
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
        elif args.command=="repair":
            preview=preview_install_repair(args.profile)
            if args.apply:
                payload={"ok":True,"repair":apply_install_repair(args.profile,preview,confirm=args.confirm).as_dict()}
            else:
                payload={"ok":preview.status!="NOT_REPAIRABLE","repair":preview.as_dict()}
                if preview.status=="NOT_REPAIRABLE":
                    print(json.dumps(payload,ensure_ascii=False,sort_keys=True));return 2
        elif args.command=="validate":
            payload={"ok":True,"validation":validate_project(args.profile).as_dict()}
        elif args.command=="configure":
            adapter=adapter_spec(args.adapter);config_args=["--profile",str(args.profile)]+(["--apply-project"] if args.apply_project else [])+(["--confirm"] if args.confirm else [])
            code,adapter_payload=call_adapter_json(adapter.configure_entry,config_args)
            if code!=0 or adapter_payload.get("ok") is not True:raise StoreError(str(adapter_payload.get("error","Configuration adapter refusée.")))
            payload={"ok":True,"configuration":{key:value for key,value in adapter_payload.items() if key!="ok"}}
        elif args.command=="serve":
            profile=load_profile(args.profile)
            transport="streamable-http" if args.streamable_http else "stdio"
            if args.describe:
                with MemoryStore.open(profile,args.profile) as store:
                    payload={"ok":True,"serve":{"format":"vera-serve//v1","project_id":store.identity.project_id,"transport":transport,"status":"DESCRIBED","tools":len(TOOL_NAMES)}}
            else:
                serve_args=["--profile",str(args.profile)]+(["--streamable-http","--host",args.host,"--port",str(args.port)] if args.streamable_http else [])
                mcp_server_main(serve_args);return 0
        elif args.command=="upgrade":
            if args.confirm is not True:raise StoreError("Mise à niveau refusée sans confirmation explicite.")
            profile=load_profile(args.profile)
            with MemoryStore.open(profile,args.profile) as store:
                version=max(store.migration_checksums,default=0)
                payload={"ok":True,"upgrade":{"format":"vera-upgrade/v1","project_id":store.identity.project_id,"schema_version":version,"status":"UP_TO_DATE","mutation":"MIGRATIONS_APPLIED_IF_PENDING"}}
        elif args.command=="dashboard":
            profile=load_profile(args.profile)
            located=shutil.which("vera-mmu-desktop")
            payload={"ok":located is not None,"dashboard":{"format":"vera-dashboard/v1","status":"AVAILABLE" if located else "NOT_INSTALLED","executable":located,"remediation":"Aucune action requise." if located else "Installer le paquet desktop VERA, puis relancer cette commande."}}
            if located is None:
                print(json.dumps(payload,ensure_ascii=False,sort_keys=True));return 2
        elif args.command=="compile":
            profile=load_profile(args.profile)
            with MemoryStore.open(profile,args.profile) as store:
                package=compile_mcp_package(store,args.adapter).as_dict()
                if not args.with_outputs:package.pop("outputs",None)
                payload={"ok":True,"package":package}
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
    except (MigrationError,ProfileError,ProjectBootstrapError,ProjectOperationError,RecommendationError,StoreError,WizardError,WorkspaceError,ValueError) as exc:
        print(json.dumps({"ok":False,"error":str(exc)},ensure_ascii=False,sort_keys=True));return 2
    print(json.dumps(payload,ensure_ascii=False,sort_keys=True));return 0


if __name__=="__main__":raise SystemExit(main())
