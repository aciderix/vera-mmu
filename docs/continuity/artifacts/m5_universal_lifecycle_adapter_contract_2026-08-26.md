# Contrat de cadrage M5 — lifecycle universel, reprise et adapters d’hôte

> **Statut :** M5-J/K sont livrés comme Core/liaison MCP transport-neutres et M5-L comme adapter Claude Code local opt-in ; M5-M et suivants restent à réaliser. Ce document ne revendique qu’un hook exécutable **Claude Code local** installé opt-in ; il ne modifie aucun environnement home/cloud et ne revendique aucune compatibilité d’exécution hôte concrète au-delà de ce périmètre. Il remplace le cadrage trop étroit « un hook SessionStart Claude » par l’extraction du mécanisme de reprise fonctionnel ARET vers un Core VERA indépendant de l’hôte.

## 1. Décision

ARET-MMU dispose déjà d’un cycle de reprise complet : dossier issu de la mémoire canonique, hash de contrat, état de garde par session, modes `hard` et `soft`, acquittement contrôlé, refus pré-action, nudge de fin de session et réarmement autour d’une compaction. Les wrappers Claude, le bootstrap de container, le scope de confiance et la synchronisation de mémoire sont des **traductions d’hôte ou de déploiement**, non le mécanisme à mettre dans le Core.[1] [2]

**VERA adopte donc l’architecture suivante :** un `Lifecycle Core` transport-neutre porte le dossier, le rituel, la garde et l’audit. Des adapters d’hôte immuables et manifest-bound déclarent ce qu’ils savent réellement livrer, puis traduisent des événements VERA normalisés vers Claude Code, Codex, Gemini CLI, Antigravity ou un autre hôte. Aucun adapter ne peut proclamer un niveau de reprise supérieur à ses capacités documentées et testées.

```text
Project Profile + Store + manifest/instructions attestés
                         │
                         ▼
                  VERA Lifecycle Core
 dossier • hash • rituel • garde • audit • état de session
                         │
                   registry d’adapters
                         │
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼
Claude Code          Codex/Gemini      Antigravity/autre
local ou cloud       adapters dédiés   adapters dédiés
       │                 │                 │
config/hook hôte    config/hook hôte   config/hook hôte
       └──────── installation opt-in + doctor ────────┘
```

## 2. État de départ constaté

| Surface | État factuel au 26 août 2026 | Limite explicite |
|---|---|---|
| ARET de référence | Reprise fonctionnelle à `SessionStart`, `PreCompact`, `PostCompact`, `PreToolUse`, `PostToolUse` ciblé et `Stop`. | Les scripts, le dossier `.aret-memory`, les concepts ARET et le bootstrap de venv ne sont pas transférables tels quels au Core. |
| VERA M5-A à M5-L | Façade MCP réelle, manifeste, registry, adapter Pack, instructions, config, plan de hook, plan Claude, installation `.mcp.json` opt-in, Resume Dossier, garde locale hard/soft, registry lifecycle, acquittement MCP contextualisé et adapter Claude local avec hooks/installateur/doctor. | Seul Claude Code local est exécuté/installable ; cloud, home/trust/setup, multi-session et autres hôtes restent exclus. |
| Installation M5-I | Fusion atomique et idempotente du seul serveur MCP attesté dans `.mcp.json`, avec confirmation obligatoire. | Aucun `.claude`, script, hook ou setup cloud n’est écrit. Le serveur générique reste fail-closed sans hôte de Pack. |
| Profil/Store/runtime VERA | Identité project-bound, runtime confiné, SQLite migré et audit technique ; M5-J y écrit un état lifecycle atomique et audité, M5-K le lie à un registry/plan attesté et à MCP, M5-L y lie une session Claude locale et un état d’installation. | Aucun provider automatique de contenu, profil lifecycle multi-hôte, doctor cloud ou adapter hôte autre que Claude local ne consomme encore ces fondations. |

## 3. Contrat universel de lifecycle

Le Core emploie uniquement les événements suivants. Les noms de Claude, Codex, Gemini ou Antigravity ne sont pas admis dans cette couche.

| Événement VERA | Sémantique | Équivalents possibles côté hôte |
|---|---|---|
| `SESSION_OPEN` | Une session est créée, restaurée ou remise à zéro. | `SessionStart`, ou équivalent de début d’invocation. |
| `CONTEXT_PREPARE` | L’hôte prévient d’une perte/réduction de contexte imminente. | `PreCompact`, `PreCompress`. |
| `CONTEXT_RESTORED` | L’hôte confirme une perte/réconstruction de contexte. | `PostCompact`. |
| `ACTION_PRECHECK` | L’hôte demande une décision avant une action agent. | `PreToolUse`, `BeforeTool`. |
| `ACKNOWLEDGEMENT_RESULT` | L’hôte observe le résultat réel de l’acquittement de reprise. | `PostToolUse`, `AfterTool`. |
| `SESSION_ENDING` | La session/l’agent essaie de se terminer. | `Stop`, `SessionEnd`, `AfterAgent`. |

Un adapter peut ne mapper qu’un sous-ensemble. Dans ce cas, le profil, le manifeste et le doctor doivent plafonner le niveau de garantie ; le Core ne synthétise jamais un événement absent.

### 3.1. Dossier et rituel de reprise

`ResumeDossierService` construit désormais un dossier borné, hashé et lié à l’identité du projet à partir de sections explicitement fournies par l’appelant. Les providers qui extraieront règles, état/handoff, adresses, capacités/gates/policies, contexte VCS et risques restent une extension ultérieure ; aucun de ces contenus n’est aujourd’hui inventé ou hardcodé par le Core.[3]

`ResumeGuardService` valide la liste de sections exactes et bornées enregistrée avec le contrat. Il contrôle structure, bornes et hash du dossier ; il ne prétend pas juger par NLP la véracité du récapitulatif. M5-K atteste et transporte le contexte de session côté serveur ; l’observation par un hôte concret reste la responsabilité de l’adapter M5-L ou suivant. Aucun champ, vocabulaire ou playbook ARET n’est codé dans le Core.

### 3.2. Garde de reprise

| Élément d’état | Autorité | Règle de sécurité |
|---|---|---|
| `project_hash` | `ProjectIdentity` VERA | Un état d’un autre projet est invalide. |
| `adapter_id` | Registry VERA manifest-bound depuis M5-K | L’état ne survit pas à un adapter différent ; le client MCP ne choisit jamais cet adapter. |
| `session_key` | Adapter hôte futur, jamais client MCP | Une identité fournie par l’appelant est hashée avec projet+adapter ; une session non identifiable est refusée en mode dur. |
| `reason` | Enum Core | Distingue ouverture, reprise vivante, reset et perte de contexte. |
| `resume_contract_hash` | Dossier VERA canonique | Tout acquittement hash-divergent est refusé. |
| `mode` | Core ; maximum déclaré par le plan M5-K | `hard` et `soft` sont disponibles localement ; l’enforcement d’un maximum par un adapter concret commence à M5-L. |
| `status` | Machine d’état Core | `ARMED`, `ACKNOWLEDGED`, `DEGRADED`. |
| attestation d’acquittement | `LifecycleAdapterRegistry` + contexte serveur M5-K ; résultat hôte concret à M5-L+ | Le Core exige hash et sections exacts ; M5-K retire session/hash du client sans prétendre qu’un hook hôte est déjà installé. |

L’état sera local au runtime VERA, project-bound, borné et écrit atomiquement. Sa corruption ou son ambiguïté ne doit pas devenir une reprise silencieuse. Les transitions déterminantes doivent être auditées dans SQLite, sans transformer le texte du hook en connaissance canonique.

### 3.3. Anti-deadlock non négociable

Le comportement ARET doit être conservé : un dossier prêt peut armer une garde `hard` et refuser les actions jusqu’au rituel observé. Un dossier dégradé doit rester **bruyant et armé**, mais basculer en `soft` lorsqu’un acquittement fiable n’est pas réalisable ; il avertit et indique une réparation, sans bloquer la session dans une impasse.[1]

Une reprise vivante explicitement identifiée peut conserver un acquittement déjà établi. Une vraie perte de contexte, un reset ou un changement de contrat réarme la garde. Cette différence est une propriété du Core, non un détail Claude Code.

## 4. Contrat des adapters d’hôte

Un adapter est un objet runtime fourni par le processus hôte et enregistré avant le démarrage. Il ne peut pas être choisi par le client MCP, par un paramètre de tool, ni par un fichier de projet non attesté.

| Propriété | Exigence |
|---|---|
| Identité | `adapter_id`, version et capabilities immuables ; binding au manifeste de génération. |
| Mapping | Table fermée événement hôte → événement VERA ; refus des événements inconnus. |
| Session | Extraction de l’identité depuis le payload hôte. Le modèle ne choisit jamais cette identité. |
| Delivery | Traduction d’un résultat normalisé uniquement dans le protocole documenté de l’hôte : contexte, refus, notice ou absence d’effet. |
| Capabilities | Injection, interception pré-action, observation post-action, fin de session, compaction, installation locale, bootstrap cloud et trust sont déclarés séparément. |
| Installateur | Plan attesté, revue/confirmation, fusion non destructive, refus de symlink/conflit, écriture atomique. |
| Doctor | Verdict par capability installée et réellement disponible ; jamais un simple « configuré = prêt ». |

Le Core ne construit aucun script shell. Lorsqu’un hôte exige une commande de hook, elle est produite par l’adapter concerné depuis un plan attesté, avec arguments fermés. Elle ne peut contenir ni commande fournie par le modèle, ni chemin arbitraire, ni interpolation non vérifiée.

## 5. Niveaux de compatibilité déclarables

| Niveau | Conditions réelles | Promesse autorisée |
|---|---|---|
| `MCP_ONLY` | Serveur MCP utilisable. | Aucun lifecycle automatique. |
| `RESUME_DELIVERY` | Ouverture identifiable et injection de contexte. | Dossier attesté distribué ; pas de blocage annoncé. |
| `RESUME_GUARD_SOFT` | Niveau précédent et canal de notice/fin de session. | État dégradé visible et réparable sans deadlock. |
| `RESUME_GUARD_HARD` | Injection, identité stable, interception pré-action et observation fiable de l’acquittement. | Actions couvertes bloquées jusqu’au rituel validé. |
| `COMPACTION_AWARE` | Événements avant/après perte de contexte. | Checkpoint/réinjection/réarmement après compaction. |
| `CLOUD_BOOTSTRAPPED` | Déploiement de container défini, bootstrap/trust/persistance validés. | Démarrage cloud testable pour cet hôte, sans promesse de généralité. |

## 6. Matrice des hôtes étudiés

| Adapter cible | Capacité documentée | Niveau maximal à viser | Limite à rendre visible |
|---|---|---|---|
| Claude Code local | Session, pré/post-tool, stop et pré/post-compaction ; blocage pré-action. | `COMPACTION_AWARE` + `RESUME_GUARD_HARD`. | Aucun avant livraison de l’adapter local réel. |
| Claude Code web/cloud | Même lifecycle de hook ; environnement cloud avec setup, réseau et variables. | `CLOUD_BOOTSTRAPPED` après tests spécifiques. | Trust, bootstrap de dépendances et persistance restent des actions séparées, jamais induites par `.mcp.json`. |
| Codex local | Lifecycle riche, session id, hooks de commande ou MCP ; pré/post-compaction. | `COMPACTION_AWARE` pour outils effectivement couverts. | Les hooks peuvent être concurrents ; serveur MCP indisponible et outils hébergés non interceptés ne constituent pas une garde universelle.[4] |
| Gemini CLI | Session start, interception avant/après outil, identité de session et pré-compression advisory. | `RESUME_GUARD_HARD` pour outils couverts, sans post-compaction. | La migration annoncée vers Antigravity impose un adapter versionné et un doctor qui identifie le client.[5] |
| Antigravity | MCP, injection `PreInvocation`, interception `PreToolUse`, observation `PostToolUse`, `Stop`. | `TURN_GUARD_HARD`. | Aucun `SessionStart`/pre/post-compaction équivalent n’est publié dans la surface étudiée ; ne pas annoncer reprise automatique complète.[6] |
| Hôte MCP générique | MCP seulement. | `MCP_ONLY`. | Le modèle devra appeler les outils de reprise explicitement ; aucune garde hôte n’est promise. |

> **Conséquence :** « compatible avec toute IA » signifie ici que VERA possède un contrat et un adapter registry extensibles. Cela ne signifie jamais que Codex, Gemini, Antigravity ou un futur client sont déjà supportés, ni qu’un niveau de sécurité est identique partout.

## 7. Paramétrage du profil et du manifeste

Le profil devra choisir une stratégie sans modifier le code métier du projet. Le manifeste compilé doit ensuite lier cette demande à la capacité réellement fournie par l’adapter.

| Élément | Exemples | Règle |
|---|---|---|
| `integration.adapter` | `claude-code-local`, `claude-code-cloud`, `codex-local`, `gemini-cli`, `antigravity`, `generic-mcp` | Sélection contrôlée au démarrage, jamais par un client MCP. |
| `integration.mode` | `MCP_ONLY`, `RESUME_DELIVERY`, `RESUME_GUARD_SOFT`, `RESUME_GUARD_HARD` | Refus si le niveau demandé excède les capabilities de l’adapter. |
| `integration.persistence` | `LOCAL_RUNTIME`, `HOST_MANAGED`, `VCS_OPT_IN` | Ne déclenche aucun push ni sync automatique. |
| `integration.cloud_bootstrap` | `DISABLED`, `REVIEW_ONLY`, `OPT_IN` | N’installe ni ne lance de setup ou de réseau sans confirmation distincte. |
| `resume.sections` | Liste déclarée de sections | Spécifie le rituel sans injecter la doctrine ARET dans le Core. |
| `resume.degraded_policy` | `SOFT_NUDGE`, `FAIL_LOUD_ONLY` | Interdit le blocage dur en absence de voie d’acquittement sûre. |

Le `mcp_build_hash` doit être complété par un hash lifecycle et le binding `adapter_id`/version/niveau de compatibilité. Une divergence profil → manifest → plan d’installation → adapter actif doit être traitée comme un refus du doctor.

## 8. Jalons de portage, ordre et gates

| ID | Périmètre strict | Gate de sortie | Exclusions obligatoires |
|---|---|---|---|
| **M5-J** | `Lifecycle Core` et `ResumeDossierService` : état session project-bound, hash de dossier, machine d’état, modes hard/soft et audit ; les sections sont fournies explicitement, sans provider de contenu automatique. | **`PASS`** : 9 tests purs sans hôte couvrent hash divergent, sessions/adapters isolés, reprise vivante, compaction, corruption, dégradé sans deadlock, identité absente et symlink ; suite `438 passed, 37 subtests passed`, scans et roue isolée passent. | MCP public, wrapper, commande, fichier hôte, installation, Pack, bootstrap cloud. |
| **M5-K** | Registry d’adapters lifecycle, plan `vera-lifecycle-adapter-plan/v1` attesté et extension MCP d’acquittement contextualisé. | **`PASS`** : fixtures registry/plan, vrai client MCP stdio et refus d’injection session/hash/verdict/adapter ; suite `444 passed, 37 subtests passed`, scans et roue isolée passent. | Installation de hooks, adapter hôte concret et sélection Pack automatique. |
| **M5-L** | Adapter `claude-code-local` : plan spécifique, handlers/entry points fermés, installation opt-in, fusion sûre et doctor. | **`PASS`** : hook stdin/stdout, garde hard, compaction, conflit de session, install/idempotence/conflit/symlink, vrai serveur MCP stdio et suite `451 passed, 37 subtests passed`. | Cloud, trust utilisateur, réseau/bootstrap, push/sync implicite, multi-session. |
| **M5-M.1** | Plan `vera-claude-code-cloud/v1` lié aux snapshots M5-B/E/F/G/H/J/K/L, provider `PREINSTALLED_VERA` réseau-interdit et doctor observationnel. | **`PASS`** : plan stable/refus stale/provider, doctor `RUNTIME_MISSING`/trust pending-disabled-unverifiable/`RUNTIME_READY`, 4 tests ; suite `455 passed, 37 subtests passed`. | Entry point/hook cloud, connexion MCP réelle, roue/bootstrap, réseau, secret, écriture trust user-scope. |
| **M5-M.2** | Adapter `claude-code-cloud-v1` staged : état runtime atomique confirmé, session cloud distincte, hook des six événements, MCP stdio deny-by-default et trois entry points distribués. | **`PASS`** : staging→hook JSON→MCP stdio→ack sections-only→allow, compaction réarmée, 6 tests cloud et suite `457 passed, 37 subtests passed`; roue isolée `PASS`. | `.claude`, `.mcp.json`, home trust, setup, roue/bootstrap, réseau, secret, connexion/préuve Claude Code web live. |
| **M5-M.3a** | Preview, fusion et application opt-in **project-local** de configuration hôte cloud ; état runtime hashé et user-scope explicitement absent. | **`PASS`** : preview stable, conservation tiers, conflits/symlinks, confirmation/apply et runtime M5-M.2 testés ; suite `462 passed, 37 subtests passed`, roue isolée avec quatre entry points cloud. | Approbation user-scope, lecture/écriture home, secrets, réseau/bootstrap, connexion et preuve Claude Code web live. |
| **M5-M.3b** | Preview/fusion de l’unique approbation MCP VERA user-scope, préconditionnée par M5-M.3a et gardée par deux confirmations transactionnelles distinctes. | **`PASS` pour le mécanisme sous home simulé** : précondition, conflits, symlink, preview CLI et deux confirmations testés ; suite `465 passed, 37 subtests passed`. Écriture réelle et observation host restent `NOT_RUN`. | Approbation automatique cachée, écriture home sans preview/double confirmation, secrets, réseau/bootstrap, promotion de trust web ou push automatique. |
| **M5-N** | Adapter Codex : compiler sa config/hooks, respecter trust et couverture d’interception. | Conformance au niveau effectivement annoncé, y compris indisponibilité MCP et concurrence de hooks. | Prétention de garde totale sur outils non interceptés. |
| **M5-O** | Adapter Gemini CLI, versionné et conditionné à une détection du client. | Tests SessionStart/BeforeTool/AfterTool/PreCompress selon les garanties documentées. | Promesse PostCompact ou support durable sans doctor de version. |
| **M5-P** | Adapter Antigravity. | Tests `PreInvocation`/`PreToolUse`/`PostToolUse`/`Stop`, niveau `TURN_GUARD_HARD`. | Émulation fictive d’une compaction ou d’un démarrage de session absent. |
| **M5-Q** | Adapter MCP générique + rapport de compatibilité de futurs hôtes. | `MCP_ONLY` sûr et doc de capabilities. | Toute automation de reprise sans événement hôte attesté. |

### 8.1. Prochain incrément autorisé

M5-M.3a et le mécanisme M5-M.3b sont livrés. Le prochain acte autorisé n’est **pas** une évolution automatique : présenter le preview du user-scope réel, obtenir deux confirmations transactionnelles explicites et séparées immédiatement avant l’écriture, contrôler le retour host, puis exécuter le protocole de preuve live dans une session cloud fraîche. Il ne doit ni réutiliser implicitement les fichiers locaux, ni effectuer réseau/bootstrap/push sans confirmation. Cela évite de recréer un script ARET sous un nouveau nom avant de prouver le premier hôte complet.

## 9. Invariants et non-régressions à ajouter au plan de tests

1. Un client MCP ne choisit jamais adapter, session, état de garde, hash de dossier, résultat d’acquittement, commande, artifact ou verdict.
2. Un adapter absent, inconnu, incompatible ou non manifest-bound refuse l’activation.
3. Une session sans identité ne devient jamais acquittée ; en mode dur, l’action couverte est refusée.
4. Un hash de dossier ou un projet divergent ne peut pas lever une garde.
5. Un état dégradé est toujours visible et audité, mais ne crée pas un deadlock quand l’acquittement est indisponible.
6. Une reprise vivante explicitement qualifiée ne réarme pas arbitrairement ; une vraie perte de contexte réarme.
7. Le Core ne contient ni termes, imports, scripts, commandes, dépendances réseau ou règles métier ARET.
8. Aucune installation de hook, modification de trust, bootstrap cloud, synchronisation VCS ou appel réseau n’est effectuée sans un plan attesté et une confirmation propre.
9. Le doctor distingue `NOT_INSTALLED`, `CONFIGURED`, `TRUST_PENDING`, `RUNTIME_UNAVAILABLE`, `PARTIALLY_SUPPORTED` et `READY` ; il ne transforme aucun état intermédiaire en prêt.

## 10. Position actuelle et suite

**M5-A à M5-M.3a restent `PASS`; M5-M.3b est `PASS` pour son mécanisme sous home simulé. M5 demeure `IN_PROGRESS`.** M5-J a livré le mécanisme local, M5-K son attestation/transport MCP, M5-L le premier hôte local opt-in, M5-M.1 le plan/doctor cloud préinstallé, M5-M.2 l’adapter cloud staged, M5-M.3a la configuration project-local attestée et M5-M.3b la préparation user-scope à deux gates. L’écriture user-scope réelle et la preuve d’un hôte cloud réel restent `NOT_RUN`; la voie M5-N→M5-Q ajoute ensuite les autres adapters à des niveaux de preuve explicites. Aucun résultat d’oracle ARET n’est requis pour cette conformance : les suites démontrent le transport et la gouvernance de verdicts, non l’environnement local Wine.

### Références

[1]: ../../../../ARET-MMU/aret-memory/hooks/resume_guard.py "ARET-MMU — garde de reprise (lecture seule)"
[2]: ../../../../ARET-MMU/aret-memory/integration/INSTALL.md "ARET-MMU — intégration Claude et container (lecture seule)"
[3]: ../../../../ARET-MMU/aret-memory/hooks/common.py "ARET-MMU — dossier de reprise (lecture seule)"
[4]: https://learn.chatgpt.com/docs/hooks "Codex — Hooks"
[5]: https://geminicli.com/docs/hooks/reference/ "Gemini CLI — Hooks reference"
[6]: https://antigravity.google/docs/hooks/ "Google Antigravity — Hooks"
[7]: https://code.claude.com/docs/en/hooks "Claude Code — Hooks reference"
[8]: https://code.claude.com/docs/en/claude-code-on-the-web "Claude Code on the web"
[9]: ../../../src/vera_mmu/mcp_hooks.py "VERA — plan déclaratif de hooks"
[10]: ../../../src/vera_mmu/claude_code_installer.py "VERA — installateur MCP M5-I"
