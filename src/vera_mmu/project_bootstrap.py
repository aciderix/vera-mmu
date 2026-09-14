"""Guided, project-local initialization based on declarative VERA templates."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Sequence
from .agent_profiles import builtin_agent_profiles_json
from .identity import PROJECT_ID_RE
from .store import StoreError
TEMPLATE_IDS=("software","data","research","documentation","game","hardware")
_TEMPLATE_ENTITY_TYPES={
    "software":("COMPONENT","MODULE","SYMBOL","TEST","BUILD","DEPLOY"),
    "game":("ASSET","SCENE","SERVER","EVENT","PLAYER_STATE","SYSTEM_STATE"),
    "research":("EXPERIMENT","HYPOTHESIS","DATASET","RESULT","METRIC"),
    "data":("DATASET","FEATURE","MODEL","EVALUATION","METRIC","PIPELINE"),
    "hardware":("BOARD","COMPONENT","FIRMWARE","MEASUREMENT","DEVICE"),
    "documentation":("SOURCE","DOCUMENT","CLAIM","CITATION","REVISION"),
}
def _capability(identifier:str,name:str,description:str,kind:str,runner:str,validator:str,fields:tuple[str,...],gate_id:str,gate_name:str)->dict[str,object]:
    return {"id":identifier,"name":name,"description":description,"kind":kind,"runner":runner,"validator":validator,"fields":fields,"gate_id":gate_id,"gate_name":gate_name}
def _domain(prefix:str,collector:str,collector_name:str,collector_description:str,fields:tuple[str,...],collector_gate:str,collector_gate_name:str,integrity:str,integrity_name:str,integrity_description:str,integrity_gate:str,integrity_gate_name:str)->tuple[dict[str,object],...]:
    """Build one domain's three declarations: an observation, its field check and an integrity check.

    The collector runs `NOOP` and carries the domain fields, because an evidence must attach to
    an execution. The two checks run the validator profiles, whose parameter schema is fixed by
    the Core; their domain fields travel as `inputs`, which become the validator's required keys.
    """
    return (
        _capability(collector,collector_name,collector_description,"COLLECTOR","NOOP","EVIDENCE_FIELDS",fields,collector_gate,collector_gate_name),
        _capability(f"{prefix}-fields-check",f"Contrôle des champs — {collector_name.lower()}",f"Vérifie que l’evidence enregistrée porte les champs déclarés du domaine.","CHECK","EVIDENCE_FIELDS","EVIDENCE_FIELDS",fields,f"{collector_gate}_FIELDS","Champs de mesure complets"),
        _capability(integrity,integrity_name,integrity_description,"CHECK","EVIDENCE_HASH","EVIDENCE_HASH",(),integrity_gate,integrity_gate_name),
    )
_TEMPLATE_CAPABILITIES={
    "software":_domain("software","test-suite-report","Rapport de suite de tests","Enregistre le résultat déclaré d’une suite de tests du projet.",("suite","passed","failed"),"TESTS_RECORDED","Suite de tests enregistrée","build-artifact-integrity","Intégrité d’artefact de build","Vérifie qu’un artefact de build correspond exactement au hash attendu.","BUILD_INTEGRITY","Intégrité du build vérifiée"),
    "data":_domain("data","dataset-profile","Profil de jeu de données","Enregistre les mesures structurelles déclarées d’un jeu de données.",("dataset","rows","columns"),"DATASET_PROFILED","Jeu de données profilé","model-evaluation-integrity","Intégrité d’évaluation de modèle","Vérifie qu’un rapport d’évaluation correspond exactement au hash attendu.","MODEL_EVALUATED","Évaluation de modèle vérifiée"),
    "research":_domain("research","experiment-record","Enregistrement d’expérience","Enregistre l’hypothèse, la méthode et le résultat observé d’une expérience.",("hypothesis","method","outcome"),"EXPERIMENT_RECORDED","Expérience enregistrée","result-reproduction","Reproduction de résultat","Vérifie qu’un résultat publié correspond exactement à l’artefact attendu.","RESULT_REPRODUCED","Résultat reproduit"),
    "documentation":_domain("documentation","citation-record","Relevé de citation","Enregistre l’affirmation documentaire et la source qu’elle cite.",("document","claim","citation"),"CITATIONS_RECORDED","Citations relevées","revision-integrity","Intégrité de révision","Vérifie qu’une révision de document correspond au hash attendu.","REVISION_INTEGRITY","Intégrité de révision vérifiée"),
    "game":_domain("game","playtest-session","Session de playtest","Enregistre le déroulé observé d’une session de test de jeu.",("scene","outcome","duration_seconds"),"PLAYTEST_RECORDED","Playtest enregistré","asset-integrity","Intégrité d’asset","Vérifie qu’un asset de jeu correspond exactement au hash attendu.","ASSET_INTEGRITY","Intégrité des assets vérifiée"),
    "hardware":_domain("hardware","measurement-record","Relevé de mesure","Enregistre une mesure instrumentée avec sa grandeur et son unité.",("instrument","quantity","unit"),"MEASUREMENT_RECORDED","Mesure enregistrée","firmware-image-integrity","Intégrité d’image firmware","Vérifie qu’une image firmware correspond exactement au hash attendu.","FIRMWARE_INTEGRITY","Intégrité du firmware vérifiée"),
}
class ProjectBootstrapError(StoreError):pass
@dataclass(frozen=True)
class InitializationFile:
    path:str;content:str;sha256:str
    def as_dict(self)->dict[str,str]:return {"path":self.path,"content":self.content,"sha256":self.sha256}
@dataclass(frozen=True)
class ProjectInitializationPreview:
    format:str;root:str;template:str;project_id:str;project_name:str;files:tuple[InitializationFile,...];status:str;preview_hash:str
    def as_dict(self)->dict[str,object]:return {"format":self.format,"root":self.root,"template":self.template,"project_id":self.project_id,"project_name":self.project_name,"files":[x.as_dict() for x in self.files],"status":self.status,"preview_hash":self.preview_hash}
@dataclass(frozen=True)
class ProjectInitializationResult:
    status:str;root:str;files:tuple[str,...];preview_hash:str
    def as_dict(self)->dict[str,object]:return {"status":self.status,"root":self.root,"files":list(self.files),"preview_hash":self.preview_hash}
def preview_project_initialization(root:str|Path,*,template:str,project_id:str,project_name:str)->ProjectInitializationPreview:
    target=_root(root)
    if template not in TEMPLATE_IDS:raise ProjectBootstrapError("Template de projet inconnu.")
    if not isinstance(project_id,str) or PROJECT_ID_RE.fullmatch(project_id) is None:raise ProjectBootstrapError("project_id invalide.")
    if not isinstance(project_name,str) or not project_name.strip() or len(project_name)>160:raise ProjectBootstrapError("project_name invalide.")
    files=(
        _file(".vera-mmu/agent-profiles.yaml",builtin_agent_profiles_json()),
        _file(".vera-mmu/capabilities.yaml",_capabilities(template)),
        _file(".vera-mmu/gates.yaml",_gates(template)),
        _file(".vera-mmu/playbook.md",_playbook(project_name)),
        _file(".vera-mmu/policies.yaml",_policies()),
        _file(".vera-mmu/project.yaml",_profile(template,project_id,project_name)),
        _file(".vera-mmu/sync-policy.json",_sync_policy()),)
    digest=sha256("\0".join((str(target),template,project_id,project_name,*[x.sha256 for x in files])).encode()).hexdigest()
    return ProjectInitializationPreview("vera-project-initialization/v1",str(target),template,project_id,project_name,files,"PREVIEW",digest)
def apply_project_initialization(root:str|Path,preview:ProjectInitializationPreview,*,confirm:bool)->ProjectInitializationResult:
    if confirm is not True:raise ProjectBootstrapError("Initialisation refusée sans confirmation explicite.")
    target=_root(root)
    if not isinstance(preview,ProjectInitializationPreview) or preview.root!=str(target) or preview.status!="PREVIEW":raise ProjectBootstrapError("Preview d’initialisation invalide ou lié à une autre racine.")
    expected=preview_project_initialization(target,template=preview.template,project_id=preview.project_id,project_name=preview.project_name)
    if preview!=expected:raise ProjectBootstrapError("Preview d’initialisation altéré ou périmé.")
    statuses=[]
    for item in preview.files:
        path=_target(target,item.path);existing=_read(path)
        if existing is not None and existing!=item.content:raise ProjectBootstrapError(f"Cible initialisation déjà divergente : {item.path}.")
        statuses.append(existing==item.content)
    for item,unchanged in zip(preview.files,statuses):
        if not unchanged:_write(_target(target,item.path),item.content,".vera-init-")
    return ProjectInitializationResult("UNCHANGED" if all(statuses) else "INITIALIZED",str(target),tuple(item.path for item in preview.files),preview.preview_hash)
def _root(root:str|Path)->Path:
    source=Path(root).expanduser()
    if source.is_symlink():raise ProjectBootstrapError("Racine d’initialisation symlinkée refusée.")
    try:target=source.resolve(strict=True)
    except OSError as exc:raise ProjectBootstrapError("Racine d’initialisation introuvable.") from exc
    if not target.is_dir():raise ProjectBootstrapError("Racine d’initialisation non répertoire.")
    return target
def _file(path:str,content:str)->InitializationFile:return InitializationFile(path,content,sha256(content.encode()).hexdigest())
def _profile(template:str,project_id:str,name:str)->str:
    entity_types=", ".join(_TEMPLATE_ENTITY_TYPES[template])
    return f'''mmu:
  version: "2.0"
project:
  id: "{project_id}"
  name: "{name.strip()}"
  description: "Profil VERA initialisé pour {name.strip()}"
  domain: {template}
workspace:
  root: "."
  additional_roots: []
storage:
  memory_dir: ".vera-mmu"
  sqlite_file: "memory.sqlite"
  artifacts_dir: "artifacts"
  max_context_bytes: 18500
  max_resume_bytes: 14000
identity:
  include_vcs_revision: true
  include_profile_hash: true
resume:
  template: engineering
  sections:
    - id: working-rules
      required: true
    - id: current-state
      required: true
    - id: validated-facts
      required: true
    - id: risks
      required: true
    - id: next-action
      required: true
front:
  fields: [active_goal, current_work, validated_facts, blockers, risks, next_action]
knowledge:
  types: [RULE, DECISION, OBSERVATION, HYPOTHESIS, STATE, MEASUREMENT, DISCOVERY, ARCHITECTURE]
entities:
  types: [{entity_types}]
relations:
  types: [VERIFIED_BY, SUPERSEDES, INFORMED_BY, BLOCKED_BY, IMPLEMENTS, DERIVED_FROM, CONCERNS, APPLIES_TO, CAUSED_BY, EVOLVES_TO]
work:
  enabled: true
capabilities:
  catalog: ".vera-mmu/capabilities.yaml"
gates:
  catalog: ".vera-mmu/gates.yaml"
policies:
  file: ".vera-mmu/policies.yaml"
integrations:
  agent_profiles: ".vera-mmu/agent-profiles.yaml"
  enabled: []
'''
def _capabilities(template:str)->str:
    """Emit the declared capability catalog for one domain.

    A capability here is a contract for what the project must be able to prove, not a claim
    that VERA runs a domain tool: the runner profiles stay inside the closed Core set and the
    network policy stays `DENY_NETWORK`. A project is expected to edit this file.
    """
    lines=["format: vera-capability-catalog/v1","capabilities:"]
    for item in _TEMPLATE_CAPABILITIES[template]:
        fields=item["fields"]
        lines.extend((
            f"  - id: \"{item['id']}\"",
            f"    name: \"{item['name']}\"",
            f"    description: \"{item['description']}\"",
            f"    kind: {item['kind']}",
            "    version: \"1.0.0\"",
            f"    runner: {item['runner']}",
            "    network_policy: DENY_NETWORK",
            "    timeout_seconds: 120",
            "    parameter_schema:",
            "      type: object",
            "      properties:",
        ))
        # A NOOP collector carries the domain fields; the validator runners take exactly the
        # closed schema the Core fixes for them, their domain fields travelling as `inputs`.
        schema_fields = fields if item["runner"] == "NOOP" else ("validator_id", "evidence_id")
        lines.extend(f"        {name}: {{type: string}}" for name in schema_fields)
        lines.extend((
            f"      required: [{', '.join(schema_fields)}]",
            "      additionalProperties: false",
            "    yields_proof: false",
            "    policy: READ_ONLY",
            f"    inputs: [{', '.join(fields)}]" if fields else "    inputs: []",
            "    outputs: [verdict]",
            f"    validator: {item['validator']}",
            "    artifacts: []",
            "    confirmation_required: false",
        ))
    return "\n".join(lines)+"\n"
def _gates(template:str)->str:
    """Emit one required gate per declared capability, expecting an explicit `PASS`."""
    lines=["format: vera-gate-catalog/v1","gates:"]
    for item in _TEMPLATE_CAPABILITIES[template]:
        lines.extend((
            f"  - id: {item['gate_id']}",
            f"    name: \"{item['gate_name']}\"",
            f"    capability_id: \"{item['id']}\"",
            "    required: true",
            "    expected:",
            "      verdict: PASS",
        ))
    return "\n".join(lines)+"\n"
def _policies()->str:
    return """format: vera-policy-catalog/v1
filesystem:
  read: allow
  write: confirm
network:
  default: deny
process:
  allowed_runners: []
git:
  commit: confirm
  push: confirm
destructive:
  default: confirm
promotion:
  proven_requires: [admissible_pass]
"""
def _sync_policy()->str:
    return '{"auto_commit":true,"auto_push":true,"branch":"CURRENT","format":"vera-memory-sync-policy/v1","remote":"origin"}\n'
def _playbook(name:str)->str:
    return f'''# Règles de travail — {name.strip()}

## Lois VERA

1. Une observation n’est pas une preuve ; `PROVEN` requiert une preuve admissible `PASS`.
2. Les policies, gates, capabilities et chemins doivent être validés avant exécution.
3. Les erreurs, `FAIL`, `SKIPPED`, `ERROR` et `UNKNOWN` restent fail-closed.
4. Une reprise doit être liée au projet et acquittée sans fabriquer de contexte absent.
5. Toute action project-local sensible doit être prévisualisée puis explicitement confirmée.

> Ce playbook est une proposition initiale. Le projet doit le revoir, le compléter et le versionner selon ses propres règles.
'''
def _target(root:Path,relative:str)->Path:
    path=Path(relative)
    if path.is_absolute() or ".." in path.parts or len(path.parts)<2:raise ProjectBootstrapError("Chemin d’initialisation hors projet.")
    result=root/path
    if any(part.is_symlink() for part in (root,root/path.parts[0])) or result.is_symlink():raise ProjectBootstrapError("Cible d’initialisation symlinkée refusée.")
    return result
def _read(path:Path)->str|None:
    if not path.exists():return None
    if path.is_symlink() or not path.is_file():raise ProjectBootstrapError("Cible d’initialisation non régulière.")
    try:return path.read_text(encoding="utf-8")
    except (OSError,UnicodeDecodeError) as exc:raise ProjectBootstrapError("Cible d’initialisation illisible.") from exc
def _write(path:Path,content:str,prefix:str)->None:
    parent=path.parent
    if parent.is_symlink():raise ProjectBootstrapError("Répertoire d’initialisation symlinké refusé.")
    try:parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    except OSError as exc:raise ProjectBootstrapError("Création du répertoire VERA impossible.") from exc
    if not parent.is_dir() or parent.is_symlink():raise ProjectBootstrapError("Répertoire d’initialisation invalide.")
    temp:Path|None=None
    try:
        with NamedTemporaryFile(mode="w",encoding="utf-8",newline="\n",dir=parent,prefix=prefix,suffix=".tmp",delete=False) as handle:temp=Path(handle.name);handle.write(content);handle.flush();os.fsync(handle.fileno())
        os.chmod(temp,0o600);os.replace(temp,path)
    except OSError as exc:
        if temp is not None:temp.unlink(missing_ok=True)
        raise ProjectBootstrapError("Écriture atomique d’initialisation impossible.") from exc
