# UNIVERSAL DEV-MMU
## Spécification finale d’universalisation d’ARET-MMU et procédure d’implémentation end-to-end

**Version : 1.0 — 2026-08-23**  
**Base : inspection du dépôt `aciderix/ARET-MMU` + spécification d’universalisation fournie + consolidation architecturale**  
**Statut : document de référence pour l’implémentation**

---

## 0. Objet du document

Ce document définit la transformation complète d’**ARET-MMU** en **Universal Dev-MMU**, c’est-à-dire un moteur de mémoire persistante, de provenance, de preuve, de reprise et de gouvernance pouvant être déployé sur un projet nouveau ou existant, logiciel ou non, et être personnalisé par un outil visuel capable de générer un MCP adapté au projet.

La cible n’est **pas** de produire une version « ARET-MMU avec les mots ARET remplacés ». La cible est une séparation stricte entre :

1. **Universal MMU Core** : moteur générique et indépendant du domaine.
2. **Domain Packs** : spécialisations optionnelles (software, game, research, data, hardware, documentation, etc.).
3. **Project Profile** : configuration propre à un projet donné.
4. **Capability / Gate Engine** : exécution contrôlée et validation objective.
5. **MCP Compiler** : génération du MCP, des hooks, politiques et fichiers d’intégration.
6. **Dashboard** : interface visuelle de découverte, configuration, validation, prévisualisation et génération.

La philosophie fondamentale d’ARET-MMU doit être conservée : **le modèle n’est pas la source de vérité ; la mémoire canonique, les preuves, la provenance et les invariants externes le sont.**

---

# 1. Décisions d’architecture finales

## 1.1. Décision principale

```text
                 UNIVERSAL DEV-MMU
                        │
        ┌───────────────┼────────────────┐
        │               │                │
        ▼               ▼                ▼
   CORE ENGINE      DOMAIN PACK     PROJECT PROFILE
        │               │                │
        │               │                └── taxonomie
        │               │                    capacités
        │               │                    gates
        │               │                    politiques
        │               │                    workflow
        │               │
        │               └── software / game / research / data / ...
        │
        ├── Memory Store
        ├── Evidence Store
        ├── Provenance
        ├── Audit
        ├── Work Graph
        ├── Gates
        ├── Capabilities
        ├── Policy Engine
        ├── Resume / Checkpoints
        └── Bundles
                        │
                        ▼
                MCP COMPILER
                        │
           ┌────────────┼────────────┐
           ▼            ▼            ▼
        MCP tools     Hooks       Policies
           │            │            │
           └────────────┼────────────┘
                        ▼
                 Agent / IDE / CLI
```

## 1.2. Principe « Core ≠ Domain »

Le Core ne doit contenir aucune dépendance conceptuelle obligatoire à :

- PE32 / Win32 ;
- DLL ;
- Wine ;
- MinGW ;
- Unicorn ;
- x87 ;
- calling conventions ;
- fonctions natives ;
- transpilation ;
- reverse engineering ;
- `target/release/aret` ;
- `bench/*` ARET ;
- documents 70/71/80/81/91 ;
- vocabulaire ou règles exclusivement ARET.

Ces éléments deviennent un **ARET Domain Pack**.

## 1.3. Principe de conservation des invariants

Les propriétés déjà robustes d’ARET-MMU sont conservées et deviennent contractuelles dans le Core :

- SQLite canonique ;
- FIND ≠ READ ;
- adressage exact ;
- append-only pour la connaissance ;
- versionnage / supersession ;
- provenance ;
- Evidence Store séparé ;
- hash SHA-256 ;
- reçus HMAC pour les preuves admissibles ;
- promotion `PROVEN` uniquement avec preuve admissible `PASS` ;
- audit des mutations ;
- Active Front ;
- handoff ;
- Resume Guard ;
- bundles vérifiés ;
- séparation laboratoire / capacité officielle ;
- catalogue fermé de capacités ;
- paramètres bornés ;
- pas de shell arbitraire exposé au modèle.

---

# 2. État de départ et diagnostic du dépôt actuel

Le dépôt actuel constitue une excellente base, mais ses couches restent partiellement spécialisées ARET.

La structure actuelle contient déjà :

```text
aret-memory/
├── core/
├── evidence/
├── hooks/
├── integration/
├── migration/
├── ops/
├── schema/
├── scripts/
└── tests/
```

Le cœur de persistance est déjà structuré autour de `MemoryStore`, avec `knowledge`, `proof`, `proof_link`, relations, `front_state`, audit, FTS5 et triggers d’inviolabilité.

Le schéma actuel associe toutefois encore directement la connaissance à :

- `component` ;
- `function_symbol` ;
- `brick`.

Le serveur MCP embarque aussi des hypothèses ARET : dépôt racine unique, pipelines ARET, binaire `target/release/aret`, scripts `bench/*`, Wine/MinGW/Unicorn et doctrine ARET.

Le fichier `playbook.md` est explicitement une source autorisée de lois stables mais contient aujourd’hui les règles et outils ARET.

L’installation suppose encore que le paquet soit vendored sous `<projet>/aret-memory` et l’intégration documente elle-même que cette disposition doit être généralisée.

**Conclusion : le noyau est réutilisable ; l’abstraction autour du noyau ne l’est pas encore complètement.**

---

# 3. Périmètre exact de la V2 Universal Dev-MMU

## 3.1. Inclus

La V2 doit couvrir :

### Mémoire

- connaissances ;
- état courant ;
- Front ;
- handoffs ;
- observations ;
- hypothèses ;
- décisions ;
- relations ;
- historique ;
- provenance documentaire ;
- preuves ;
- artefacts ;
- assets ;
- travaux ;
- gates ;
- exécutions.

### Gouvernance

- politiques de filesystem ;
- réseau ;
- Git / VCS ;
- actions destructives ;
- secrets ;
- promotion de connaissances ;
- confirmation humaine.

### Exécution

- capabilities déclaratives ;
- runners ;
- validators ;
- oracles ;
- collectors ;
- generators ;
- exécutions persistées ;
- artefacts hashés ;
- résultats normalisés.

### Intégration

- Claude Code ;
- Cursor ;
- Codex ;
- CLI générique ;
- autres runtimes via adapters.

### Génération

- Project Profile ;
- config ;
- playbook ;
- capabilities ;
- gates ;
- policies ;
- outils MCP ;
- hooks ;
- documentation ;
- scripts d’installation ;
- tests de conformance.

## 3.2. Hors périmètre du Core

Les règles métier spécifiques d’un domaine sont externalisées en packs.

---

# 4. Architecture logicielle cible

```text
universal-dev-mmu/
│
├── core/
│   ├── store.py
│   ├── repository.py
│   ├── addressing.py
│   ├── identity.py
│   ├── config.py
│   ├── taxonomy.py
│   ├── entities.py
│   ├── relations.py
│   ├── provenance.py
│   ├── audit.py
│   ├── policy.py
│   ├── migrations.py
│   └── utils.py
│
├── memory/
│   ├── knowledge.py
│   ├── front.py
│   ├── handoff.py
│   ├── resume.py
│   ├── journal.py
│   └── search.py
│
├── work/
│   ├── goals.py
│   ├── work_items.py
│   ├── dependencies.py
│   ├── gates.py
│   └── lifecycle.py
│
├── evidence/
│   ├── capture.py
│   ├── proofs.py
│   ├── artifacts.py
│   ├── validators.py
│   ├── executions.py
│   └── admission.py
│
├── capabilities/
│   ├── registry.py
│   ├── schema.py
│   ├── runners/
│   │   ├── shell.py
│   │   ├── python.py
│   │   ├── mcp.py
│   │   ├── git.py
│   │   ├── http.py
│   │   ├── docker.py
│   │   └── filesystem.py
│   ├── validators.py
│   └── sandbox.py
│
├── integrations/
│   ├── base.py
│   ├── claude_code/
│   ├── cursor/
│   ├── codex/
│   └── generic/
│
├── domains/
│   ├── software/
│   ├── game/
│   ├── research/
│   ├── data/
│   ├── hardware/
│   └── documentation/
│
├── server/
│   ├── mmu_server.py
│   ├── tool_registry.py
│   ├── config_loader.py
│   └── instructions.py
│
├── generator/
│   ├── profile_compiler.py
│   ├── mcp_generator.py
│   ├── hook_generator.py
│   ├── policy_generator.py
│   ├── docs_generator.py
│   └── installer_generator.py
│
├── dashboard/
│   ├── scanner/
│   ├── profile_editor/
│   ├── capability_builder/
│   ├── gate_builder/
│   ├── policy_editor/
│   ├── mcp_preview/
│   └── validation/
│
├── cli/
│   └── main.py
│
├── schema/
├── migrations/
├── templates/
├── profiles/
└── tests/
```

---

# 5. Refactorisation du Core

## 5.1. `core/repository.py`

Le fichier actuel est trop centralisé. Il doit devenir une façade mince.

### Cible

```python
class MemoryStore(
    BaseStore,
    KnowledgeService,
    EntityService,
    RelationService,
    WorkService,
    EvidenceService,
    ResumeService,
    BundleService,
    AuditService,
):
    pass
```

Éviter les mixins purement artificiels si une composition de services rend le code plus clair. L’objectif est la séparation des responsabilités, pas la multiplication des classes.

### Règle

Chaque service doit rester indépendant du transport MCP.

---

# 6. Project Profile

## 6.1. Rôle

Le Project Profile devient la source déclarative de toutes les décisions de personnalisation qui ne sont pas des invariants du Core.

### Fichier canonique

```text
.mmu/project.yaml
```

### Structure minimale

```yaml
mmu:
  version: "2.0"

project:
  id: "mon-projet"
  name: "Mon Projet"
  description: "..."
  domain: "software"

workspace:
  root: "."
  additional_roots: []

storage:
  memory_dir: ".mmu"
  sqlite_file: "memory.sqlite"
  artifacts_dir: "artifacts"
  max_context_bytes: 18500
  max_resume_bytes: 12500

identity:
  include_vcs_revision: true
  include_profile_hash: true

resume:
  template: "engineering"
  sections: []

knowledge:
  types: []

entities:
  types: []

relations:
  types: []

work:
  enabled: true

capabilities:
  catalog: ".mmu/capabilities.yaml"

gates:
  catalog: ".mmu/gates.yaml"

policies:
  file: ".mmu/policies.yaml"

integrations:
  claude_code:
    enabled: true
```

---

# 7. Taxonomie universelle

## 7.1. Types de connaissances

Le Core conserve les statuts épistémiques, mais les types deviennent configurables.

### Types Core recommandés

```text
RULE
DECISION
OBSERVATION
HYPOTHESIS
STATE
MEASUREMENT
DISCOVERY
ARCHITECTURE
```

### Types projet

Exemples :

```text
REQUIREMENT
INCIDENT
API_CONTRACT
BENCHMARK
DESIGN
LESSON
EXPERIMENT
CUSTOMER_FACT
GAME_MECHANIC
```

## 7.2. Statuts

Les statuts suivants restent des primitives du Core :

```text
ACTIVE
PROVEN
OBSERVED
HYPOTHESIS
SUPERSEDED
OBSOLETE
CONFLICTING
```

Les extensions sont possibles mais doivent déclarer leur sémantique.

---

# 8. Remplacer `function_symbol` par `entity` + `symbol`

## 8.1. Registre d’entités

```sql
CREATE TABLE entity_type (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    schema_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL
) STRICT;

CREATE TABLE entity (
    id TEXT PRIMARY KEY,
    type_id TEXT NOT NULL REFERENCES entity_type(id),
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL
) STRICT;
```

## 8.2. `symbol`

Le type `symbol` reste utile pour les projets techniques mais devient générique :

```sql
CREATE TABLE symbol (
    id TEXT PRIMARY KEY,
    component_id TEXT REFERENCES entity(id),
    kind TEXT NOT NULL,
    path TEXT NOT NULL DEFAULT '',
    identifier TEXT NOT NULL,
    signature TEXT NOT NULL DEFAULT '',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL,
    UNIQUE(component_id, path, identifier)
) STRICT;
```

`FUNCTION`, `CLASS`, `METHOD`, `ENDPOINT`, `SERVICE`, `HOOK`, `MODULE`, `TABLE`, etc. deviennent des valeurs de `kind` ou des types déclaratifs selon le besoin.

---

# 9. Relations configurables

Créer un registre :

```sql
CREATE TABLE relation_type (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    from_types_json TEXT NOT NULL DEFAULT '[]',
    to_types_json TEXT NOT NULL DEFAULT '[]',
    lifecycle TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL
) STRICT;
```

Les relations Core bootstrapées comprennent au minimum :

```text
VERIFIED_BY
SUPERSEDES
INFORMED_BY
BLOCKED_BY
IMPLEMENTS
DERIVED_FROM
CONCERNS
APPLIES_TO
CAUSED_BY
EVOLVES_TO
```

Le projet peut ajouter :

```text
DEPENDS_ON
CALLS
IMPORTS
IMPLEMENTS
TARGETS
DERIVED_FROM_DATASET
VALIDATES
```

---

# 10. Work Graph universel

## 10.1. Remplacement conceptuel de `brick`

`brick` devient une vue ou un type spécialisé de `work_item`.

```sql
CREATE TABLE work_item (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL,
    priority INTEGER,
    parent_id TEXT REFERENCES work_item(id),
    assignee TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    created_by TEXT NOT NULL
) STRICT;
```

## 10.2. Hiérarchie

```text
GOAL
 └── EPIC
      └── WORK_ITEM
           └── SUBTASK
                └── GATE
                     └── EXECUTION
                          └── EVIDENCE
```

## 10.3. États

```text
PLANNED
READY
ACTIVE
BLOCKED
VERIFYING
DONE
FAILED
SUPERSEDED
CANCELLED
```

---

# 11. Gate Engine

## 11.1. But

Introduire une discipline de type Unlazy mais intégrée à l’Evidence Store d’ARET-MMU.

Une tâche ne devient pas automatiquement `DONE` parce que l’agent affirme l’avoir terminée.

## 11.2. Schéma

```sql
CREATE TABLE gate (
    id TEXT PRIMARY KEY,
    work_item_id TEXT REFERENCES work_item(id),
    name TEXT NOT NULL,
    capability_id TEXT NOT NULL,
    required INTEGER NOT NULL DEFAULT 1,
    expected_json TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL
) STRICT;
```

## 11.3. Cycle

```text
Gate
 ↓
Capability sélectionnée
 ↓
Execution
 ↓
Validator
 ↓
Evidence
 ↓
PASS / FAIL / ERROR / SKIPPED / UNKNOWN
 ↓
Gate satisfied ?
```

## 11.4. Règle

Une gate `PASS` doit être liée à une exécution réelle. Un simple texte « pass » produit par le modèle ne peut jamais constituer une preuve.

---

# 12. Capability Engine

## 12.1. Pourquoi remplacer le catalogue `PIPELINES`

Le catalogue ARET actuel est excellent mais contient une connaissance métier spécifique. Il doit devenir une instance du moteur générique.

## 12.2. Modèle

Une capability possède :

```text
id
name
description
kind
runner
policy
inputs
parameters
outputs
validator
artifacts
timeout
confirmation requirements
network requirements
```

## 12.3. Types

```text
ACTION
CHECK
ORACLE
COLLECTOR
GENERATOR
QUERY
```

## 12.4. Exemple

```yaml
capabilities:
  unit_tests:
    kind: CHECK
    runner: shell
    policy: READ_ONLY
    dependencies: [pytest]
    timeout_seconds: 180
    command: ["pytest", "-q"]
    result:
      exit_code: 0
      verdict: PASS
```

## 12.5. Exemple Network

```yaml
fetch_dataset:
  kind: COLLECTOR
  runner: shell
  policy: NETWORK
  allowed_sources:
    - "https://trusted.example/dataset.tar.gz"
  command: ["python3", "scripts/fetch_dataset.py"]
```

---

# 13. Règles de sécurité du Capability Engine

Une capability ne peut jamais recevoir une commande shell arbitraire du client MCP.

Le client choisit :

```text
capability_id
```

et transmet seulement des paramètres explicitement déclarés.

Le runner :

1. valide les paramètres par schéma ;
2. résout les chemins depuis les racines autorisées ;
3. applique la policy ;
4. vérifie les dépendances ;
5. applique le timeout ;
6. capture stdout/stderr ;
7. génère l’artefact ;
8. calcule les hashes ;
9. enregistre l’exécution ;
10. produit une preuve lorsque la capability est `yields_proof: true`.

---

# 14. Execution Store

Ajouter une entité d’exécution distincte de `proof`.

```sql
CREATE TABLE execution (
    id TEXT PRIMARY KEY,
    capability_id TEXT NOT NULL,
    status TEXT NOT NULL,
    exit_code INTEGER,
    parameters_json TEXT NOT NULL,
    environment_json TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT,
    artifact_hash TEXT,
    result_json TEXT NOT NULL DEFAULT '{}',
    created_by TEXT NOT NULL
) STRICT;
```

Une execution est le **fait qu’une action s’est produite**.

Une proof est la **preuve admissible dérivée de cette exécution**.

Cette distinction est importante pour éviter de confondre événement et vérité.

---

# 15. Evidence Store universel

Conserver le modèle actuel et l’étendre à :

```text
COMMAND_PROOF
TEST_PROOF
CI_PROOF
API_PROOF
HASH_PROOF
METRIC_PROOF
FILE_PROOF
EXTERNAL_ATTESTATION
HUMAN_ASSERTION
MODEL_EVALUATION
```

## 15.1. Règle de promotion

```text
PASS + admissible = promotion possible
FAIL                  = diagnostic seulement
ERROR                 = indéterminé
SKIPPED               = non exécuté faute de prérequis
UNKNOWN               = non promouvable
```

## 15.2. HMAC

Le HMAC reste obligatoire pour une preuve admissible si la policy du projet le requiert.

Le secret ne doit jamais être exposé au modèle.

---

# 16. Provenance

La provenance documentaire actuelle est conservée mais rendue générique :

```text
source_type
repository
revision
path
start_line
end_line
section
content_hash
import_batch_id
```

Pour une source autre que Git :

```text
URL
DOCUMENT_ID
DATASET_VERSION
EXTERNAL_RECORD_ID
```

Le principe reste : **une affirmation persistante doit pouvoir indiquer d’où elle vient.**

---

# 17. Project Identity

Chaque Store doit avoir une identité du projet :

```sql
CREATE TABLE project_identity (
    project_id TEXT PRIMARY KEY,
    project_slug TEXT NOT NULL,
    profile_version TEXT NOT NULL,
    profile_hash TEXT NOT NULL,
    workspace_fingerprint TEXT NOT NULL,
    vcs_type TEXT,
    vcs_revision TEXT,
    created_at TEXT NOT NULL
) STRICT;
```

Cette identité doit être vérifiée à chaque restauration.

Une mémoire issue du projet A ne doit pas être injectée comme mémoire canonique du projet B.

---

# 18. Adressage universel

## 18.1. Format cible

```text
mmu://<project>/<resource>/<id>
```

Exemples :

```text
mmu://my-app/knowledge/KN-00042
mmu://my-app/entity/ENT-00007
mmu://my-app/work/WI-00019
mmu://my-app/gate/G-00004
mmu://my-app/proof/PRF-00088
mmu://my-app/execution/EX-00102
mmu://my-app/artifact/AST-00003
mmu://my-app/front/current
```

## 18.2. Compatibilité

Pendant la migration :

```text
ARET://...
```

reste lisible mais n’est plus généré pour les nouvelles ressources.

---

# 19. Front et Resume Template

## 19.1. Front configurable

Le Front n’est plus supposé avoir des clés ARET fixes.

Le profil déclare :

```yaml
front:
  fields:
    - active_goal
    - current_work
    - validated_facts
    - blockers
    - risks
    - next_action
```

Projet recherche :

```text
active_experiment
current_hypothesis
last_measurement
open_questions
```

Projet jeu :

```text
active_system
current_bug
last_validation
runtime_state
next_action
```

## 19.2. Resume Ritual

Les six champs actuels deviennent un template configurable. Exemple :

```yaml
resume:
  sections:
    - id: rules
      required: true
    - id: current_state
      required: true
    - id: validated_facts
      required: true
    - id: risks
      required: true
    - id: next_action
      required: true
```

Le système de hash et de barrière reste inchangé conceptuellement.

---

# 20. Playbook universel

Le fichier actuel `playbook.md` devient :

```text
.mmu/playbook.md
```

mais son contenu est projet-spécifique.

Le Core impose uniquement un petit noyau de lois universelles :

1. ne pas présenter comme prouvé ce qui ne l’est pas ;
2. ne pas réécrire silencieusement l’historique ;
3. conserver la provenance ;
4. distinguer recherche et lecture exacte ;
5. respecter les policies ;
6. conserver les preuves séparées des affirmations ;
7. arrêter bruyamment en cas d’incertitude critique ;
8. ne pas contourner les gates.

Tout le reste est configurable.

---

# 21. Policy Engine

Créer `.mmu/policies.yaml`.

Exemple :

```yaml
filesystem:
  read: allow
  write:
    allow:
      - ./src
      - ./tests
      - ./.mmu

network:
  default: deny

process:
  allowed_runners:
    - shell
    - python

git:
  commit: allow
  push: confirm

destructive:
  default: confirm

promotion:
  proven_requires:
    - admissible_pass
```

Chaque capability référence une policy.

---

# 22. Git / VCS abstraction

`ops/git_memory.py` devient un adapter :

```text
VersionControlProvider
├── GitProvider
├── MercurialProvider
├── SVNProvider
└── NoVCSProvider
```

Le Core ne doit jamais supposer que Git existe.

---

# 23. Bundles universels

Le bundle actuel est conservé et enrichi :

```text
bundle.zip
├── manifest.json
├── project-profile.yaml
├── snapshot.json
├── capabilities.yaml
├── gates.yaml
├── policies.yaml
├── artifacts/
└── schema/
```

Le manifest contient :

```text
schema_hash
profile_hash
memory_hash
artifact_inventory
source_device_id
project_identity
```

Les imports restent non fusionnels par défaut.

---

# 24. MCP Core API

La cible conserve une API Core stable.

## Boot / Resume

```text
mmu_boot
mmu_restore
mmu_get_front
mmu_get_resume_brief
mmu_get_resume_status
mmu_acknowledge_resume
```

## FIND / READ

```text
mmu_find
mmu_read
mmu_read_batch
mmu_get_related
```

## Mémoire

```text
mmu_append_knowledge
mmu_update_front
mmu_replace_front
mmu_prepare_handoff
```

## Evidence

```text
mmu_get_proofs
mmu_record_proof
mmu_attach_proof
mmu_read_artifact
```

## Work

```text
mmu_create_work_item
mmu_update_work_item
mmu_create_gate
mmu_get_work_graph
```

## Capabilities

```text
mmu_get_capability_catalog
mmu_run_capability
mmu_get_executions
```

## Transport

```text
mmu_sync
mmu_export
mmu_export_bundle
mmu_import_bundle
mmu_doctor
```

Les outils réellement exposés au modèle sont sélectionnés/générés selon le profil.

---

# 25. MCP Compiler

## 25.1. Entrées

```text
ProjectProfile
Domain Packs
Capability Catalog
Gate Catalog
Policy Catalog
Integration Profile
```

## 25.2. Processus

```text
load
 ↓
normalize
 ↓
validate
 ↓
canonicalize
 ↓
compute profile hash
 ↓
resolve capabilities
 ↓
resolve gates
 ↓
resolve policies
 ↓
resolve integrations
 ↓
generate tool schemas
 ↓
generate instructions
 ↓
generate hooks
 ↓
generate config
 ↓
generate documentation
 ↓
run static validation
 ↓
produce MCP package
```

## 25.3. Déterminisme

Même profil + mêmes packs + même version du générateur = même sortie canonique.

---

# 26. Instructions MCP générées

Le texte actuel `SERVER_INSTRUCTIONS` ne doit plus être hardcodé avec des références ARET.

Il doit être composé de :

```text
CORE DOCTRINE
+
PROJECT PLAYBOOK
+
CAPABILITY RULES
+
POLICY SUMMARY
+
RESUME PROTOCOL
```

L’ensemble est hashé et lié au Profile Hash.

---

# 27. Intégrations

## 27.1. Interface commune

Créer :

```python
class RuntimeAdapter:
    def install(self, project_root): ...
    def generate_hooks(self, profile): ...
    def generate_config(self, profile): ...
    def validate(self, project_root): ...
```

## 27.2. Claude Code

L’adapter génère :

```text
.claude/settings.json
.claude/hooks/
.mcp.json
```

## 27.3. Autres agents

Même contrat d’événements :

```text
SESSION_START
PRE_COMPACT
POST_COMPACT
PRE_TOOL
POST_TOOL
STOP
```

---

# 28. CLI universelle

## Commandes

```bash
mmu init
mmu scan
mmu configure
mmu validate
mmu generate
mmu install
mmu serve
mmu doctor
mmu migrate
mmu export
mmu import
mmu dashboard
mmu upgrade
```

### `mmu init`

Crée :

```text
.mmu/
project.yaml
playbook.md
capabilities.yaml
gates.yaml
policies.yaml
memory.sqlite
artifacts/
```

et installe l’intégration choisie.

### `mmu scan`

Analyse le projet sans créer automatiquement de vérité canonique.

### `mmu validate`

Valide les fichiers déclaratifs et leurs relations.

### `mmu generate`

Compile le MCP.

### `mmu doctor`

Vérifie l’installation runtime complète.

---

# 29. Dashboard visuel

## 29.1. Principe

Le Dashboard n’est pas seulement un éditeur de fichiers. C’est un **IDE de configuration et de génération de MMU**.

## 29.2. Parcours principal

```text
1. Scanner le projet
2. Détecter la structure
3. Proposer un profil
4. Choisir le domaine
5. Modifier la taxonomie
6. Définir les entités
7. Définir les relations
8. Configurer le Work Graph
9. Déclarer les capabilities
10. Construire les gates
11. Définir les policies
12. Configurer le Resume
13. Choisir les intégrations
14. Prévisualiser le MCP
15. Valider
16. Générer
17. Installer
18. Lancer Doctor
```

---

# 30. Scanner de projet

Le scanner doit détecter au minimum :

- gestionnaire de version ;
- langages ;
- frameworks ;
- gestionnaires de dépendances ;
- scripts de build ;
- suites de tests ;
- linters ;
- CI ;
- Docker ;
- documentation ;
- datasets ;
- assets ;
- sous-projets ;
- fichiers de configuration.

Il doit produire des observations `DETECTED`, jamais des vérités `PROVEN` par défaut.

---

# 31. Recommandation automatique de profil

Exemple :

```text
Détection :
TypeScript + React + Node + Vitest + Playwright + GitHub Actions

Profil recommandé :
Software / Web Application

Capabilities proposées :
✓ install
✓ build
✓ test
✓ lint
✓ typecheck
✓ e2e
✓ package

Gates proposées :
✓ BUILD_OK
✓ UNIT_TESTS_OK
✓ TYPECHECK_OK
✓ E2E_OK
```

L’utilisateur peut modifier chaque élément.

---

# 32. Capability Builder visuel

Chaque capability est affichée comme un contrat :

```text
Nom
Type
Runner
Commande / API
Entrées
Sorties
Timeout
Policy
Artifacts
Validator
Proof admissible ?
Confirmation requise ?
```

Le Dashboard doit refuser :

- commande non bornée ;
- chemins hors racines ;
- réseau sans policy ;
- capability sans timeout ;
- sortie non interprétable quand utilisée comme gate ;
- dépendance inexistante ;
- placeholder présenté comme validator.

---

# 33. Gate Builder

Écran :

```text
Gate : BUILD_OK

Capability : build

Exigences :
[✓] exit_code == 0
[✓] artifact exists
[ ] stdout contains "success"

Promotion :
[✓] peut satisfaire la gate
[✓] peut créer une proof
```

Le Dashboard doit indiquer clairement la différence entre :

- validation technique ;
- appréciation sémantique ;
- simple observation.

---

# 34. MCP Preview

Le Dashboard doit afficher avant génération :

```text
Core tools : 18
Project tools : 11
Read-only : 21
Write : 5
Sensitive : 3
Network : 2
Gates : 7
Capabilities : 16

Profile hash : ...
Policy hash : ...
```

### Alertes

```text
ERROR : capability X n’a aucun validator objectif.
WARNING : gate Y dépend d’une capability NETWORK.
ERROR : chemin de sortie hors périmètre.
WARNING : aucun secret HMAC configuré alors que PROVEN est activé.
```

---

# 35. Import d’un projet existant

Le Dashboard doit proposer :

```text
README
Docs
ADRs
TODO
CHANGELOG
Issues exportées
CI
Tests
Configuration
Git history
```

Le contenu importé doit être stocké avec provenance.

Par défaut :

```text
OBSERVED
```

et non `PROVEN`.

Le projet est ensuite progressivement enrichi par des preuves et validations.

---

# 36. Zero Pollution

L’installation d’Universal Dev-MMU ne doit nécessiter aucune modification du code métier.

Par défaut :

```text
project/
├── .mmu/
├── .claude/
└── code existant inchangé
```

Les fichiers temporaires :

```text
*.sqlite-wal
*.sqlite-shm
runtime/
```

restent ignorés.

La mémoire canonique et les fichiers de profile doivent être explicitement versionnables ou exportables selon la policy.

---

# 37. Migration ARET-MMU → Universal Dev-MMU

La migration doit être **progressive et réversible**.

## Phase 0 — Freeze

Créer un tag ou commit de référence ARET-MMU.

Capturer :

- tests ;
- schéma ;
- hash de migrations ;
- comportement MCP ;
- comportement des hooks ;
- bundle d’exemple ;
- état du repository.

## Phase 1 — Compatibility Layer

Créer un profile :

```text
profiles/aret.yaml
```

Le comportement doit rester fonctionnellement équivalent.

## Phase 2 — Extraction du Core

Déplacer sans changement sémantique :

- MemoryStore ;
- Evidence ;
- Audit ;
- Resume ;
- Bundles ;
- Addressing ;
- policies ;
- transactions.

## Phase 3 — Externalisation ARET

Déplacer :

- `PIPELINES` ARET ;
- playbook ARET ;
- toolchain ARET ;
- assets ARET ;
- concepts reverse engineering ;
- tests spécifiques.

vers :

```text
profiles/aret/
domains/aret/
```

## Phase 4 — Schéma universel

Migrer :

```text
function_symbol → symbol
brick → work_item
component → entity type COMPONENT
```

Ajouter les registres dynamiques.

## Phase 5 — Capability Engine

Remplacer le catalogue Python statique.

## Phase 6 — Work/Gates

Ajouter le graphe de travail et les gates.

## Phase 7 — MCP Compiler

Générer les outils projet.

## Phase 8 — Dashboard

Ajouter scanner + configurateur + générateur.

## Phase 9 — Conformance

Valider Universal MMU sur plusieurs domaines.

## Phase 10 — Dépréciation ARET API

Conserver temporairement des alias `aret_*` vers `mmu_*`.

---

# 38. Migration SQL proposée

## 001-006

Conserver pour compatibilité et historique.

## 007

Introduire :

```text
project_identity
entity_type
entity
relation_type
symbol
work_item
gate
execution
capability_catalog
policy
```

## 008

Migrer `function_symbol` vers `symbol`.

## 009

Migrer `brick` vers `work_item`.

## 010

Ajouter les registries dynamiques de types de knowledge.

## 011

Ajouter Work Graph / Gates.

## 012

Ajouter Profile Identity et hashes.

Chaque migration doit conserver son checksum immuable comme aujourd’hui.

---

# 39. Contraintes SQL à conserver

### PROVEN

Le trigger actuel de protection doit être conservé conceptuellement.

### Append-only

Une connaissance ne doit pas être réécrite silencieusement.

### Audit

Les mutations métier critiques doivent produire un événement d’audit.

### WAL

Les bundles et synchronisations doivent forcer un checkpoint WAL selon la politique actuelle.

### Confinement

Les chemins d’artefacts doivent rester bornés aux racines autorisées.

---

# 40. Tests de conformance du Core

Créer des fixtures :

```text
fixture-empty
fixture-software
fixture-web
fixture-game
fixture-research
fixture-data
fixture-document
fixture-hardware
fixture-multi-repo
fixture-no-git
fixture-existing-project
```

Chaque fixture doit valider :

```text
init
scan
configure
validate
generate
boot
find
read
write
proof
promotion
handoff
compact
resume
bundle
restore
doctor
```

---

# 41. Tests de sécurité

Tester au minimum :

- path traversal ;
- commande arbitraire ;
- injection shell ;
- injection de paramètres ;
- capability inconnue ;
- policy absente ;
- réseau non autorisé ;
- écriture hors scope ;
- artefact falsifié ;
- hash falsifié ;
- HMAC invalide ;
- promotion `PROVEN` sans proof ;
- preuve `SKIPPED` promue par erreur ;
- bundle altéré ;
- mauvais project identity ;
- profile hash incohérent ;
- resume hash incohérent ;
- mémoire importée dans le mauvais projet.

---

# 42. Tests de qualité des Gates

Une Gate ne doit jamais accepter une sortie purement déclarative sans validation.

Exemple à refuser :

```bash
echo "PASS"
```

si la capacité est censée vérifier une suite de tests.

Le validator doit attester d’un état réel du projet ou d’un artefact réel.

---

# 43. Tests de reprise

Tester :

```text
fresh session
→ SessionStart
→ resume injected
→ guard armed
→ acknowledge
→ tool allowed
```

Puis :

```text
session
→ PreCompact
→ PostCompact
→ resume rebuilt
→ hash changed
→ old acknowledgement rejected
```

Puis :

```text
corrupted memory
→ status degraded
→ loud failure
```

---

# 44. Tests de compatibilité ARET

Le profile ARET doit reproduire les propriétés actuelles :

```text
FIND / READ
PROVEN gating
HMAC evidence
Resume Guard
pipelines ARET
playbook ARET
roadmap
bundle
hooks
```

Il ne faut pas considérer la migration comme terminée tant que les tests ARET de référence ne sont pas équivalents ou meilleurs.

---

# 45. `mmu doctor`

Le Doctor doit produire un rapport machine + humain :

```text
PROJECT IDENTITY ........ PASS
PROFILE ................ PASS
SCHEMA .................. PASS
SQLITE INTEGRITY ........ PASS
WAL ..................... PASS
ARTIFACT STORE .......... PASS
HMAC .................... PASS
CAPABILITY CATALOG ...... PASS
GATES ................... PASS
POLICIES ................ PASS
RUNTIME ADAPTER ......... PASS
MCP ..................... PASS
HOOKS ................... PASS
RESUME .................. PASS
VCS ..................... PASS
```

Chaque échec doit pointer vers l’élément qui le répare.

---

# 46. Versionnage et profile hash

Calculer au minimum :

```text
profile_hash
policy_hash
capability_catalog_hash
gate_catalog_hash
mcp_build_hash
```

Une execution doit conserver les hashes nécessaires à sa reproductibilité.

---

# 47. Génération documentaire

Le générateur doit produire :

```text
MMU_SETUP.md
MMU_TOOLS.md
MMU_GATES.md
MMU_POLICIES.md
MMU_ARCHITECTURE.md
MMU_MAINTENANCE.md
```

Ces documents sont des vues dérivées du profile, non la source canonique de configuration.

---

# 48. Dashboard : modèles de domaines

Le produit doit fournir des templates :

## Software

- component
- module
- symbol
- test
- build
- deploy

## Game

- asset
- scene
- server
- event
- player/system state

## Research

- experiment
- hypothesis
- dataset
- result
- metric

## Data / ML

- dataset
- feature
- model
- evaluation
- metric
- pipeline

## Hardware

- board
- component
- firmware
- measurement
- device

## Documentation

- source
- document
- claim
- citation
- revision

Ces packs restent optionnels.

---

# 49. Le générateur de MCP « parfait »

Le système ne doit jamais promettre une perfection absolue. Il doit générer un MCP **optimal selon les contraintes déclarées et les capacités détectées**.

Le générateur doit optimiser :

- surface d’outils minimale ;
- sécurité ;
- pertinence ;
- contexte ;
- vérifiabilité ;
- maintenabilité ;
- compatibilité runtime.

Il doit produire un rapport :

```text
MCP generated

Core tools: 18
Project tools: 13
Read-only: 23
Write: 4
Sensitive: 4
Network: 1
Gates: 8
Capabilities: 17

Coverage:
Memory .......... 100%
Build ........... 100%
Test ............ 100%
Deploy .......... 80%
Provenance ...... 100%

Uncovered project areas:
- deployment rollback
- visual regression
```

Le projet peut alors choisir d’ajouter des capabilities.

---

# 50. Procédure de travail complète pour l’implémentation

## Étape 1 — établir le baseline

1. Taguer l’état actuel.
2. Lancer toute la suite de tests.
3. Capturer un bundle.
4. Capturer un état de conformance MCP.
5. Capturer le comportement des hooks.
6. Noter les versions Python / dépendances.

## Étape 2 — introduire une couche de compatibilité

Créer :

```text
mmu.*
```

avec alias temporaires :

```text
aret.*
```

## Étape 3 — créer le nouveau namespace

Introduire :

```text
universal_mmu/
```

sans supprimer l’ancien namespace.

## Étape 4 — déplacer les primitives

Déplacer progressivement :

```text
addressing
memory
proof
audit
resume
bundle
policy
```

## Étape 5 — introduire `project.yaml`

Faire démarrer le Store depuis une configuration explicite.

## Étape 6 — remplacer les hardcodes

Chaque constante ARET doit devenir une configuration ou un Domain Pack.

Créer une matrice :

```text
ARET hardcode
→ target abstraction
→ migration path
→ test
```

## Étape 7 — refactoriser le schéma

Ajouter les tables universelles puis migrer les concepts existants.

## Étape 8 — extraire les pipelines

Créer le Capability Engine puis réimplémenter les pipelines ARET comme capabilities du pack ARET.

## Étape 9 — ajouter Gates / Work Graph

Faire fonctionner les gates sur les executions et preuves réelles.

## Étape 10 — compiler le MCP

Construire le Tool Registry puis le générateur.

## Étape 11 — générer les hooks

Faire générer l’intégration par le runtime adapter.

## Étape 12 — créer le Dashboard

Commencer par un wizard simple puis évoluer vers un éditeur graphique complet.

## Étape 13 — conformance multi-domaines

Valider sur plusieurs fixtures.

## Étape 14 — migration finale ARET

Passer ARET sur son propre profile généré et vérifier qu’il ne dépend plus du Core d’éléments ARET.

---

# 51. Méthode d’implémentation par lot

Chaque changement doit suivre :

```text
1. Inspecter
2. Définir l’invariant
3. Ajouter ou modifier les tests
4. Implémenter
5. Exécuter les tests ciblés
6. Exécuter les tests Core
7. Exécuter les tests de conformance
8. Exécuter les tests ARET si concerné
9. Vérifier git diff
10. Vérifier absence de hardcode ARET
11. Commit atomique
12. Mise à jour mémoire / handoff
```

Aucun « big bang ».

---

# 52. Registre de découplage obligatoire

Créer un document interne :

```text
DECOUPLING_MATRIX.md
```

Colonnes :

| Élément | Couplage actuel | Abstraction cible | Fichier cible | Tests | Statut |
|---|---|---|---|---|---|
| `ARET://` | Core | `mmu://` | `core/addressing.py` | addressing | TODO |
| `function_symbol` | SQL | `symbol/entity` | schema | migration | TODO |
| `brick` | SQL | `work_item` | schema | work graph | TODO |
| `PIPELINES` | Python | Capability Catalog | capabilities | capability tests | TODO |
| `SERVER_INSTRUCTIONS` | Python | generated instructions | generator | snapshot tests | TODO |
| ARET playbook | Core config | Domain Pack | domains/aret | profile tests | TODO |
| ARET repo root | server | Workspace | core/workspace.py | security | TODO |

Ce tableau devient la référence d’avancement.

---

# 53. Registre des invariants non régressifs

Créer :

```text
INVARIANTS.md
```

## Invariants absolus

```text
I001 SQLite = canonique
I002 FIND != READ
I003 Knowledge append-only
I004 PROVEN => admissible PASS
I005 Artifact hash checked before read
I006 Shell direct != canonical proof
I007 Capability catalogue closed
I008 User input cannot create arbitrary command
I009 Resume hash must match armed contract
I010 Bundle manifest/hash chain valid
I011 Project identity must match
I012 Profile hash attached to generated runtime/proofs
```

Toute modification Core doit indiquer les invariants affectés et les tests associés.

---

# 54. Definition of Done globale

L’universalisation n’est terminée que lorsque :

### Core

- aucun code Core ne dépend d’ARET ;
- tous les tests Core passent ;
- migrations vérifiées ;
- bundles vérifiés.

### ARET

- ARET fonctionne comme Domain Pack ;
- ses pipelines existants fonctionnent ;
- ses gates fonctionnent ;
- ses preuves restent admissibles ;
- son Resume Guard reste opérationnel.

### Universalité

- au moins cinq domaines différents sont validés ;
- un projet sans Git fonctionne ;
- un projet multi-repo fonctionne ;
- un projet existant peut être importé ;
- un projet vide peut être initialisé.

### Génération

- Dashboard génère un profile valide ;
- le profile est déterministe ;
- le MCP généré est reproductible ;
- `mmu doctor` passe ;
- l’installation est réparable automatiquement.

### Sécurité

- pas de shell arbitraire ;
- pas de path traversal ;
- pas de promotion sans preuve ;
- pas de mémoire croisée entre projets ;
- pas de rupture silencieuse.

---

# 55. Roadmap recommandée

## M0 — Baseline

- freeze ;
- tests ;
- bundle ;
- matrice de couplage.

## M1 — Universal Core

- config ;
- project identity ;
- workspace resolver ;
- generic addressing ;
- service decomposition.

## M2 — Universal Schema

- entity registry ;
- relation registry ;
- symbol ;
- work item ;
- execution ;
- capability registry.

## M3 — Capability / Evidence / Gates

- runner engine ;
- validators ;
- evidence ;
- gates ;
- work graph.

## M4 — ARET Domain Pack

- migration des pipelines ARET ;
- playbook ARET ;
- toolchain ARET ;
- compatibilité.

## M5 — MCP Compiler

- Tool Registry ;
- instruction generator ;
- hook generator ;
- policy generator.

## M6 — CLI

- init ;
- scan ;
- validate ;
- generate ;
- doctor ;
- install.

## M7 — Dashboard

- wizard ;
- scanner ;
- capability editor ;
- gate builder ;
- policy editor ;
- MCP preview.

## M8 — Conformance multi-domaines

- software ;
- game ;
- research ;
- data ;
- documentation / hardware.

## M9 — Release

- package ;
- documentation ;
- migration tool ;
- compatibility guarantees.

---

# 56. Stratégie de packaging

Le projet doit pouvoir être installé globalement :

```bash
pip install universal-dev-mmu
```

ou via un environnement isolé :

```bash
uvx universal-dev-mmu
```

ou localement :

```bash
python -m mmu.cli
```

Le projet utilisateur ne doit pas avoir à installer Python si le runtime choisi utilise une autre distribution du MCP généré.

Le Dashboard doit pouvoir générer plusieurs formes de distribution :

```text
pip package
container
standalone executable
vendored runtime
```

---

# 57. Compatibility policy

Pendant la migration :

```text
ARET-MMU v1
        ↓
compat layer
        ↓
Universal Dev-MMU v2
```

Les API `aret_*` sont conservées en alias pendant une période de transition.

Les adresses `ARET://` sont acceptées en lecture.

Les nouveaux objets utilisent `mmu://`.

---

# 58. Principes de conception à ne jamais violer

1. Le modèle n’est jamais la base.
2. Le texte du modèle n’est jamais une preuve suffisante.
3. FIND n’est jamais une preuve.
4. Une recherche ne doit jamais réécrire silencieusement la mémoire.
5. Une donnée absente reste absente.
6. Un résultat indéterminé reste indéterminé.
7. Une capability ne reçoit jamais une commande arbitraire.
8. Toute action sensible est policy-gated.
9. Toute connaissance `PROVEN` est traçable jusqu’à sa preuve.
10. Toute preuve est traçable jusqu’à son execution et son environnement.
11. Toute reprise est liée à un état hashé.
12. Toute mémoire est liée à une identité de projet.
13. Toute génération de MCP est déterministe.
14. Toute spécialisation métier appartient à un Domain Pack.
15. Le Core doit survivre à la disparition de l’agent et du runtime d’origine.

---

# 59. Résultat attendu

À la fin du chantier, un utilisateur doit pouvoir faire :

```bash
cd mon-projet
mmu init
mmu scan
mmu dashboard
```

Puis, dans le Dashboard :

```text
Projet détecté
        ↓
Profil proposé
        ↓
Taxonomie
        ↓
Entités
        ↓
Relations
        ↓
Workflow
        ↓
Capabilities
        ↓
Gates
        ↓
Policies
        ↓
Resume
        ↓
Intégration Agent
        ↓
Preview MCP
        ↓
Validate
        ↓
Generate
        ↓
Install
```

Et obtenir :

```text
.mmu/
├── project.yaml
├── playbook.md
├── capabilities.yaml
├── gates.yaml
├── policies.yaml
├── memory.sqlite
├── artifacts/
└── runtime/

.mcp.json
.claude/
```

sans modifier le code métier du projet.

L’agent dispose alors d’un MCP dont la surface reflète réellement le projet, avec :

```text
mémoire persistante
+ provenance
+ graph
+ état courant
+ reprise
+ preuves
+ gates
+ capacités
+ politiques
+ audit
```

Le même moteur peut ensuite être configuré pour un autre projet totalement différent sans fork du Core.

---

# 60. Conclusion architecturale

Le projet final ne doit plus être pensé comme :

```text
ARET-MMU + configuration
```

mais comme :

```text
Universal Dev-MMU
│
├── Core universel
├── Domain Packs
├── Project Profiles
├── Capability Engine
├── Gate Engine
├── Evidence Store
├── Policy Engine
├── MCP Compiler
├── Runtime Adapters
├── Dashboard
└── CLI
```

**ARET devient le premier client critique et le premier Domain Pack de référence.**

La force de l’ancien ARET-MMU — mémoire déterministe, provenance, preuves, reprise, invariants, garde-fous — est conservée. Les idées utiles d’Unlazy — décomposition explicite et validation par gates — sont absorbées dans un modèle plus général. La configuration, les pipelines, les entités, les relations, les workflows et les politiques deviennent déclaratifs. Le Dashboard devient un compilateur de projet et non un simple formulaire.

Le critère de réussite ultime est donc :

> **À partir d’un projet inconnu, le système doit pouvoir découvrir son environnement, proposer un modèle, permettre à l’utilisateur de le corriger visuellement, valider ce modèle, générer un MCP déterministe et sécurisé, installer les intégrations nécessaires et démontrer par des tests de conformance que ce MCP respecte les invariants du Universal Dev-MMU.**

---

# Annexe A — Sources et base de travail

- Dépôt de référence : `https://github.com/aciderix/ARET-MMU`
- Spécification d’universalisation fournie : `ARET-MMU_Specification_Universalisation (2).md`
- Éléments inspectés dans le dépôt :
  - `aret-memory/core/repository.py`
  - `aret-memory/core/addressing.py`
  - `aret-memory/schema/001_initial.sql`
  - `aret-memory/evidence/adapters/oracles.py`
  - `aret-memory/evidence/adapters/pipelines.py`
  - `aret-memory/aret_mmu_server.py`
  - `aret-memory/docs/CONTRATS_OPERATIONNELS.md`
  - `aret-memory/docs/CONTRAT_ORACLES.md`
  - `aret-memory/docs/ADAPTATEURS_ORACLES.md`
  - `aret-memory/docs/architecture/ARET-MMU_Architecture_Document_Definitif_v5_final.md`
  - `aret-memory/integration/INSTALL.md`
  - `aret-memory/config/playbook.md`
  - suites de tests `aret-memory/tests/`

---

# Annexe B — Critère de sortie du chantier

Le chantier est considéré **DONE** lorsque la commande suivante fonctionne sur une machine propre :

```bash
mmu init
mmu scan
mmu validate
mmu generate
mmu doctor
```

et qu’un projet test au moins dans chacun des profils suivants peut être configuré et démarrer une session agent avec :

```text
boot
resume
find
read
work graph
gate
capability execution
evidence
proof
promotion
bundle
restore
```

sans modifier son code métier et sans introduire de dépendance à ARET dans le Core.

