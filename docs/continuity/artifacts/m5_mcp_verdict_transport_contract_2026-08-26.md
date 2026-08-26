# M5 — Façade MCP, manifeste, registries, adapters, lifecycle et installations — jalons M5-A/B/C/D/E/F/G/H/I/J/K/L — 2026-08-26

> **Statut :** `M5-A/B/C/D/E/F/G/H/I/J/K/L/M.1/M.2 PASS` — façade `5ffe182`, manifeste `5de260d`, registry `50cc79a`, adapter Pack `e073fa2`, instructions `9010293`, config `5dab574`, hooks `ea7235a`, plan hôte `8b38b1b`, installateur `674929c`, Lifecycle Core `e576b1a`, registry/acquittement `df73425`, adapter Claude local `45fe9af`, plan/doctor cloud `940fb7e`, adapter cloud staged `f79415b`.
> **Portée :** transport fermé, manifeste, registries runtime/lifecycle, runtime de Pack, doctrine, config, cycle SessionStart, revue hôte, installation MCP opt-in, acquittement contextualisé, plan cloud préinstallé et adapter cloud runtime-confined. L’installation/trust host cloud, la preuve Claude Code web live et les adapters d’hôtes autres que Claude restent hors des jalons réalisés.

## 1. Décision de portage

ARET-MMU était déjà un serveur MCP opérationnel : catalogue fermé, transport `stdio` et HTTP, enveloppes d’erreur structurées et test de bout en bout par un vrai client. VERA-MMU n’a donc **pas** réimplémenté le protocole MCP. Le jalon M5-A porte ce socle de transport et ses garde-fous, puis le raccorde au Core universel livré par M1–M3 et aux Domain Packs isolés par M4.

> La façade MCP est un adaptateur : elle ne réinterprète jamais un verdict et ne remplace jamais les policies du Core.

| Référence ARET-MMU | Portage M5-A VERA | Décision |
|---|---|---|
| Serveur MCP, `stdio`, réponses structurées et client réel | `src/vera_mmu/mcp_server.py`, SDK `mcp>=2.0,<3.0`, entry point `vmmu-mcp` | Porté et adapté. |
| Catalogue fermé / paramètres bornés | Huit outils publics exactement, schémas MCP générés par le SDK | Porté comme invariant. |
| Oracles et pipelines ARET | Adapter de fixture déclaré côté serveur uniquement | Gardé hors du Core ; l’adapter réel relève d’un manifest/Pack postérieur. |
| Front, handoff, knowledge, hooks spécifiques ARET | Aucun portage mécanique | À généraliser dans les lots M5/M6 suivants. |
| Services universels capability, evidence, validation, admission et gate | Appelés par la façade sans dupliquer leur sémantique | Réutilisés. |
| Catalogue/policies/contracts/adapters déclarés | `mcp_manifest.py` compile une forme canonique liée au projet et aux migrations | Ajouté en M5-B, sans shell ni runtime implicite. |
| Résolution d’adapter | `mcp_adapters.py` indexe des objets hôte, sans chargement dynamique, puis résout chaque capability attestée | Ajouté en M5-C, manifest-bound et fail-closed. |
| Adapter de Pack | `domain_packs/aret/mcp_adapter.py` délègue une capability ARET au runner fermé et crée ses références de gate | Ajouté en M5-D ; absent du Core. |
| Instructions MCP | `mcp_instructions.py` dérive une doctrine stable et le catalogue manifeste vers texte/hash | Ajouté en M5-E ; sans playbook ni contenu de Pack. |
| Configuration MCP | `mcp_integration.py` dérive un JSON `mcpServers` standard depuis manifeste+instructions | Ajouté en M5-F ; prévisualisation runtime, pas d’installation implicite. |
| Plan de hooks | `mcp_hooks.py` dérive un plan `SessionStart` manifest/instruction/config-bound | Ajouté en M5-G ; donnée déclarative, non une commande. |
| Adapter Claude Code | `claude_code_integration.py` traduit les quatre snapshots en plan de revue cible | Ajouté en M5-H ; installation/hook exécutable explicitement refusés. |
| Installateur Claude Code | `claude_code_installer.py` applique le seul serveur attesté après confirmation | Ajouté en M5-I ; `.mcp.json` seulement, sans hook. |
| Lifecycle Core | `session_lifecycle.py` porte dossier, état local et garde hard/soft | Ajouté en M5-J ; aucun hôte ni hook. |
| Adapter lifecycle attesté | `lifecycle_adapters.py` compile/résout un plan manifest-bound et `mcp_server.py` acquitte le seul état armé du contexte hôte | Ajouté en M5-K ; fixture de preuve seulement, sans adapter installable. |
| Adapter Claude local | `claude_code_local.py` lie hooks project-local, liaison de session runtime, serveur MCP local, installateur et doctor à M5-J/K | Ajouté en M5-L ; opt-in, session locale unique, sans cloud/Pack/réseau. |
| Plan Claude cloud | `claude_code_cloud.py` lie le plan cloud au plan local et aux snapshots M5 ; provider unique préinstallé et doctor read-only. | Ajouté en M5-M.1 ; sans entry point/hook cloud, bootstrap, réseau, secret ou trust appliqué. |
| Adapter Claude cloud staged | `claude_code_cloud.py` stage un runtime project-local, résout une session cloud distincte, expose hook et serveur MCP stdio deny-by-default. | Ajouté en M5-M.2 ; sans `.claude`, `.mcp.json`, home settings/trust, réseau, setup ou preuve web live. |

## 2. Surface M5-A livrée

| Outil MCP | Entrées client bornées | Sortie persistée ou dérivée | Interdits structurels |
|---|---|---|---|
| `mmu_get_capability_catalog` | aucune | capabilities `ALLOW`, contrats, policies et schémas | shell, URL ou chemin. |
| `mmu_run_capability` | `capability_id`, `parameters` | `execution_id`, `evidence_id`, `asset_id`, `verdict`, `gate_id` | verdict, score, `stdout`, `stderr`, `exit_code`, commande ou artifact client. |
| `mmu_get_execution` | `execution_id` exact | execution persistée et résultat enregistré | inférence de succès à partir d’un texte. |
| `mmu_read_artifact` | `asset_id` exact | bytes vérifiés, hash, taille et MIME | lecture hors Asset Store. |
| `mmu_validate_evidence` | `evidence_id` exact | validation persistée `PASS` ou `FAIL` | validator client ou bypass. |
| `mmu_decide_admission` | `evidence_id`, `validation_id` exacts | admission `ADMITTED` ou refus structuré | promotion d’un non-`PASS`. |
| `mmu_evaluate_gate` | `gate_id` exact | statut dérivé des admissions persistées | gate `PASS` synthétique. |
| `mmu_acknowledge_resume` | objet `sections` exact | `{acknowledged: true}` seulement après état armé et contexte hôte attesté | session, adapter, version, hash, verdict, statut, shell, commande ou chemin client. |

La façade n’importe aucun Domain Pack. Elle n’exécute aucun subprocess, n’ouvre aucun réseau et n’utilise aucun shell. Lorsqu’un manifeste est fourni, celui-ci est recompilé et vérifié contre l’identité du store, ses migrations, ses capabilities, contrats et policies; son catalogue borne les tools. En M5-C, un `RuntimeAdapterRegistry` ne reçoit que des objets déjà instanciés par l’hôte : il refuse chemins, commandes, doublons et adapters absents, puis choisit l’objet correspondant à la capability du manifeste. Adapter direct et registry sont mutuellement exclusifs; un registry sans manifeste est refusé. Sans adapter, l’entry point générique `vmmu-mcp` refuse l’exécution : il est volontairement fail-closed.

## 3. Matrice de conformance exécutée

Le test `tests/test_mcp_stdio_verdict_transport.py` démarre `tests/mcp_verdict_fixture_server.py` comme sous-processus `stdio`, initialise une vraie `ClientSession` MCP, inspecte le catalogue et appelle les huit outils ; sans registry lifecycle, le huitième refuse fail-closed. L’adapter choisit son scénario uniquement au démarrage du serveur ; le client appelle toujours la même capability et ne reçoit aucun droit de fournir un résultat.

| Scénario produit côté serveur | Verdict transporté | Validation asset | Admission | Gate |
|---|---:|---:|---:|---:|
| Résumé `272/272` | `PASS` | `PASS` | `ADMITTED` | `PASS` |
| Résumé `271/272` | `FAIL` | `PASS` | refusée | `FAIL` |
| Prérequis absent | `SKIPPED` | `PASS` | refusée | `FAIL` |
| Timeout | `ERROR` | `PASS` | refusée | `FAIL` |
| Sortie inconnue | `ERROR` | `PASS` | refusée | `FAIL` |
| Format Wine hashé non promouvable | `UNKNOWN` | `PASS` | refusée | `FAIL` |
| Asset déclaré avec hash altéré | `PASS` | `FAIL` | refusée | `FAIL` |

Le test vérifie aussi que le schéma de `mmu_run_capability` ne déclare que `capability_id` et `parameters`. Une tentative de transmettre `parameters.verdict = "PASS"` retourne `VERA_ERROR`; elle ne crée aucune réussite ni admission implicite.

## 4. Corrections et garde-fous observés

Le SDK MCP exécute les handlers synchrones dans un thread distinct. Le Store SQLite VERA restant volontairement attaché à son thread propriétaire, les handlers de la façade sont asynchrones : ils restent sur le thread du serveur, sans désactiver le garde-fou SQLite. Ce correctif porte sur le transport ; les règles Core de persistance et de policy ne sont pas modifiées.

Les erreurs métier sont retournées sous l’enveloppe stable `{ok, operation, error}` avec le code `VERA_ERROR`. Une exception ne peut pas se convertir en verdict positif, et le client ne peut pas faire tomber le serveur pour contourner un refus.

## 5. Preuves de jalon

| Contrôle | Résultat |
|---|---|
| Rouge initial | SDK MCP absent, puis dépendance explicitement ajoutée au paquet. |
| Matrice MCP réelle | `2 passed, 7 subtests passed`. |
| Régressions ciblées Pack/Core | `5 passed, 15 subtests passed`. |
| Suite complète VERA | `404 passed, 32 subtests passed` après M5-B. |
| Frontière Core | Aucun import ARET/Pack, subprocess, shell ou réseau dans `mcp_server.py`. |
| Intégrité Git | `git diff --check` : `PASS`. |
| Packaging | Roues isolées M5-A, M5-B et M5-C construites ; `vmmu --help`, `vmmu-mcp --help` et inclusion de `mcp_manifest.py` / `mcp_adapters.py` : `PASS`. |
| Manifeste M5-B | Canonique quel que soit l’ordre des bindings, lié à l’identité projet et aux checksums de migrations; toute divergence de catalogue, policy, binding ou projet est refusée. |
| Registry M5-C | Resolution capability→adapter exacte, sans execution pendant la résolution; absence, doublon, adapter inconnu, chemin/commande ou runtime ambigu sont refusés. |
| Adapter Pack M5-D | Une capability `aret-oracle-*` est convertie en oracle du catalogue fermé; seuls `fixture` quand déclarée, référence toolkit, binaire attesté, préflight et sandbox du runner Pack peuvent participer. |
| Hôte Pack M5-D | Le manifest doit couvrir exclusivement les capabilities `ALLOW` du Pack; une capability autorisée étrangère sans adapter est refusée avant le démarrage MCP. |
| Vrai client stdio M5-D | Le client appelle l’hôte ARET, ne peut pas injecter `command`, puis atteint validation, admission et gate par le runner fermé. |
| Suite complète M5-D | `413 passed, 37 subtests passed`. |
| Instructions M5-E | Texte canonique contenant identité projet, `mcp_build_hash`, doctrine universelle et lignes capability/runner/network/timeout/adapter ; SHA-256 `instructions_hash` stable. |
| Vérification M5-E | Le serveur recompile les instructions à partir du store+manifeste et refuse objet, hash ou texte différent avant de démarrer. |
| Hôte Pack M5-E | `build_aret_mcp_runtime` attache les instructions compilées à la façade, plutôt que le texte générique par défaut. |
| Suite complète M5-E | `416 passed, 37 subtests passed`. |
| Configuration M5-F | JSON canonique `mcpServers` avec `vmmu-mcp --profile ${CLAUDE_PROJECT_DIR:-.}/<profile>` et hashes `mcp_build_hash` / `instructions_hash` en environnement descriptif. |
| Prévisualisation M5-F | Écrit seulement `<runtime>/generated/mcp.json` en création exclusive; ne touche jamais `.mcp.json`, `.claude/` ni le code métier. |
| Suite complète M5-F | `419 passed, 37 subtests passed`. |
| Plan M5-G | JSON canonique `hookPlan.SessionStart` avec `DECLARATIVE_ONLY`, `HOST_ADAPTER_REQUIRED` et source d’instructions attestées; `hook_plan_hash` stable. |
| Prévisualisation M5-G | Écrit seulement `<runtime>/generated/hooks.json` en création exclusive; ne crée aucun script, hook Claude ou fichier `.claude/`. |
| Suite complète M5-G | `422 passed, 37 subtests passed`. |
| Adapter M5-H | JSON canonique de revue avec cible `.mcp.json`, hash de contenu et `installation: REVIEW_REQUIRED`. |
| Hooks M5-H | `SessionStart` est rendu `UNTRANSLATED` avec motif explicite tant qu’aucun adapter exécutable n’est attesté. |
| Prévisualisation M5-H | Écrit seulement `<runtime>/generated/claude-code-integration.json` en création exclusive; ne touche ni `.mcp.json` ni `.claude/`. |
| Suite complète M5-H | `425 passed, 37 subtests passed`. |
| Installation M5-I | `confirm=True` requis; fusionne uniquement `mcpServers.vera-mmu-<project_id>` dans `.mcp.json`, en préservant les autres clés/serveurs. |
| Refus M5-I | Serveur VERA conflictuel, JSON non objet, `mcpServers` non objet, symlink, snapshot divergent ou confirmation absente : refus sans écriture. |
| Idempotence M5-I | Serveur déjà strictement identique : `UNCHANGED`, zéro réécriture. Sinon écriture atomique `.mcp.json` uniquement. |
| Suite complète M5-I | `429 passed, 37 subtests passed`. |
| Lifecycle Core M5-J | Dossier project/profile-bound, état runtime atomique, garde hard/soft anti-deadlock et acquittement hashé. | `438 passed, 37 subtests passed`. |
| Plan/registry M5-K | `vera-lifecycle-adapter-plan/v1` stable et manifest-bound ; adapter absent/dupliqué/version/mode divergent, plan stale/tampered ou bootstrap partiel refusés. | `22 passed, 7 subtests passed` ciblés ; suite `444 passed, 37 subtests passed`. |
| Vrai client stdio M5-K | Fixture générique fixe la session côté serveur ; `mmu_acknowledge_resume` n’expose que `sections`, relit le hash local et refuse contexte hôte absent ou sections injectées. | `PASS`; aucun Pack, hook ou hôte réel n’est utilisé. |
| Plan Claude local M5-L | Plan `vera-claude-code-local/v1` lié aux snapshots M5-B/E/F/G/H/K, hooks fixes `SessionStart`/`PreToolUse`/`PostToolUse`/compaction/`Stop`, serveur MCP local et doctor. | `7 passed` ciblés ; suite `451 passed, 37 subtests passed`. |
| Conformance M5-L réelle | Hook stdin/stdout arme la session; vrai `ClientSession` stdio appelle l’acquittement local puis PreToolUse devient autorisé. | `PASS`; aucune capability Pack n’est exécutable. |
| Installation M5-L | `confirm=True`, fusion non destructive de `.claude/settings.json`, remplacement du seul serveur VERA M5-I et état runtime attesté. | Idempotence, conflit, symlink et doctor sans écriture testés ; aucune écriture home/cloud. |
| Plan/doctor M5-M.1 | `vera-claude-code-cloud/v1`, lié aux snapshots M5-B/E/F/G/H/J/K/L ; provider `PREINSTALLED_VERA`, réseau interdit, trust preview et secrets externes seulement. | `4 passed`, suite `455 passed, 37 subtests passed`; stale/provider non admis/observation invalide refusés. `RUNTIME_READY` ne prouve pas de session cloud live. |
| Adapter cloud M5-M.2 | Staging confirmé `vera-claude-code-cloud-runtime/v1`, adapter `claude-code-cloud-v1`, hook des six événements et MCP stdio avec `DenyRuntimeAdapter`. | `2 failed` rouge puis conformance staging→hook→MCP→ack→allow et compaction réarmée ; `6 passed`, suite `457 passed, 37 subtests passed`, roue isolée avec trois entry points cloud. |

## 6. Limites et suite M5

`M5-A/B/C/D/E/F/G/H/I/J/K/L` ne prétend pas que l’entry point MCP générique puisse exécuter ARET sans configuration d’hôte : il demeure fail-closed. M5-D ajoute le premier adapter de Pack, mais son hôte reste explicitement construit avec une référence toolkit, des dépendances et un registry côté serveur. La fixture d’intégration ne sert qu’à démontrer ce **transport MCP** ; elle ne rend pas le runner de test configurable par le client.

M5-B livre `vera-mcp-manifest/v1` : une compilation canonique de l’identité de projet, des checksums de migrations, des tools, capabilities `ALLOW`, contracts, policies et bindings symboliques d’adapter. Le SHA-256 du JSON canonique est le `mcp_build_hash`; le serveur refuse un manifeste étranger, périmé, altéré ou associé à un adapter différent. M5-C livre le registry qui résout ces symboles vers des objets explicitement fournis par l’hôte, sans import dynamique ni commande. M5-D livre `AretClosedOracleMCPAdapter` et `build_aret_mcp_runtime`, tous deux dans le Pack : le premier délègue exclusivement à `run_closed_oracle`; le second refuse tout catalogue `ALLOW` que l’adapter ne couvre pas. M5-E livre `vera-mcp-instructions/v1`, M5-F `vera-mcp-integration/v1`, M5-G `vera-mcp-hooks/v1`, M5-H `vera-claude-code-integration/v1` et M5-I l’unique write-path `.mcp.json`. M5-I recompile les cinq snapshots, exige confirmation explicite et fusionne seulement le serveur attesté; il refuse les symlinks/conflits et n’installe aucun hook. M5-J apporte le Lifecycle Core; M5-K lie un plan/registry lifecycle au manifeste et ajoute l’acquittement MCP contextualisé sans accepter session, adapter ou hash client. M5-L livre l’adapter Claude Code **local** : hooks project-local fixes, liaison d’une session active par projet, serveur MCP local limité à l’acquittement, installation confirmée et doctor sans effet de bord. M5-M.1 ajoute le plan `vera-claude-code-cloud/v1` et son doctor préinstallé : il lie les snapshots locaux/cloud, refuse le bootstrap réseau et constate un fait de trust sans le lire ni l’appliquer. M5-M.2 ajoute le staging runtime-confined, l’adapter session cloud, le hook des six événements et le serveur MCP cloud deny-by-default, avec bindings refabriqués depuis le catalogue ALLOW plutôt que fournis par le client. La configuration host `.claude`/`.mcp.json`, le trust home user-scope, la connexion prouvée dans Claude Code web, la roue/bootstrap, le support multi-session et chaque autre hôte restent des lots distincts. M6 fournira ensuite CLI, doctor et expérience opératoire. Aucune capacité cloud web live, multi-session ou multi-hôte ne peut être déduite de M5-A/B/C/D/E/F/G/H/I/J/K/L/M.1/M.2.

## Références

[1]: ../../../src/vera_mmu/mcp_server.py "Façade MCP universelle fermée"
[2]: ../../../tests/test_mcp_stdio_verdict_transport.py "Conformance stdio par client MCP réel"
[3]: ../../../tests/mcp_verdict_fixture_server.py "Adapter de scénario serveur réservé aux tests"
[4]: ../../../src/vera_mmu/domain_packs/aret/closed_oracle_runner.py "Runner Pack ARET fermé"
[5]: ../../../src/vera_mmu/validators.py "Validation `EVIDENCE_ASSET`"
[6]: ../../../src/vera_mmu/admission.py "Admission policy-gated"
[7]: ../../../src/vera_mmu/gates.py "Évaluation de gate dérivée"
[8]: ../../../src/vera_mmu/mcp_manifest.py "Compilation et vérification de manifeste MCP"
[9]: ../../../tests/test_mcp_manifest.py "Conformance I007/I008/I011/I012 du manifeste"
[10]: ../../../src/vera_mmu/mcp_adapters.py "Registry d’adapters serveur fermé"
[11]: ../../../tests/test_mcp_adapter_registry.py "Conformance I007/I008/I012/I014 du registry"
[12]: ../../../src/vera_mmu/domain_packs/aret/mcp_adapter.py "Adapter MCP du Pack ARET"
[13]: ../../../src/vera_mmu/domain_packs/aret/mcp_runtime.py "Assemblage manifest-bound du runtime ARET"
[14]: ../../../tests/test_aret_mcp_stdio_runtime.py "Conformance MCP stdio de l’adapter Pack"
[15]: ../../../src/vera_mmu/mcp_instructions.py "Compilation d’instructions MCP manifest-bound"
[16]: ../../../tests/test_mcp_instructions.py "Conformance de stabilité et de liaison des instructions"
[17]: ../../../src/vera_mmu/mcp_integration.py "Prévisualisation d’intégration MCP manifest-bound"
[18]: ../../../tests/test_mcp_integration_config.py "Conformance JSON, stabilité et confinement de configuration"
[19]: ../../../src/vera_mmu/mcp_hooks.py "Plan de hooks MCP déclaratif et manifest-bound"
[20]: ../../../tests/test_mcp_hook_plan.py "Conformance de plan SessionStart non exécutable"
[21]: ../../../src/vera_mmu/claude_code_integration.py "Adapter de revue Claude Code attesté"
[22]: ../../../tests/test_claude_code_integration_adapter.py "Conformance de traduction et refus Claude Code"
[23]: ../../../src/vera_mmu/claude_code_installer.py "Installateur MCP Claude Code opt-in et attesté"
[24]: ../../../tests/test_claude_code_mcp_installer.py "Conformance de fusion, idempotence et refus d’installation"
[25]: ../../../src/vera_mmu/claude_code_local.py "Adapter Claude Code local attesté"
[26]: ../../../tests/test_claude_code_local_adapter.py "Plan, hooks, installation et doctor Claude local"
[27]: ../../../tests/test_claude_code_local_mcp_runtime.py "Conformance hook local vers MCP stdio réel"
[28]: ../../../src/vera_mmu/claude_code_cloud.py "Plan cloud préinstallé et doctor observationnel"
[29]: ../../../tests/test_claude_code_cloud_plan.py "Conformance plan/doctor cloud M5-M.1"
